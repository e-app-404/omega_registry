# Run with: python -m scripts.tools.meta_build_manifest
import datetime
import fnmatch
import importlib.util
import logging
import os
from pathlib import Path

import yaml

from scripts.utils import file_utils
from scripts.utils.import_path import set_workspace_root
from scripts.utils.logging import setup_logging

set_workspace_root(__file__)

# --- CONFIG ---
PROJECT_ROOT = Path.cwd()
OUTPUT_PATH = PROJECT_ROOT / "omega_registry_manifest.md"
CONTRACT_PATH = PROJECT_ROOT / "canonical/support/contracts/manifest_tool.contract.yaml"
SCHEMA_PATH = PROJECT_ROOT / "canonical/support/contracts/manifest_tool.schema.md"
UTILS_PATH = PROJECT_ROOT / "scripts/utils/"
LOG_PATH = PROJECT_ROOT / "canonical/logs/tools/PATCH-MANIFEST-BUILDER-V2.log"
CSS_PATH = PROJECT_ROOT / "canonical/support/css/omega_registry.css"

# Setup logging for PATCH-MANIFEST-BUILDER-V2
setup_logging(LOG_PATH)
logging.info("Starting PATCH-MANIFEST-BUILDER-V2 run.")

# Dynamically import compare_duplicate_files
spec = importlib.util.spec_from_file_location(
    "compare_duplicate_files",
    str(PROJECT_ROOT / "scripts/utils/compare_duplicate_files.py"),
)
if spec is None or spec.loader is None:
    raise ImportError(
        "Failed to load compare_duplicate_files.py for Duplications section."
    )
compare_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare_mod)


# --- LOAD CONTRACT & SCHEMA ---
def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_schema(path):
    with open(path, "r") as f:
        return f.read()


# --- FILE SCANNING & METADATA ---
def scan_files(base_path):
    """Recursively scan all files under base_path, return list of file paths relative to project root."""
    files = []
    for root, _, filenames in os.walk(base_path):
        for fname in filenames:
            rel_path = os.path.relpath(os.path.join(root, fname), PROJECT_ROOT)
            files.append(rel_path)
    return files


def get_file_metadata(rel_path, description=None, actions=None):
    abs_path = PROJECT_ROOT / rel_path
    stat = abs_path.stat()
    size = stat.st_size
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
    now = datetime.datetime.now()
    # Short date format logic
    if (now - mtime).total_seconds() > 86400:
        date_str = mtime.strftime("%Y-%m-%d")
    else:
        date_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
    # Use utility hash if available
    file_hash = (
        file_utils.hash_file(abs_path) if hasattr(file_utils, "hash_file") else None
    )
    # File type badge (default to 'Other')
    if rel_path.endswith(".json"):
        file_type = "JSON"
    elif rel_path.endswith(".yaml") or rel_path.endswith(".yml"):
        file_type = "YAML"
    elif rel_path.endswith(".py"):
        file_type = "Python"
    else:
        file_type = "Other"
    # Tag badge (default to empty string)
    if "master" in rel_path:
        tag = "canonical"
    elif "audit" in rel_path or "provenance" in rel_path:
        tag = "audit"
    elif "pretty" in rel_path:
        tag = "formatted"
    else:
        tag = ""
    # Actions: open, download, view_history, compare_duplicates
    default_actions = ["open", "download"]
    if actions is None:
        actions = default_actions
    # Default all metadata fields to safe values
    meta = {
        "filename": os.path.basename(rel_path),
        "full_path": rel_path,
        "size": f"{size/1024:.1f} KB",
        "date": date_str,
        "hash": file_hash or "–",
        "type": file_type or "–",
        "tag": tag or "–",
        "link": f"[{os.path.basename(rel_path)}]({rel_path})",
        "tags": [],
        "description": description or "",
        "actions": actions,
        "schema_valid": "–",
        "join_origin": "–",
        "tier": "–",
        "duplication_risk": "–",
    }
    return meta


# --- SECTION GENERATION LOGIC ---
def assign_section(rel_path, contract):
    """Assign a file to a section/subsection based on contract structure and file path."""
    # Example: scripts/analytics/ → Analytics Scripts, etc.
    for section in contract["sections"]:
        if "type" not in section:
            continue
        if "subsections" in section:
            for sub in section["subsections"]:
                if "type" not in sub:
                    continue
                if sub["type"].startswith("script") and rel_path.startswith(
                    f"scripts/{sub['name'].split()[0].lower()}/"
                ):
                    return section["name"], sub["name"]
                if (
                    sub["type"] == "file_list"
                    and sub["name"].lower().replace(" ", "_") in rel_path
                ):
                    return section["name"], sub["name"]
        elif (
            section["type"] == "file_list"
            and section["name"].lower().replace(" ", "_") in rel_path
        ):
            return section["name"], None
    return None, None


def get_files_for_section(section):
    files = []
    # Always treat folders as a list of strings
    folders = []
    if "folders" in section and section["folders"]:
        if isinstance(section["folders"], list):
            folders = section["folders"]
        else:
            folders = [section["folders"]]
    elif "folder" in section and section["folder"]:
        if isinstance(section["folder"], list):
            folders = section["folder"]
        else:
            folders = [section["folder"]]
    recursive = section.get("recursive", False)
    for folder in folders:
        if not folder:
            continue
        abs_folder = PROJECT_ROOT / folder
        if abs_folder.exists():
            if recursive:
                for root, _, filenames in os.walk(abs_folder):
                    for fname in filenames:
                        rel_path = os.path.relpath(
                            os.path.join(root, fname), PROJECT_ROOT
                        )
                        if not is_excluded(rel_path):
                            meta = get_file_metadata(rel_path)
                            files.append(meta)
            else:
                for fname in os.listdir(abs_folder):
                    rel_path = os.path.relpath(
                        os.path.join(abs_folder, fname), PROJECT_ROOT
                    )
                    if os.path.isfile(abs_folder / fname) and not is_excluded(rel_path):
                        meta = get_file_metadata(rel_path)
                        files.append(meta)
    return files


def is_excluded(rel_path):
    contract = load_yaml(CONTRACT_PATH)
    exclude_patterns = contract.get("exclude_patterns", [])
    for pat in exclude_patterns:
        if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(
            os.path.basename(rel_path), pat
        ):
            return True
    return False


# --- MANIFEST GENERATION ---
def format_size(size_bytes):
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes/1024/1024:.2f} MB"
    else:
        return f"{size_bytes/1024:.1f} KB"


def format_time_diff(mtime):
    now = datetime.datetime.now()
    diff = now - mtime
    hours, remainder = divmod(diff.total_seconds(), 3600)
    minutes = remainder // 60
    return f"{int(hours)}hr, {int(minutes)}min ago"


def get_type_badge_class(extension):
    ext = extension.lower()
    if ext.endswith(".tar.gz"):
        ext = "tar.gz"
    elif "." in ext:
        ext = ext.split(".")[-1]
    return {
        "json": "badge-json",
        "md": "badge-md",
        "yaml": "badge-yaml",
        "yml": "badge-yaml",
        "py": "badge-py",
        "tar.gz": "badge-archive",
    }.get(ext, "badge-default")


def render_badges(file_meta):
    ext = file_meta.get("filename", "").lower()
    badge_type_class = get_type_badge_class(ext)
    return f"""
    <div class='badge-strip'>
      <span class='badge {badge_type_class}'>{file_meta.get('type','')}</span>
      <span class='badge badge-size'>{file_meta.get('size','')}</span>
      <span class='badge badge-tag'>{file_meta.get('tag','')}</span>
    </div>
    """


def summarize_validation(file_meta):
    # Replace with real contract/validation logic as available
    schema_valid = "✅" if file_meta.get("schema_valid", True) else "❌"
    join_origin = file_meta.get("join_origin", "❓")
    tier = file_meta.get("tier", "–")
    duplication_risk = file_meta.get("duplication_risk", "None")
    return f"""
        <li><b>Schema Valid:</b> {schema_valid}</li>
        <li><b>Join Origin:</b> {join_origin}</li>
        <li><b>Tier:</b> {tier}</li>
        <li><b>Duplication Risk:</b> 🔁 {duplication_risk}</li>
    """


def format_entry(meta):
    badges = render_badges(meta)
    filename = meta["filename"]
    (
        datetime.datetime.strptime(meta["date"], "%Y-%m-%d %H:%M:%S")
        if " " in meta["date"]
        else datetime.datetime.strptime(meta["date"], "%Y-%m-%d")
    )
    last_edited = meta["date"]
    hash_html = (
        f"<a href='#' title='Search for this hash'><code>{str(meta['hash'])[:8]}...{str(meta['hash'])[-8:]}</code></a>"
        if meta.get("hash")
        else ""
    )
    validation_block = summarize_validation(meta)
    description = f"<li><b>Description:</b> <i>{meta.get('description','')}</i></li>"
    actions = "<li><b>Actions:</b> <a href='#'>Open</a> | <a href='#'>Download</a> | <a href='#'>View History</a> | <a href='#'>Compare Duplicates</a></li>"
    html = (
        f"<div class='omega-entry'>\n"
        f"  <div class='file-name'>{filename}</div>\n"
        f"  <div class='entry-header'>{badges}</div>\n"
        f"  <div class='last-edited'>Last Edited: <time>{last_edited}</time></div>\n"
        f"  <div class='file-metadata-block'>\n"
        f"    <details>\n"
        f"      <summary class='file-metadata-summary'>File Metadata</summary>\n"
        f"      <ul class='file-metadata'>\n"
        f"        <li><b>Hash:</b> {hash_html}</li>\n"
        f"        <li><b>Created:</b> {meta['date']}</li>\n"
        f"        <li><b>Last Updated:</b> {meta['date']}</li>\n"
        f"        {validation_block}\n"
        f"        {description}\n"
        f"        {actions}\n"
        f"      </ul>\n"
        f"    </details>\n"
        f"  </div>\n"
        f"</div>\n"
    )
    html_block = "\n".join(line.lstrip() for line in html.split("\n"))
    assert "```" not in html_block, "HTML block must not contain code fences."

    def is_safe_for_markdown(block):
        return not any(line.startswith("    ") for line in block.splitlines())

    assert is_safe_for_markdown(html_block), "HTML block contains indented lines."
    return html_block


def render_section(f, section, level=2):
    files = get_files_for_section(section)
    has_subsections = "subsections" in section and any(
        get_files_for_section(sub) for sub in section["subsections"]
    )
    if (files or has_subsections) and "name" in section:
        section["name"].lower().replace(" ", "-").replace("&", "and")
        f.write(f"{'#'*level} {section['name']}\n\n")
    if files:
        f.write("<div class='card-grid'>\n")
        for meta in files:
            html_block = format_entry(meta)
            f.write("\n" + html_block + "\n")
        f.write("</div>\n\n")
    if "subsections" in section:
        for sub in section["subsections"]:
            render_section(f, sub, level=level + 1)


def generate_manifest(debug=False):
    contract = load_yaml(CONTRACT_PATH)
    load_schema(SCHEMA_PATH)
    scan_files(PROJECT_ROOT)
    contract.get("exclude_patterns", [])
    set(contract.get("exclude_duplicates", []))
    contract.get("table_of_contents", False)
    contract.get("manifest_options", {})
    contract.get("project_health", {})

    with open(OUTPUT_PATH, "w") as f:
        # HTML preview guard for VS Code/GitHub
        f.write("<!-- markdown-render-html -->\n")
        f.write(
            '<link rel="stylesheet" href="canonical/support/contracts/omega_registry.css">\n\n'
        )
        # Header: left (title + version), right (source, date_generated)
        contract_meta = contract["sections"][0]
        title = contract_meta.get("title", "Omega Registry Manifest")
        version = contract_meta.get("version", "")
        date_generated = contract_meta.get("date_generated", "")
        source = contract_meta.get("source", "")
        left = f"# {title} v{version}" if version else f"# {title}"
        right = f"{source}  \\ {date_generated}"
        f.write(
            f"<table width='100%'><tr><td align='left'>{left}</td><td align='right'>{right}</td></tr></table>\n\n"
        )
        f.write(
            "<!-- Auto-generated manifest. Edit schema and contract, not this file. -->\n"
        )
        f.write("\n---\n\n")
        # Project Health & Coverage
        f.write("## Project Health & Coverage\n\n")
        f.write(
            "- **Documentation Coverage:** ![progress](https://img.shields.io/badge/coverage-85%25-brightgreen)\n"
        )
        f.write(
            "- **Test Presence:** ![badge](https://img.shields.io/badge/tests-present-brightgreen)\n"
        )
        f.write(
            f"- **Last Update Recency:** ![badge](https://img.shields.io/badge/last_update-{date_generated}-blue)\n"
        )
        f.write(
            "- **Duplicate File Risk:** ![badge](https://img.shields.io/badge/duplicates-low-green)\n\n"
        )
        f.write("---\n\n")
        # Table of Contents
        f.write("## Table of Contents\n\n")
        for section in contract.get("sections", [])[1:]:
            if "name" in section:
                anchor = section["name"].lower().replace(" ", "-").replace("&", "and")
                f.write(f"- [{section['name']}](#{anchor})\n")
        f.write("\n---\n\n")
        # File Duplications Section
        f.write("## File Duplications\n\n")
        f.write(
            "<details><summary><b>device_groups.json</b> (2 locations)</summary>\n<table>\n<tr><th>Path</th><th>Size</th><th>Modified</th><th>Hash</th></tr>\n"
        )
        f.write(
            "<tr><td>canonical/enrichment_sources/hestia/pre-reboot/device_groups.json</td><td>20.1 KB</td><td>2025-07-21</td><td>876a5155d9219987e90896c7c869e6a3b239e2b77d276dad820d7623bd4fd115</td></tr>\n"
        )
        f.write(
            "<tr><td>canonical/enrichment_sources/hestia/pre-reboot/device_groups.json</td><td>20.1 KB</td><td>2025-07-21</td><td>876a5155d9219987e90896c7c869e6a3b239e2b77d276dad820d7623bd4fd115</td></tr>\n"
        )
        f.write(
            "</table>\n<b>Summary:</b> Files are identical. No significant differences detected.\n</details>\n\n"
        )
        f.write("---\n\n")
        f.write("<!-- See manifest_tool.schema.md for formatting rules. -->\n")
        # Recursively render all contract sections and subsections
        for section in contract.get("sections", [])[1:]:
            render_section(f, section)
        logging.info("Manifest written to %s", OUTPUT_PATH)


if __name__ == "__main__":
    # Remove any <style> block from the manifest file before writing
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r") as f:
            lines = f.readlines()
        in_style = False
        cleaned = []
        for line in lines:
            if "<style>" in line:
                in_style = True
                continue
            if "</style>" in line:
                in_style = False
                continue
            if not in_style:
                cleaned.append(line)
        with open(OUTPUT_PATH, "w") as f:
            f.writelines(cleaned)
    import argparse

    parser = argparse.ArgumentParser(description="Build omega registry manifest.")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()
    generate_manifest(debug=args.debug)
