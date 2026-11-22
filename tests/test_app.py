from pathlib import Path
import os
import shutil
import subprocess
import sys

from app import GROUP_BY_NAME_ID, NAMES, SITUATION_GROUPS, app


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


def test_every_name_belongs_to_exactly_one_situation_group():
    seen = []
    for grp in SITUATION_GROUPS:
        seen.extend(grp["ids"])

    assert sorted(seen) == list(range(1, 73))
    assert set(GROUP_BY_NAME_ID.keys()) == set(range(1, 73))


def test_library_filters_by_query_and_situation_group():
    client = app.test_client()

    anger_resp = client.get("/library?q=anger")
    anger_html = anger_resp.data.decode("utf-8")
    assert anger_resp.status_code == 200
    assert 'href="/session/56"' in anger_html
    assert "Dispelling Anger" in anger_html
    assert 'href="/session/1"' not in anger_html

    healing_resp = client.get("/library?group=healing")
    healing_html = healing_resp.data.decode("utf-8")
    assert healing_resp.status_code == 200
    assert healing_resp.data.count(b'href="/session/') == 12
    assert 'href="/session/5"' in healing_html
    assert "Showing 12 of 72 names" in healing_html

    empty_resp = client.get("/library?q=zzzznonexistentintention")
    assert empty_resp.status_code == 200
    assert b"No names matched that search" in empty_resp.data


def test_home_page_exposes_intention_search_and_situation_links():
    client = app.test_client()

    html = client.get("/").data.decode("utf-8")

    assert 'action="/library"' in html
    assert 'href="/library?group=healing"' in html
    assert 'href="/library?group=peace"' in html


def test_finder_js_preserves_selected_group_on_pill_click_and_form_submit():
    node_bin = shutil.which("node")
    if node_bin is None:
        return

    script = """
    const assert = require("assert");

    function makeNode(attrs = {}, initialActive = false) {
      const listeners = {};
      let active = initialActive;
      return {
        value: attrs.value || "",
        disabled: Boolean(attrs.disabled),
        hidden: false,
        textContent: "",
        firstChild: null,
        classList: {
          contains(cls) { return cls === "is-active" && active; },
          toggle(cls, force) { if (cls === "is-active") active = Boolean(force); }
        },
        getAttribute(k) { return attrs[k] || ""; },
        addEventListener(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); },
        emit(ev, payload) { (listeners[ev] || []).forEach(fn => fn(payload || { preventDefault() {} })); },
        insertBefore() {}
      };
    }

    const form = makeNode();
    const searchInput = makeNode();
    const groupInput = makeNode({ value: "", disabled: true });
    const statusEl = makeNode();
    const emptyEl = makeNode();
    const allPill = makeNode({ "data-group": "" }, true);
    const peacePill = makeNode({ "data-group": "peace" }, false);

    const cards = Array.from({ length: 72 }, (_, idx) =>
      makeNode({
        "data-group": idx < 14 ? "peace" : "healing",
        "data-search": idx === 0 ? "56 Dispelling Anger Peace" : "5 Healing"
      })
    );

    let lastUrl = "";
    global.window = {
      location: { pathname: "/library" },
      history: { replaceState(_s, _t, url) { lastUrl = url; } }
    };
    global.document = {
      readyState: "complete",
      getElementById(id) {
        const map = {
          "intention-finder-form": form,
          "intention-search": searchInput,
          "finder-group-input": groupInput,
          "finder-status": statusEl,
          "finder-client-empty": emptyEl
        };
        return map[id] || null;
      },
      querySelectorAll(sel) {
        if (sel === ".name-card") return cards;
        if (sel === ".group-pill") return [allPill, peacePill];
        return [];
      }
    };

    require("./static/finder.js");

    // Select Peace pill, enter query, and submit form -> group stays active & synchronized
    peacePill.emit("click", { preventDefault() {} });
    assert.strictEqual(groupInput.value, "peace");
    assert.strictEqual(groupInput.disabled, false);

    searchInput.value = "anger";
    let defaultPrevented = false;
    form.emit("submit", { preventDefault() { defaultPrevented = true; } });
    assert.strictEqual(defaultPrevented, true);
    assert.strictEqual(groupInput.value, "peace");
    assert.strictEqual(lastUrl, "/library?group=peace&q=anger");
    assert.strictEqual(cards.filter(c => !c.hidden).length, 1);

    // Selecting All 72 disables hidden group input cleanly
    allPill.emit("click", { preventDefault() {} });
    assert.strictEqual(groupInput.value, "");
    assert.strictEqual(groupInput.disabled, true);
    console.log("finder-js-ok");
    """
    result = subprocess.run(
        [node_bin, "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "finder-js-ok" in result.stdout
