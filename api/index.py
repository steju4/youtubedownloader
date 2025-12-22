from flask import Flask

app = Flask(__name__)

# --- Frontend mit Client-Side Logic ---
# Wir verschieben die Logik in den Browser (JavaScript).
# Dadurch kommt die Anfrage von DEINER IP (die nicht blockiert ist),
# statt von der blockierten Vercel-Server-IP.

HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Julian's Video Downloader</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #121212; color: #eee; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .container { background-color: #1e1e1e; padding: 2.5rem; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); text-align: center; width: 90%; max-width: 450px; border: 1px solid #333; }
        h1 { margin-bottom: 0.5rem; font-size: 1.8rem; color: #fff; }
        p.subtitle { color: #888; margin-bottom: 2rem; font-size: 0.9rem; }
        input { width: 100%; padding: 14px; margin-bottom: 1rem; border-radius: 8px; border: 1px solid #333; background-color: #2a2a2a; color: white; box-sizing: border-box; font-size: 1rem; }
        input:focus { outline: none; border-color: #4a90e2; }
        button { background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); color: white; border: none; padding: 14px 28px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: 600; font-size: 1rem; transition: all 0.2s; }
        button:hover { opacity: 0.9; transform: translateY(-1px); }
        button:disabled { background: #444; cursor: not-allowed; transform: none; }
        .status { margin-top: 1.5rem; font-size: 0.85rem; min-height: 20px; transition: color 0.3s; }
        .loader { display: inline-block; width: 12px; height: 12px; border: 2px solid #fff; border-radius: 50%; border-top-color: transparent; animation: spin 1s linear infinite; margin-right: 8px; vertical-align: middle; display: none;}
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Video Downloader</h1>
        <p class="subtitle">Client-Side Processing (Unblocked)</p>
        
        <input type="text" id="urlInput" placeholder="Link einfügen (YouTube, TikTok...)" required>
        <button id="dlBtn" onclick="startDownload()">Download Starten</button>
        
        <p class="status" id="statusText">Bereit.</p>
    </div>

    <script>
        async function startDownload() {
            const url = document.getElementById('urlInput').value;
            const btn = document.getElementById('dlBtn');
            const status = document.getElementById('statusText');
            
            if (!url) {
                status.style.color = '#ff5555';
                status.innerText = "Bitte Link eingeben!";
                return;
            }

            // UI Reset
            btn.disabled = true;
            btn.innerText = "Suche Link...";
            status.style.color = '#888';
            status.innerText = "Frage Cobalt API (via Browser)...";

            // Liste von Instanzen, die wir client-seitig abfragen
            const instances = [
                "https://cobalt-backend.canine.tools",
                "https://cobalt-api.clxxped.lol",
                "https://nuko-c.meowing.de",
                "https://capi.3kh0.net",
                "https://api.cobalt.tools/api/json",
                "https://cobalt.api.wuk.sh/api/json",
                "https://co.wuk.sh/api/json"
            ];

            let success = false;

            for (const api_url of instances) {
                try {
                    console.log("Versuche:", api_url);
                    
                    const response = await fetch(api_url, {
                        method: "POST",
                        headers: {
                            "Accept": "application/json",
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            url: url,
                            // New API (v10+)
                            videoQuality: "1080",
                            audioFormat: "mp3",
                            filenameStyle: "basic",
                            youtubeVideoCodec: "h264",
                            // Old API (Legacy fallback)
                            vQuality: "1080",
                            aFormat: "mp3",
                            filenamePattern: "basic",
                            vCodec: "h264"
                        })
                    });

                    const data = await response.json();

                    if (data.url) {
                        status.style.color = '#55ff55';
                        status.innerText = "Link gefunden! Download startet...";
                        
                        // Direkter Download-Start im Browser
                        window.location.href = data.url;
                        success = true;
                        break;
                    } 
                    else if (data.picker) {
                        // Falls es mehrere Versionen gibt, nimm die erste
                        status.style.color = '#55ff55';
                        status.innerText = "Link gefunden! Download startet...";
                        window.location.href = data.picker[0].url;
                        success = true;
                        break;
                    }
                } catch (e) {
                    console.warn("Fehler bei Instanz:", api_url, e);
                    // Weiter zur nächsten Instanz
                }
            }

            if (!success) {
                status.style.color = '#ff5555';
                status.innerText = "Fehler: Konnte Video nicht finden (CORS/Block).";
            }
            
            btn.disabled = false;
            btn.innerText = "Download Starten";
        }
    </script>
</body>
</html>
"""

# Da wir Flask nur noch zum Ausliefern der HTML brauchen,
# fangen wir einfach ALLE Pfade ab und geben immer die Page zurück.
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    return HTML_PAGE

if __name__ == '__main__':
    app.run(debug=True)