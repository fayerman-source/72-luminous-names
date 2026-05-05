# 72 Names Meditations

A small Flask demo app for browsing the 72 Names meditation library and playing locally generated audio sessions.

This repository is public-demo ready, not production ready. The current access flow is an in-memory demo unlock: no payment is processed, no account is persisted, and no real subscription is created.

## Project Structure

- `app.py` - Flask app, route handlers, and the in-memory `NAMES` catalog.
- `templates/` - Jinja templates for the home page, library, session player, and base layout.
- `static/audio/` - Local MP3 output directory. Generated MP3 files are ignored by Git.
- `generate_audio.py` - Utility that creates placeholder MP3 files with `ffmpeg`.
- `vercel.json` - Vercel Python deployment configuration.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For development tests, also install:

```bash
pip install -r requirements-dev.txt
```

Create local environment settings:

```bash
cp .env.example .env
```

Set `SECRET_KEY` to a long random value before running the app. Flask will load `.env` automatically when `python-dotenv` is installed.

## Run Locally

```bash
flask --app app run --debug
```

Open `http://127.0.0.1:5000`.

## Audio Assets

Generated MP3 files are intentionally not committed. To create local placeholder audio, install `ffmpeg`, then run:

```bash
python generate_audio.py
```

The generated files are test tones and should be replaced with real recordings before a production release.

## Tests

```bash
pytest
```

The tests cover basic routing, demo unlock behavior, catalog integrity, and the missing-audio UI state.

## Deployment Notes

This app can deploy to Vercel through `@vercel/python`. Set `SECRET_KEY` in the deployment environment. Do not use the demo unlock flow as production authentication or payment logic.
