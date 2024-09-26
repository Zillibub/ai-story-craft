import argparse
from pathlib import Path
from rag.openai_assistant import create_assistant
from rag.langchain_agent import LangChanAgent
from subtitles_extractor import extract_subtitles
from db.models_crud import AgentCRUD


class StoryCraft:

    def __init__(self, video_path: Path, work_directory: Path):
        self.work_directory = work_directory
        self.video_path = video_path

        self.work_directory.mkdir(exist_ok=True)

    def evaluate(self, assistant_name: str = None):
        if not self.work_directory.exists():
            self.work_directory.mkdir()

        subtitles_path = self.work_directory / 'subtitles.json'
        if not subtitles_path.exists():
            extract_subtitles(self.video_path, subtitles_path)

        agent = LangChanAgent.create(
            video_path=self.video_path,
            subtitle_file_path=subtitles_path,
            agent_dir=self.work_directory / 'agent'
        )
        AgentCRUD().create(name=assistant.name, description=description)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Creates assistant')
    parser.add_argument('-v', '--video_path', type=str, required=True,
                        help='Path to the video file')
    parser.add_argument('-d', '--work_directory', type=str, required=True,
                        help='Path to the output working directory')
    parser.add_argument('-a', '--assistant_name', type=str, required=False,
                        help='Path to the output working directory')
    args = parser.parse_args()
    StoryCraft(Path(args.video_path), Path(args.work_directory)).evaluate(assistant_name=args.assistant_name)
