import argparse
from db.models_crud import VideoCRUD, AgentCRUD, ActiveAgentCRUD
from pathlib import Path
import shutil

def delete_video(video_hash: str):
    """
    Debug method to completely remove a video and its associated data
    
    Args:
        video_hash: Hash of the video to delete
    """
    # Get video record
    video = VideoCRUD().get_by_hash(video_hash)
    if not video:
        raise ValueError(f"Video with hash {video_hash} not found")

    # Delete video and audio files
    video_path = Path(video.video_path)
    if video_path.exists():
        video_path.unlink()
    
    if video.audio_path:
        audio_path = Path(video.audio_path)
        if audio_path.exists():
            audio_path.unlink()

    # Find and delete associated agent
    agent = AgentCRUD().get_by_name(video.title)
    if agent:
        # Delete agent directory
        agent_dir = Path(agent.agent_dir)
        if agent_dir.exists():
            shutil.rmtree(agent_dir)
        
        # Delete active agent references
        active_agents = ActiveAgentCRUD().get_by_agent_id(agent.id)
        if active_agents:
            for active_agent in active_agents:
                ActiveAgentCRUD().delete(active_agent.id)
        
        # Delete agent record
        AgentCRUD().delete(agent.id)

    # Delete video record
    VideoCRUD().delete(video.id)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deleted video record')
    parser.add_argument('video_hash', type=str, help='Hash of the video to delete')
    delete_video("some_hash")
    print("Deleted")