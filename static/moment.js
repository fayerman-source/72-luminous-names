(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.LuminousMoment = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var MINUTES_PER_WINDOW = 20;

  function formatHhMm(totalMinutes) {
    var wrapped = ((totalMinutes % 1440) + 1440) % 1440;
    var hh = Math.floor(wrapped / 60);
    var mm = wrapped % 60;
    return (hh < 10 ? "0" + hh : String(hh)) + ":" + (mm < 10 ? "0" + mm : String(mm));
  }

  function computeMomentWindow(hour, minute) {
    var h = Math.max(0, Math.min(23, Math.floor(Number(hour) || 0)));
    var m = Math.max(0, Math.min(59, Math.floor(Number(minute) || 0)));
    var minuteOfDay = h * 60 + m;
    var slotIndex = Math.floor(minuteOfDay / MINUTES_PER_WINDOW);
    var startMin = slotIndex * MINUTES_PER_WINDOW;
    var endMin = startMin + MINUTES_PER_WINDOW;
    return {
      slotIndex: slotIndex,
      nameId: slotIndex + 1,
      windowStart: formatHhMm(startMin),
      windowEnd: formatHhMm(endMin)
    };
  }

  function initMomentCard() {
    if (typeof document === "undefined") return;
    var catalogEl = document.getElementById("names-catalog-json");
    var labelEl = document.getElementById("moment-window-label");
    var hebEl = document.getElementById("moment-hebrew");
    var trEl = document.getElementById("moment-translit");
    var meaningEl = document.getElementById("moment-meaning");
    var linkEl = document.getElementById("moment-link");

    if (!catalogEl || !labelEl || !hebEl || !trEl || !meaningEl || !linkEl) return;

    var catalog = [];
    try {
      catalog = JSON.parse(catalogEl.textContent || "[]");
    } catch (_e) {
      return;
    }
    if (catalog.length !== 72) return;

    function refresh() {
      var now = new Date();
      var win = computeMomentWindow(now.getHours(), now.getMinutes());
      var entry = catalog[win.slotIndex];
      if (!entry) return;

      labelEl.textContent =
        "Current 20-minute window · " +
        win.windowStart +
        "–" +
        win.windowEnd +
        " (local time) · #" +
        entry.id +
        " of 72";
      hebEl.textContent = entry.name;
      trEl.textContent = entry.transliteration;
      meaningEl.textContent = entry.meaning + " — " + entry.theme;
      linkEl.setAttribute("href", "/session/" + entry.id);
    }

    refresh();
    setInterval(refresh, 30000);
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initMomentCard);
    } else {
      initMomentCard();
    }
  }

  return {
    MINUTES_PER_WINDOW: MINUTES_PER_WINDOW,
    formatHhMm: formatHhMm,
    computeMomentWindow: computeMomentWindow
  };
});
