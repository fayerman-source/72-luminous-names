from pathlib import Path
import os
import shutil
import subprocess
import sys

from app import NAMES, app


def test_home_page_links_into_the_catalog():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Browse all 72 names" in response.data
    assert b'href="/session/1"' in response.data


def test_library_is_public_and_lists_every_name():
    client = app.test_client()

    response = client.get("/library")

    assert response.status_code == 200
    assert response.data.count(b'href="/session/') == 72


def test_session_page_is_public():
    client = app.test_client()

    response = client.get("/session/1")

    assert response.status_code == 200
    assert b"Vav Hey Vav" in response.data


def test_session_shows_audio_player_when_mp3_exists(monkeypatch, tmp_path):
    client = app.test_client()
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    Path(audio_dir / "1.mp3").write_bytes(b"placeholder")
    monkeypatch.setattr(app, "static_folder", str(tmp_path))

    response = client.get("/session/1")

    assert response.status_code == 200
    assert b"/static/audio/1.mp3" in response.data
    assert b"being prepared" not in response.data


def test_session_shows_fallback_when_audio_is_missing(monkeypatch, tmp_path):
    client = app.test_client()
    monkeypatch.setattr(app, "static_folder", str(tmp_path))

    response = client.get("/session/1")

    assert response.status_code == 200
    assert b"being prepared" in response.data


def test_unknown_name_returns_404():
    client = app.test_client()

    response = client.get("/session/999")

    assert response.status_code == 404


def test_session_page_carries_social_preview_metadata():
    client = app.test_client()

    html = client.get("/session/12").data

    assert b'property="og:type" content="music.song"' in html
    assert b'property="og:title"' in html
    assert b'property="og:image"' in html
    assert b'property="og:audio"' in html
    assert b'rel="canonical"' in html
    assert b"Unconditional Love" in html


def test_session_pages_link_to_neighbouring_names():
    client = app.test_client()

    html = client.get("/session/1").data

    assert b'href="/session/72"' in html
    assert b'href="/session/2"' in html


def test_sitemap_lists_every_page():
    client = app.test_client()

    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    assert response.data.count(b"<loc>") == 74  # home, library, 72 names


def test_robots_points_at_the_sitemap():
    client = app.test_client()

    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert b"/sitemap.xml" in response.data


def test_every_name_has_an_audio_file():
    audio_dir = Path(app.static_folder) / "audio"

    missing = [name["id"] for name in NAMES if not (audio_dir / f"{name['id']}.mp3").exists()]

    assert missing == []


def test_names_catalog_has_expected_ids():
    ids = [name["id"] for name in NAMES]

    assert len(NAMES) == 72
    assert ids == list(range(1, 73))


def test_app_runs_with_no_configuration_at_all():
    # Stateless by design: no SECRET_KEY, no .env, nothing to set before the
    # app can boot. This is what lets a preview deployment come up clean.
    env = os.environ.copy()
    env.pop("SECRET_KEY", None)
    env.pop("FLASK_DEBUG", None)

    result = subprocess.run(
        [sys.executable, "-c", "import app; print('booted')"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "booted" in result.stdout


def test_session_renders_breath_paced_player_controls_and_rtl_letters():
    client = app.test_client()

    html = client.get("/session/5").data.decode("utf-8")

    assert 'dir="rtl"' in html
    assert '<span class="hebrew-letter" data-letter-index="0">מ</span>' in html
    assert '<span class="hebrew-letter" data-letter-index="1">ה</span>' in html
    assert '<span class="hebrew-letter" data-letter-index="2">ש</span>' in html
    for minutes, seconds in [("3 minutes", "180"), ("5 minutes", "300"), ("11 minutes", "660"), ("18 minutes", "1080")]:
        assert f'<option value="{seconds}"' in html
        assert minutes in html
    for interval in ["4", "6", "8"]:
        assert f'<option value="{interval}"' in html
    assert 'id="drone-enabled"' in html
    assert 'src="/static/player.js"' in html

    js_resp = client.get("/static/player.js")
    assert js_resp.status_code == 200
    assert b"AudioContext" in js_resp.data


def test_player_js_helpers_progress_letters_and_breath_phases():
    node_bin = shutil.which("node")
    if node_bin is None:
        return

    script = """
    const assert = require("assert");
    const player = require("./static/player.js");
    assert.strictEqual(player.formatRemainingSeconds(300), "05:00");
    assert.strictEqual(player.formatRemainingSeconds(65), "01:05");
    assert.strictEqual(player.computeActiveLetterIndex(1, 18, 3), 0);
    assert.strictEqual(player.computeActiveLetterIndex(7, 18, 3), 1);
    assert.strictEqual(player.computeActiveLetterIndex(15, 18, 3), 2);
    assert.ok(player.computeBreathPhase(1, 6).includes("Inhale"));
    assert.ok(player.computeBreathPhase(4, 6).includes("Exhale"));
    console.log("player-js-ok");
    """
    result = subprocess.run(
        [node_bin, "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "player-js-ok" in result.stdout
