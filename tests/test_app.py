from pathlib import Path
import os
import subprocess
import sys

from app import NAMES, app


def test_home_page_loads_with_demo_copy():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Demo Access" in response.data
    assert b"No payment is processed" in response.data


def test_library_requires_demo_unlock():
    client = app.test_client()

    response = client.get("/library")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_demo_unlock_grants_library_access():
    client = app.test_client()

    response = client.post("/subscribe", data={"email": "Demo@Example.com"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/library")

    library = client.get("/library")
    assert library.status_code == 200
    assert b"72 sessions available" in library.data


def test_invalid_demo_unlock_rejects_missing_email():
    client = app.test_client()

    response = client.post("/subscribe", data={"email": ""}, follow_redirects=True)

    assert response.status_code == 200
    assert b"Enter a valid email" in response.data


def test_session_shows_missing_audio_message(monkeypatch, tmp_path):
    client = app.test_client()
    monkeypatch.setattr(app, "static_folder", str(tmp_path))

    with client.session_transaction() as flask_session:
        flask_session["subscribed"] = True

    response = client.get("/session/1")

    assert response.status_code == 200
    assert b"Audio has not been generated locally" in response.data


def test_session_shows_audio_player_when_mp3_exists(monkeypatch, tmp_path):
    client = app.test_client()
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    Path(audio_dir / "1.mp3").write_bytes(b"placeholder")
    monkeypatch.setattr(app, "static_folder", str(tmp_path))

    with client.session_transaction() as flask_session:
        flask_session["subscribed"] = True

    response = client.get("/session/1")

    assert response.status_code == 200
    assert b"Local demo audio" in response.data
    assert b"/static/audio/1.mp3" in response.data


def test_names_catalog_has_expected_ids():
    ids = [name["id"] for name in NAMES]

    assert len(NAMES) == 72
    assert ids == list(range(1, 73))


def test_import_requires_secret_key_even_when_debug_enabled():
    env = os.environ.copy()
    env.pop("SECRET_KEY", None)
    env["FLASK_DEBUG"] = "true"

    result = subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "SECRET_KEY environment variable is required" in result.stderr
