import time
from pathlib import Path
from celery import Celery
from story_craft import StoryCraft
from core.settings import settings
from urllib.parse import parse_qs, urlparse
from integrations.youtube import download_video, download_audio

celery_app = Celery("worker", broker=settings.CELERY_BACKEND_URL,  backend=settings.CELERY_BACKEND_URL)


@celery_app.task
def process_youtube_video(youtube_url: str):
    if not Path(settings.working_directory).exists():
        raise FileNotFoundError(f"Working directory not found: {settings.working_directory}")
    parsed_url = urlparse(youtube_url)
    query_params = parse_qs(parsed_url.query)

    v_param = query_params.get('v', None)
    if not v_param:
        raise ValueError("Invalid YouTube URL: missing video ID")

    video_path = Path(settings.videos_directory, f"{v_param[0]}.mp4")
    audio_path = None

    has_audio = download_video(Path(youtube_url), video_path)
    if not has_audio:
        audio_path = Path(settings.videos_directory, f"{v_param[0]}.wav")
        download_audio(Path(youtube_url), audio_path)

    StoryCraft(
        work_directory=Path(settings.working_directory),
        video_path=video_path,
        audio_path=audio_path
    ).evaluate(assistant_name=v_param[0])

@celery_app.task
def wait(message):
    time.sleep(2)