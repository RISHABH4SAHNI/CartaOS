# -*- coding: utf-8 -*-
# backend/cartaos/utils/ai_utils.py

"""
Utilities for interacting with the Gemini AI API.

This module provides functions for generating analytical summaries using the Gemini AI API.
"""

import logging
from pathlib import Path
from typing import Optional

from google.genai import Client, models

from cartaos import config

from .external_calls import ExternalCallManager
from .keychain import get_secure_api_key

_CLIENT: Optional[Client] = None
_EXTERNAL_CALL_MANAGER: Optional[ExternalCallManager] = None


def get_client(api_key: str) -> Client:
    """
    Creates and returns a singleton instance of the Gemini AI client.

    The client is created only once, and subsequent calls return the same instance.

    Args:
        api_key (str): The API key for the Gemini AI service.

    Returns:
        Client: The Gemini AI client instance.
    """
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    _CLIENT = Client(api_key=api_key.strip())
    logging.info("Gemini AI client initialized successfully.")
    return _CLIENT


def get_client_with_retries() -> Client:
    """
    Creates and returns a Gemini AI client with retry capabilities.
    This function is deprecated - use get_client(api_key) instead.
    """
    raise NotImplementedError("Use get_client(api_key) instead")


def get_external_call_manager() -> ExternalCallManager:
    """Get or create the external call manager for AI operations."""
    global _EXTERNAL_CALL_MANAGER
    if _EXTERNAL_CALL_MANAGER is None:
        _EXTERNAL_CALL_MANAGER = ExternalCallManager(
            timeout=60.0,  # Longer timeout for AI calls
            max_retries=3,
            base_delay=2.0,
            circuit_breaker_threshold=5,
        )
    return _EXTERNAL_CALL_MANAGER


async def generate_content_with_retries(
    prompt: str, api_key: str, model: str = "models/gemini-2.5-pro"
) -> Optional[str]:
    """
    Generate content using Gemini AI with timeout and retry protection.

    Args:
        prompt (str): The prompt to send to the AI
        model (str): The model to use for generation
        api_key (str): The API key for the Gemini AI service

    Returns:
        Optional[str]: Generated content or None if generation fails
    """
    manager = get_external_call_manager()

    async def ai_call():
        client = get_client(api_key)
        response = client.models.generate_content(model=model, contents=prompt)

        if response and hasattr(response, "text"):
            return response.text
        else:
            raise ValueError("AI response was empty or did not contain text")

    try:
        return await manager.call_with_retry(ai_call)
    except Exception as e:
        logging.error(
            "Error during Gemini AI API call with retries: %s", e, exc_info=True
        )
        return None


def generate_summary(text: str, api_key: str) -> Optional[str]:
    """
    Generates the analytical summary using the Gemini AI API.

    Args:
        text (str): The text to be summarized.
        api_key (str): The API key for the Gemini AI service.

    Returns:
        Optional[str]: Generated summary or None if generation fails.
    """
    if not api_key or not api_key.strip():
        logging.error("API key is required for summary generation")
        return None

    try:
        client = get_client(api_key)
    except ValueError as e:
        logging.error("Failed to generate summary due to configuration error: %s", e)
        return None

    logging.info("Generating summary with AI model...")
    prompt_path = config.PROMPTS_DIR / "summary_prompt.md"

    try:
        if not prompt_path.exists():
            logging.error("Prompt file not found at: %s", prompt_path)
            return None

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        prompt = prompt_template.format(text=text)

        response = client.models.generate_content(
            model="models/gemini-2.5-pro", contents=prompt
        )

        if response and hasattr(response, "text"):
            logging.info("Summary generated successfully.")
            return response.text
        else:
            logging.warning(
                "AI response was empty or did not contain text. Details: %s", response
            )
            return None

    except Exception as e:
        logging.error("Error during Gemini AI API call: %s", e, exc_info=True)
        return None


async def generate_summary_with_retries(text: str, api_key: str) -> Optional[str]:
    """
    Generates the analytical summary using the Gemini AI API with retry protection.

    Args:
        text (str): The text to be summarized.
        api_key (str): The API key for the Gemini AI service.

    Returns:
        Optional[str]: Generated summary or None if generation fails.
    """
    if not api_key or not api_key.strip():
        logging.error("API key is required for summary generation")
        return None

    prompt_path = config.PROMPTS_DIR / "summary_prompt.md"

    try:
        if not prompt_path.exists():
            logging.error("Prompt file not found at: %s", prompt_path)
            return None

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        prompt = prompt_template.format(text=text)

        return await generate_content_with_retries(prompt, api_key)

    except Exception as e:
        logging.error("Error preparing summary generation: %s", e, exc_info=True)
        return None
