# 🏗 CartaOS Architecture

This document provides a detailed overview of the CartaOS technical architecture, components, and data flow.

---

## 1. Guiding Principles

- **Modularity:** Each part of the pipeline (triage, OCR, summarization) is a distinct module that can be maintained and improved independently.
- **Simplicity:** The system relies on a simple, folder-based pipeline, making it easy to understand, debug, and extend.
- **Extensibility:** The architecture is designed to allow for new processing steps or different AI models to be integrated in the future.

---

## 2. High-Level Overview

CartaOS is a modern desktop application built on the Tauri framework. It combines a web-based frontend (Svelte) with a powerful Python backend, all packaged into a single native executable for Windows, macOS, and Linux.

The project is structured as a **monorepo** to manage the different parts of the application in a single repository.

---

## 3. Core Components

### 3.1. Frontend (`./frontend`)

The user interface is a modern web application responsible for displaying the state of the document library and allowing user interaction.

- **Framework:** **Svelte with TypeScript** provides a fast, reactive, and type-safe user interface.
- **Build Tool:** **Vite** enables a fast and modern development experience.
- **Styling:** **Tailwind CSS** is used for a utility-first approach to styling, allowing for rapid and consistent UI development.
- **Testing:** **Vitest** is used for unit tests, and **Playwright** for end-to-end testing.

### 3.2. Processing Backend (`./backend`)

The backend contains all the business logic for the document processing pipeline. It can be run as a standalone CLI or as a server for the GUI.

- **Language:** **Python** (3.12+)
- **Dependency Management:** **Poetry** is used for managing project dependencies and virtual environments.
- **Core Logic:**
    - `triage.py`: Analyzes new documents and routes them to the correct processing stage.
    - `ocr.py`: Uses **Tesseract** and **PyMuPDF** to perform Optical Character Recognition on scanned documents and images.
    - `processor.py`: Communicates with the **Google Gemini API** to generate summaries of the document text.
- **API & CLI:**
    - **FastAPI** provides an HTTP server to communicate with the frontend.
    - **Typer** provides a powerful and user-friendly command-line interface.
- **Quality:**
    - **Ruff** is used for high-performance linting.
    - **MyPy** is used for static type checking.
    - **Pytest** is used for unit and integration testing.

### 3.3. Desktop Core (`./src-tauri`)

The core of the desktop application, which binds the web frontend to the operating system.

- **Framework:** **Tauri** is a toolkit for building lightweight, secure, and cross-platform desktop applications using web technologies.
- **Language:** **Rust** is used for the core backend logic, providing performance, safety, and system-level integration.
- **Responsibilities:**
    - Manages the application window and lifecycle.
    - Provides a secure bridge for communication between the Svelte frontend and the Python backend.
    - Handles native system interactions like file dialogs and notifications.

### 3.4. Development Environment Installer (`./backend/cartaos/install_dev_env`)

To ensure a consistent and reliable setup for developers, CartaOS includes a dedicated installer script.

- **Responsibility:** The installer's primary role is to **check for required system dependencies** (like Python, Node.js, Poetry, and Tesseract) and provide clear installation instructions if they are missing.
- **Functionality:** It does **not** attempt to install system-level packages. Its main action is to set up the project-local environments by running `npm ci` for the frontend and `poetry install` for the backend.

---

## 4. Data Flow

The application uses a folder-based pipeline to process documents. This makes the state of the system transparent and easy to inspect.

```
[Input Files] -> [00_Inbox] -> [CLI/GUI Action] -> [01_Library] -> [02_Triage] -> [04_ReadyForOCR] -> [05_ReadyForSummary] -> [07_Processed]
```
- **`00_Inbox`**: User drops new files here.
- **`01_Library`**: Originals are stored and managed.
- **`02_Triage`**: Files are analyzed.
- **`04_ReadyForOCR`**: Scans and images wait for text extraction.
- **`05_ReadyForSummary`**: Text-ready files wait for AI summarization.
- **`07_Processed`**: Final outputs (original, `.txt`, `_summary.md`) are stored here.
