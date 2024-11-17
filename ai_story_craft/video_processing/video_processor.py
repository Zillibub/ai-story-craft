import hashlib
from pytubefix import YouTube
from pathlib import Path
from core.settings import settings
from urllib.parse import parse_qs, urlparse
from integrations.youtube import download_video, download_audio
from db.models_crud import VideoCRUD
from db.models import Video


class YoutubeVideoProcessor:

    def __init__(self, video_record: Video):
        self.video_record = video_record

    def process(self):
        parsed_url = urlparse(self.video_record.url)
        query_params = parse_qs(parsed_url.query)

        v_param = query_params.get('v', None)
        if not v_param:
            raise ValueError("Invalid YouTube URL: missing video ID")

        video_path = Path(self.video_record.video_path)
        audio_path = None

        # Edge case not covered:
        # if the video without audio was downloaded and the process was interrupted
        # when the audio was being downloaded
        if not video_path.exists():
            has_audio = download_video(Path(self.video_record.url), video_path)
            if not has_audio:
                audio_path = Path(settings.videos_directory, f"{v_param[0]}.wav")
                download_audio(Path(self.video_record.url), audio_path)
                self.video_record = VideoCRUD().update(self.video_record, audio_path=audio_path)

        self.video_record = VideoCRUD().update(self.video_record, is_downloaded=True)

    @classmethod
    def from_url(cls, video_url: str):

        yt = YouTube(video_url)
        yt.check_availability()

        url_hash = hashlib.md5(video_url.encode()).hexdigest()
        video_record = VideoCRUD().create(
            url=video_url,
            hash_sum=url_hash,
            type='youtube',
            title=yt.title,
            video_path=settings.videos_directory / f"{url_hash}.mp4",
        )
        return cls(video_record)