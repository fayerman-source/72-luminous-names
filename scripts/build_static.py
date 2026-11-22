import argparse
from pathlib import Path
import shutil
import sys
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402

DEFAULT_BASE_URL = "https://72-luminous-names.vercel.app"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
EXPORT_MARKER = ".static_export_manifest"
PROTECTED_REPO_DIRS = {
    ".git",
    ".github",
    "static",
    "templates",
    "tests",
    "scripts",
    ".venv",
    "venv",
    "env",
}


def validate_output_dir(output_dir, repo_root: Path = ROOT, static_src=None) -> Path:
    raw_path = Path(output_dir)
    if raw_path.is_symlink():
        raise ValueError(f"Refusing to use symlink as output directory: {raw_path}")

    out_root = raw_path.resolve()
    resolved_repo = Path(repo_root).resolve()
    resolved_home = Path.home().resolve()

    if out_root == Path(out_root.anchor) or out_root == resolved_home:
        raise ValueError(f"Refusing to use unsafe system path as output directory: {out_root}")

    if out_root == resolved_repo or resolved_repo.is_relative_to(out_root):
        raise ValueError(
            f"Refusing to use repository root or its ancestor as output directory: {out_root}"
        )

    if static_src is not None:
        resolved_static = Path(static_src).resolve()
        if (
            out_root == resolved_static
            or out_root.is_relative_to(resolved_static)
            or resolved_static.is_relative_to(out_root)
        ):
            raise ValueError(
                f"Refusing to use static source directory as output directory: {out_root}"
            )

    if out_root.is_relative_to(resolved_repo):
        top_part = out_root.relative_to(resolved_repo).parts[0]
        if top_part in PROTECTED_REPO_DIRS or (resolved_repo / top_part).is_file():
            raise ValueError(
                f"Refusing to overwrite repository source path: {out_root}"
            )

    if out_root.exists():
        if not out_root.is_dir():
            raise ValueError(f"Output path exists and is not a directory: {out_root}")
        if any(out_root.iterdir()) and not (out_root / EXPORT_MARKER).is_file():
            raise ValueError(
                f"Refusing to delete non-empty directory without {EXPORT_MARKER}: {out_root}"
            )

    return out_root


def route_to_output_path(output_dir: Path, route_path: str) -> Path:
    out_root = output_dir.resolve()
    clean = "/" + route_path.lstrip("/")
    if clean == "/":
        target = out_root / "index.html"
    else:
        rel = clean.lstrip("/").rstrip("/")
        suffix = Path(rel).suffix
        if suffix in {".xml", ".txt", ".html", ".json", ".webmanifest"}:
            target = out_root / rel
        else:
            target = out_root / rel / "index.html"

    resolved = target.resolve()
    resolved.relative_to(out_root)
    return resolved


def parse_sitemap_paths(sitemap_xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(sitemap_xml_bytes)
    locs = root.findall("sm:url/sm:loc", SITEMAP_NS)
    if not locs:
        locs = [el for el in root.iter() if el.tag.endswith("loc")]
    paths = []
    for loc in locs:
        if loc.text:
            parsed = urlsplit(loc.text.strip())
            paths.append(parsed.path or "/")
    return paths


def export_static_site(
    output_dir,
    flask_app=app,
    base_url=DEFAULT_BASE_URL,
    include_audio=True,
):
    out_root = validate_output_dir(
        output_dir,
        repo_root=ROOT,
        static_src=flask_app.static_folder,
    )
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / EXPORT_MARKER).write_text("72-luminous-names static export\n", encoding="utf-8")

    clean_base = base_url.rstrip("/")
    client = flask_app.test_client()

    sitemap_resp = client.get("/sitemap.xml", base_url=clean_base)
    if sitemap_resp.status_code != 200:
        raise RuntimeError(f"GET /sitemap.xml failed with HTTP {sitemap_resp.status_code}")

    sitemap_paths = parse_sitemap_paths(sitemap_resp.data)
    if not sitemap_paths:
        raise RuntimeError("No <loc> entries found in /sitemap.xml")

    exported_routes = {}

    def write_route(route_path: str, payload: bytes):
        dest = route_to_output_path(out_root, route_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        exported_routes[route_path] = dest

    write_route("/sitemap.xml", sitemap_resp.data)

    robots_resp = client.get("/robots.txt", base_url=clean_base)
    if robots_resp.status_code != 200:
        raise RuntimeError(f"GET /robots.txt failed with HTTP {robots_resp.status_code}")
    write_route("/robots.txt", robots_resp.data)

    for path in sitemap_paths:
        resp = client.get(path, base_url=clean_base)
        if resp.status_code != 200:
            raise RuntimeError(f"GET {path} failed with HTTP {resp.status_code}")
        write_route(path, resp.data)

    not_found_resp = client.get("/__static_export_404_probe__", base_url=clean_base)
    if not_found_resp.status_code != 404:
        raise RuntimeError(
            f"Expected 404 for unknown route probe, got HTTP {not_found_resp.status_code}"
        )
    write_route("/404.html", not_found_resp.data)

    static_src = Path(flask_app.static_folder)
    copied_static = 0
    if static_src.exists():
        static_dst = out_root / "static"
        for src_file in sorted(static_src.rglob("*")):
            if not src_file.is_file() or src_file.name == ".gitkeep":
                continue
            rel = src_file.relative_to(static_src)
            if not include_audio and rel.parts and rel.parts[0] == "audio":
                continue
            dst_file = static_dst / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            copied_static += 1

    return {
        "output_dir": out_root,
        "sitemap_paths": sitemap_paths,
        "exported_routes": exported_routes,
        "copied_static_files": copied_static,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Freeze all Flask pages and static assets into a static folder."
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "dist"),
        help="Destination folder for the static export (default: ./dist)",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Canonical base URL used while rendering external links",
    )
    parser.add_argument(
        "--skip-audio",
        action="store_true",
        help="Skip copying static/audio/*.mp3 into the output directory",
    )
    args = parser.parse_args(argv)
    summary = export_static_site(
        output_dir=args.output,
        base_url=args.base_url,
        include_audio=not args.skip_audio,
    )
    print(
        f"Exported {len(summary['exported_routes'])} routes and "
        f"{summary['copied_static_files']} static assets to {summary['output_dir']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
