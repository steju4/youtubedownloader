from flask import Flask, request, jsonify, make_response
import re
import concurrent.futures
import requests as http

app = Flask(__name__)

# ── Piped instances (server-side, no CORS issues) ─────────────────────────────
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.adminforge.de",
    "https://api.piped.yt",
    "https://pipedapi.drgns.space",
    "https://pipedapi.owo.si",
    "https://piped-api.privacy.com.de",
]

# ── Invidious instances (server-side, combined video+audio streams) ────────────
INVIDIOUS_INSTANCES = [
    "https://inv.tux.pizza",
    "https://invidious.privacyredirect.com",
    "https://yt.cdaut.de",
    "https://invidious.nerdvpn.de",
    "https://inv.nadeko.net",
]

HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Julian's Video Downloader</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #121212; color: #eee;
               display: flex; align-items: center; justify-content: center;
               min-height: 100vh; margin: 0; padding: 1rem; }
        .container { background: #1e1e1e; padding: 2.5rem; border-radius: 12px;
                     box-shadow: 0 8px 32px rgba(0,0,0,.4); text-align: center;
                     width: 100%; max-width: 500px; border: 1px solid #333; }
        h1 { margin: 0 0 .4rem; font-size: 1.8rem; color: #fff; }
        p.sub { color: #888; margin: 0 0 2rem; font-size: .9rem; }
        input { width: 100%; padding: 14px; margin-bottom: 1rem; border-radius: 8px;
                border: 1px solid #333; background: #2a2a2a; color: #fff; font-size: 1rem; }
        input:focus { outline: none; border-color: #4a90e2; }
        #dlBtn { background: linear-gradient(135deg,#4a90e2,#357abd); color: #fff;
                 border: none; padding: 14px; border-radius: 8px; cursor: pointer;
                 width: 100%; font-weight: 600; font-size: 1rem; transition: .2s; }
        #dlBtn:hover { opacity: .9; transform: translateY(-1px); }
        #dlBtn:disabled { background: #444; cursor: not-allowed; transform: none; }
        #dlLink { display: none; margin-top: 1rem; padding: 13px;
                  background: linear-gradient(135deg,#27ae60,#1e8449); color: #fff;
                  border-radius: 8px; text-decoration: none; font-weight: 600;
                  font-size: .95rem; width: 100%; }
        #dlLink:hover { opacity: .9; }
        .status { margin-top: 1.2rem; font-size: .85rem; min-height: 20px; color: #888; }
        #dbg { margin-top: 1rem; font-size: .68rem; color: #555; text-align: left;
               display: none; max-height: 140px; overflow-y: auto; background: #111;
               padding: 8px; border-radius: 4px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Video Downloader</h1>
        <p class="sub">YouTube &middot; TikTok &middot; und mehr</p>
        <input type="text" id="url" placeholder="Link einf&uuml;gen (YouTube, TikTok ...)"/>
        <button id="dlBtn" onclick="go()">Download Starten</button>
        <a id="dlLink" target="_blank">&#x1F4E5; Download-Link &mdash; hier klicken</a>
        <p class="status" id="st">Bereit.</p>
        <div id="dbg"></div>
    </div>
<script>
let _ticker;

function log(m) {
    const d = document.getElementById('dbg');
    d.style.display = 'block';
    d.innerHTML += '<div>' + new Date().toTimeString().slice(0,8) + ' ' + m + '</div>';
    d.scrollTop = d.scrollHeight;
}

function st(msg, color) {
    document.getElementById('st').style.color = color || '#888';
    document.getElementById('st').textContent = msg;
}

function startTicker(base) {
    let i = 0;
    _ticker = setInterval(() => { st(base + '.'.repeat((i++ % 3) + 1), '#aaa'); }, 600);
}

function stopTicker() { clearInterval(_ticker); }

async function go() {
    const url = document.getElementById('url').value.trim();
    const btn = document.getElementById('dlBtn');
    document.getElementById('dbg').innerHTML = '';
    document.getElementById('dlLink').style.display = 'none';
    if (!url) { st('Bitte Link eingeben!', '#f55'); return; }

    btn.disabled = true;
    btn.textContent = 'Suche…';
    startTicker('Suche Download-Link');
    log('URL: ' + url);

    try {
        const ctrl = new AbortController();
        setTimeout(() => ctrl.abort(), 55000);

        const resp = await fetch('/api/get-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
            signal: ctrl.signal,
        });

        stopTicker();
        const data = await resp.json();

        if (!resp.ok || !data.url) {
            log('Fehler: ' + (data.error || 'Unbekannt'));
            st('Fehler: ' + (data.error || 'Kein Download-Link gefunden.').slice(0, 120), '#f55');
        } else {
            const name = (data.title || 'video').replace(/[<>:"/\\\\|?*]/g, '_')
                       + '.' + (data.ext || 'mp4');
            const src = data.source ? ' [' + data.source + ']' : '';
            const warn = data.audioWarning ? ' ⚠️ kein Ton' : '';
            log('OK: ' + data.quality + src + warn);
            st('✓ Gefunden!' + warn + ' Download gestartet.', '#5f5');

            const a = document.getElementById('dlLink');
            a.href = data.url; a.download = name; a.style.display = 'block';

            const tmp = document.createElement('a');
            tmp.href = data.url; tmp.target = '_blank'; tmp.rel = 'noopener';
            document.body.appendChild(tmp); tmp.click(); document.body.removeChild(tmp);
        }
    } catch (e) {
        stopTicker();
        log('Fehler: ' + e.message);
        st('Fehler: ' + e.message.slice(0, 100), '#f55');
    }

    btn.disabled = false; btn.textContent = 'Download Starten';
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('url').addEventListener('keydown', e => {
        if (e.key === 'Enter') go();
    });
});
</script>
</body>
</html>
"""


def extract_youtube_id(url):
    for pat in [r'[?&]v=([a-zA-Z0-9_-]{11})', r'youtu\.be/([a-zA-Z0-9_-]{11})',
                r'/shorts/([a-zA-Z0-9_-]{11})', r'/embed/([a-zA-Z0-9_-]{11})']:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def _best_url_from_info(info):
    """Extract (url, ext, quality) from a yt-dlp info dict."""
    if info.get('requested_formats'):
        rf = info['requested_formats'][0]
        return rf.get('url'), rf.get('ext', 'mp4'), str(rf.get('height', '?')) + 'p'
    if info.get('url'):
        return info['url'], info.get('ext', 'mp4'), str(info.get('height', '?')) + 'p'
    for fmt in reversed(info.get('formats', [])):
        if fmt.get('vcodec', 'none') != 'none' and fmt.get('acodec', 'none') != 'none' and fmt.get('url'):
            return fmt['url'], fmt.get('ext', 'mp4'), str(fmt.get('height', '?')) + 'p'
    for fmt in reversed(info.get('formats', [])):
        if fmt.get('url'):
            return fmt['url'], fmt.get('ext', 'mp4'), str(fmt.get('height', '?')) + 'p'
    return None, 'mp4', '?'


def try_ytdlp(url):
    """
    Use yt-dlp for non-YouTube URLs (TikTok, Twitter, etc.) and as a best-effort
    attempt for YouTube with the android_vr client.
    """
    import yt_dlp

    # Try android_vr first (current yt-dlp default, works for many non-YT platforms)
    # then tv as a secondary attempt.
    for client in ['android_vr', 'tv']:
        try:
            opts = {
                'format': (
                    'best[vcodec!=none][acodec!=none]'
                    '/best[height<=720][vcodec!=none][acodec!=none]'
                    '/best'
                ),
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'socket_timeout': 8,
                'extractor_args': {'youtube': {'player_client': [client]}},
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                continue
            dl_url, ext, quality = _best_url_from_info(info)
            if dl_url:
                return {
                    'url': dl_url,
                    'title': info.get('title', 'video'),
                    'ext': ext,
                    'quality': quality,
                    'source': f'yt-dlp/{client}',
                }
        except Exception as e:
            msg = str(e)
            # Bot-detection is a hard stop for YouTube – skip remaining clients
            if 'Sign in' in msg or 'bot' in msg.lower() or 'LOGIN_REQUIRED' in msg:
                raise RuntimeError('YouTube bot-detection: ' + msg[:120])
            # For other platforms keep trying
            continue
    return None


def try_piped(video_id):
    """Server-side Piped API call – bypasses browser CORS restrictions."""
    for base in PIPED_INSTANCES:
        try:
            r = http.get(f'{base}/streams/{video_id}', timeout=7)
            if not r.ok:
                continue
            data = r.json()
            streams = [s for s in (data.get('videoStreams') or []) if s.get('url')]
            if not streams:
                continue

            combined = [s for s in streams if s.get('videoOnly') is False]
            pool = combined if combined else streams

            def _q(s):
                q = s.get('quality', '0')
                return int(q.replace('p', '')) if q.replace('p', '').isdigit() else 0

            pool.sort(key=_q, reverse=True)
            best = pool[0]
            return {
                'url': best['url'],
                'title': data.get('title', 'video'),
                'ext': 'mp4',
                'quality': best.get('quality', '?'),
                'source': 'piped',
                'audioWarning': not combined,
            }
        except Exception:
            continue
    return None


def try_invidious(video_id):
    """Server-side Invidious API – returns combined video+audio formatStreams."""
    for base in INVIDIOUS_INSTANCES:
        try:
            r = http.get(
                f'{base}/api/v1/videos/{video_id}',
                params={'fields': 'formatStreams,title'},
                timeout=7,
            )
            if not r.ok:
                continue
            data = r.json()
            streams = data.get('formatStreams') or []
            if not streams:
                continue

            def _res(s):
                res = s.get('resolution', '0p')
                return int(res.replace('p', '')) if res.replace('p', '').isdigit() else 0

            streams.sort(key=_res, reverse=True)
            best = streams[0]
            return {
                'url': best['url'],
                'title': data.get('title', 'video'),
                'ext': 'mp4',
                'quality': best.get('qualityLabel', best.get('resolution', '?')),
                'source': 'invidious',
            }
        except Exception:
            continue
    return None


@app.route('/api/get-url', methods=['POST', 'OPTIONS'])
def get_download_url():
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    body = request.get_json(silent=True) or {}
    url = body.get('url', '').strip()
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    video_id = extract_youtube_id(url)
    errors = []

    # Run all applicable strategies in parallel; return on first success
    tasks = {'ytdlp': (try_ytdlp, (url,))}
    if video_id:
        tasks['piped'] = (try_piped, (video_id,))
        tasks['invidious'] = (try_invidious, (video_id,))

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        fmap = {pool.submit(fn, *args): name for name, (fn, args) in tasks.items()}
        try:
            for fut in concurrent.futures.as_completed(fmap, timeout=28):
                name = fmap[fut]
                try:
                    result = fut.result()
                    if result:
                        return jsonify(result)
                    errors.append(f'{name}: no result')
                except Exception as exc:
                    errors.append(f'{name}: {str(exc)[:120]}')
        except concurrent.futures.TimeoutError:
            errors.append('timeout after 28s')

    return jsonify({'error': ' | '.join(errors) or 'All strategies failed'}), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    return HTML_PAGE


if __name__ == '__main__':
    app.run(debug=True)
