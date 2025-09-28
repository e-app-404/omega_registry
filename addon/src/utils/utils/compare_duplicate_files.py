import hashlib
import os
from typing import Dict, List


def file_hash(path: str, block_size: int = 65536) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            hasher.update(block)
    return hasher.hexdigest()


def compare_duplicate_files(file_paths: List[str]) -> Dict:
    """
    Compare duplicate files and return a summary of differences for manifest rendering.
    Args:
        file_paths: List of file paths for the same basename.
    Returns:
        Dict with keys: filename, summary, left, right
    """
    if len(file_paths) != 2:
        return {
            "filename": os.path.basename(file_paths[0]),
            "summary": "More than two duplicates found. Only first two compared.",
            "left": {},
            "right": {},
        }
    left, right = file_paths
    left_stat = os.stat(left)
    right_stat = os.stat(right)
    left_hash = file_hash(left)
    right_hash = file_hash(right)
    summary = []
    if left_hash == right_hash:
        summary.append("Files are identical in content.")
    else:
        summary.append("Files differ in content.")
    if left_stat.st_size != right_stat.st_size:
        summary.append(
            f"Size differs: {left_stat.st_size/1024:.1f} KB vs {right_stat.st_size/1024:.1f} KB."
        )
    if int(left_stat.st_mtime) != int(right_stat.st_mtime):
        summary.append(
            f"Last modified: {os.path.basename(left)} at {left_stat.st_mtime}, {os.path.basename(right)} at {right_stat.st_mtime}."
        )
    return {
        "filename": os.path.basename(left),
        "summary": " ".join(summary),
        "left": {
            "path": left,
            "size": f"{left_stat.st_size/1024:.1f} KB",
            "mtime": left_stat.st_mtime,
            "hash": left_hash,
        },
        "right": {
            "path": right,
            "size": f"{right_stat.st_size/1024:.1f} KB",
            "mtime": right_stat.st_mtime,
            "hash": right_hash,
        },
    }
