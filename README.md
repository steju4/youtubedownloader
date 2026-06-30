# YouTube / Video Downloader

Ein einfacher Video-Downloader (Flask auf Vercel) für YouTube, TikTok, X/Twitter,
Instagram u.v.m. Basiert auf [yt-dlp](https://github.com/yt-dlp/yt-dlp) mit
Piped/Invidious als Fallback.

## ⚠️ Wichtig: YouTube braucht Cookies

YouTube blockiert Anfragen von Rechenzentrums-IPs (Vercel läuft auf AWS) mit einer
Bot-Erkennung (*"Sign in to confirm you're not a bot"*). Der **einzige zuverlässige
Weg**, YouTube von Vercel aus herunterzuladen, ist yt-dlp mit echten Account-Cookies
zu authentifizieren.

Andere Plattformen (TikTok, X, Instagram …) funktionieren **ohne** Cookies.

### Cookies einrichten (einmalig, ~3 Minuten)

1. **Cookies exportieren** – installiere im Browser eine Extension wie
   *"Get cookies.txt LOCALLY"* (Chrome/Firefox), gehe auf
   <https://www.youtube.com> (eingeloggt) und exportiere die Cookies als
   `cookies.txt` (Netscape-Format).

   > Tipp: Nutze am besten ein **Wegwerf-/Zweitkonto**, nicht dein Hauptkonto –
   > YouTube kann bei viel automatisiertem Traffic Konten flaggen.

2. **In Base64 umwandeln** (vermeidet Zeilenumbruch-Probleme in Vercel):

   ```bash
   # macOS / Linux
   base64 -w0 cookies.txt   # Linux
   base64 cookies.txt       # macOS (ohne -w0)
   ```

   Kopiere die komplette Ausgabe (eine lange Zeile).

3. **In Vercel als Umgebungsvariable hinterlegen**
   → Projekt → *Settings* → *Environment Variables*:

   | Name                  | Wert                          |
   | --------------------- | ----------------------------- |
   | `YOUTUBE_COOKIES_B64` | *(die Base64-Zeile aus Schritt 2)* |

   Für alle Environments (Production + Preview) setzen.

4. **Neu deployen** (Vercel → Deployments → Redeploy), damit die Variable
   übernommen wird.

> Alternativ kannst du den **rohen** `cookies.txt`-Inhalt in `YOUTUBE_COOKIES`
> ablegen – Base64 (`YOUTUBE_COOKIES_B64`) ist aber robuster.

### Cookies erneuern

YouTube-Cookies laufen nach einiger Zeit ab. Wenn YouTube-Downloads wieder mit
Bot-Erkennung fehlschlagen, exportiere die Cookies neu und aktualisiere die
Umgebungsvariable.

## Architektur

`api/index.py` (Flask) stellt zwei Dinge bereit:

- `GET /` – die Single-Page-Oberfläche
- `POST /api/get-url` – nimmt `{ "url": "..." }` und probiert **parallel**
  mehrere Strategien (yt-dlp, YouTube-TV-API, Piped, Invidious); die erste
  erfolgreiche gewinnt.

Alle externen Aufrufe laufen **serverseitig** (kein CORS-Problem im Browser).

## Lokale Entwicklung

```bash
pip install -r requirements.txt
export YOUTUBE_COOKIES_B64="$(base64 -w0 cookies.txt)"   # optional
python api/index.py
# → http://127.0.0.1:5000
```
