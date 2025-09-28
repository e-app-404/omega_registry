# file_utils.py
"""
Utility functions for file operations in the Omega Registry project.
"""
import hashlib
import os
from pathlib import Path


def hash_file(path, algo="sha256", chunk_size=65536):
    """
    Compute the hash of a file using the specified algorithm.
    Args:
        path (str or Path): Path to the file.
        algo (str): Hash algorithm ('sha256', 'md5', etc.).
        chunk_size (int): Read chunk size in bytes.
    Returns:
        str: Hex digest of the file's hash.
    """
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def is_text_file(path, blocksize=512):
    """
    Heuristically determine if a file is a text file.
    Args:
        path (str or Path): Path to the file.
        blocksize (int): Number of bytes to check.
    Returns:
        bool: True if file is likely text, False if binary.
    """
    try:
        with open(path, "rb") as f:
            chunk = f.read(blocksize)
            if b"\0" in chunk:
                return False
            # Try decoding as utf-8
            try:
                chunk.decode("utf-8")
                return True
            except UnicodeDecodeError:
                return False
    except Exception:
        return False


def get_file_type(path):
    """
    Return a simple file type string based on extension or content.
    Args:
        path (str or Path): Path to the file.
    Returns:
        str: File type (e.g., 'json', 'yaml', 'txt', 'py', 'bin', etc.)
    """
    ext = Path(path).suffix.lower().lstrip(".")
    if ext:
        return ext
    return "bin" if not is_text_file(path) else "txt"


def get_file_size(path):
    """
    Return the file size in bytes.
    Args:
        path (str or Path): Path to the file.
    Returns:
        int: File size in bytes.
    """
    return os.path.getsize(path)


def list_files_recursive(base_path, ignore_hidden=True):
    """
    Recursively list all files under base_path.
    Args:
        base_path (str or Path): Directory to scan.
        ignore_hidden (bool): Whether to skip hidden files/dirs.
    Returns:
        list of Path: All file paths found.
    """
    files = []
    for root, dirs, filenames in os.walk(base_path):
        if ignore_hidden:
            # Remove hidden dirs in-place
            dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in filenames:
            if ignore_hidden and fname.startswith("."):
                continue
            files.append(Path(root) / fname)
    return files


def filter_files_by_extension(files, extensions):
    """
    Filter a list of files by extension.
    Args:
        files (list of Path): Files to filter.
        extensions (set or list): Extensions to include (e.g., {'json', 'yaml'}).
    Returns:
        list of Path: Filtered files.
    """
    extensions = set(e.lstrip(".").lower() for e in extensions)
    return [f for f in files if f.suffix.lower().lstrip(".") in extensions]


def normalize_path(path):
    """
    Normalize a file path to use forward slashes and be relative to project root.
    Args:
        path (str or Path): Path to normalize.
    Returns:
        str: Normalized path as string.
    """
    return str(Path(path).as_posix())
