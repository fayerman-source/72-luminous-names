# Scripts

Manual tooling and research. Nothing here is imported by the Flask app, and `pytest`
run from the repo root collects only `tests/` (see `pytest.ini`).

## Audio QC

```bash
python scripts/qc_audio.py
```

Probes all 72 files in `static/audio/` for presence, readability, duration (`5s–45s`),
peak/mean volume, internal/trailing silences (`>=4s` below `-45 dB`), and catalog-wide
loudness swings (`±4.5 dB` around the median and `<=6.0 dB` total spread). Exits with
code `1` when any track or catalog loudness check fails. See `scripts/AUDIO_QC_REPORT.md`
for the current audit of shipped files.

## Voice-search probes

The `probe_*.py` files are one-off experiments used to choose the voice for the
catalog — Gemini native TTS, ElevenLabs, and Google Cloud TTS were all tried:

| File | What it tries |
| --- | --- |
| `probe_gemini_format*.py` | Gemini native-audio response formats |
| `probe_gemini_singing.py` / `probe_gemini_male.py` | Chanting-style prompts |
| `probe_gemini_tts_legacy.py` | Old `google.generativeai` SDK (deprecated) |
| `probe_gemini_tts_v2.py` | New `google.genai` SDK |
| `probe_elevenlabs*.py` | ElevenLabs multilingual voices |
| `probe_google_tts.py` / `probe_google_studio.py` | Google Cloud Text-to-Speech |

They are kept for provenance, not as a supported workflow.

> **Warning:** the probes write to `static/audio/1.mp3` (or dump `test_male.raw`,
> `test_part_*.raw` into the current directory). Running one **overwrites a real
> catalog asset**. Restore it afterwards with `git checkout static/audio/1.mp3`.

These files expect `GEMINI_API_KEY` or `ELEVENLABS_API_KEY` in the environment. They
are not declared in `requirements.txt`; install their SDKs ad hoc if you re-run them.
