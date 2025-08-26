# -*- coding: utf-8 -*-
# backend/cartaos/processor.py

"""
processor.py
Handles the processing of PDF files to generate summaries using AI.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

from rich.progress import (BarColumn, Progress, SpinnerColumn, TaskID,
                           TextColumn, TimeRemainingColumn)
from slugify import slugify

from .utils.ai_utils import generate_summary
from .utils.pdf_utils import extract_text
from .utils.text_utils import sanitize
from .utils.utils import WarningCaptureHandler
from .config import AppConfig


class CartaOSProcessor:
    """Encapsulates the entire process of generating a summary for a PDF file."""

    def __init__(
        self,
        pdf_path: Path,
        config: AppConfig,
        dry_run: bool = False,
        debug: bool = False,
        force_ocr: bool = False,
    ) -> None:
        """
        Initializes the CartaOSProcessor with paths and configuration options.

        Args:
            pdf_path (Path): Path to the PDF file to be processed.
            config (AppConfig): Application configuration instance.
            dry_run (bool): If True, processes without saving or moving files.
            debug (bool): If True, saves extracted text and stops before AI call.
            force_ocr (bool): If True, forces OCR processing before summarization.
        """
        self.pdf_path: Path = pdf_path
        self.config: AppConfig = config
        self.dry_run: bool = dry_run
        self.debug: bool = debug
        self.force_ocr: bool = force_ocr

        self.captured_warnings: List[str] = []
        self._setup_warning_capture()


    def _setup_warning_capture(self) -> None:
        """Configures a handler to capture pdfminer warnings in memory."""
        pdfminer_logger: logging.Logger = logging.getLogger("pdfminer")
        pdfminer_logger.setLevel(logging.WARNING)
        handler: WarningCaptureHandler = WarningCaptureHandler(self.captured_warnings)
        pdfminer_logger.addHandler(handler)
        pdfminer_logger.propagate = False

    def _save_summary(self, summary_content: str) -> None:
        """
        Saves the summary content to a .md file.

        Args:
            summary_content (str): The content of the summary to be saved.
        """
        base_name: str = self.pdf_path.stem
        safe_name: str = slugify(base_name)

        md_output_path: Path = self.config.summary_dir / f"{safe_name}.md"
        os.makedirs(self.config.summary_dir, exist_ok=True)
        with open(md_output_path, "w", encoding="utf-8") as f:
            f.write(summary_content)

    def _move_pdf(self) -> None:
        """Moves the original PDF to the processed directory."""
        pdf_output_path: Path = self.config.processed_pdf_dir / self.pdf_path.name
        shutil.move(self.pdf_path, pdf_output_path)

    def process(self) -> bool:
        """
        Orchestrates the entire processing workflow.

        Returns:
            bool: True if processing is successful, False otherwise.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task: TaskID = progress.add_task("[cyan]Processing PDF...", total=100)

            progress.update(task, advance=20)
            logging.info("Extracting text from the PDF...")
            text: Optional[str] = extract_text(self.pdf_path)
            if not text:
                logging.error("Process stopped: text could not be extracted.")
                return False

            progress.update(task, advance=20)
            if self.debug:
                debug_path: Path = (
                    self.pdf_path.parent / f"{self.pdf_path.stem}_extracted_text.txt"
                )
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(text)
                logging.info(f"DEBUG MODE: Extracted text saved to {debug_path}")
                logging.info("Process stopped after text extraction as requested.")
                progress.update(task, advance=60)
                return True

            sanitized_text: str = sanitize(text)

            progress.update(task, advance=20)
            logging.info("Generating summary with the AI model...")

            if not self.config.api_key:
                logging.error("API key not configured. Cannot generate summary.")
                return False

            summary: Optional[str] = generate_summary(sanitized_text, self.config.api_key)
            if not summary:
                logging.error("Process stopped: summary could not be generated.")
                return False

            progress.update(task, advance=20)
            if self.dry_run:
                logging.info("[DRY RUN] Process would be successful.")
                print(summary)
                return True

            self._save_summary(summary)
            self._move_pdf()
            logging.info("File processed successfully.")
            return True
