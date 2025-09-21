# Moved from utils/logging.py
from pathlib import Path
import json

def write_patch_log(patch_id, data, base_dir="logs/patches"):
    path = Path(base_dir) / f"{patch_id}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(data)

def append_conversation_log(message, base_dir="logs/conversations", filename="copilot_chronological_chatlog.log"):
    path = Path(base_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(f"{message.strip()}\n")
