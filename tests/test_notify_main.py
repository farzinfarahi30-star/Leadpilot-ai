import io
import sys
import builtins
import json
import os
import importlib

import pytest

# Ensure the module uses the patched environment variables
os.environ['GH_REPOSITORY'] = 'owner/repo'
os.environ['GH_TOKEN'] = 'dummy-token'

def capture_stdout(func, *args, **kwargs):
    """Utility to capture stdout of a function."""
    captured = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = captured
    try:
        func(*args, **kwargs)
    finally:
        sys.stdout = sys_stdout
    return captured.getvalue()

def test_main_handles_missing_report_file(monkeypatch):
    """
    When the expected JSON report file does not exist, `main` should
    print a friendly message and exit without raising.
    """
    # Ensure the file truly does not exist
    report_path = 'reports/public-paid-task-scout.json'
    if os.path.exists(report_path):
        os.remove(report_path)

    # Reload the module to guarantee a fresh state
    notify = importlib.import_module('nova_earning_agent.notify')
    importlib.reload(notify)

    output = capture_stdout(notify.main)
    assert 'Report file not found' in output
    # No exception should be raised – the test would fail otherwise

def test_main_handles_empty_candidates(monkeypatch, tmp_path):
    """
    When the JSON file exists but contains no candidates, `main` should
    report that there are no qualified leads.
    """
    # Create a temporary reports directory with an empty candidates list
    reports_dir = tmp_path / 'reports'
    reports_dir.mkdir()
    report_file = reports_dir / 'public-paid-task-scout.json'
    report_file.write_text(json.dumps({'candidates': []}), encoding='utf-8')

    # Patch the working directory to the temporary location
    monkeypatch.chdir(tmp_path)

    # Reload the module to pick up the new cwd
    notify = importlib.import_module('nova_earning_agent.notify')
    importlib.reload(notify)

    output = capture_stdout(notify.main)
    assert 'No qualified leads' in output
