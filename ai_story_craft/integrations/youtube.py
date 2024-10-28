import pytubefix
from pathlib import Path


def parse_resolution(stream):
    try:
        return int(stream.resolution[:-1])
    except (TypeError, ValueError):
        return 0


def download_video(video_url: Path, output_path: Path) -> bool:
    """

    :param video_url:
    :param output_path: Path to save video
    :return: True if audio stream is included in the video stream, False otherwise
    """
    if output_path.exists():
        raise FileExistsError(f"File already exists: {output_path}")
    yt = pytubefix.YouTube(str(video_url))

    video_streams = yt.streams.filter(only_video=True)
    video_streams = sorted(video_streams, key=parse_resolution, reverse=True)

    if len(video_streams) == 0:
        raise ValueError("No video streams found")

    highest_resolution_stream = video_streams[0]
    highest_resolution_stream.download(output_path.parent, filename=output_path.name)

    # Sometimes the audio stream is not included in the video stream, needed to be downloaded separately
    return bool(highest_resolution_stream.audio_codec)

def download_audio(audio_url: Path, output_path: Path):
    """

    :param audio_url:
    :param output_path: Path to save audio
    :return:
    """
    if output_path.exists():
        raise FileExistsError(f"File already exists: {output_path}")
    yt = pytubefix.YouTube(str(audio_url))

    audio_streams = yt.streams.filter(only_audio=True)

    if len(audio_streams) == 0:
        raise ValueError("No audio streams found")

    audio_streams[0].download(output_path.parent, filename=output_path.name)