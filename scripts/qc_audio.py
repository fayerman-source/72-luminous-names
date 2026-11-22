import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys

MIN_DURATION_SEC = 5.0
MAX_DURATION_SEC = 45.0
MIN_SIZE_KB = 50.0
SILENCE_NOISE_DB = -45.0
MIN_SILENCE_DETECT_SEC = 4.0
MAX_SILENCE_SEC = 4.0
MIN_MEAN_VOLUME_DB = -30.0
MAX_MEAN_VOLUME_DB = -16.0
MAX_MEDIAN_SWING_DB = 4.5
MAX_CATALOG_SPREAD_DB = 6.0


def parse_db(raw_value):
    if raw_value is None:
        return None
    cleaned = raw_value.replace("dB", "").strip()
    if cleaned in {"-inf", "-infinity"}:
        return float("-inf")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_ffmpeg_audio_stats(stderr_text, total_duration=0.0):
    max_vol_db = None
    mean_vol_db = None
    silences = []
    open_silence_start = None

    for line in stderr_text.splitlines():
        if "max_volume:" in line:
            max_vol_db = parse_db(line.split("max_volume:", 1)[1])
        elif "mean_volume:" in line:
            mean_vol_db = parse_db(line.split("mean_volume:", 1)[1])
        elif "silence_start:" in line:
            try:
                open_silence_start = float(line.split("silence_start:", 1)[1].strip())
            except ValueError:
                open_silence_start = None
        elif "silence_duration:" in line:
            try:
                dur = float(line.split("silence_duration:", 1)[1].strip().split()[0])
                silences.append(dur)
                open_silence_start = None
            except ValueError:
                pass

    if open_silence_start is not None and total_duration > open_silence_start:
        silences.append(total_duration - open_silence_start)

    return {
        "max_vol_db": max_vol_db,
        "mean_vol_db": mean_vol_db,
        "silences": silences,
        "max_silence_sec": max(silences) if silences else 0.0,
    }


def get_audio_info(file_path):
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(file_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def get_audio_stats(file_path, total_duration=0.0, min_silence_sec=MIN_SILENCE_DETECT_SEC):
    detect_sec = max(0.1, float(min_silence_sec))
    filter_chain = (
        f"volumedetect,silencedetect=noise={SILENCE_NOISE_DB}dB:d={detect_sec}"
    )
    cmd = [
        "ffmpeg", "-i", str(file_path), "-af", filter_chain, "-f", "null", os.devnull,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return parse_ffmpeg_audio_stats(result.stderr, total_duration=total_duration)


def evaluate_track(
    track,
    median_mean_db=None,
    min_duration_sec=MIN_DURATION_SEC,
    max_duration_sec=MAX_DURATION_SEC,
    min_size_kb=MIN_SIZE_KB,
    max_silence_sec=MAX_SILENCE_SEC,
    min_mean_db=MIN_MEAN_VOLUME_DB,
    max_mean_db=MAX_MEAN_VOLUME_DB,
    max_median_swing_db=MAX_MEDIAN_SWING_DB,
):
    if not track.get("exists", False):
        return ["MISSING"]
    if not track.get("probe_ok", True):
        return ["UNREADABLE"]

    issues = []
    duration = track["duration_sec"]
    size_kb = track["size_kb"]
    max_vol_db = track["max_vol_db"]
    mean_vol_db = track["mean_vol_db"]
    longest_silence = track.get("max_silence_sec", 0.0)

    if max_vol_db == float("-inf") or mean_vol_db == float("-inf"):
        issues.append("SILENT")
    if duration < min_duration_sec:
        issues.append("SHORT")
    if duration > max_duration_sec:
        issues.append("OVERLONG")
    if size_kb < min_size_kb:
        issues.append("SMALL")
    if longest_silence >= max_silence_sec and "SILENT" not in issues:
        issues.append(f"LONG_SILENCE({longest_silence:.1f}s)")

    if mean_vol_db is not None and mean_vol_db != float("-inf"):
        swing_flagged = False
        if mean_vol_db < min_mean_db:
            issues.append("TOO_QUIET")
            swing_flagged = True
        elif mean_vol_db > max_mean_db:
            issues.append("TOO_LOUD")
            swing_flagged = True

        if median_mean_db is not None and abs(mean_vol_db - median_mean_db) > max_median_swing_db:
            if not swing_flagged:
                delta = mean_vol_db - median_mean_db
                issues.append(f"LOUDNESS_SWING({delta:+.1f}dB)")

    return issues


def evaluate_catalog(
    tracks,
    max_duration_sec=MAX_DURATION_SEC,
    max_silence_sec=MAX_SILENCE_SEC,
    max_median_swing_db=MAX_MEDIAN_SWING_DB,
    max_catalog_spread_db=MAX_CATALOG_SPREAD_DB,
):
    valid_means = [
        t["mean_vol_db"]
        for t in tracks
        if t.get("exists")
        and t.get("probe_ok", True)
        and t.get("mean_vol_db") is not None
        and t["mean_vol_db"] != float("-inf")
    ]
    median_mean_db = statistics.median(valid_means) if valid_means else None
    spread_db = (max(valid_means) - min(valid_means)) if len(valid_means) >= 2 else 0.0

    results = []
    for t in tracks:
        issues = evaluate_track(
            t,
            median_mean_db=median_mean_db,
            max_duration_sec=max_duration_sec,
            max_silence_sec=max_silence_sec,
            max_median_swing_db=max_median_swing_db,
        )
        enriched = dict(t)
        enriched["issues"] = issues
        results.append(enriched)

    return {
        "tracks": results,
        "median_mean_db": median_mean_db,
        "min_mean_db": min(valid_means) if valid_means else None,
        "max_mean_db": max(valid_means) if valid_means else None,
        "spread_db": spread_db,
        "spread_exceeded": spread_db > max_catalog_spread_db,
    }


def format_db(val):
    if val is None:
        return "N/A"
    if val == float("-inf"):
        return "-inf dB"
    return f"{val:.1f} dB"


def run_qc(
    audio_dir=None,
    max_duration_sec=MAX_DURATION_SEC,
    max_silence_sec=MAX_SILENCE_SEC,
    max_median_swing_db=MAX_MEDIAN_SWING_DB,
):
    if audio_dir is None:
        audio_dir = Path(__file__).resolve().parents[1] / "static" / "audio"
    else:
        audio_dir = Path(audio_dir)

    raw_tracks = []
    for i in range(1, 73):
        file_path = audio_dir / f"{i}.mp3"
        if not file_path.exists():
            raw_tracks.append({"id": i, "exists": False})
            continue

        size_kb = file_path.stat().st_size / 1024.0
        info = get_audio_info(file_path)
        if not info or "format" not in info or "duration" not in info["format"]:
            raw_tracks.append({"id": i, "exists": True, "probe_ok": False, "size_kb": size_kb})
            continue

        duration = float(info["format"]["duration"])
        stats = get_audio_stats(
            file_path,
            total_duration=duration,
            min_silence_sec=max_silence_sec,
        )
        raw_tracks.append({
            "id": i,
            "exists": True,
            "probe_ok": True,
            "duration_sec": duration,
            "size_kb": size_kb,
            "max_vol_db": stats["max_vol_db"],
            "mean_vol_db": stats["mean_vol_db"],
            "max_silence_sec": stats["max_silence_sec"],
            "silences": stats["silences"],
        })

    summary = evaluate_catalog(
        raw_tracks,
        max_duration_sec=max_duration_sec,
        max_silence_sec=max_silence_sec,
        max_median_swing_db=max_median_swing_db,
    )

    header = (
        f"{'ID':<4} | {'Duration':<9} | {'Max Vol':<10} | {'Mean Vol':<10} | "
        f"{'Max Sil':<8} | {'Size':<9} | Status"
    )
    print(header)
    print("-" * len(header))

    failed = []
    for item in summary["tracks"]:
        issues = item["issues"]
        if not item.get("exists"):
            print(f"{item['id']:<4} | {'-':<9} | {'-':<10} | {'-':<10} | {'-':<8} | {'-':<9} | FAIL: MISSING")
            failed.append(item)
            continue
        if not item.get("probe_ok", True):
            print(f"{item['id']:<4} | {'-':<9} | {'-':<10} | {'-':<10} | {'-':<8} | {item['size_kb']:>7.1f}K | FAIL: UNREADABLE")
            failed.append(item)
            continue

        status = "OK" if not issues else "FAIL: " + ", ".join(issues)
        if issues:
            failed.append(item)
        print(
            f"{item['id']:<4} | {item['duration_sec']:>8.2f}s | "
            f"{format_db(item['max_vol_db']):<10} | {format_db(item['mean_vol_db']):<10} | "
            f"{item['max_silence_sec']:>6.2f}s | {item['size_kb']:>7.1f}K | {status}"
        )

    print("-" * len(header))
    if summary["median_mean_db"] is not None:
        spread_note = "FAIL" if summary["spread_exceeded"] else "OK"
        print(
            f"Loudness summary: median={summary['median_mean_db']:.1f} dB, "
            f"range=[{summary['min_mean_db']:.1f} dB, {summary['max_mean_db']:.1f} dB], "
            f"spread={summary['spread_db']:.1f} dB ({spread_note}, max allowed {MAX_CATALOG_SPREAD_DB:.1f} dB)"
        )
    print(f"Tracks passing: {len(summary['tracks']) - len(failed)}/{len(summary['tracks'])}; failing: {len(failed)}")

    has_failure = bool(failed) or summary["spread_exceeded"]
    return 1 if has_failure else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit static/audio/{1..72}.mp3 quality.")
    parser.add_argument("--audio-dir", default=None, help="Directory containing {1..72}.mp3")
    parser.add_argument("--max-duration", type=float, default=MAX_DURATION_SEC, help="Max duration in seconds")
    parser.add_argument("--max-silence", type=float, default=MAX_SILENCE_SEC, help="Max single silence in seconds")
    parser.add_argument("--max-swing", type=float, default=MAX_MEDIAN_SWING_DB, help="Max dB deviation from catalog median")
    args = parser.parse_args(argv)
    return run_qc(
        audio_dir=args.audio_dir,
        max_duration_sec=args.max_duration,
        max_silence_sec=args.max_silence,
        max_median_swing_db=args.max_swing,
    )


if __name__ == "__main__":
    sys.exit(main())
