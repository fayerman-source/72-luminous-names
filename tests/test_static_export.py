from pathlib import Path
import pytest

from app import app
from scripts.build_static import (
    EXPORT_MARKER,
    ROOT,
    export_static_site,
    main,
    parse_sitemap_paths,
    route_to_output_path,
)


def test_every_route_in_sitemap_is_exported(tmp_path):
    live_sitemap = app.test_client().get("/sitemap.xml").data
    expected_paths = parse_sitemap_paths(live_sitemap)
    assert len(expected_paths) == 74

    out_dir = tmp_path / "dist"
    summary = export_static_site(
        output_dir=out_dir,
        base_url="https://72-luminous-names.vercel.app",
        include_audio=False,
    )

    assert summary["sitemap_paths"] == expected_paths
    for route_path in expected_paths:
        exported_file = route_to_output_path(out_dir, route_path)
        assert exported_file.exists(), f"Missing exported file for {route_path}: {exported_file}"
        html = exported_file.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html

    assert (out_dir / "sitemap.xml").exists()
    assert (out_dir / "robots.txt").exists()
    assert (out_dir / "404.html").exists()
    assert (out_dir / "static" / "banner.png").exists()
    assert 'https://72-luminous-names.vercel.app/session/1' in (
        out_dir / "session" / "1" / "index.html"
    ).read_text(encoding="utf-8")


def test_static_export_copies_audio_assets_by_default(monkeypatch, tmp_path):
    fake_static = tmp_path / "fake_static"
    (fake_static / "audio").mkdir(parents=True)
    (fake_static / "banner.png").write_bytes(b"png-bytes")
    (fake_static / "audio" / "1.mp3").write_bytes(b"mp3-bytes")
    (fake_static / "audio" / ".gitkeep").write_bytes(b"")
    monkeypatch.setattr(app, "static_folder", str(fake_static))

    out_dir = tmp_path / "dist_full"
    rc = main(["--output", str(out_dir)])

    assert rc == 0
    assert (out_dir / "static" / "banner.png").read_bytes() == b"png-bytes"
    assert (out_dir / "static" / "audio" / "1.mp3").read_bytes() == b"mp3-bytes"
    assert not (out_dir / "static" / "audio" / ".gitkeep").exists()


def test_route_to_output_path_rejects_traversal(tmp_path):
    with pytest.raises(ValueError):
        route_to_output_path(tmp_path / "dist", "/../../outside.html")


def test_export_rejects_repo_root_ancestors_source_dirs_and_unmarked_dirs(tmp_path):
    for unsafe_target in [
        ROOT,
        ROOT.parent,
        ROOT / "static",
        ROOT / "static" / "audio",
        ROOT / "templates",
        ROOT / "scripts",
    ]:
        with pytest.raises(ValueError):
            export_static_site(output_dir=unsafe_target, include_audio=False)
        assert unsafe_target.exists()

    occupied = tmp_path / "important_folder"
    occupied.mkdir()
    keep_file = occupied / "keep.txt"
    keep_file.write_text("do not delete", encoding="utf-8")

    with pytest.raises(ValueError, match=EXPORT_MARKER):
        export_static_site(output_dir=occupied, include_audio=False)
    assert keep_file.read_text(encoding="utf-8") == "do not delete"


def test_export_allows_reexporting_previous_marked_directory(tmp_path):
    out_dir = tmp_path / "dist_repeat"
    export_static_site(output_dir=out_dir, include_audio=False)
    stale_file = out_dir / "stale.txt"
    stale_file.write_text("old", encoding="utf-8")

    assert (out_dir / EXPORT_MARKER).is_file()
    export_static_site(output_dir=out_dir, include_audio=False)

    assert not stale_file.exists()
    assert (out_dir / "index.html").is_file()
