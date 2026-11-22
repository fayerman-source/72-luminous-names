from types import SimpleNamespace
import builtins
import shutil
import subprocess
import pytest

import generate_audio as audio_mod


class _FakeClient:
    def __init__(self, response):
        self.models = SimpleNamespace(generate_content=lambda **_kwargs: response)


def _audio_response(pcm_bytes: bytes):
    part = SimpleNamespace(inline_data=SimpleNamespace(data=pcm_bytes))
    candidate = SimpleNamespace(content=SimpleNamespace(parts=[part]))
    return SimpleNamespace(candidates=[candidate])


def test_module_imports_without_google_genai():
    assert len(audio_mod.NAMES) == 72


def test_create_client_raises_actionable_error_when_sdk_missing(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "google" or name.startswith("google."):
            raise ImportError("No module named 'google'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="requirements-audio.txt"):
        audio_mod._create_client("dummy-key")


def test_generate_audio_fails_loudly_and_cleans_temp_file_on_ffmpeg_error(monkeypatch, tmp_path):
    created_temps = []
    real_named_temp = audio_mod.tempfile.NamedTemporaryFile

    def tracking_temp(*args, **kwargs):
        handle = real_named_temp(*args, **kwargs)
        created_temps.append(handle.name)
        return handle

    def failing_run(cmd, **_kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd, stderr="Invalid PCM stream")

    monkeypatch.setattr(audio_mod.tempfile, "NamedTemporaryFile", tracking_temp)
    monkeypatch.setattr(audio_mod.subprocess, "run", failing_run)

    client = _FakeClient(_audio_response(b"\x00\x00" * 240))
    with pytest.raises(RuntimeError, match="ffmpeg failed.*Invalid PCM stream"):
        audio_mod.generate_audio(audio_mod.NAMES[0], str(tmp_path), client)

    assert len(created_temps) == 1
    assert not (tmp_path / "1.mp3").exists()
    assert not any(tmp_path.glob("*.raw"))
    for path in created_temps:
        assert not audio_mod.os.path.exists(path)


def test_generate_audio_fails_loudly_when_ffmpeg_binary_missing(monkeypatch, tmp_path):
    def missing_run(_cmd, **_kwargs):
        raise FileNotFoundError("ffmpeg")

    monkeypatch.setattr(audio_mod.subprocess, "run", missing_run)
    client = _FakeClient(_audio_response(b"\x00\x00" * 240))

    with pytest.raises(RuntimeError, match="ffmpeg is not installed"):
        audio_mod.generate_audio(audio_mod.NAMES[0], str(tmp_path), client)


def test_generate_audio_raises_when_response_contains_no_audio(tmp_path):
    empty_resp = SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[]))])
    client = _FakeClient(empty_resp)

    with pytest.raises(RuntimeError, match="No audio data returned"):
        audio_mod.generate_audio(audio_mod.NAMES[0], str(tmp_path), client)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_generate_audio_writes_mp3_with_synthetic_pcm(tmp_path):
    # 0.1s of 24kHz 16-bit mono silence (synthetic local bytes; no external API calls)
    client = _FakeClient(_audio_response(b"\x00\x00" * 2400))

    ok = audio_mod.generate_audio(audio_mod.NAMES[0], str(tmp_path), client)

    out_mp3 = tmp_path / "1.mp3"
    assert ok is True
    assert out_mp3.exists()
    assert out_mp3.stat().st_size > 100


def test_main_returns_nonzero_without_api_key(monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    rc = audio_mod.main()

    assert rc == 1
    assert "GEMINI_API_KEY" in capsys.readouterr().err
