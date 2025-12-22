from flask import Flask, request, Response, stream_with_context
import subprocess

app = Flask(__name__)

# --- 1. Das Frontend (HTML/CSS) ---
# Wir speichern das HTML einfach in einer Variable, damit alles in einer Datei bleibt.
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
            box-sizing: border-box; /* Wichtig damit Padding nicht die Breite sprengt */
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
        .note {
            margin-top: 1rem;
            font-size: 0.8rem;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📺 Video Downloader</h1>
        <form action="/api/download" method="get">
            <input type="text" name="url" placeholder="YouTube Link hier einfügen..." required>
            <button type="submit">Herunterladen</button>
        </form>
        <p class="note">Hinweis: Auf Vercel funktionieren nur kurze Videos (< 10s Timeout).</p>
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

    # Wir nutzen subprocess, um yt-dlp als Prozess zu starten und den Output direkt abzufangen.
    # '-o -' bedeutet: Schreib das Video in den Standard-Output (stdout) statt in eine Datei.
    # '-f best' versucht das beste Format zu nehmen (Achtung: ohne ffmpeg auf Vercel werden Formate, die Audio+Video mergen müssen, evtl. scheitern. 'best' nimmt oft mp4 legacy).
    cmd = ['yt-dlp', '-f', 'best', '-o', '-', video_url]

    def generate():
        # Prozess starten
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Daten in Chunks (Häppchen) lesen und an den Browser schicken
        while True:
            chunk = process.stdout.read(4096)
            if not chunk:
                break
            yield chunk
        process.wait()

    # Wir sagen dem Browser: "Hier kommt eine Datei, nenn sie video.mp4"
    return Response(stream_with_context(generate()), 
                    mimetype='video/mp4',
                    headers={"Content-Disposition": "attachment; filename=video.mp4"})

if __name__ == '__main__':
    app.run(debug=True)