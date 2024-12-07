import hashlib
from pytubefix import YouTube
from pathlib import Path
from core.settings import settings
from urllib.parse import parse_qs, urlparse
from integrations.youtube import download_video, download_audio
from db.models_crud import VideoCRUD
from db.models import Video


class YoutubeVideoProcessor:
    """
    Processes a YouTube video:
    - Downloads the video stream with the highest resolution
    - Downloads the audio stream if it is not included in the video stream
    - If the video was already downloaded, it skips the download process
    """

    def __init__(self, video_record: Video):
        self.video_record = video_record

    def process(self):

        if self.video_record.is_downloaded:
            return

        parsed_url = urlparse(self.video_record.url)
        query_params = parse_qs(parsed_url.query)

        v_param = query_params.get('v', None)
        if not v_param:
            raise ValueError("Invalid YouTube URL: missing video ID")

        video_path = Path(self.video_record.video_path)

        # Edge case not covered:
        # if the video without audio was downloaded and the process was interrupted
        # when the audio was being downloaded
        if not video_path.exists():
            has_audio = download_video(Path(self.video_record.url), video_path)
            if not has_audio:
                audio_path = Path(settings.videos_directory, f"{self.video_record.hash_sum}.wav")
                download_audio(Path(self.video_record.url), audio_path)
                self.video_record = VideoCRUD().update(
                    id=self.video_record.id,
                    audio_path=str(audio_path),
                    has_audio=False
                )

        self.video_record = VideoCRUD().update(id=self.video_record.id, is_downloaded=True)

    @staticmethod
    def hash_url(video_url: str) -> str:
        return hashlib.md5(video_url.encode()).hexdigest()

    def is_processed(self, video_url: str):
        video_record = VideoCRUD().get_by_hash(self.hash_url(video_url))
        return video_record.is_downloaded

    @staticmethod
    def get_duration(video_url: str) -> int:
        """
        Get the duration of a YouTube video in seconds
        :param video_url:
        :return:
        """
        yt = YouTube(video_url)
        yt.check_availability()
        return yt.length

    @staticmethod
    def check_availability(video_url: str):
        yt = YouTube(video_url)
        try:
            yt.check_availability()
        except Exception as e:
            raise ValueError(e)

    @classmethod
    def from_url(cls, video_url: str):

        yt = YouTube(video_url)
        yt.check_availability()

        url_hash = cls.hash_url(video_url)
        if not VideoCRUD().get_by_hash(url_hash):
            video_record = VideoCRUD().create(
                url=video_url,
                hash_sum=url_hash,
                video_type='youtube',
                title=yt.title,
                video_path=str(Path(settings.videos_directory) / f"{url_hash}.mp4"),
            )
        else:
            video_record = VideoCRUD().get_by_hash(url_hash)
        return cls(video_record)