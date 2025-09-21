import os
from pathlib import Path

def resolve_path(base, *paths):
    return os.path.abspath(os.path.join(base, *paths))

def project_root():
    return Path(__file__).parent.parent.parent.resolve()
