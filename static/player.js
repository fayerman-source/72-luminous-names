(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.LuminousPlayer = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function formatRemainingSeconds(totalSeconds) {
    var clamped = Math.max(0, Math.ceil(Number(totalSeconds) || 0));
    var mins = Math.floor(clamped / 60);
    var secs = clamped % 60;
    var mm = mins < 10 ? "0" + mins : String(mins);
    var ss = secs < 10 ? "0" + secs : String(secs);
    return mm + ":" + ss;
  }

  function computeActiveLetterIndex(currentTimeSec, trackDurationSec, letterCount) {
    var count = Math.max(1, Number(letterCount) || 3);
    var t = Math.max(0, Number(currentTimeSec) || 0);
    var rawDur = Number(trackDurationSec);
    // Pace right-to-left scanning across the track duration, capped at 24s per
    // 3-letter cycle so multi-pass recordings still advance steadily.
    var cycleSec = rawDur > 0 && isFinite(rawDur) ? Math.min(rawDur, 24) : 18;
    var posInCycle = t % cycleSec;
    var idx = Math.floor((posInCycle / cycleSec) * count);
    return Math.min(count - 1, Math.max(0, idx));
  }

  function computeBreathPhase(elapsedSec, intervalSec) {
    var total = Math.max(1, Number(intervalSec) || 6);
    var elapsed = Math.max(0, Number(elapsedSec) || 0);
    if (elapsed < total / 2) {
      return "Inhale slowly — scan right to left";
    }
    return "Exhale gently — rest in the intention";
  }

  function createDroneEngine() {
    var ctx = null;
    var masterGain = null;
    var oscillators = [];
    var active = false;

    function ensureContext() {
      if (!ctx) {
        var AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return null;
        ctx = new AudioCtx();
      }
      if (ctx.state === "suspended") {
        ctx.resume().catch(function () {});
      }
      return ctx;
    }

    function playChime() {
      var audioCtx = ensureContext();
      if (!audioCtx) return;
      var now = audioCtx.currentTime;
      var osc = audioCtx.createOscillator();
      var gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(432, now);
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.05, now + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.8);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 1.85);
    }

    function start() {
      if (active) return;
      var audioCtx = ensureContext();
      if (!audioCtx) return;

      var now = audioCtx.currentTime;
      var filter = audioCtx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(280, now);

      masterGain = audioCtx.createGain();
      masterGain.gain.setValueAtTime(0.0001, now);
      masterGain.gain.exponentialRampToValueAtTime(0.055, now + 1.4);

      filter.connect(masterGain);
      masterGain.connect(audioCtx.destination);

      var voices = [
        { freq: 110.0, type: "sine", gain: 0.6 },
        { freq: 165.0, type: "sine", gain: 0.3 },
        { freq: 220.0, type: "triangle", gain: 0.15 }
      ];

      oscillators = voices.map(function (v) {
        var osc = audioCtx.createOscillator();
        var voiceGain = audioCtx.createGain();
        osc.type = v.type;
        osc.frequency.setValueAtTime(v.freq, now);
        voiceGain.gain.setValueAtTime(v.gain, now);
        osc.connect(voiceGain);
        voiceGain.connect(filter);
        osc.start(now);
        return osc;
      });

      active = true;
    }

    function stop() {
      if (!active || !ctx || !masterGain) {
        active = false;
        return;
      }
      var now = ctx.currentTime;
      var toStop = oscillators.slice();
      oscillators = [];
      active = false;
      try {
        masterGain.gain.cancelScheduledValues(now);
        masterGain.gain.setValueAtTime(Math.max(0.0001, masterGain.gain.value), now);
        masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.6);
      } catch (_e) {}
      setTimeout(function () {
        toStop.forEach(function (osc) {
          try {
            osc.stop();
            osc.disconnect();
          } catch (_err) {}
        });
      }, 650);
    }

    return { start: start, stop: stop, playChime: playChime };
  }

  function initDomPlayer() {
    if (typeof document === "undefined") return;
    var audio = document.getElementById("chant-audio");
    var toggleBtn = document.getElementById("session-toggle-btn");
    var durationSelect = document.getElementById("session-duration");
    var intervalSelect = document.getElementById("breath-interval");
    var droneCheckbox = document.getElementById("drone-enabled");
    var cueEl = document.getElementById("breath-cue");
    var timerEl = document.getElementById("session-timer");
    var letterEls = Array.prototype.slice.call(
      document.querySelectorAll(".hebrew-letter")
    );

    if (!audio || !toggleBtn || !durationSelect || !intervalSelect) return;

    var drone = createDroneEngine();
    var running = false;
    var inBreathPause = false;
    var sessionEndMs = 0;
    var pauseStartMs = 0;
    var pauseTotalSec = 6;
    var cycleCount = 0;
    var tickTimer = null;
    var breathTimeout = null;
    var wakeLockSentinel = null;
    var sessionToken = 0;

    function setHighlightedLetter(activeIndex) {
      letterEls.forEach(function (el, idx) {
        if (idx === activeIndex) {
          el.classList.add("is-active");
        } else {
          el.classList.remove("is-active");
        }
      });
    }

    function updateIdleTimerPreview() {
      if (running || !timerEl) return;
      var secs = Number(durationSelect.value) || 300;
      timerEl.textContent = formatRemainingSeconds(secs) + " session ready";
    }

    function acquireWakeLock(expectedToken) {
      if (navigator.wakeLock && navigator.wakeLock.request) {
        navigator.wakeLock.request("screen").then(function (sentinel) {
          if (!running || sessionToken !== expectedToken) {
            if (sentinel && sentinel.release) {
              sentinel.release().catch(function () {});
            }
            return;
          }
          wakeLockSentinel = sentinel;
        }).catch(function () {});
      }
    }

    function releaseWakeLock() {
      if (wakeLockSentinel && wakeLockSentinel.release) {
        wakeLockSentinel.release().catch(function () {});
        wakeLockSentinel = null;
      }
    }

    function startChantCycle() {
      if (!running) return;
      inBreathPause = false;
      cycleCount += 1;
      if (cueEl) {
        cueEl.textContent = "Chanting — follow each illuminated letter right to left";
      }
      audio.currentTime = 0;
      var playPromise = audio.play();
      if (playPromise && playPromise.catch) {
        playPromise.catch(function () {
          if (cueEl) {
            cueEl.textContent = "Tap play on the audio bar below to allow browser playback";
          }
        });
      }
    }

    function stopSession(completed) {
      sessionToken += 1;
      running = false;
      inBreathPause = false;
      if (tickTimer) {
        clearInterval(tickTimer);
        tickTimer = null;
      }
      if (breathTimeout) {
        clearTimeout(breathTimeout);
        breathTimeout = null;
      }
      audio.pause();
      audio.currentTime = 0;
      if (completed && droneCheckbox && droneCheckbox.checked) {
        drone.playChime();
      }
      drone.stop();
      releaseWakeLock();
      setHighlightedLetter(-1);
      toggleBtn.textContent = "Begin Timed Session";
      toggleBtn.setAttribute("aria-pressed", "false");
      if (cueEl) {
        cueEl.textContent = completed
          ? "Session complete — sit quietly for a breath"
          : "Scan right to left · Choose duration and press Begin Timed Session";
      }
      if (timerEl) {
        timerEl.textContent = completed
          ? "Completed " + cycleCount + (cycleCount === 1 ? " chant cycle" : " chant cycles")
          : formatRemainingSeconds(Number(durationSelect.value) || 300) + " session ready";
      }
    }

    function onTick() {
      if (!running) return;
      var remainingSec = (sessionEndMs - Date.now()) / 1000;
      if (remainingSec <= 0) {
        stopSession(true);
        return;
      }
      if (timerEl) {
        timerEl.textContent =
          formatRemainingSeconds(remainingSec) + " remaining · Cycle " + Math.max(1, cycleCount);
      }
      if (inBreathPause) {
        var elapsedPause = (Date.now() - pauseStartMs) / 1000;
        if (cueEl) {
          cueEl.textContent = computeBreathPhase(elapsedPause, pauseTotalSec);
        }
      } else if (!audio.paused) {
        var idx = computeActiveLetterIndex(audio.currentTime, audio.duration, letterEls.length);
        setHighlightedLetter(idx);
      }
    }

    toggleBtn.addEventListener("click", function () {
      if (running) {
        stopSession(false);
        return;
      }
      var durationSec = Number(durationSelect.value) || 300;
      pauseTotalSec = Number(intervalSelect.value) || 6;
      sessionEndMs = Date.now() + durationSec * 1000;
      cycleCount = 0;
      sessionToken += 1;
      running = true;
      toggleBtn.textContent = "End Session";
      toggleBtn.setAttribute("aria-pressed", "true");
      acquireWakeLock(sessionToken);

      if (droneCheckbox && droneCheckbox.checked) {
        drone.playChime();
        drone.start();
      }
      startChantCycle();
      onTick();
      tickTimer = setInterval(onTick, 200);
    });

    audio.addEventListener("play", function () {
      if (!running || !inBreathPause) return;
      if (breathTimeout) {
        clearTimeout(breathTimeout);
        breathTimeout = null;
      }
      inBreathPause = false;
      cycleCount += 1;
      if (cueEl) {
        cueEl.textContent = "Chanting — follow each illuminated letter right to left";
      }
    });

    audio.addEventListener("timeupdate", function () {
      if (!audio.paused && letterEls.length > 0) {
        var idx = computeActiveLetterIndex(audio.currentTime, audio.duration, letterEls.length);
        setHighlightedLetter(idx);
      }
    });

    audio.addEventListener("ended", function () {
      if (!running) {
        setHighlightedLetter(-1);
        return;
      }
      var remainingMs = sessionEndMs - Date.now();
      pauseTotalSec = Number(intervalSelect.value) || 6;
      if (remainingMs <= 1000) {
        stopSession(true);
        return;
      }
      inBreathPause = true;
      pauseStartMs = Date.now();
      setHighlightedLetter(-1);
      if (cueEl) {
        cueEl.textContent = computeBreathPhase(0, pauseTotalSec);
      }
      breathTimeout = setTimeout(function () {
        if (running && Date.now() < sessionEndMs) {
          startChantCycle();
        } else if (running) {
          stopSession(true);
        }
      }, Math.min(remainingMs, pauseTotalSec * 1000));
    });

    if (droneCheckbox) {
      droneCheckbox.addEventListener("change", function () {
        if (!running) return;
        if (droneCheckbox.checked) {
          drone.start();
        } else {
          drone.stop();
        }
      });
    }

    durationSelect.addEventListener("change", updateIdleTimerPreview);
    window.addEventListener("pagehide", function () {
      if (running) stopSession(false);
    });
    updateIdleTimerPreview();
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initDomPlayer);
    } else {
      initDomPlayer();
    }
  }

  return {
    formatRemainingSeconds: formatRemainingSeconds,
    computeActiveLetterIndex: computeActiveLetterIndex,
    computeBreathPhase: computeBreathPhase,
    initDomPlayer: initDomPlayer
  };
});
