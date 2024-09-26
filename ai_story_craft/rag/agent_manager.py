from utils.singleton import Singleton
from rag.langchain_agent import LangChanAgent

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
            raise ValueError(f"Agent {agent_id} not found.")
        return self.agents.get(agent_id)