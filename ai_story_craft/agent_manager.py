from pathlib import Path
from utils.singleton import Singleton
from rag.langchain_agent import LangChanAgent
from db.models_crud import AgentCRUD, ActiveAgentCRUD, ChatCRUD

class AgentManager(metaclass=Singleton):
    """Agent manager class."""
    def __init__(self):
        self.agents = {}

    def add(self, agent_id: str, agent: LangChanAgent):
        """Add agent."""
        self.agents[agent_id] = agent

    def get(self, agent_id) -> LangChanAgent:
        """Get agent."""
        if agent_id not in self.agents:
            agent_db = AgentCRUD().read(agent_id)
            if not agent_db:
                raise ValueError(f"Agent {agent_id} not found.")
            self.add(agent_db.id, LangChanAgent.load(Path(agent_db.agent_dir)))

        return self.agents.get(agent_id)