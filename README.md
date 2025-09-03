# 📚 CartaOS — [C]uration, [A]nalysis, and [R]efinement of [T]exts for [A]cademia ([O]pen [S]ource)

> *Free your documents. Free your mind.*

---

![CartaOS Banner](docs/assets/banner.png) <!-- Optional header image -->

<p align="center">
  <a href="https://github.com/CartaOS/CartaOS/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/CartaOS/CartaOS/frontend-tests.yml?branch=main&label=Frontend%20Tests&logo=github&style=for-the-badge" alt="Frontend Tests">
  </a>
  <a href="https://github.com/CartaOS/CartaOS/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/CartaOS/CartaOS/backend-ci.yml?branch=main&label=Backend%20CI&logo=github&style=for-the-badge" alt="Backend CI">
  </a>
  <a href="https://github.com/CartaOS/CartaOS/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/CartaOS/CartaOS/rust-ci.yml?branch=main&label=Rust%20CI&logo=github&style=for-the-badge" alt="Rust CI">
  </a>
  <a href="https://github.com/CartaOS/CartaOS/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/CartaOS/CartaOS?style=for-the-badge&logo=open-source-initiative&logoColor=white" alt="License">
  </a>
  <img src="https://img.shields.io/github/languages/top/CartaOS/CartaOS?style=for-the-badge&color=blue&logo=python" alt="Top Language">
  <img src="https://img.shields.io/github/v/release/CartaOS/CartaOS?style=for-the-badge&color=brightgreen&logo=semver" alt="Version">
  <img src="https://img.shields.io/github/contributors/CartaOS/CartaOS?style=for-the-badge&color=orange&logo=github" alt="Contributors">
</p>

---

## 🌍 Overview

**CartaOS** is an open-source system for **C**uration, **A**nalysis, and **R**efinement of **T**exts for **A**cademia (**O**pen **S**ource).  
It helps researchers, educators, activists, and other knowledge workers transform raw collections of digital documents (PDFs, e-books, images) into an **organized, searchable knowledge base** enriched with AI-powered insights.

---

## 🛠 How It Works — Workflow

The system follows a **multi-stage pipeline**, where documents move through structured directories as they are processed:

1. 📥 **Inbox (`00_Inbox`) / Triage (`02_Triage`)** — Drop files here. The `triage.py` module classifies them into ready-to-analyze or needing correction.  
2. 🧪 **Correction Lab (`03_Lab`)** — Manual corrections for poor scans using tools like ScanTailor Advanced.  
3. 🖹 **Ready for OCR (`04_ReadyForOCR`)** — Cleaned files awaiting OCR.  
4. 📝 **Ready for Summary (`05_ReadyForSummary`)** — High-quality text files awaiting AI analysis.  
5. 📦 **Processed (`07_Processed`)** — Final PDFs and `.md` summaries stored here.

---

## ✨ Features

- 📂 **Document Ingestion** — Automatically process PDFs, EPUBs, and image-based docs.  
- 🤖 **AI Analysis** — Summaries, key concepts, and tags via LLMs (Google Gemini, OpenAI, etc.).  
- 🖹 **OCR & Image Processing** — High-quality text extraction with Tesseract, PyMuPDF, pdfplumber.  
- 🧼 **Pre-processing & Refinement** — Deskewing, cleaning, and splitting for optimal results.  
- 🖥 **Dual Interface** — Python/Typer CLI + Tauri/Svelte/Tailwind GUI.  
- 🔌 **Knowledge Tools Integration** — Planned Zotero & Obsidian support.  
- 🧩 **Plugin Architecture** — Extend with custom modules.

---

## ⚙ Tech Stack

- 🐍 **Python** — Core logic, automation, Typer CLI.  
- 🖥 **Tauri + Svelte + Tailwind** — Modern, lightweight desktop GUI.  
- 🦀 **Rust** — High-performance modules.  
- 📜 **AGPLv3** — Free software, open for everyone.

---

## 📂 Directory Structure

```yaml
📦 CartaOS
 ┣ 📂 backend                               # 🖥 Backend core logic
 ┃ ┗ 📂 cartaos
 ┃    ┣ 📜 __init__.py                      # 📄 Package init
 ┃    ┣ 📜 triage.py                        # 📄 File triage module
 ┃    ┣ 📜 lab.py                           # 📄 Correction lab helper
 ┃    ┣ 📜 processor.py                     # 📄 AI summary processor
 ┃    ┗ 📜 install_dev_env                  # ⚙ Cross-platform installer
 ┣ 📂 frontend                              # 🎨 GUI frontend
 ┃ ┗ 📂 src
 ┃    ┗ 📂 components                       # 🧩 UI Components
 ┣ 📂 data                                  # 📁 Main document storage
 ┃ ┣ 📂 00_Inbox                            # 📥 Incoming files
 ┃ ┣ 📂 02_Triage                           # 🗂 Pre-analysis sorting
 ┃ ┣ 📂 03_Lab                              # 🧪 Manual corrections
 ┃ ┣ 📂 04_ReadyForOCR                      # 🖹 OCR queue
 ┃ ┣ 📂 05_ReadyForSummary                  # 📝 Summary queue
 ┃ ┗ 📂 07_Processed                        # 📦 Completed docs
 ┣ 📂 docs                                  # 📚 Documentation
 ┃ ┗ 📂 assets                              # 🖼 Images, banners
 ┣ 📜 README.md
 ┗ 📜 LICENSE
````

---

## 🚀 Installation

### Quick Start (Recommended)

Download the latest release for your platform:

#### Linux
```bash
# Debian/Ubuntu (.deb package)
wget https://github.com/CartaOS/CartaOS/releases/latest/download/CartaOS_0.1.0_amd64.deb
sudo dpkg -i CartaOS_0.1.0_amd64.deb

# Fedora/RHEL (.rpm package)
wget https://github.com/CartaOS/CartaOS/releases/latest/download/CartaOS-0.1.0-1.x86_64.rpm
sudo dnf install CartaOS-0.1.0-1.x86_64.rpm

# Universal (.AppImage)
wget https://github.com/CartaOS/CartaOS/releases/latest/download/CartaOS_0.1.0_amd64.AppImage
chmod +x CartaOS_0.1.0_amd64.AppImage
./CartaOS_0.1.0_amd64.AppImage
```

#### Windows & macOS
*Coming soon - installers in development*

### Development Setup

For developers who want to build from source:

```bash
git clone https://github.com/CartaOS/CartaOS.git
cd CartaOS
python3 -m backend.cartaos.install_dev_env
```

This installer:
* Detects your OS and package manager
* Installs dependencies (Tesseract, unpaper, poppler-utils, etc.)
* Sets up Rust, Node.js, Poetry, and Tauri CLI

### System Requirements

- **OS**: Linux (Windows/macOS support coming soon)
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 100MB for app + space for document processing
- **Network**: Internet connection for AI features

---

## 📸 Screenshots

### Main Interface
![CartaOS Main Interface](docs/assets/main-interface.png)
*The main CartaOS interface showing the Pipeline view with document queue management and processing controls.*

### Key Features

| Feature | Screenshot | Description |
|---------|------------|-------------|
| **Pipeline Management** | ![Pipeline View](docs/assets/pipeline-view.png) | Document queue with triage, OCR, and summarization controls |
| **Settings Configuration** | ![Settings View](docs/assets/settings-view.png) | API key and vault path configuration with validation |
| **Lab Workspace** | ![Lab View](docs/assets/lab-view.png) | Document analysis and manual correction workspace |
| **Summaries Display** | ![Summaries View](docs/assets/summaries-view.png) | AI-generated document summaries and insights |

### Processing Workflow
![Processing Workflow](docs/assets/workflow-diagram.png)
*Visual representation of the document processing pipeline from inbox to final processed documents.*

---

## 🤝 Contributing

We welcome pull requests and discussions in the [GitHub Issues](https://github.com/CartaOS/CartaOS/issues).
Follow our [Contributing Guide](CONTRIBUTING.md) for setup, coding standards, and testing.

---

## 📜 License

Licensed under **AGPLv3** — see the [LICENSE](LICENSE) file.
