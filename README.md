# Mirror Mirror

Mirror Mirror is a face-aware personal diary app.
It detects facial signals in the browser, drafts a short reflection with Gemini, and auto-saves each scan as a new entry.

## Highlights

- Browser camera scan + `face-api.js` mood/age/energy signals
- Unified smart pipeline for every capture:
  - `TensorFlow.js + coco-ssd` first (scene/object routing)
  - then auto-route to `face-api.js` / `MediaPipe` / `Tesseract.js` as needed
- Gemini-generated diary text auto-saved on each scan
- Like/Not me feedback on each entry
- Random writing style per entry, adapted over time from feedback
- Delete diary entries with confirmation
- Feedback + delete controls inside diary entry cards
- Face-API readings popup to inspect live detection stats
- If face is not detected, capture still auto-saves a scene-based entry from local analysis
- Scene entries can keep snapshot context (depending on snapshot setting)
- Theme customization (`Warm`, `Ocean`, `Forest`, `Night`)
- Camera switch button (front/back)
- 3-2-1 capture countdown for more accurate "moment" scans
- Smart auto decisions by engine (capture-first, no extra analysis screens)
- Diary grouped by day with multiple scans inside each day
- Snapshot save preference (`Only when useful` / `Always` / `Never`)
- Prompt hardening to reduce repetitive phrasing across entries
- Optional PIN lock for local diary privacy
- Export/import diary JSON backups
- Session-first API key handling for privacy
- Optional server key mode with `GEMINI_API_KEY`
- Auto-download face model files from server when missing
- Render-ready backend (`Flask` + `gunicorn`)

## Privacy behavior

- Face analysis runs in the browser.
- Diary text generation is sent to Gemini API (through `/gemini` on backend).
- Diary entries are stored in browser local storage.
- API key is session-first for privacy.
- Local visual analysis (`TensorFlow.js`, `MediaPipe`, `face-api.js`, `Tesseract.js`) runs locally in-browser.

## Stack

- Frontend: `index.html` (vanilla HTML/CSS/JS)
- Face analysis: `face-api.js` (CDN)
- Backend: `server.py` (`Flask`, `requests`)
- Prod server: `gunicorn`

## API endpoints

- `GET /` serves app
- `GET /config` returns server feature config (`serverKeyConfigured`, `defaultModel`)
- `GET /healthz` basic health check
- `POST /gemini` Gemini proxy with model fallback
- `GET /weights/status` model file availability
- `POST /weights/prefetch` pre-download missing model files
- `GET /weights/<file>` serve model files (auto-download when missing)

## Local run

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

Open `http://localhost:8080`.

## Environment variables

- `PORT` (optional): server port (Render sets this automatically)
- `GEMINI_API_KEY` (optional): enables server key mode
- `GEMINI_MODEL` (optional): default model, example `gemini-2.0-flash`

## Testing

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Deploy to Render

### Blueprint (recommended)

1. Push repo to GitHub
2. Render -> `New +` -> `Blueprint`
3. Select repo
4. Render reads `render.yaml` and deploys

### Manual Web Service

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT server:app`

## Gemini troubleshooting

If you see Gemini errors:

1. Verify API key is valid and active in Google AI Studio.
2. Keep using the default model unless debugging.
3. If using server key mode, confirm `GEMINI_API_KEY` is set in Render environment variables.
4. Check Render logs for upstream `4xx/5xx` messages.
5. If API fails, app falls back to local text so diary flow still works.
