import argparse
from pathlib import Path
from rag.langchain_agent import LangChanAgent
from subtitles_extractor import extract_subtitles
from db.models_crud import AgentCRUD, AgentAccessCRUD
from db.models import Agent
from db.models_crud import ChatCRUD


class StoryCraft:

    def __init__(
            self,
            work_directory: Path,
            video_path: Path,
            audio_path: Path = None
    ):
        """

        :param work_directory: directory to store the files for the video
        :param video_path:
        :param audio_path:
        """
        self.work_directory = work_directory
        self.video_path = video_path
        self.audio_path = audio_path

        self.work_directory.mkdir(exist_ok=True)

    def evaluate(
            self,
            chat_id: str,
            assistant_name: str = None,
            language: str = None,
            overwrite: bool = False
    ) -> Agent:
        if not self.work_directory.exists():
            self.work_directory.mkdir()

        # Get or create chat
        chat = ChatCRUD().get_by_external_id(chat_id)
        if chat is None:
            chat = ChatCRUD().create(chat_id=chat_id)

        # Check if agent already exists
        existing_agent = AgentCRUD().get_by_name(assistant_name or self.video_path.stem)
        if existing_agent:
            # Grant access to existing agent
            AgentAccessCRUD().grant_access(chat.id, existing_agent.id)
            return existing_agent

        subtitles_path = self.work_directory / 'subtitles.json'
        if not subtitles_path.exists():
            extract_subtitles(
                self.video_path,
                subtitles_path,
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
        
        # Create agent and grant access
        created_agent = AgentCRUD().create(
            name=agent.name,
            description=agent.description,
            agent_dir=str(agent_dir)
        )
        AgentAccessCRUD().grant_access(chat.id, created_agent.id)
        
        return created_agent


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
