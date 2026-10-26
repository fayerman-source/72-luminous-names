# 72 Names - Flask Meditation App

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Set SECRET_KEY
```

## Run

```bash
flask --app app run --debug    # Local dev
gunicorn app:app               # Production
```

## Test

```bash
pip install -r requirements-dev.txt
pytest
```

## Audio Generation

Requires `ffmpeg` and `GEMINI_API_KEY`:

```bash
python generate_audio.py
```

## Notes

- `SECRET_KEY` env var is required (raises `RuntimeError` if missing)
- Audio files: `static/audio/{id}.mp3` (72 files matching `NAMES` catalog)
- Every page is public; there is no account, gate, or payment flow
- `/sitemap.xml` and `/robots.txt` are generated from `NAMES`
- Verify with `python scripts/qc_audio.py` (all 72 files present and audible)
