import argparse
from pathlib import Path
from assistant import create_assistant
from subtitles_extractor import extract_subtitles
from db.models_crud import AssistantCRUD


class StoryCraft:

    def __init__(self, video_path: Path, work_directory: Path):
        self.work_directory = work_directory
        self.video_path = video_path

        self.work_directory.mkdir(exist_ok=True)

    def evaluate(self):
        if not self.work_directory.exists():
            self.work_directory.mkdir()

        subtitles_path = self.work_directory / 'subtitles.txt'
        if not subtitles_path.exists():
            extract_subtitles(self.video_path, subtitles_path)

        assistant = create_assistant(name='assistant_1', subtitle_file=subtitles_path)
        AssistantCRUD().create(external_id=assistant.id, name=assistant.name)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Creates assistant')
    parser.add_argument('-v', '--video_path', type=str, required=True,
                        help='Path to the video file')
    parser.add_argument('-d', '--work_directory', type=str, required=True,
                        help='Path to the output working directory')
    args = parser.parse_args()

    StoryCraft(Path(args.video_path), Path(args.work_directory)).evaluate()
