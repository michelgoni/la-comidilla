"""Debug entry point that runs load_config without calling the model."""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "src"))

from extract import load_config

if __name__ == "__main__":
    config = load_config()
    print({"base_url": config["base_url"], "model": config["model"]})
    print("api_key set:", bool(config["api_key"]))
