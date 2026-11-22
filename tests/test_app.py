from pathlib import Path
import os
import subprocess
import sys
import pytest

from app import NAMES, app, get_public_base_url


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


def test_untrusted_host_header_returns_400():
    client = app.test_client()

    assert client.get("/", headers={"Host": "evil.example"}).status_code == 400
    assert client.get("/session/999", headers={"Host": "evil.example"}).status_code == 400


def test_spoofed_forwarded_headers_and_query_do_not_affect_canonical_or_sitemap():
    client = app.test_client()
    spoofed = {
        "X-Forwarded-Host": "evil.example",
        "X-Forwarded-Proto": "javascript",
    }

    session_resp = client.get("/session/1?utm_source=tracker&foo=bar", headers=spoofed)
    html = session_resp.data.decode("utf-8")
    assert session_resp.status_code == 200
    assert 'href="https://72-luminous-names.vercel.app/session/1"' in html
    assert 'property="og:url" content="https://72-luminous-names.vercel.app/session/1"' in html
    assert "evil.example" not in html
    assert "javascript:" not in html
    assert "utm_source" not in html

    sitemap_resp = client.get("/sitemap.xml", headers=spoofed)
    xml = sitemap_resp.data.decode("utf-8")
    assert sitemap_resp.status_code == 200
    assert "<loc>https://72-luminous-names.vercel.app/session/1</loc>" in xml
    assert "evil.example" not in xml


def test_public_base_url_env_controls_external_metadata(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://names.example.org")
    client = app.test_client()

    html = client.get("/session/12").data.decode("utf-8")
    sitemap_xml = client.get("/sitemap.xml").data.decode("utf-8")
    robots_txt = client.get("/robots.txt").data.decode("utf-8")

    assert 'rel="canonical" href="https://names.example.org/session/12"' in html
    assert 'property="og:image" content="https://names.example.org/static/banner.png"' in html
    assert 'property="og:audio" content="https://names.example.org/static/audio/12.mp3"' in html
    assert "<loc>https://names.example.org/library</loc>" in sitemap_xml
    assert "Sitemap: https://names.example.org/sitemap.xml" in robots_txt


def test_404_omits_canonical_and_missing_audio_omits_og_audio(monkeypatch, tmp_path):
    client = app.test_client()

    not_found_html = client.get("/session/999").data.decode("utf-8")
    assert 'rel="canonical"' not in not_found_html
    assert 'property="og:url"' not in not_found_html

    monkeypatch.setattr(app, "static_folder", str(tmp_path))
    missing_audio_html = client.get("/session/1").data.decode("utf-8")
    assert 'property="og:audio"' not in missing_audio_html


def test_invalid_public_base_url_is_rejected(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "javascript://alert(1)")

    with pytest.raises(ValueError):
        get_public_base_url()
