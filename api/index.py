from flask import Flask, request, Response, stream_with_context
import yt_dlp
import requests

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
        button { background-color: #cc0000; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%; }
        button:hover { background-color: #ff3333; }
        .error { color: #ff6b6b; margin-top: 1rem; font-size: 0.9rem; word-break: break-word; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📺 Downloader V3 (Anti-Bot)</h1>
        <form action="/api/download" method="get">
            <input type="text" name="url" placeholder="YouTube Link..." required>
            <button type="submit">Laden</button>
        </form>
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
        return "Keine URL!", 400

    try:
        # TRICK 1: Wir geben uns als Android-App aus.
        # Das umgeht oft die "Sign in"-Sperre für Cloud-IPs.
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios']
                }
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            # TRICK 2: Wir müssen die Header (User-Agent etc.) von yt-dlp übernehmen!
            # Sonst blockt YouTube den Download-Request von 'requests'
            dl_headers = info.get('http_headers')

        if not direct_url:
            return "Fehler: Kein Link gefunden.", 500

        # Stream mit den richtigen Headern anfragen
        req = requests.get(direct_url, headers=dl_headers, stream=True)

        def generate():
            for chunk in req.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

        return Response(stream_with_context(generate()), 
                        content_type='video/mp4',
                        headers={"Content-Disposition": "attachment; filename=video.mp4"})

    except Exception as e:
        return f"""
        <div style="color: red; font-family: monospace;">
            <h2>Fehler!</h2>
            <p>YouTube hat den Server blockiert. Das passiert leider oft bei Cloud-Hostern.</p>
            <p>Details: {str(e)}</p>
            <p><strong>Lösung (Plan B):</strong> Du müsstest Cookies exportieren (siehe Chat).</p>
        </div>
        """, 500

if __name__ == '__main__':
    app.run(debug=True)