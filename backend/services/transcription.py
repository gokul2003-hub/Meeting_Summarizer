import os
import sys
import time
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)

# Ensure ffmpeg binary from imageio_ffmpeg is configured on PATH as ffmpeg.exe & ffprobe.exe
try:
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(exe)

    if sys.platform == "win32":
        target_ffmpeg = os.path.join(ffmpeg_dir, "ffmpeg.exe")
        if not os.path.exists(target_ffmpeg):
            try:
                shutil.copyfile(exe, target_ffmpeg)
            except Exception:
                pass

        target_ffprobe = os.path.join(ffmpeg_dir, "ffprobe.exe")
        if not os.path.exists(target_ffprobe):
            try:
                shutil.copyfile(exe, target_ffprobe)
            except Exception:
                pass

    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.path.pathsep + os.environ.get("PATH", "")
except Exception as e:
    logger.warning(f"Could not load imageio_ffmpeg: {e}")

_model = None


def get_model():
    global _model
    if _model is None:
        import whisper
        model_name = os.getenv("WHISPER_MODEL", "tiny")
        logger.info(f"Loading local Whisper model: '{model_name}'...")
        _model = whisper.load_model(model_name)
    return _model


def _get_audio_duration(file_path: str) -> float:
    """Return audio duration in seconds using ffprobe/ffmpeg, or file-size heuristic on failure."""
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    if file_size == 0:
        return 0.0

    # 1. Try ffprobe / ffmpeg
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        result = subprocess.run(
            [ffmpeg_exe, "-i", file_path],
            capture_output=True, text=True, timeout=30,
        )
        for line in result.stderr.splitlines():
            if "Duration:" in line:
                time_str = line.split("Duration:")[1].split(",")[0].strip()
                parts = time_str.split(":")
                if len(parts) == 3:
                    h, m, s = parts
                    val = float(h) * 3600 + float(m) * 60 + float(s)
                    if val > 0:
                        return val
    except Exception:
        pass

    # 2. Fallback heuristic: non-empty file (>100 bytes)
    if file_size > 100:
        return 60.0

    return 0.0


def transcribe(file_path: str) -> str:
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    if file_size == 0:
        raise ValueError("Audio file is empty (0 bytes). Please upload a valid audio or transcript file.")

    duration = _get_audio_duration(file_path)
    if duration < 0.5:
        raise ValueError(
            f"Audio file is too short or empty (duration: {duration:.2f}s). "
            "Please provide a recording with audible speech."
        )

    # Cloud OpenAI Whisper API if key is available
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            with open(file_path, "rb") as audio_file:
                transcript_res = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                )
                text = transcript_res.text.strip()
                if text:
                    return text
        except Exception as e:
            logger.warning(f"OpenAI Whisper API call failed: {e}. Falling back to local Whisper.")

    # Local Whisper model transcription
    start_time = time.time()
    logger.info(f"Starting local Whisper transcription for '{file_path}'...")
    model = get_model()
    result = model.transcribe(file_path, fp16=False)
    elapsed = time.time() - start_time
    logger.info(f"Local Whisper transcription completed in {elapsed:.2f} seconds.")
    text = result.get("text", "").strip()
    if not text:
        raise ValueError("Whisper produced no transcript. The audio may be silent or contain no speech.")
    return text
