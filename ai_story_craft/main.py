from pathlib import Path
from assistant import Assistant
from subtitles_extractor import extract_subtitles


if __name__ == "__main__":
    assistant = Assistant.create_assistant(name='assistant_1', subtitle_file=Path('../../data/short/subtitles.srt'))

    pass
