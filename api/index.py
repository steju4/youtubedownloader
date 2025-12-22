from flask import Flask, request, redirect
import requests
import json

app = Flask(__name__)

# --- Frontend ---
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
        input { width: 100%; padding: 14px; margin-bottom: 1rem; border-radius: 8px; border: 1px solid #333; background-color: #2a2a2a; color: white; box-sizing: border-box; font-size: 1rem; transition: border-color 0.2s; }
        input:focus { outline: none; border-color: #666; }
        button { background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%); color: white; border: none; padding: 14px 28px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: 600; font-size: 1rem; transition: transform 0.1s, opacity 0.2s; }
        button:hover { opacity: 0.9; transform: translateY(-1px); }
        .status { margin-top: 1.5rem; font-size: 0.85rem; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Video Downloader</h1>
        <p class="subtitle">Powered by Cobalt API (No Auth)</p>
        <form action="/api/download" method="get">
            <input type="text" name="url" placeholder="Link einfügen (YouTube, TikTok, Instagram...)" required>
            <button type="submit">Download Starten</button>
        </form>
        <p class="status">Umgeht Vercel-Timeouts durch Redirect 🚀</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_PAGE

@app.route('/api/download')
def download():
    video_url = request.args.get('url')
    if not video_url:
        return "Keine URL angegeben!", 400

    # Liste von Cobalt-Instanzen (falls eine down ist, probieren wir die nächste)
    # Cobalt ist ein Service, der genau für 'No-Auth' Downloads gemacht ist.
    instances = [
        "https://api.cobalt.tools/api/json",
        "https://cobalt.api.wuk.sh/api/json",
        "https://co.wuk.sh/api/json"
    ]

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    payload = {
        "url": video_url,
        "vCodec": "h264",
        "vQuality": "1080",
        "aFormat": "mp3",
        "filenamePattern": "basic"
    }

    for api_url in instances:
        try:
            print(f"Versuche Instanz: {api_url}")
            resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Cobalt gibt uns verschiedene Status zurück
                if data.get('status') == 'error':
                    print(f"API Fehler: {data.get('text')}")
                    continue # Nächste Instanz probieren
                
                download_link = data.get('url')
                
                if download_link:
                    # DER TRICK: Wir leiten den Browser direkt zum Download-Server um.
                    # Vercel ist damit raus aus dem Datentransfer -> Kein Timeout!
                    return redirect(download_link, code=302)
                
                # Manchmal gibt es einen 'picker' (mehrere Qualitäten)
                if data.get('picker'):
                    return redirect(data['picker'][0]['url'], code=302)
                    
        except Exception as e:
            print(f"Fehler bei {api_url}: {e}")
            continue

    return """
    <div style="font-family: sans-serif; text-align: center; color: #333; margin-top: 50px;">
        <h2>Entschuldigung! 😓</h2>
        <p>Alle öffentlichen Downloader-APIs sind gerade überlastet oder blockieren Vercel.</p>
        <p>Versuch es in ein paar Minuten nochmal.</p>
    </div>
    """, 502

if __name__ == '__main__':
    app.run(debug=True)