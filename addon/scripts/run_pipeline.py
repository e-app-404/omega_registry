#!/usr/bin/env python3
import subprocess
import sys
import os

def run(script, *args):
    base = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(base, script)
    cmd = [sys.executable, path] + list(args)
    subprocess.run(cmd)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: run_pipeline.py <script> [args...]")
        sys.exit(1)
    run(sys.argv[1], *sys.argv[2:])
