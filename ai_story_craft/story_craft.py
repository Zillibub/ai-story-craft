from pathlib import Path
from subtitles_extractor import extract_subtitles


class StoryCraft:

    def __init__(self, video_path: Path, work_directory: Path):
        self.work_directory = work_directory
        self.video_path = video_path

    def evaluate(self):
        extract_subtitles(self.video_path, self.work_directory / 'subtitles.srt')
