# 🤝 Contributing to CartaOS

First off — thanks for your interest in contributing to **CartaOS**! 🚀  
We welcome developers, researchers, designers, and documentation writers.

---

## 📋 How to Contribute

### 1. Fork & Clone
```bash
git fork https://github.com/CartaOS/CartaOS.git
cd CartaOS
````

### 2. Install Dev Environment

```bash
python3 -m backend.cartaos.install_dev_env
```

### 3. Create a Feature Branch

```bash
git checkout -b feat/my-feature
```

### 4. Commit with Conventional Commits

```
feat: add OCR post-processing
fix: correct Tesseract language setting
docs: update README installation steps
```

### 5. Push and Open a PR

```bash
git push origin feat/my-feature
```

---

## 🧪 Testing and the TDD Approach

To ensure code quality and maintainability, CartaOS strongly encourages the adoption of **TDD (Test-Driven Development)**.

The expected development cycle is **Red-Green-Refactor**:

1.  **🔴 Red:** Write a failing test for the desired functionality.
2.  **🟢 Green:** Write the simplest possible code to make the test pass.
3.  **🔵 Refactor:** Refactor the implementation code, keeping the test green.

Before committing your code, always run the full test suite to ensure nothing has been broken:

```bash
pytest
```

Adopting TDD not only improves quality but also serves as living documentation and protects against future regressions.

---

## 📜 Branch Policy

* `main` → stable, production-ready code.
* `dev` → active development.

---

## 📢 Communication

Join discussions on [GitHub Issues](https://github.com/CartaOS/CartaOS/issues).