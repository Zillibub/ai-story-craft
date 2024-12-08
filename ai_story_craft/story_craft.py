import argparse
from pathlib import Path
from rag.langchain_agent import LangChanAgent
from subtitles_extractor import extract_subtitles
from db.models_crud import AgentCRUD, AgentAccessCRUD, ChatCRUD, VideoCRUD
from db.models import Agent, Video


class StoryCraft:

    def __init__(
            self,
            work_directory: Path,
            video_db: Video,
    ):
        """

        :param work_directory: directory to store the files for the video
        :param video_db:  database record
        """
        self.work_directory = work_directory
        self.video = video_db
        self.video_path = Path(video_db.video_path)
        self.audio_path = Path(video_db.audio_path) if video_db.audio_path else None

        self.work_directory.mkdir(exist_ok=True)

    def evaluate(
            self,
            external_chat_id: str,
            assistant_name: str = None,
            language: str = None,
            overwrite: bool = False
    ) -> Agent:
        if not self.work_directory.exists():
            self.work_directory.mkdir()

        assistant_name = assistant_name or self.video_path.stem

        # Get or create chat
        chat = ChatCRUD().get_by_external_id(external_chat_id)
        if chat is None:
            chat = ChatCRUD().create(chat_id=external_chat_id)

        # Check if agent already exists
        existing_agent = AgentCRUD().get_by_name(assistant_name)
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
            name=assistant_name,
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
    parser.add_argument('-v', '--video_id', type=str, required=True,
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
    video_db = VideoCRUD().read(args.video_id)
    StoryCraft(
        video_db=video_db,
        work_directory=Path(args.work_directory)
    ).evaluate(
        assistant_name=args.assistant_name,
        language=args.language,
        overwrite=args.overwrite
    )
