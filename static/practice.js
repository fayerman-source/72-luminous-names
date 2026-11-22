(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.LuminousPractice = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var STORAGE_KEY = "luminous72.practice.v1";
  var DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

  function validNameId(val) {
    var n = Number(val);
    return Number.isInteger(n) && n >= 1 && n <= 72 ? n : null;
  }

  function uniqueSortedNumbers(items) {
    var seen = {};
    var out = [];
    (Array.isArray(items) ? items : []).forEach(function (v) {
      var id = validNameId(v);
      if (id !== null && !seen[id]) {
        seen[id] = true;
        out.push(id);
      }
    });
    return out.sort(function (a, b) { return a - b; });
  }

  function uniqueSortedDates(items) {
    var seen = {};
    var out = [];
    (Array.isArray(items) ? items : []).forEach(function (v) {
      var s = typeof v === "string" ? v.trim() : "";
      if (DATE_RE.test(s) && !seen[s]) {
        seen[s] = true;
        out.push(s);
      }
    });
    return out.sort();
  }

  function normalizeState(raw) {
    var obj = raw && typeof raw === "object" ? raw : {};
    return {
      savedIds: uniqueSortedNumbers(obj.savedIds),
      practicedDates: uniqueSortedDates(obj.practicedDates),
      completedNameIds: uniqueSortedNumbers(obj.completedNameIds)
    };
  }

  function formatLocalDate(dateObj) {
    var d = dateObj instanceof Date ? dateObj : new Date();
    var y = d.getFullYear();
    var m = d.getMonth() + 1;
    var day = d.getDate();
    return (
      String(y) +
      "-" +
      (m < 10 ? "0" + m : String(m)) +
      "-" +
      (day < 10 ? "0" + day : String(day))
    );
  }

  function toggleSavedName(state, nameId) {
    var clean = normalizeState(state);
    var id = validNameId(nameId);
    if (id === null) return clean;
    var exists = clean.savedIds.indexOf(id) !== -1;
    var nextSaved = exists
      ? clean.savedIds.filter(function (x) { return x !== id; })
      : clean.savedIds.concat([id]);
    return normalizeState({
      savedIds: nextSaved,
      practicedDates: clean.practicedDates,
      completedNameIds: clean.completedNameIds
    });
  }

  function recordPracticeDay(state, nameId, dateStr) {
    var clean = normalizeState(state);
    var day = DATE_RE.test(String(dateStr || "")) ? String(dateStr) : formatLocalDate(new Date());
    var id = validNameId(nameId);
    var nextDates = clean.practicedDates.concat([day]);
    var nextCompleted = id !== null ? clean.completedNameIds.concat([id]) : clean.completedNameIds;
    return normalizeState({
      savedIds: clean.savedIds,
      practicedDates: nextDates,
      completedNameIds: nextCompleted
    });
  }

  function getDayProgress(state) {
    var clean = normalizeState(state);
    var totalDays = clean.practicedDates.length;
    var cycleDay = totalDays === 0 ? 0 : ((totalDays - 1) % 72) + 1;
    return {
      totalDays: totalDays,
      cycleDay: cycleDay,
      savedCount: clean.savedIds.length,
      completedNamesCount: clean.completedNameIds.length
    };
  }

  function loadState() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      return raw ? normalizeState(JSON.parse(raw)) : normalizeState({});
    } catch (_e) {
      return normalizeState({});
    }
  }

  function saveState(state) {
    var clean = normalizeState(state);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(clean));
    } catch (_e) {}
    return clean;
  }

  function parseSessionIdFromPath(pathname) {
    var match = /^\/session\/(\d+)\/?$/.exec(pathname || "");
    return match ? validNameId(Number(match[1])) : null;
  }

  function parseCardNameId(anchorEl) {
    var match = /\/session\/(\d+)/.exec(anchorEl.getAttribute("href") || "");
    return match ? validNameId(Number(match[1])) : null;
  }

  function initDom(nowProvider) {
    if (typeof document === "undefined") return;

    var getNow = typeof nowProvider === "function" ? nowProvider : function () { return new Date(); };
    var state = loadState();
    var lastRenderedDay = formatLocalDate(getNow());
    var badgeEl = document.getElementById("practice-summary-badge");
    var refreshActiveView = null;

    function currentToday() {
      return formatLocalDate(getNow());
    }

    function renderHeaderBadge() {
      if (!badgeEl) return;
      var prog = getDayProgress(state);
      if (prog.totalDays === 0 && prog.savedCount === 0) {
        badgeEl.hidden = true;
        badgeEl.textContent = "";
        return;
      }
      var parts = [];
      if (prog.totalDays > 0) {
        parts.push("Day " + prog.cycleDay + "/72");
      }
      if (prog.savedCount > 0) {
        parts.push("★ " + prog.savedCount + " saved");
      }
      badgeEl.textContent = parts.join(" · ");
      badgeEl.hidden = false;
    }

    var sessionId = parseSessionIdFromPath(window.location.pathname);
    if (sessionId !== null) {
      var playerRoot = document.querySelector(".player");
      var anchorTarget = playerRoot && playerRoot.querySelector(".audio-player");
      if (playerRoot && anchorTarget) {
        var bar = document.createElement("div");
        bar.className = "practice-session-bar";

        var saveBtn = document.createElement("button");
        saveBtn.type = "button";
        saveBtn.className = "practice-chip";

        var markBtn = document.createElement("button");
        markBtn.type = "button";
        markBtn.className = "practice-chip";

        var dayLabel = document.createElement("span");
        dayLabel.className = "practice-day-readout";

        bar.appendChild(saveBtn);
        bar.appendChild(markBtn);
        bar.appendChild(dayLabel);
        playerRoot.insertBefore(bar, anchorTarget);

        function renderSessionControls() {
          var today = currentToday();
          lastRenderedDay = today;
          var isSaved = state.savedIds.indexOf(sessionId) !== -1;
          var practicedToday = state.practicedDates.indexOf(today) !== -1;
          var prog = getDayProgress(state);

          saveBtn.textContent = isSaved ? "★ Saved" : "☆ Save Name";
          saveBtn.setAttribute("aria-pressed", isSaved ? "true" : "false");
          saveBtn.classList.toggle("is-active", isSaved);

          markBtn.textContent = practicedToday ? "✓ Practiced today" : "Mark practiced today";
          markBtn.setAttribute("aria-pressed", practicedToday ? "true" : "false");
          markBtn.classList.toggle("is-active", practicedToday);

          dayLabel.textContent =
            prog.totalDays > 0
              ? "Day " + prog.cycleDay + " of 72 (" + prog.totalDays + (prog.totalDays === 1 ? " day" : " days") + " total)"
              : "Day 0 of 72 · Local-only practice log";
          renderHeaderBadge();
        }

        refreshActiveView = renderSessionControls;

        saveBtn.addEventListener("click", function () {
          state = saveState(toggleSavedName(loadState(), sessionId));
          renderSessionControls();
        });

        markBtn.addEventListener("click", function () {
          state = saveState(recordPracticeDay(loadState(), sessionId, currentToday()));
          renderSessionControls();
        });

        var audioEl = playerRoot.querySelector("audio");
        if (audioEl) {
          audioEl.addEventListener("ended", function () {
            state = saveState(recordPracticeDay(loadState(), sessionId, currentToday()));
            renderSessionControls();
          });
        }

        renderSessionControls();
      }
    }

    if (window.location.pathname === "/library") {
      var sessionLinks = Array.prototype.slice.call(
        document.querySelectorAll('a[href^="/session/"]')
      );
      if (sessionLinks.length > 0) {
        var gridParent = sessionLinks[0].parentElement;
        var filterSavedOnly = false;

        var libBar = document.createElement("div");
        libBar.className = "practice-library-bar";

        var summaryText = document.createElement("span");
        summaryText.className = "practice-day-readout";

        var savedToggle = document.createElement("button");
        savedToggle.type = "button";
        savedToggle.className = "practice-chip";
        savedToggle.setAttribute("aria-pressed", "false");

        var emptySavedMsg = document.createElement("p");
        emptySavedMsg.className = "practice-empty-note";
        emptySavedMsg.hidden = true;
        emptySavedMsg.textContent = "No saved names yet — open any name and press Save Name.";

        libBar.appendChild(summaryText);
        libBar.appendChild(savedToggle);

        if (gridParent && gridParent.parentElement) {
          gridParent.parentElement.insertBefore(libBar, gridParent);
          gridParent.parentElement.insertBefore(emptySavedMsg, gridParent);
        }

        function renderLibraryPractice() {
          var prog = getDayProgress(state);
          summaryText.textContent =
            prog.totalDays > 0
              ? "Practice: Day " + prog.cycleDay + " of 72 · " + prog.completedNamesCount + "/72 names visited"
              : "Local practice: 0 days logged · Saved only in this browser";
          savedToggle.textContent = "★ Saved only (" + prog.savedCount + ")";
          savedToggle.setAttribute("aria-pressed", filterSavedOnly ? "true" : "false");
          savedToggle.classList.toggle("is-active", filterSavedOnly);

          var visibleSaved = 0;
          sessionLinks.forEach(function (card) {
            var id = parseCardNameId(card);
            if (id === null) return;
            var isSaved = state.savedIds.indexOf(id) !== -1;
            var isDone = state.completedNameIds.indexOf(id) !== -1;

            var marker = card.querySelector(".practice-card-marker");
            if (!marker && (isSaved || isDone)) {
              marker = document.createElement("div");
              marker.className = "practice-card-marker";
              card.appendChild(marker);
            }
            if (marker) {
              var flags = [];
              if (isSaved) flags.push("★ Saved");
              if (isDone) flags.push("✓ Practiced");
              marker.textContent = flags.join(" · ");
              marker.hidden = flags.length === 0;
            }

            if (filterSavedOnly) {
              card.style.display = isSaved ? "" : "none";
              if (isSaved) visibleSaved += 1;
            } else {
              card.style.display = "";
            }
          });

          emptySavedMsg.hidden = !(filterSavedOnly && visibleSaved === 0);
          renderHeaderBadge();
        }

        refreshActiveView = renderLibraryPractice;

        savedToggle.addEventListener("click", function () {
          state = loadState();
          filterSavedOnly = !filterSavedOnly;
          renderLibraryPractice();
        });

        renderLibraryPractice();
      }
    }

    function syncExternalState() {
      state = loadState();
      if (refreshActiveView) {
        refreshActiveView();
      } else {
        renderHeaderBadge();
      }
    }

    if (typeof window !== "undefined" && window.addEventListener) {
      window.addEventListener("storage", function (ev) {
        if (!ev || !ev.key || ev.key === STORAGE_KEY) {
          syncExternalState();
        }
      });
      window.addEventListener("focus", syncExternalState);
    }
    if (document.addEventListener) {
      document.addEventListener("visibilitychange", function () {
        if (!document.hidden) syncExternalState();
      });
    }
    var midnightTimer = setInterval(function () {
      if (currentToday() !== lastRenderedDay) {
        syncExternalState();
      }
    }, 60000);
    if (midnightTimer && typeof midnightTimer.unref === "function") {
      midnightTimer.unref();
    }

    renderHeaderBadge();
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () { initDom(); });
    } else {
      initDom();
    }
  }

  return {
    STORAGE_KEY: STORAGE_KEY,
    normalizeState: normalizeState,
    formatLocalDate: formatLocalDate,
    toggleSavedName: toggleSavedName,
    recordPracticeDay: recordPracticeDay,
    getDayProgress: getDayProgress,
    initDom: initDom
  };
});
