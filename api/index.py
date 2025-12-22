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
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1a1a1a;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: #2d2d2d;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            text-align: center;
            width: 90%;
            max-width: 400px;
        }
        h1 { margin-bottom: 1.5rem; font-size: 1.5rem; color: #ff0000; }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            margin-bottom: 1rem;
            border: none;
            border-radius: 5px;
            background-color: #404040;
            color: white;
            box-sizing: border-box;
        }
        button {
            background-color: #cc0000;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
            width: 100%;
        }
        button:hover { background-color: #ff3333; }
        .note { margin-top: 1rem; font-size: 0.8rem; color: #888; }
        .error { color: #ff6b6b; margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 YouTube Downloader V2</h1>
        <form action="/api/download" method="get">
            <input type="text" name="url" placeholder="YouTube Link hier einfügen..." required>
            <button type="submit">Download Starten</button>
        </form>
        <p class="note">Funktioniert am besten mit kürzeren Videos (Shorts, Clips).</p>
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
        return "Bitte eine URL angeben!", 400

    try:
        # 1. Informationen holen (OHNE Download)
        # Wir suchen explizit nach 'best' (Video+Audio kombiniert), oft MP4.
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'noplaylist': True
        }
        
        # Hier nutzen wir yt-dlp nur als "Suchmaschine" für den echten Link
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            title = info.get('title', 'video')

        if not direct_url:
            return "Fehler: Konnte keinen direkten Videolink finden.", 500

        # 2. Den Stream weiterleiten (Proxy)
        # Wir laden das Video stückchenweise von Google und reichen es an dich weiter
        req = requests.get(direct_url, stream=True)

        def generate():
            for chunk in req.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

        # Wir setzen den Dateinamen auf "video.mp4", um Header-Probleme mit Sonderzeichen zu vermeiden
        return Response(stream_with_context(generate()), 
                        content_type='video/mp4',
                        headers={"Content-Disposition": "attachment; filename=video.mp4"})

    except Exception as e:
        # Falls was schief geht, siehst du den Fehler direkt im Browser
        return f"Ein Fehler ist aufgetreten: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)