#!/usr/bin/env python3
"""
Test runner for TidyMe project
"""

import subprocess
import sys
import os

def run_tests():
    """Run the test suite"""
    print("Running TidyMe test suite...")

    # Activate virtual environment if it exists
    venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'activate')
    if os.path.exists(venv_path):
        activate_cmd = f"source {venv_path} && python -m pytest"
    else:
        activate_cmd = "python -m pytest"

    try:
        result = subprocess.run(activate_cmd, shell=True, cwd=os.path.dirname(__file__))
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def run_specific_test(test_file):
    """Run a specific test file"""
    print(f"Running specific test: {test_file}")

    venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'activate')
    if os.path.exists(venv_path):
        cmd = f"source {venv_path} && python -m pytest tests/{test_file}"
    else:
        cmd = f"python -m pytest tests/{test_file}"

    try:
        result = subprocess.run(cmd, shell=True, cwd=os.path.dirname(__file__))
        return result.returncode == 0
    except Exception as e:
        print(f"Error running test: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        success = run_specific_test(test_file)
    else:
        success = run_tests()

    sys.exit(0 if success else 1)