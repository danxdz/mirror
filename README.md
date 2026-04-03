# Mirror Mirror

Mirror Mirror is a private-feeling camera diary app.
It reads facial expression signals in the browser, then writes a short daily reflection using Gemini.

## What the app does

1. User enters name, age, and Gemini API key.
2. App opens camera and detects face expression, estimated age, and energy score.
3. App asks Gemini to write a 2-3 sentence diary entry.
4. Entry is saved and shown in a personal timeline.

## Core features

- Multi-screen flow: setup, API key, mirror scan, diary, settings.
- Face analysis with `face-api.js` (tiny face detector, expression net, age/gender net).
- Local diary history stored in browser `localStorage`.
- Friendly fallback text when Gemini is unavailable.
- Auto-download model weights from server when missing.
- Render-ready Python backend using Flask + Gunicorn.

## Privacy notes

- Camera processing runs in the browser.
- User profile, API key, and diary entries are stored in local browser storage.
- Gemini requests are proxied through `/gemini` on the Flask server and sent to Google Gemini API.

## Tech stack

- Frontend: vanilla HTML/CSS/JS (`index.html`)
- AI vision: `face-api.js` via CDN
- Backend: Flask (`server.py`)
- HTTP: `requests`
- Production server: `gunicorn`

## Project structure

```text
.
|-- index.html
|-- server.py
|-- requirements.txt
|-- render.yaml
|-- download_models.py
`-- weights/
```

## Run locally

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

Open `http://localhost:8080`.

## Model files

No manual step is required for normal use.
When the browser asks for `/weights/...`, the server downloads missing model files automatically into `weights/`.

Optional pre-download:

```bash
python download_models.py
```

## Publish to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-user>/<your-repo>.git
git push -u origin main
```

## Deploy to Render

### Option A: Blueprint (recommended)

1. Push this repo to GitHub.
2. In Render, click `New +` -> `Blueprint`.
3. Select the repo.
4. Render reads `render.yaml` and deploys automatically.

### Option B: Manual Web Service

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT server:app`

## Environment and runtime

- Python version is pinned in `render.yaml`.
- Server reads `PORT` from environment (Render-compatible).

## Known limitations

- Browser must allow camera access.
- If internet is blocked, model download and Gemini calls will fail.
- API key format is validated client-side by prefix check (`AIza...`).
