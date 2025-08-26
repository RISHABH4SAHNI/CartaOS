# -*- coding: utf-8 -*-
# backend/tests/test_processor_paths.py

import os
from pathlib import Path

import pytest

from cartaos.processor import CartaOSProcessor
from cartaos.config import AppConfig


@pytest.fixture
def base_config(monkeypatch):
    """Create a base AppConfig for testing."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    return AppConfig()


def make_pdf(tmp_path: Path) -> Path:
    p = tmp_path / "doc.pdf"
    p.write_bytes(b"%PDF-1.4\n%...\n")
    return p


def test_summary_dir_prefers_obsidian_vault_when_valid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, base_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault))

    # Create a new config with the vault path set
    config = AppConfig()
    proc = CartaOSProcessor(pdf_path=pdf, config=config)
    assert config.summary_dir == vault / "Summaries"


def test_summary_dir_fallback_when_vault_invalid_or_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, base_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)
    # Ensure env var is unset
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)

    config = AppConfig()
    proc = CartaOSProcessor(pdf_path=pdf, config=config)
    assert config.summary_dir == config.processed_pdf_dir / "Summaries"

    # Even if set but not a directory, should fallback
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "missing_dir"))
    config2 = AppConfig()
    proc2 = CartaOSProcessor(pdf_path=pdf, config=config2)
    assert config2.summary_dir == config2.processed_pdf_dir / "Summaries"


def test_generate_summary_empty_string_is_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, base_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)
    monkeypatch.setattr("cartaos.processor.extract_text", lambda p: "raw")
    monkeypatch.setattr("cartaos.processor.sanitize", lambda t: "sanitized")
    # Empty string is falsy
    monkeypatch.setattr("cartaos.processor.generate_summary", lambda t, k: "")

    proc = CartaOSProcessor(pdf_path=pdf, config=base_config)
    assert proc.process() is False
