# registry_inputs.py
"""
Utility for fetching canonical registry input file paths for the Omega Registry pipeline.
"""
import os

from scripts.utils.pipeline_config import REGISTRY_SOURCE_FILES

REGISTRY_INPUTS_DIR = "canonical/registry_inputs/"


def get_registry_input_files():
    """
    Returns a list of absolute paths to all canonical registry input files.
    """
    return [
        os.path.join(REGISTRY_INPUTS_DIR, fname)
        for fname in REGISTRY_SOURCE_FILES.values()
    ]
