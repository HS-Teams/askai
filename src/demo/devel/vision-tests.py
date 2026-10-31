"""Run native image captioning on an explicitly supplied image."""
import argparse
from pathlib import Path
from askai.core.engine.openai.openai_vision import OpenAIVision

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    print(OpenAIVision().caption(args.image.name, args.image.parent))
