# Repository Guidelines

## Project Structure & Module Organization

This repository is a small Flask application for browsing and playing the 72 names meditation sessions. Core server logic, route handlers, and the in-memory `NAMES` catalog live in `app.py`. Jinja templates are in `templates/` (`base.html`, `index.html`, `library.html`, `session.html`). Generated audio files are stored as numbered MP3s in `static/audio/`, matching name IDs such as `static/audio/1.mp3`. `generate_audio.py` contains the audio-generation utility, and `vercel.json` configures deployment through `@vercel/python`.

## Build, Test, and Development Commands

Create and activate a local environment before installing dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the app locally with:

```bash
flask --app app run --debug
```

For production-style serving, use:

```bash
gunicorn app:app
```

Regenerate audio only when intentionally updating assets:

```bash
python generate_audio.py
```

## Coding Style & Naming Conventions

Use Python 3 with four-space indentation and clear snake_case names for functions, variables, and route helpers. Keep route handlers small and template-oriented; move repeated presentation logic into templates rather than duplicating markup in Python. Preserve the `NAMES` item shape (`id`, `name`, `transliteration`, `meaning`, `theme`, `duration`) so templates and audio paths stay aligned.

## Testing Guidelines

No formal test suite is currently present. When adding behavior, prefer `pytest` tests under a new `tests/` directory, with files named `test_<feature>.py`. At minimum, manually verify `/`, `/library`, `/session/<id>`, login/logout flows, and that each referenced audio file exists. If adding tests, document the command, typically:

```bash
pytest
```

## Commit & Pull Request Guidelines

Use concise, imperative commit messages such as `Add session filtering` or `Fix missing audio route`. Pull requests should include a short summary, manual test notes, any new environment variables, and screenshots for visible template changes.

## Security & Configuration Tips

Set `SECRET_KEY` outside the code before running the app; there is no checked-in fallback secret. Do not commit secrets, payment keys, generated credentials, or local virtual environments. Treat `static/audio/` changes as intentional asset updates and mention them in the PR summary.
