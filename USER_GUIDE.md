# CartaOS User Guide

Welcome to CartaOS! This guide will walk you through the essential features and workflows to help you get the most out of the application.

---

## 1. Core Concept: The Document Pipeline

CartaOS is built around a powerful multi-stage pipeline designed to transform raw document files into a structured, searchable knowledge base. Each document you add moves through a series of folders, with a specific process applied at each stage.

Here is the flow:

1.  **`00_Inbox`**: The starting point. Place all your new PDF, JPG, or PNG files here.
2.  **`01_Library`**: The central, managed library where CartaOS stores and organizes your original documents.
3.  **`02_Triage`**: Documents are analyzed here. Based on their content and format, they are routed to the appropriate next step.
4.  **`04_ReadyForOCR`**: Scanned documents or images with text land here, waiting to be processed by the Optical Character Recognition (OCR) engine.
5.  **`05_ReadyForSummary`**: Documents with extracted text are moved here, ready for the AI to generate a concise summary.
6.  **`07_Processed`**: The final destination. Here you will find your original document, a `.txt` file with the raw text, and a `.md` file containing the AI-generated summary.

---

## 2. Getting Started: Processing Your First Document

Let's walk through processing a single document from start to finish.

### Step 1: Add a Document

-   Find the `00_Inbox` folder in your CartaOS directory.
-   Copy or move your PDF or image file into this folder.

### Step 2: Run the Pipeline

-   Open your terminal or command prompt.
-   Navigate to the CartaOS project directory.
-   Run the main processing command:

    ```bash
    cartaos process
    ```

This command starts the pipeline. It will automatically:
- Move the file from the Inbox to the Library.
- Triage the document.
- Perform OCR if necessary.
- Generate an AI summary.

### Step 3: Find Your Output

-   Once the process is complete, navigate to the `07_Processed` folder.
-   Inside, you will find a new folder named after your original document.
-   This folder contains:
    -   A copy of the original file.
    -   A `_raw_text.txt` file with the full text extracted from the document.
    -   A `_summary.md` file with the AI-generated summary.

---

## 3. Use Case Walkthroughs

### For the Academic Researcher

**Goal:** Quickly analyze a dozen new research papers for relevance.

1.  **Batch Ingest:** Drop all 12 PDF papers into the `00_Inbox` folder.
2.  **Run Processing:** Execute `cartaos process`.
3.  **Review Summaries:** Instead of opening each 30-page paper, go to the `07_Processed` directory and read the `_summary.md` file for each paper. This allows you to quickly grasp the key findings and decide which papers require a full read-through.

### For the Investigative Journalist

**Goal:** Process a large leak of 500 scanned pages to find key information.

1.  **Secure Ingest:** Place all scanned JPG or PNG files into the `00_Inbox`.
2.  **Run Full Pipeline:** Execute `cartaos process`.
3.  **Search the Text:** Once processing is complete, you have a fully searchable text archive. Use your favorite command-line tools (like `grep` or `rg`) to search the `_raw_text.txt` files within the `07_Processed` directory for names, locations, or keywords relevant to your investigation.

### For the Archivist

**Goal:** Digitize and preserve a collection of historical, typewritten letters.

1.  **Scan & Ingest:** Scan each letter as a high-resolution PNG file and place them in the `00_Inbox`.
2.  **Run OCR & Archive:** Execute `cartaos process`.
3.  **Verify & Store:** The `07_Processed` folder now acts as your digital archive. You have the original scan, a searchable plain-text version, and a summary for cataloging. This makes the collection accessible to researchers without handling the fragile originals.

---

For any issues, please consult the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide.
