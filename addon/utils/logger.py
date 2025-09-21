from datetime import datetime

def log_patch_action(message, logfiles=None):
    """
    Write a timestamped log entry to one or more log files.
    By default, logs to PATCH_CENTRALIZED-PREREBOOT-LOADER.log and copilot_patchlog_overview.log.
    """
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    log_entry = f"[{ts}] {message}\n"
    if logfiles is None:
        logfiles = ["PATCH_CENTRALIZED-PREREBOOT-LOADER.log", "copilot_patchlog_overview.log"]
    for path in logfiles:
        with open(path, "a") as f:
            f.write(log_entry)
