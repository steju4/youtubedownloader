from flask import Flask, request, Response, stream_with_context
import yt_dlp
import requests
import re

app = Flask(__name__)

# --- Frontend (HTML/CSS) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Julian's Video Downloader</title>
    <style>
        body { font-family: sans-serif; background-color: #1a1a1a; color: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .container { background-color: #2d2d2d; padding: 2rem; border-radius: 15px; text-align: center; width: 90%; max-width: 400px; }
        input { width: 100%; padding: 10px; margin-bottom: 1rem; border-radius: 5px; border: none; }
        button { background-color: #0066cc; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold;}
        button:hover { background-color: #0052a3; }
        .info { font-size: 0.8rem; color: #aaa; margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Downloader (No-Auth)</h1>
        <form action="/api/download" method="get">
            <input type="text" name="url" placeholder="YouTube Link..." required>
            <button type="submit">Download</button>
        </form>
        <p class="info">Versucht: Embedded-Trick -> Invidious Fallback</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_PAGE

def get_video_id(url):
    """Extrahiert die Video-ID aus einem YouTube-Link"""
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return video_id_match.group(1) if video_id_match else None

def get_invidious_stream(video_id):
    """Fallback: Fragt eine öffentliche Invidious-Instanz nach dem Link"""
    # Liste von Instanzen, falls eine down ist
    instances = [
        "https://inv.tux.pizza",
        "https://invidious.drgns.space",
        "https://vid.puffyan.us"
    ]
    
    for instance in instances:
        try:
            # Wir nutzen die API der Instanz
            api_url = f"{instance}/api/v1/videos/{video_id}"
            resp = requests.get(api_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                # Wir suchen nach mp4 Streams
                for stream in data.get('formatStreams', []):
                    if stream.get('container') == 'mp4':
                        return stream.get('url')
        except:
            continue
    return None

@app.route('/api/download')
def download():
    video_url = request.args.get('url')
    if not video_url:
        return "Keine URL!", 400

    direct_url = None
    
    # --- STRATEGIE 1: yt-dlp mit "Embedded Player" Tarnung ---
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'noplaylist': True,
            # Dieser Trick umgeht oft die Bot-Erkennung:
            'extractor_args': {
                'youtube': {
                    'player_client': ['web_embedded', 'mediaconnect']
                }
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            print("Erfolg mit yt-dlp!")
            
    except Exception as e:
        print(f"yt-dlp blockiert: {e}")
        # --- STRATEGIE 2: Invidious API Fallback ---
        print("Versuche Invidious Fallback...")
        vid_id = get_video_id(video_url)
        if vid_id:
            direct_url = get_invidious_stream(vid_id)

    if not direct_url:
        return "Fehler: YouTube blockiert Vercel komplett und keine Invidious-Instanz hat geantwortet.", 500

    # Stream weiterleiten
    try:
        req = requests.get(direct_url, stream=True, timeout=10)
        
        def generate():
            for chunk in req.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

        return Response(stream_with_context(generate()), 
                        content_type='video/mp4',
                        headers={"Content-Disposition": "attachment; filename=video.mp4"})
    except Exception as e:
        return f"Stream-Fehler: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)