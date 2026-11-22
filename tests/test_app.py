from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

from app import NAMES, app, name_for_moment


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


def test_name_for_moment_cycle_boundaries():
    cases = [
        ((0, 0, 0), 1, "00:00", "00:20"),
        ((0, 19, 59), 1, "00:00", "00:20"),
        ((0, 20, 0), 2, "00:20", "00:40"),
        ((11, 59, 59), 36, "11:40", "12:00"),
        ((12, 0, 0), 37, "12:00", "12:20"),
        ((23, 39, 59), 71, "23:20", "23:40"),
        ((23, 40, 0), 72, "23:40", "00:00"),
        ((23, 59, 59), 72, "23:40", "00:00"),
    ]
    for (hh, mm, ss), expected_id, expected_start, expected_end in cases:
        dt = datetime(2026, 11, 22, hh, mm, ss, tzinfo=timezone.utc)
        res = name_for_moment(dt)
        assert res["name"]["id"] == expected_id
        assert res["window_start"] == expected_start
        assert res["window_end"] == expected_end

    # Every one of the 72 Names covers exactly 20 minutes across the 1,440-minute day
    counts = {}
    for minute_of_day in range(24 * 60):
        dt = datetime(2026, 11, 22, minute_of_day // 60, minute_of_day % 60, tzinfo=timezone.utc)
        nid = name_for_moment(dt)["name"]["id"]
        counts[nid] = counts.get(nid, 0) + 1
    assert set(counts.keys()) == set(range(1, 73))
    assert all(c == 20 for c in counts.values())


def test_home_page_renders_server_moment_and_client_updater(monkeypatch):
    import app as app_mod

    fixed_dt = datetime(2026, 11, 22, 23, 45, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(app_mod, "name_for_moment", lambda dt=None: name_for_moment(fixed_dt))

    client = app.test_client()
    html = client.get("/").data.decode("utf-8")

    assert 'id="moment-card"' in html
    assert "23:40–00:00 (UTC)" in html
    assert "#72 of 72" in html
    assert 'href="/session/72"' in html
    assert 'src="/static/moment.js"' in html


def test_browser_and_server_moment_rules_match_across_entire_day():
    node_bin = shutil.which("node")
    if node_bin is None:
        return

    script = """
    const m = require("./static/moment.js");
    const out = [];
    for (let h = 0; h < 24; h++) {
      for (let min = 0; min < 60; min++) {
        out.push(m.computeMomentWindow(h, min));
      }
    }
    console.log(JSON.stringify(out));
    """
    proc = subprocess.run(
        [node_bin, "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )
    js_windows = json.loads(proc.stdout)
    assert len(js_windows) == 1440

    for idx, js_win in enumerate(js_windows):
        dt = datetime(2026, 11, 22, idx // 60, idx % 60, tzinfo=timezone.utc)
        py_win = name_for_moment(dt)
        assert js_win["nameId"] == py_win["name"]["id"]
        assert js_win["windowStart"] == py_win["window_start"]
        assert js_win["windowEnd"] == py_win["window_end"]
