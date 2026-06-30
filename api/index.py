from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Julian's Video Downloader</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background-color: #121212; color: #eee; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 1rem; }
        .container { background-color: #1e1e1e; padding: 2.5rem; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); text-align: center; width: 100%; max-width: 500px; border: 1px solid #333; }
        h1 { margin: 0 0 0.4rem; font-size: 1.8rem; color: #fff; }
        p.subtitle { color: #888; margin: 0 0 2rem; font-size: 0.9rem; }
        input { width: 100%; padding: 14px; margin-bottom: 1rem; border-radius: 8px; border: 1px solid #333; background-color: #2a2a2a; color: white; font-size: 1rem; }
        input:focus { outline: none; border-color: #4a90e2; }
        button#dlBtn { background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: 600; font-size: 1rem; transition: all 0.2s; }
        button#dlBtn:hover { opacity: 0.9; transform: translateY(-1px); }
        button#dlBtn:disabled { background: #444; cursor: not-allowed; transform: none; }
        #dlLink { display: none; margin-top: 1rem; padding: 13px; background: linear-gradient(135deg, #27ae60 0%, #1e8449 100%); color: white; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.95rem; width: 100%; }
        #dlLink:hover { opacity: 0.9; }
        .status { margin-top: 1.2rem; font-size: 0.85rem; min-height: 20px; color: #888; }
        #debugLog { margin-top: 1rem; font-size: 0.68rem; color: #555; text-align: left; display: none; max-height: 130px; overflow-y: auto; background: #111; padding: 8px; border-radius: 4px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Video Downloader</h1>
        <p class="subtitle">YouTube &middot; TikTok &middot; und mehr</p>

        <input type="text" id="urlInput" placeholder="Link einfügen (YouTube, TikTok ...)" />
        <button id="dlBtn" onclick="startDownload()">Download Starten</button>
        <a id="dlLink" target="_blank">&#x1F4E5; Download-Link &mdash; hier klicken</a>
        <p class="status" id="statusText">Bereit.</p>
        <div id="debugLog"></div>
    </div>

    <script>
    // Piped-Instanzen als Fallback (YouTube-only, CORS-aktiviert)
    const PIPED_INSTANCES = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.adminforge.de",
        "https://api.piped.yt",
        "https://pipedapi.drgns.space",
        "https://pipedapi.owo.si",
        "https://piped-api.privacy.com.de",
    ];

    function log(msg) {
        console.log(msg);
        const d = document.getElementById('debugLog');
        d.style.display = 'block';
        d.innerHTML += '<div>' + new Date().toTimeString().slice(0,8) + ' ' + msg + '</div>';
        d.scrollTop = d.scrollHeight;
    }

    function setStatus(msg, color) {
        const s = document.getElementById('statusText');
        s.style.color = color || '#888';
        s.textContent = msg;
    }

    function showDownloadLink(url, filename) {
        const a = document.getElementById('dlLink');
        a.href = url;
        a.download = filename || '';
        a.style.display = 'block';
    }

    function extractYoutubeId(url) {
        const patterns = [
            /[?&]v=([a-zA-Z0-9_-]{11})/,
            /youtu\.be\/([a-zA-Z0-9_-]{11})/,
            /\/shorts\/([a-zA-Z0-9_-]{11})/,
            /\/embed\/([a-zA-Z0-9_-]{11})/,
        ];
        for (const p of patterns) {
            const m = url.match(p);
            if (m) return m[1];
        }
        return null;
    }

    // Strategie 1: Backend-Endpunkt nutzt yt-dlp serverseitig
    async function tryBackend(url) {
        log("Strategie 1: Backend (yt-dlp) ...");
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), 25000);
        try {
            const resp = await fetch('/api/get-url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
                signal: ctrl.signal,
            });
            clearTimeout(timer);
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.error || 'HTTP ' + resp.status);
            }
            const data = await resp.json();
            if (!data.url) throw new Error('Keine URL in Backend-Antwort');
            log('Backend OK: ' + (data.quality || '?') + ' ' + (data.ext || ''));
            return data;
        } catch (e) {
            clearTimeout(timer);
            throw e;
        }
    }

    // Strategie 2: Piped API direkt aus dem Browser (nur YouTube)
    async function tryPiped(url) {
        const videoId = extractYoutubeId(url);
        if (!videoId) {
            log("Kein YouTube-Link – Piped übersprungen.");
            return null;
        }
        log("Strategie 2: Piped API (Video-ID: " + videoId + ") ...");

        for (const base of PIPED_INSTANCES) {
            try {
                log("Versuche " + base);
                const ctrl = new AbortController();
                const timer = setTimeout(() => ctrl.abort(), 10000);
                const resp = await fetch(base + '/streams/' + videoId, { signal: ctrl.signal });
                clearTimeout(timer);

                if (!resp.ok) { log("HTTP " + resp.status + " bei " + base); continue; }

                const data = await resp.json();
                const streams = (data.videoStreams || []).filter(s => s.url);

                // Kombinierte Streams bevorzugen (videoOnly === false)
                const combined = streams.filter(s => s.videoOnly === false);
                const pool = combined.length > 0 ? combined : streams;

                if (pool.length === 0) { log("Keine Streams bei " + base); continue; }

                pool.sort((a, b) => (parseInt(b.quality) || 0) - (parseInt(a.quality) || 0));
                const best = pool[0];
                log("Piped OK: " + best.quality + (combined.length === 0 ? " (nur Video, kein Ton)" : ""));

                return {
                    url: best.url,
                    title: data.title || 'video',
                    ext: 'mp4',
                    quality: best.quality || '?',
                    audioWarning: combined.length === 0,
                };
            } catch (e) {
                log("Fehler bei " + base + ": " + e.message);
            }
        }
        return null;
    }

    async function startDownload() {
        const url = document.getElementById('urlInput').value.trim();
        const btn = document.getElementById('dlBtn');
        document.getElementById('debugLog').innerHTML = '';
        document.getElementById('dlLink').style.display = 'none';

        if (!url) { setStatus("Bitte Link eingeben!", '#ff5555'); return; }

        btn.disabled = true;
        btn.textContent = "Suche...";
        setStatus("Verarbeite Link ...", '#aaa');

        let result = null;

        // --- Strategie 1: Backend ---
        setStatus("Schritt 1/2: Backend (yt-dlp) ...", '#aaa');
        try {
            result = await tryBackend(url);
        } catch (e) {
            log("Backend fehlgeschlagen: " + e.message);
        }

        // --- Strategie 2: Piped ---
        if (!result) {
            setStatus("Schritt 2/2: Piped API ...", '#aaa');
            try {
                result = await tryPiped(url);
            } catch (e) {
                log("Piped fehlgeschlagen: " + e.message);
            }
        }

        if (result && result.url) {
            const filename = (result.title || 'video').replace(/[<>:"/\\\\|?*]/g, '_') + '.' + (result.ext || 'mp4');
            const warn = result.audioWarning ? " (kein Ton – nur Video verfügbar)" : "";
            setStatus("✓ Link gefunden!" + warn + " Download wurde gestartet.", '#55ff55');
            showDownloadLink(result.url, filename);
            // Automatisch öffnen
            const a = document.createElement('a');
            a.href = result.url;
            a.target = '_blank';
            a.rel = 'noopener';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } else {
            setStatus("Fehler: Kein Download-Link gefunden. Siehe Log.", '#ff5555');
        }

        btn.disabled = false;
        btn.textContent = "Download Starten";
    }

    // Enter-Taste
    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('urlInput').addEventListener('keydown', e => {
            if (e.key === 'Enter') startDownload();
        });
    });
    </script>
</body>
</html>
"""


@app.route('/api/get-url', methods=['POST', 'OPTIONS'])
def get_download_url():
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        import yt_dlp

        ydl_opts = {
            # Bevorzuge kombinierte Streams (Video+Audio in einer Datei)
            'format': (
                'best[height<=1080][vcodec!=none][acodec!=none]'
                '/best[vcodec!=none][acodec!=none]'
                '/best[height<=720]'
                '/best'
            ),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'socket_timeout': 12,
            'extractor_args': {
                'youtube': {'player_client': ['web', 'android']},
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return jsonify({'error': 'Keine Video-Informationen gefunden'}), 500

        title = info.get('title', 'video')
        download_url = None
        ext = 'mp4'
        quality = '?'

        # Wenn yt-dlp mehrere Formate gewählt hat (Merge nötig) → nimm Video-Teil
        if info.get('requested_formats'):
            rf = info['requested_formats'][0]
            download_url = rf.get('url')
            ext = rf.get('ext', 'mp4')
            quality = str(rf.get('height', '?')) + 'p'

        # Einzelnes Format direkt verfügbar
        elif info.get('url'):
            download_url = info['url']
            ext = info.get('ext', 'mp4')
            quality = str(info.get('height', '?')) + 'p'

        # Formate-Liste durchsuchen
        elif info.get('formats'):
            for fmt in reversed(info['formats']):
                if (fmt.get('vcodec', 'none') != 'none'
                        and fmt.get('acodec', 'none') != 'none'
                        and fmt.get('url')):
                    download_url = fmt['url']
                    ext = fmt.get('ext', 'mp4')
                    quality = str(fmt.get('height', '?')) + 'p'
                    break
            # Fallback: beliebige URL
            if not download_url:
                for fmt in reversed(info['formats']):
                    if fmt.get('url'):
                        download_url = fmt['url']
                        ext = fmt.get('ext', 'mp4')
                        quality = str(fmt.get('height', '?')) + 'p'
                        break

        if not download_url:
            return jsonify({'error': 'Keine Download-URL gefunden'}), 500

        return jsonify({
            'url': download_url,
            'title': title,
            'ext': ext,
            'quality': quality,
        })

    except Exception as exc:
        msg = str(exc)
        if len(msg) > 400:
            msg = msg[:400] + '…'
        return jsonify({'error': msg}), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    return HTML_PAGE


if __name__ == '__main__':
    app.run(debug=True)
