# -*- coding: utf-8 -*-
# backend/tests/test_processor_edge_cases.py

from pathlib import Path

import pytest

from cartaos.processor import CartaOSProcessor
from cartaos.config import AppConfig


def make_pdf(tmp_path: Path, name: str = "doc.pdf") -> Path:
    p = tmp_path / name
    p.write_bytes(b"%PDF-1.4\n")
    return p


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """Create a mock AppConfig for testing."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "")
    return AppConfig()


def test_process_fails_when_text_extraction_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mock_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)
    monkeypatch.setattr("cartaos.processor.extract_text", lambda p: None)
    proc = CartaOSProcessor(pdf, config=mock_config)
    assert proc.process() is False


def test_process_fails_when_generate_summary_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mock_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)
    monkeypatch.setattr("cartaos.processor.extract_text", lambda p: "hello")
    monkeypatch.setattr("cartaos.processor.sanitize", lambda t: t)
    monkeypatch.setattr("cartaos.processor.generate_summary", lambda t, k: None)
    proc = CartaOSProcessor(pdf, config=mock_config)
    assert proc.process() is False


def test_save_summary_slugifies_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pdf = make_pdf(tmp_path, name="My Report (v1).pdf")
    monkeypatch.setattr("cartaos.processor.extract_text", lambda p: "content")
    monkeypatch.setattr("cartaos.processor.sanitize", lambda t: t)
    monkeypatch.setattr("cartaos.processor.generate_summary", lambda t, k: "Summary Text")

    # Create config with custom directories
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "")
    config = AppConfig()
    config.processed_pdf_dir = tmp_path / "07_Processed"
    config.summary_dir = config.processed_pdf_dir / "Summaries"

    # Avoid moving the PDF so we can assert summary file easily  
    monkeypatch.setattr("cartaos.processor.CartaOSProcessor._move_pdf", lambda self: None)

    proc = CartaOSProcessor(pdf, config=config)
    assert proc.process() is True

    md = tmp_path / "07_Processed" / "Summaries" / "my-report-v1.md"
    assert md.exists()
    assert md.read_text(encoding="utf-8") == "Summary Text"
