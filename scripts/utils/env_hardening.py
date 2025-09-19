#!/usr/bin/env python3
"""
Python Environment Hardening Script
Performs the following steps:
1. Remove all __pycache__ directories and .pyc files
2. Add __init__.py to all package directories
3. Verify virtual environment integrity
4. Run a shadow path audit
5. Standardize all script shebangs
6. Run the omega registry pipeline
Logs results for each step and halts on failure.
"""
import os
import subprocess
import sys
from pathlib import Path

LOGFILE = "env_hardening.log"
EXPECTED_PYTHON_VERSION = "3.13"
REPO_ROOT = Path(__file__).resolve().parents[2]


def log(msg):
    with open(LOGFILE, "a") as f:
        f.write(msg + "\n")
    print(msg)


def run(cmd, check=True, capture_output=True, shell=False, env=None):
    log(f"[RUN] {cmd}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            shell=shell,
            env=env,
            text=True,
        )
        if result.stdout:
            log(result.stdout.strip())
        if result.stderr:
            log(result.stderr.strip())
        return result
    except subprocess.CalledProcessError as e:
        log(f"[FAIL] {e}\n{e.stdout}\n{e.stderr}")
        sys.exit(1)


def step1_remove_pycache_and_pyc():
    log("Step 1: Removing __pycache__ directories and .pyc files...")
    run(
        [
            "find",
            str(REPO_ROOT),
            "-name",
            "__pycache__",
            "-type",
            "d",
            "-exec",
            "rm",
            "-rf",
            "{}",
            "+",
        ]
    )
    run(["find", str(REPO_ROOT), "-name", "*.pyc", "-exec", "rm", "-f", "{}", "+"])
    log("Step 1 complete.")


def step2_add_init_py():
    log("Step 2: Adding __init__.py to package directories...")
    pkgs = [
        REPO_ROOT / "scripts/__init__.py",
        REPO_ROOT / "scripts/utils/__init__.py",
        REPO_ROOT / "scripts/omega_registry/__init__.py",
    ]
    for pkg in pkgs:
        pkg.parent.mkdir(parents=True, exist_ok=True)
        pkg.touch(exist_ok=True)
        log(f"Ensured {pkg.relative_to(REPO_ROOT)} exists.")
    log("Step 2 complete.")


def step3_verify_venv():
    log("Step 3: Verifying virtual environment integrity...")
    which = run(["which", "python3"])
    if "venv/bin/python3" not in which.stdout:
        log("[FAIL] python3 does not point to venv/bin/python3")
        sys.exit(1)
    version = run(["python3", "--version"])
    if EXPECTED_PYTHON_VERSION not in version.stdout:
        log(
            f"[FAIL] python3 version mismatch: expected {EXPECTED_PYTHON_VERSION}, got {version.stdout.strip()}"
        )
        sys.exit(1)
    log("Step 3 complete.")


def step4_shadow_path_audit():
    log("Step 4: Running shadow path audit...")
    run(["which", "-a", "python3"])
    log("Step 4 complete.")


def step5_standardize_shebangs():
    log("Step 5: Standardizing script shebangs...")
    # Find all scripts with #!/usr/bin/env python and replace with python3
    for path in REPO_ROOT.rglob("*.py"):
        try:
            with open(path, "r") as f:
                lines = f.readlines()
            if (
                lines
                and lines[0].startswith("#!/usr/bin/env python")
                and not lines[0].startswith("#!/usr/bin/env python3")
            ):
                lines[0] = "#!/usr/bin/env python3\n"
                with open(path, "w") as f:
                    f.writelines(lines)
                log(f"Updated shebang in {path.relative_to(REPO_ROOT)}")
        except Exception as e:
            log(f"[FAIL] Could not update shebang in {path}: {e}")
            sys.exit(1)
    log("Step 5 complete.")


def step6_run_pipeline():
    log("Step 6: Running omega registry pipeline...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    cmd = [
        "python3",
        "-m",
        "scripts.generate_omega_registry_v2",
        "--output",
        "canonical/omega_registry_master.json",
        "--contract",
        "canonical/support/manifests/enrichment_manifest.omega.yaml",
        "--strict",
    ]
    run(cmd, env=env)
    log("Step 6 complete.")


def main():
    open(LOGFILE, "w").close()  # Clear log
    step1_remove_pycache_and_pyc()
    step2_add_init_py()
    step3_verify_venv()
    step4_shadow_path_audit()
    step5_standardize_shebangs()
    step6_run_pipeline()
    log("All steps completed successfully.")


if __name__ == "__main__":
    main()
