from pathlib import Path
from assistant import create_assistant
from subtitles_extractor import extract_subtitles


if __name__ == "__main__":
    assistant = create_assistant(name='assistant_1', subtitle_file=Path('../../data/short/subtitles.txt'))

    pass
