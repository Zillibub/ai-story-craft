from pathlib import Path
from subtitles_extractor import extract_subtitles


class StoryCraft:

    def __init__(self, video_path: Path, work_directory: Path):
        self.work_directory = work_directory
        self.video_path = video_path

    def evaluate(self):
        if not self.work_directory.exists():
            self.work_directory.mkdir()
        extract_subtitles(self.video_path, self.work_directory / 'subtitles.txt')


if __name__ == '__main__':
    video_path = Path('../../data/jupyter_notebook_tutorial.mp4')
    work_directory = Path('../../data/short')
    work_directory.mkdir(exist_ok=True)
    StoryCraft(video_path, work_directory).evaluate()