# -*- coding: utf-8 -*- 
# tests/test_shell_utils.py

import os
import platform
import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, List, Optional
from unittest.mock import patch

import pytest

from cartaos.install_dev_env.shell_utils import (
    get_shell_recommendation,
    run_and_check,
    run_command,
)


# --- Tests for run_command (check=False, the default) ---

def test_run_command_success(monkeypatch: pytest.MonkeyPatch):
    """Verify that a successful command returns True and its stdout."""

    def fake_run(*args, **kwargs) -> CompletedProcess:
        return CompletedProcess(args, returncode=0, stdout="OK", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    ok, output = run_command(["echo", "hello"])
    assert ok is True
    assert output == "OK"

def test_run_command_failure_returns_combined_output(monkeypatch: pytest.MonkeyPatch):
    """Verify that a failed command (check=False) returns False and combined output."""

    def fake_run(*args, **kwargs) -> CompletedProcess:
        return CompletedProcess(
            args, returncode=1, stdout="some out", stderr="some err"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    ok, out = run_command(["cmd"])
    assert ok is False
    assert out == "some out\nsome err"

def test_run_command_file_not_found(monkeypatch: pytest.MonkeyPatch):
    """Verify that FileNotFoundError is caught and returns False."""

    def fake_run(*args: Any, **kwargs: Any) -> None:
        raise FileNotFoundError("file not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    ok, output = run_command(["doesnotexist"])
    assert ok is False
    assert "Command not found: doesnotexist" in output


# --- Tests for run_command (check=True) and run_and_check ---

def test_run_command_check_true_raises_on_failure(monkeypatch: pytest.MonkeyPatch):
    """Verify that run_command with check=True raises CalledProcessError on failure."""

    def fake_run(*args, **kwargs):
        # When check=True, subprocess.run raises this error on non-zero exit codes.
        # We simulate that behavior here.
        raise subprocess.CalledProcessError(1, args[0], output="out", stderr="err")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(subprocess.CalledProcessError):
        run_command(["failing_cmd"], check=True)

def test_run_and_check_success():
    """Test that run_and_check returns stdout on success."""
    with patch(
        "cartaos.install_dev_env.shell_utils.run_command",
        return_value=(True, "Success output"),
    ) as mock_run:
        result = run_and_check(["echo", "hello"])
        assert result == "Success output"
        mock_run.assert_called_once_with(["echo", "hello"], env=None, cwd=None, use_login_shell=False, check=True)

def test_run_and_check_raises_on_failure():
    """Test that run_and_check propagates exceptions on failure."""
    with patch(
        "cartaos.install_dev_env.shell_utils.run_command",
        side_effect=subprocess.CalledProcessError(1, "cmd"),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            run_and_check(["failing_cmd"])


# --- Other Utility Tests ---

def test_get_shell_recommendation_variants(monkeypatch: pytest.MonkeyPatch):
    """Test shell recommendation for various environments."""
    monkeypatch.setenv("SHELL", "/bin/zsh")
    assert "zshrc" in get_shell_recommendation()

    monkeypatch.setenv("SHELL", "/bin/bash")
    rec = get_shell_recommendation()
    assert "bashrc" in rec or "profile" in rec

    monkeypatch.setenv("SHELL", "/usr/bin/fish")
    assert "restart your terminal" in get_shell_recommendation()

    monkeypatch.delenv("SHELL", raising=False)
    assert "restart your terminal" in get_shell_recommendation()