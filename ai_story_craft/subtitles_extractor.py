import ffmpeg
import tempfile
import json
from openai import OpenAI
from typing import Iterator, TextIO
from pathlib import Path
from core.settings import settings
import whisper


def extract_subtitles_api(
        video_path: Path,
        output_path: Path,
        audio_path: Path = None
):
    """Extract subtitles using OpenAI's Whisper API"""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    with tempfile.TemporaryDirectory() as temp_dir:
        if not audio_path:
            audio_path = Path(temp_dir, video_path.stem + '.mp3')
            ffmpeg.input(str(video_path)).output(
                str(audio_path),
                acodec="libmp3lame", ab="32k", ac=1, ar="8k"
            ).run(quiet=True, overwrite_output=True)
        
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=settings.whisper_api_model,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        with open(output_path, "w", encoding="utf-8") as srt:
            json.dump(dict(transcription), srt)


def extract_subtitles_local(
        video_path: Path,
        output_path: Path,
        model_name: str = "base",
        audio_path: Path = None
):
    """
    Extract subtitles using local Whisper model
    :param video_path:
    :param output_path:
    :param model_name:
    :param audio_path:
    :return:
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Load the Whisper model
    model = whisper.load_model(model_name)

    with tempfile.TemporaryDirectory() as temp_dir:
        if not audio_path:
            audio_path = Path(temp_dir, video_path.stem + '.mp3')
            ffmpeg.input(str(video_path)).output(
                str(audio_path),
                acodec="libmp3lame", ab="32k", ac=1, ar="8k"
            ).run(quiet=True, overwrite_output=True)
        
        # Perform transcription
        result = model.transcribe(str(audio_path))

        with open(output_path, "w", encoding="utf-8") as srt:
            json.dump(result, srt)


def extract_subtitles(
        video_path: Path,
        output_path: Path,
        audio_path: Path = None
):
    """Main function to extract subtitles using either API or local model based on settings"""
    if settings.whisper_use_api:
        return extract_subtitles_api(video_path, output_path, audio_path)
    else:
        return extract_subtitles_local(video_path, output_path, settings.whisper_model, audio_path)


def write_srt(transcript: Iterator[dict], file: TextIO):
    for i, segment in enumerate(transcript, start=1):
        start_time = format_timestamp(segment['start'], always_include_hours=True)
        end_time = format_timestamp(segment['end'], always_include_hours=True)
        text = segment['text'].strip().replace('-->', '->')
        file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n")
    file.flush()


def format_timestamp(seconds: float, always_include_hours: bool = False):
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return f"{hours_marker}{minutes:02d}:{seconds:02d},{milliseconds:03d}"
