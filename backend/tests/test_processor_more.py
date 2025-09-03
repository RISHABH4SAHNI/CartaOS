# -*- coding: utf-8 -*-
# backend/tests/test_processor_more.py

import builtins
from pathlib import Path

import pytest

from cartaos.processor import CartaOSProcessor
from cartaos.config import AppConfig


def make_pdf(tmp_path: Path) -> Path:
    p = tmp_path / "doc.pdf"
    p.write_bytes(b"%PDF-1.4\n%...\n")
    return p


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """Create a mock AppConfig for testing."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "")
    return AppConfig()


def test_process_extract_text_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mock_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)

    # Patch the imported name inside cartaos.processor
    monkeypatch.setattr("cartaos.processor.extract_text", lambda p: None)

    proc = CartaOSProcessor(pdf_path=pdf, config=mock_config)
    assert proc.process() is False


def test_process_debug_path_creates_debug_file_and_returns_true(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mock_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)
    # Simulate extracted text
    monkeypatch.setattr("cartaos.processor.extract_text", lambda p: "hello text")

    # Ensure sanitize and generate_summary never used in debug path by raising if called
    def boom(*a, **k):
        raise AssertionError("Should not be called in debug mode")

    monkeypatch.setattr("cartaos.processor.sanitize", boom)
    monkeypatch.setattr("cartaos.processor.generate_summary", boom)

    proc = CartaOSProcessor(pdf_path=pdf, config=mock_config, debug=True)


    ok = proc.process()
    assert ok is True
    debug_file = pdf.parent / f"{pdf.stem}_extracted_text.txt"
    assert debug_file.exists()
    assert debug_file.read_text(encoding="utf-8") == "hello text"


def test_process_dry_run_logs_summary_and_returns_true(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture, mock_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)

    # Regular path: extract -> sanitize -> generate_summary -> dry_run True
    monkeypatch.setattr("cartaos.processor.extract_text", lambda p: "raw")
    monkeypatch.setattr("cartaos.processor.sanitize", lambda t: "sanitized")
    monkeypatch.setattr("cartaos.processor.generate_summary", lambda t, k: "the summary")

    # Avoid file operations in dry run; process should not call _save/_move
    save_called = {"save": False, "move": False}

    def fake_save(self, s):
        save_called["save"] = True

    def fake_move(self):
        save_called["move"] = True

    monkeypatch.setattr(CartaOSProcessor, "_save_summary", fake_save)
    monkeypatch.setattr(CartaOSProcessor, "_move_pdf", fake_move)

    with caplog.at_level('INFO'):
        proc = CartaOSProcessor(pdf_path=pdf, config=mock_config, dry_run=True)
        ok = proc.process()
        assert ok is True

        log_messages = [rec.message for rec in caplog.records]
        assert any("[DRY RUN] Process would be successful." in msg for msg in log_messages)
        assert any("Summary: the summary" in msg for msg in log_messages)

    # Ensure no file ops in dry run
    assert save_called["save"] is False
    assert save_called["move"] is False


def test_process_generate_summary_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mock_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)

    monkeypatch.setattr("cartaos.processor.extract_text", lambda p: "raw")
    monkeypatch.setattr("cartaos.processor.sanitize", lambda t: "sanitized")
    monkeypatch.setattr("cartaos.processor.generate_summary", lambda t, k: None)

    proc = CartaOSProcessor(pdf_path=pdf, config=mock_config)
    assert proc.process() is False


def test_process_defaults_full_success_saves_and_moves(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mock_config: AppConfig
) -> None:
    pdf = make_pdf(tmp_path)

    # Ensure normal pipeline succeeds
    monkeypatch.setattr("cartaos.processor.extract_text", lambda p: "raw")
    monkeypatch.setattr("cartaos.processor.sanitize", lambda t: "sanitized")
    monkeypatch.setattr("cartaos.processor.generate_summary", lambda t, k: "the summary")

    calls = {"save": 0, "move": 0}

    def fake_save(self, s):
        calls["save"] += 1

    def fake_move(self):
        calls["move"] += 1

    monkeypatch.setattr(CartaOSProcessor, "_save_summary", fake_save)
    monkeypatch.setattr(CartaOSProcessor, "_move_pdf", fake_move)

    # Default args: dry_run must be False so save/move happen
    proc = CartaOSProcessor(pdf_path=pdf, config=mock_config)
    ok = proc.process()
    assert ok is True
    assert calls["save"] == 1
    assert calls["move"] == 1
