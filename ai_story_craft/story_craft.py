import argparse
from pathlib import Path
from rag.langchain_agent import LangChanAgent
from subtitles_extractor import extract_subtitles
from db.models_crud import AgentCRUD


class StoryCraft:

    def __init__(
            self,
            work_directory: Path,
            video_path: Path,
            audio_path: Path = None
    ):
        self.work_directory = work_directory
        self.video_path = video_path
        self.audio_path = audio_path

        self.work_directory.mkdir()

    def evaluate(
            self,
            assistant_name: str = None,
            language: str = None,
            overwrite: bool = False
    ):
        if not self.work_directory.exists():
            self.work_directory.mkdir()

        subtitles_path = self.work_directory / 'subtitles.json'
        if not subtitles_path.exists():
            extract_subtitles(
                self.video_path,
                subtitles_path,
                language=language,
                audio_path=self.audio_path
            )

        agent_dir = self.work_directory / 'agent'

        agent = LangChanAgent.create(
            name=assistant_name or self.video_path.stem,
            video_path=self.video_path,
            subtitle_file_path=subtitles_path,
            agent_dir=agent_dir,
            overwrite=overwrite
        )
        AgentCRUD().create(
            name=agent.name,
            description=agent.description,
            agent_dir=str(agent_dir)
        )


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Creates assistant')
    parser.add_argument('-v', '--video_path', type=str, required=True,
                        help='Path to the video file')
    parser.add_argument('-d', '--work_directory', type=str, required=True,
                        help='Path to the output working directory')
    parser.add_argument('-a', '--assistant_name', type=str, required=False,
                        help='Path to the output working directory')
    parser.add_argument('-l', '--language', type=str, required=False,
                        help='Language for subtitles extraction')
    parser.add_argument('-o', '--overwrite', type=bool, required=False,
                        help='Override folder if exists')
    args = parser.parse_args()
    StoryCraft(
        video_path=Path(args.video_path),
        work_directory=Path(args.work_directory)
    ).evaluate(
        assistant_name=args.assistant_name,
        language=args.language,
        overwrite=args.overwrite
    )
