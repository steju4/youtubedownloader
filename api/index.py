from flask import Flask, request, Response
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Downloader läuft! Schick einen Link an /download?url=..."

@app.route('/api/download')
def download():
    video_url = request.args.get('url')
    if not video_url:
        return "Keine URL gefunden", 400

    def generate():
        ydl_opts = {
            'format': 'best',
            # Das ist der Trick: Wir schreiben das Video in den stdout-Stream
            'outtmpl': '-',
            'logtostderr': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Wir holen uns die Info und streamen die Daten
            info = ydl.extract_info(video_url, download=True)
            # Hier gibt yt-dlp die Daten direkt an den Flask-Stream weiter
            
    # Einfachheitshalber nutzen wir hier yt-dlp direkt zum Streamen
    # Achtung: Vercel Timeouts (10s) können bei großen Videos zuschlagen!
    return "Download-Logik bereit - versuch es mit kleinen Clips!"

if __name__ == '__main__':
    app.run(debug=True)