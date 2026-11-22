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


def test_pages_include_local_practice_tracker_without_cookies():
    client = app.test_client()

    for path in ["/", "/library", "/session/1"]:
        resp = client.get(path)
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert 'id="practice-summary-badge"' in html
        assert 'src="/static/practice.js"' in html
        assert "Set-Cookie" not in resp.headers

    js_resp = client.get("/static/practice.js")
    assert js_resp.status_code == 200
    assert b"luminous72.practice.v1" in js_resp.data


def test_practice_js_saved_names_and_day_counter_logic():
    node_bin = shutil.which("node")
    if node_bin is None:
        return

    script = """
    const assert = require("assert");
    const p = require("./static/practice.js");

    let state = p.normalizeState({});
    assert.deepStrictEqual(state, { savedIds: [], practicedDates: [], completedNameIds: [] });

    state = p.toggleSavedName(state, 5);
    state = p.toggleSavedName(state, 12);
    assert.deepStrictEqual(state.savedIds, [5, 12]);
    state = p.toggleSavedName(state, 5);
    assert.deepStrictEqual(state.savedIds, [12]);

    // Invalid IDs are ignored
    state = p.toggleSavedName(state, 999);
    state = p.toggleSavedName(state, 0);
    assert.deepStrictEqual(state.savedIds, [12]);

    // Recording twice on the same calendar day increments the day counter only once
    state = p.recordPracticeDay(state, 5, "2026-11-21");
    state = p.recordPracticeDay(state, 12, "2026-11-21");
    assert.strictEqual(p.getDayProgress(state).totalDays, 1);
    assert.strictEqual(p.getDayProgress(state).cycleDay, 1);
    assert.deepStrictEqual(state.completedNameIds, [5, 12]);

    state = p.recordPracticeDay(state, 13, "2026-11-22");
    assert.strictEqual(p.getDayProgress(state).totalDays, 2);
    assert.strictEqual(p.getDayProgress(state).cycleDay, 2);

    // Day 73 wraps to cycle day 1 while preserving total days practiced
    const seventyThreeDays = Array.from({ length: 73 }, (_, i) => {
      const d = new Date(Date.UTC(2026, 0, 1 + i));
      return d.toISOString().slice(0, 10);
    });
    const wrapped = p.getDayProgress({ savedIds: [], practicedDates: seventyThreeDays, completedNameIds: [] });
    assert.strictEqual(wrapped.totalDays, 73);
    assert.strictEqual(wrapped.cycleDay, 1);
    console.log("practice-js-ok");
    """
    result = subprocess.run(
        [node_bin, "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "practice-js-ok" in result.stdout


def test_practice_js_refreshes_state_across_tabs_and_across_midnight():
    node_bin = shutil.which("node")
    if node_bin is None:
        return

    script = """
    const assert = require("assert");

    // Shared in-memory localStorage across two simulated tabs
    const backingStore = new Map();
    const storage = {
      getItem(k) { return backingStore.has(k) ? backingStore.get(k) : null; },
      setItem(k, v) { backingStore.set(k, String(v)); }
    };

    function createTab(pathname, initialDate) {
      let currentNow = initialDate;
      const winListeners = {};
      const children = [];
      function makeEl(tag) {
        const listeners = {};
        return {
          tag,
          type: "",
          className: "",
          textContent: "",
          hidden: false,
          children: [],
          classList: { toggle() {} },
          setAttribute() {},
          appendChild(ch) { this.children.push(ch); return ch; },
          insertBefore(node) { children.push(node); return node; },
          querySelector(sel) {
            if (sel === ".audio-player") return { tag: "div" };
            if (sel === "audio") return audio;
            return null;
          },
          addEventListener(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); },
          emit(ev) { (listeners[ev] || []).forEach(fn => fn()); }
        };
      }
      const badge = makeEl("span");
      const audio = makeEl("audio");
      const playerRoot = makeEl("div");

      const win = {
        localStorage: storage,
        location: { pathname },
        addEventListener(ev, fn) { (winListeners[ev] = winListeners[ev] || []).push(fn); },
        emit(ev, payload) { (winListeners[ev] || []).forEach(fn => fn(payload)); }
      };
      const doc = {
        readyState: "loading",
        hidden: false,
        addEventListener() {},
        createElement: makeEl,
        getElementById(id) { return id === "practice-summary-badge" ? badge : null; },
        querySelector(sel) { return sel === ".player" ? playerRoot : null; },
        querySelectorAll() { return []; }
      };

      return {
        mount(mod) {
          global.window = win;
          global.document = doc;
          mod.initDom(() => currentNow);
        },
        setNow(d) { currentNow = d; },
        win,
        doc,
        badge,
        audio,
        getButtons() { return children[0].children; }
      };
    }

    // Load module with readyState="loading" so we control mounting per tab
    global.window = { localStorage: storage, location: { pathname: "/" }, addEventListener() {} };
    global.document = { readyState: "loading", addEventListener() {} };
    const p = require("./static/practice.js");

    const tab1 = createTab("/session/1", new Date(2026, 10, 21, 23, 58, 0));
    const tab2 = createTab("/session/2", new Date(2026, 10, 21, 23, 58, 0));
    tab1.mount(p);
    tab2.mount(p);

    // 1. Both tabs already open: save #1 in tab1, then save #2 in tab2 -> neither overwrites the other
    global.window = tab1.win; global.document = tab1.doc;
    tab1.getButtons()[0].emit("click"); // save #1

    global.window = tab2.win; global.document = tab2.doc;
    tab2.getButtons()[0].emit("click"); // save #2

    const persisted = JSON.parse(storage.getItem(p.STORAGE_KEY));
    assert.deepStrictEqual(persisted.savedIds, [1, 2]);

    // Storage event synchronizes tab1's header badge immediately
    global.window = tab1.win; global.document = tab1.doc;
    tab1.win.emit("storage", { key: p.STORAGE_KEY });
    assert.ok(tab1.badge.textContent.includes("★ 2 saved"));

    // 2. Midnight rollover on an already-open session tab
    const markBtn = tab1.getButtons()[1];
    markBtn.emit("click"); // 2026-11-21
    assert.strictEqual(markBtn.textContent, "✓ Practiced today");
    assert.deepStrictEqual(JSON.parse(storage.getItem(p.STORAGE_KEY)).practicedDates, ["2026-11-21"]);

    // Advance past local midnight to 2026-11-22
    tab1.setNow(new Date(2026, 10, 22, 0, 2, 0));
    tab1.win.emit("focus");
    assert.strictEqual(markBtn.textContent, "Mark practiced today");

    // Audio completion on the new day logs 2026-11-22 instead of stale 2026-11-21
    tab1.audio.emit("ended");
    assert.deepStrictEqual(
      JSON.parse(storage.getItem(p.STORAGE_KEY)).practicedDates,
      ["2026-11-21", "2026-11-22"]
    );
    console.log("practice-tabs-midnight-ok");
    """
    result = subprocess.run(
        [node_bin, "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "practice-tabs-midnight-ok" in result.stdout
