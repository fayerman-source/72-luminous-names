(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.LuminousFinder = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function initFinder() {
    if (typeof document === "undefined") return;
    var form = document.getElementById("intention-finder-form");
    var input = document.getElementById("intention-search");
    var groupInput = document.getElementById("finder-group-input");
    var cards = Array.prototype.slice.call(document.querySelectorAll(".name-card"));
    var pills = Array.prototype.slice.call(document.querySelectorAll(".group-pill"));
    var statusEl = document.getElementById("finder-status");
    var clientEmptyEl = document.getElementById("finder-client-empty");

    // Only intercept client-side when all 72 cards are present in the DOM;
    // when the page was server-filtered via ?q= or ?group=, normal links reload the full set.
    if (!input || cards.length !== 72) return;

    var activeGroup = "";
    pills.forEach(function (pill) {
      if (pill.classList.contains("is-active")) {
        activeGroup = pill.getAttribute("data-group") || "";
      }
    });

    function syncGroupInput() {
      if (!groupInput && form && document.createElement) {
        groupInput = document.createElement("input");
        groupInput.type = "hidden";
        groupInput.id = "finder-group-input";
        groupInput.name = "group";
        form.insertBefore(groupInput, form.firstChild || null);
      }
      if (groupInput) {
        groupInput.value = activeGroup;
        groupInput.disabled = !activeGroup;
      }
    }

    function applyFilter() {
      syncGroupInput();
      var q = (input.value || "").trim().toLowerCase();
      var visible = 0;

      cards.forEach(function (card) {
        var cardGroup = card.getAttribute("data-group") || "";
        var text = (card.getAttribute("data-search") || "").toLowerCase();
        var groupOk = !activeGroup || cardGroup === activeGroup;
        var queryOk = !q || text.indexOf(q) !== -1;
        var show = groupOk && queryOk;
        card.hidden = !show;
        if (show) visible += 1;
      });

      if (statusEl) {
        var suffix = q ? ' matching "' + input.value.trim() + '"' : "";
        statusEl.textContent = "Showing " + visible + " of 72 names" + suffix;
      }
      if (clientEmptyEl) {
        clientEmptyEl.hidden = visible > 0;
      }

      if (typeof window !== "undefined" && window.history && window.history.replaceState) {
        var params = new URLSearchParams();
        if (activeGroup) params.set("group", activeGroup);
        if (q) params.set("q", input.value.trim());
        var nextUrl = window.location.pathname + (params.toString() ? "?" + params.toString() : "");
        window.history.replaceState(null, "", nextUrl);
      }
    }

    syncGroupInput();
    input.addEventListener("input", applyFilter);

    if (form) {
      form.addEventListener("submit", function (ev) {
        ev.preventDefault();
        applyFilter();
      });
    }

    pills.forEach(function (pill) {
      pill.addEventListener("click", function (ev) {
        ev.preventDefault();
        activeGroup = pill.getAttribute("data-group") || "";
        pills.forEach(function (p) {
          p.classList.toggle("is-active", p === pill);
        });
        applyFilter();
      });
    });
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initFinder);
    } else {
      initFinder();
    }
  }

  return { initFinder: initFinder };
});
