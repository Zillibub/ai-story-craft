import pytubefix
from pathlib import Path
from typing import Tuple


def parse_resolution(stream):
    try:
        return int(stream.resolution[:-1])
    except (TypeError, ValueError):
        return 0


def download_video(video_url: Path, output_path: Path) -> Tuple[Path, bool]:
    if output_path.exists():
        raise FileExistsError(f"File already exists: {output_path}")
    yt = pytubefix.YouTube(str(video_url))

    video_streams = yt.streams.filter(only_video=True)
    video_streams = sorted(video_streams, key=parse_resolution, reverse=True)

    if len(video_streams) == 0:
        raise ValueError("No video streams found")

    highest_resolution_stream = video_streams[0]
    highest_resolution_stream.download(output_path)

    return output_path, not highest_resolution_stream.audio_codec

def download_audio(video_url: Path, output_path: Path) -> Path:
    if output_path.exists():
        raise FileExistsError(f"File already exists: {output_path}")
    yt = pytubefix.YouTube(str(video_url))

    audio_streams = yt.streams.filter(only_audio=True)

    if len(audio_streams) == 0:
        raise ValueError("No audio streams found")

    audio_streams[0].download(output_path)

    return output_path