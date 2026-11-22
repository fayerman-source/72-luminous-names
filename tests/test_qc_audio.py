from scripts.qc_audio import (
    evaluate_catalog,
    evaluate_track,
    parse_ffmpeg_audio_stats,
)


def _sample_track(**overrides):
    base = {
        "id": 1,
        "exists": True,
        "probe_ok": True,
        "duration_sec": 24.0,
        "size_kb": 380.0,
        "max_vol_db": -6.5,
        "mean_vol_db": -24.5,
        "max_silence_sec": 1.2,
    }
    base.update(overrides)
    return base


def test_parse_ffmpeg_audio_stats_extracts_volume_and_silences():
    stderr = """
    [silencedetect @ 0x1] silence_start: 14.20
    [silencedetect @ 0x1] silence_end: 26.62 | silence_duration: 12.42
    [Parsed_volumedetect_0 @ 0x2] mean_volume: -31.3 dB
    [Parsed_volumedetect_0 @ 0x2] max_volume: -9.4 dB
    """
    stats = parse_ffmpeg_audio_stats(stderr, total_duration=111.1)

    assert stats["mean_vol_db"] == -31.3
    assert stats["max_vol_db"] == -9.4
    assert stats["max_silence_sec"] == 12.42


def test_parse_ffmpeg_audio_stats_handles_unclosed_trailing_silence():
    stderr = """
    [silencedetect @ 0x1] silence_start: 18.0
    [Parsed_volumedetect_0 @ 0x2] mean_volume: -25.0 dB
    [Parsed_volumedetect_0 @ 0x2] max_volume: -7.0 dB
    """
    stats = parse_ffmpeg_audio_stats(stderr, total_duration=25.5)

    assert stats["max_silence_sec"] == 7.5


def test_evaluate_track_passes_healthy_recording():
    issues = evaluate_track(_sample_track(), median_mean_db=-25.0)
    assert issues == []


def test_evaluate_track_catches_overlong_and_quiet_track():
    issues = evaluate_track(
        _sample_track(id=21, duration_sec=281.26, mean_vol_db=-31.2),
        median_mean_db=-25.2,
    )
    assert "OVERLONG" in issues
    assert "TOO_QUIET" in issues


def test_evaluate_track_catches_long_internal_silence():
    issues = evaluate_track(
        _sample_track(id=42, duration_sec=111.10, max_silence_sec=12.42, mean_vol_db=-31.3),
        median_mean_db=-25.2,
    )
    assert "OVERLONG" in issues
    assert any(i.startswith("LONG_SILENCE(") for i in issues)


def test_evaluate_track_catches_relative_loudness_swing():
    issues = evaluate_track(
        _sample_track(id=45, mean_vol_db=-19.1),
        median_mean_db=-25.2,
    )
    assert any(i.startswith("LOUDNESS_SWING(") for i in issues)


def test_evaluate_track_catches_missing_short_small_and_silent():
    assert evaluate_track({"id": 9, "exists": False}) == ["MISSING"]

    short_small = evaluate_track(_sample_track(duration_sec=3.0, size_kb=20.0))
    assert "SHORT" in short_small
    assert "SMALL" in short_small

    silent = evaluate_track(_sample_track(max_vol_db=float("-inf"), mean_vol_db=float("-inf"), max_silence_sec=20.0))
    assert silent == ["SILENT"]


def test_evaluate_catalog_flags_excessive_catalog_loudness_spread():
    tracks = [
        _sample_track(id=1, mean_vol_db=-24.0),
        _sample_track(id=36, mean_vol_db=-35.6),
        _sample_track(id=45, mean_vol_db=-19.1),
    ]
    summary = evaluate_catalog(tracks)

    assert summary["spread_exceeded"] is True
    assert round(summary["spread_db"], 1) == 16.5
    by_id = {t["id"]: t["issues"] for t in summary["tracks"]}
    assert by_id[1] == []
    assert "TOO_QUIET" in by_id[36]
    assert any(i.startswith("LOUDNESS_SWING(") for i in by_id[45])
