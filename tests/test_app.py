from pathlib import Path
import os
import shutil
import subprocess
import sys
import pytest

from app import GROUP_BY_NAME_ID, NAMES, SITUATION_GROUPS, app, get_public_base_url


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


def test_names_catalog_matches_exodus_14_19_21():
    # Masoretic consonantal text of Exodus 14:19-21 (72 letters per verse):
    # v.19 forward, v.20 reversed, v.21 forward.
    v19 = "ויסעמלאךהאלהיםההלךלפנימחנהישראלוילךמאחריהםויסעעמודהענןמפניהםויעמדמאחריהם"
    v20 = "ויבאביןמחנהמצריםוביןמחנהישראלויהיהענןוהחשךויאראתהלילהולאקרבזהאלזהכלהלילה"
    v21 = "ויטמשהאתידועלהיםויולךיהוהאתהיםברוחקדיםעזהכלהלילהוישםאתהיםלחרבהויבקעוהמים"
    sofit_to_medial = str.maketrans("ךםןףץ", "כמנפצ")

    assert len(v19) == len(v20) == len(v21) == 72
    for idx, entry in enumerate(NAMES):
        expected = (v19[idx] + v20[71 - idx] + v21[idx]).translate(sofit_to_medial)
        actual = entry["name"].translate(sofit_to_medial)
        assert actual == expected, f"Name #{entry['id']} {entry['name']} != {expected}"

    assert NAMES[2]["name"] == "סיט"
    assert NAMES[2]["transliteration"] == "Samech Yud Tet"


def test_session_3_renders_corrected_triad():
    client = app.test_client()

    html = client.get("/session/3").data.decode("utf-8")

    assert "סיט" in html
    assert "Samech Yud Tet" in html
    assert "סית" not in html
    assert "Samech Yud Tav" not in html


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
    assert 'href="/library?q=anger"' in anger_html
    assert 'href="/library?group=peace&amp;q=anger"' in anger_html

    encoded_resp = client.get("/library?q=time+travel")
    encoded_html = encoded_resp.data.decode("utf-8")
    assert 'href="/library?group=clarity&amp;q=time+travel"' in encoded_html

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


def test_player_js_releases_late_wakelock_and_cancels_breath_timeout_on_manual_play():
    node_bin = shutil.which("node")
    if node_bin is None:
        return

    script = """
    const assert = require("assert");

    function makeElem(initialValue) {
      const listeners = {};
      return {
        value: initialValue || "",
        checked: false,
        textContent: "",
        paused: true,
        currentTime: 0,
        duration: 18,
        attrs: {},
        classList: { add() {}, remove() {} },
        setAttribute(k, v) { this.attrs[k] = v; },
        addEventListener(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); },
        emit(ev) { (listeners[ev] || []).forEach(fn => fn()); },
        play() { this.paused = false; this.emit("play"); return Promise.resolve(); },
        pause() { this.paused = true; }
      };
    }

    const els = {
      "chant-audio": makeElem(),
      "session-toggle-btn": makeElem(),
      "session-duration": makeElem("180"),
      "breath-interval": makeElem("1"),
      "drone-enabled": makeElem(),
      "breath-cue": makeElem(),
      "session-timer": makeElem()
    };

    let resolveWakeLock;
    let sentinelReleased = 0;
    const sentinel = { release() { sentinelReleased += 1; return Promise.resolve(); } };

    global.window = { addEventListener() {} };
    Object.defineProperty(globalThis, "navigator", {
      value: {
        wakeLock: {
          request() {
            return new Promise(res => { resolveWakeLock = res; });
          }
        }
      },
      configurable: true
    });
    global.document = {
      readyState: "complete",
      getElementById(id) { return els[id] || null; },
      querySelectorAll() { return [makeElem(), makeElem(), makeElem()]; }
    };

    const player = require("./static/player.js");

    // 1. Start session, then stop BEFORE wakeLock promise resolves -> sentinel must release immediately on resolve
    els["session-toggle-btn"].emit("click");
    els["session-toggle-btn"].emit("click");
    resolveWakeLock(sentinel);

    setImmediate(() => {
      assert.strictEqual(sentinelReleased, 1, "Late wakeLock sentinel should be released");

      // 2. Start session, finish first chant -> enter breath pause -> user manually plays audio
      els["breath-interval"].value = "0.05";
      els["session-toggle-btn"].emit("click");
      resolveWakeLock(sentinel);
      els["chant-audio"].paused = true;
      els["chant-audio"].emit("ended");
      assert.ok(els["breath-cue"].textContent.includes("Inhale"));

      // Simulate native Play mid-breath-pause at currentTime = 5s
      els["chant-audio"].currentTime = 5;
      els["chant-audio"].paused = false;
      els["chant-audio"].emit("play");
      assert.ok(els["breath-cue"].textContent.includes("Chanting"));

      setTimeout(() => {
        // Stale breathTimeout must NOT have fired and reset currentTime to 0
        assert.strictEqual(els["chant-audio"].currentTime, 5);
        els["session-toggle-btn"].emit("click");
        console.log("player-dom-edge-cases-ok");
      }, 90);
    });
    """
    result = subprocess.run(
        [node_bin, "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "player-dom-edge-cases-ok" in result.stdout


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


def test_production_host_works_with_no_new_environment_variables():
    base_env = os.environ.copy()
    for var in ("PUBLIC_BASE_URL", "TRUSTED_HOSTS", "TRUST_PROXY", "SECRET_KEY", "FLASK_DEBUG", "VERCEL"):
        base_env.pop(var, None)

    probe = """
import app as app_mod

client = app_mod.app.test_client()
for path in ["/", "/library", "/session/1", "/sitemap.xml", "/robots.txt"]:
    r = client.get(path, headers={"Host": "72-luminous-names.vercel.app"})
    assert r.status_code == 200, (path, r.status_code)

preview = client.get("/", headers={"Host": "72-luminous-names-git-main-fayerman.vercel.app"})
assert preview.status_code == 200
print("prod-host-direct-ok")
"""
    direct = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=Path(__file__).resolve().parents[1],
        env=base_env,
        capture_output=True,
        text=True,
    )
    assert direct.returncode == 0, direct.stderr
    assert "prod-host-direct-ok" in direct.stdout

    vercel_env = base_env.copy()
    vercel_env["VERCEL"] = "1"
    vercel_probe = """
import app as app_mod

client = app_mod.app.test_client()
for path in ["/", "/library", "/session/1", "/sitemap.xml", "/robots.txt"]:
    r = client.get(
        path,
        headers={
            "Host": "internal-lambda.local",
            "X-Forwarded-Host": "72-luminous-names.vercel.app",
            "X-Forwarded-Proto": "https",
        },
    )
    assert r.status_code == 200, (path, r.status_code)
html = client.get(
    "/session/1",
    headers={
        "Host": "internal-lambda.local",
        "X-Forwarded-Host": "72-luminous-names.vercel.app",
        "X-Forwarded-Proto": "https",
    },
).data.decode("utf-8")
assert 'rel="canonical" href="https://72-luminous-names.vercel.app/session/1"' in html
print("prod-host-vercel-ok")
"""
    on_vercel = subprocess.run(
        [sys.executable, "-c", vercel_probe],
        cwd=Path(__file__).resolve().parents[1],
        env=vercel_env,
        capture_output=True,
        text=True,
    )
    assert on_vercel.returncode == 0, on_vercel.stderr
    assert "prod-host-vercel-ok" in on_vercel.stdout
