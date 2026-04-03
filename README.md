# Mirror Mirror

Mirror Mirror is a face-aware personal diary app.
It detects facial signals in the browser, drafts a short reflection with Gemini, and auto-saves each scan as a new entry.

## Highlights

- Browser camera scan + `face-api.js` mood/age/energy signals
- Gemini-generated diary text auto-saved on each scan
- Like/Not me feedback on each entry
- Random writing style per entry, adapted over time from feedback
- Delete diary entries with confirmation
- Feedback + delete controls inside diary entry cards
- Face-API readings popup to inspect live detection stats
- If face is not detected, optional "resume entry" can still be saved from recent context
- No-face resume entries can optionally keep current snapshot and link recent previous photos
- Theme customization (`Warm`, `Ocean`, `Forest`, `Night`)
- Camera switch button (front/back) + preferred default camera
- Photo snapshot preference per scan (`ask`, `always`, `never`)
- Diary grouped by day with multiple scans inside each day
- Optional PIN lock for local diary privacy
- Export/import diary JSON backups
- Safer API key modes:
  - `session` (recommended): key is forgotten when tab closes
  - `local`: key is saved in browser storage
- Optional server key mode with `GEMINI_API_KEY`
- Auto-download face model files from server when missing
- Render-ready backend (`Flask` + `gunicorn`)

## Privacy behavior

- Face analysis runs in the browser.
- Diary text generation is sent to Gemini API (through `/gemini` on backend).
- Diary entries are stored in browser local storage.
- API key storage depends on selected mode.

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
2. In app settings, try model `gemini-2.0-flash`.
3. If using server key mode, confirm `GEMINI_API_KEY` is set in Render environment variables.
4. Check Render logs for upstream `4xx/5xx` messages.
5. If API fails, app falls back to local text so diary flow still works.
