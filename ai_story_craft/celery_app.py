import time
from integrations.telegram import MessageSender
from pathlib import Path
from celery import Celery
from story_craft import StoryCraft
from core.settings import settings
from urllib.parse import parse_qs, urlparse

from integrations.youtube import download_video, download_audio

celery_app = Celery("worker", broker=settings.CELERY_BACKEND_URL,  backend=settings.CELERY_BACKEND_URL)


@celery_app.task
def process_youtube_video(youtube_url: str, update_sender: dict = None):
    update_sender = MessageSender.from_dict(update_sender) if update_sender else None
    if update_sender:
        update_sender.update_message("Processing video...")
    if not Path(settings.working_directory).exists():
        if update_sender:
            update_sender.update_message(f"Working directory not found: {settings.working_directory}")
        raise FileNotFoundError(f"Working directory not found: {settings.working_directory}")

    parsed_url = urlparse(youtube_url)
    query_params = parse_qs(parsed_url.query)

    v_param = query_params.get('v', None)
    if not v_param:
        raise ValueError("Invalid YouTube URL: missing video ID")

    video_path = Path(settings.videos_directory, f"{v_param[0]}.mp4")
    audio_path = None

    # Edge case not covered:
    # if the video without audio was downloaded and the process was interrupted
    # when the audio was being downloaded
    if not video_path.exists():
        has_audio = download_video(Path(youtube_url), video_path)
        if not has_audio:
            audio_path = Path(settings.videos_directory, f"{v_param[0]}.wav")
            download_audio(Path(youtube_url), audio_path)

    if update_sender:
        update_sender.update_message("Importing subtitles...")

    StoryCraft(
        work_directory=Path(settings.working_directory) / v_param[0],
        video_path=video_path,
        audio_path=audio_path
    ).evaluate(assistant_name=v_param[0])

    if update_sender:
        update_sender.update_message("Video processed.")

@celery_app.task
def wait(update_sender: dict):
    """
    Test method to simulate a running task
    :param update_sender:
    :return:
    """
    update_sender = MessageSender.from_dict(update_sender)
    update_sender.update_message("Waiting...")
    time.sleep(2)
    update_sender.update_message("Done waiting.")
