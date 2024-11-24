import time
from integrations.messenger import MessageSender as TelegramMessageSender
from integrations.discord_messenger import DiscordMessageSender
from pathlib import Path
from celery import Celery
from story_craft import StoryCraft
from core.settings import settings
from video_processing.youtube_video_processor import YoutubeVideoProcessor

celery_app = Celery("worker", broker=settings.CELERY_BACKEND_URL,  backend=settings.CELERY_BACKEND_URL)

def check_celery_worker() -> bool:
    try:
        response = celery_app.control.ping(timeout=1.0)
        if response:
            return True
        else:
            return False
    except Exception:
        return False

@celery_app.task
def process_youtube_video(youtube_url: str, update_sender: dict = None):
    if update_sender:
        if 'chat_id' in update_sender:
            update_sender = TelegramMessageSender.from_dict(update_sender)
        else:
            update_sender = DiscordMessageSender.from_dict(update_sender)
        update_sender.update_message("Processing video...")
        
    if not Path(settings.working_directory).exists():
        if update_sender:
            update_sender.send_message(f"Working directory not found: {settings.working_directory}")
        raise FileNotFoundError(f"Working directory not found: {settings.working_directory}")

    video_processor = YoutubeVideoProcessor.from_url(youtube_url)
    if update_sender:
        update_sender.send_message("Downloading video...")
    video_processor.process()

    if update_sender:
        update_sender.send_message("Extracting subtitles...")

    StoryCraft(
        work_directory=Path(settings.working_directory) / video_processor.video_record.hash_sum,
        video_path=Path(video_processor.video_record.video_path),
        audio_path=Path(video_processor.video_record.audio_path) if video_processor.video_record.audio_path else None
    ).evaluate(assistant_name=video_processor.video_record.title)

    if update_sender:
        update_sender.send_message("Video processed successfully.")

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
