# tagging.py
# Utility for assigning tags and colors to manifest entries

TAG_COLOR_MAP = {
    "critical": "#ff4d4d",
    "important": "#ffd700",
    "info": "#4da6ff",
    "automation": "#4dff88",
    "sensor": "#b3b3ff",
    "default": "#e0e0e0",
}

FILETYPE_MAP = {
    "json": "JSON",
    "md": "Markdown",
    "yaml": "YAML",
    "yml": "YAML",
    "txt": "Text",
    "csv": "CSV",
    "py": "Python",
    "none": "JSON",
}


def get_filetype_tag(filename):
    ext = filename.split(".")[-1].lower() if "." in filename else "none"
    return FILETYPE_MAP.get(ext, "Other")


def get_tag_color(tag):
    return TAG_COLOR_MAP.get(tag, TAG_COLOR_MAP["default"])


def render_tags(tags):
    if not tags:
        return ""
    return " ".join(
        [
            f"<span style='background:{get_tag_color(tag)};color:#222;padding:2px 6px;border-radius:6px;margin-right:2px'>{tag}</span>"
            for tag in tags
        ]
    )
