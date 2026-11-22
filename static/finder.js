(function () {
  "use strict";
  if (typeof document === "undefined") return;

  function initFinder() {
    var input = document.getElementById("intention-search");
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

    function applyFilter() {
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

      if (window.history && window.history.replaceState) {
        var params = new URLSearchParams();
        if (activeGroup) params.set("group", activeGroup);
        if (q) params.set("q", input.value.trim());
        var nextUrl = window.location.pathname + (params.toString() ? "?" + params.toString() : "");
        window.history.replaceState(null, "", nextUrl);
      }
    }

    input.addEventListener("input", applyFilter);

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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initFinder);
  } else {
    initFinder();
  }
})();
