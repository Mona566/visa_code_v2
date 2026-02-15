# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python automation tool for filling Irish INIS (Irish Naturalisation and Immigration Service) online visa application forms. It uses a three-stage pipeline: PDF OCR → LLM field extraction → Selenium browser automation.

## Development Commands

### Running the Application
```bash
# 1. Convert PDF documents to Markdown via OCR
python pdf_to_markdown.py files/passport.pdf

# 2. Extract structured visa fields from Markdown using LLM
python llm_analysis.py

# 3. Launch automated form filling
python insert_browser.py
```

### Testing
```bash
# Run all tests
python tests/run_tests.py
python -m unittest discover tests -v

# Run a specific test module
python -m unittest tests.test_utils -v
python -m unittest tests.test_form_helpers -v
python -m unittest tests.test_page_detection -v

# Run a specific test class or method
python -m unittest tests.test_utils.TestUtils.test_setup_logging -v
```

### Dependencies
```bash
pip install -r requirements_pdf_ocr.txt
# Also required: selenium, langchain-openai, python-dotenv, pymupdf
```

## Architecture

### Three-Stage Pipeline

```
PDF Files → [pdf_to_markdown.py] → *.pdf.md → [llm_analysis.py] → JSON → [insert_browser.py + insert_function/] → INIS Form
```

1. **`pdf_to_markdown.py`** — Renders PDFs via pymupdf, sends images to Tencent Cloud OCR, returns Markdown. Falls back from Accurate OCR to Basic OCR on failure.

2. **`llm_analysis.py`** — Feeds Markdown to an OpenAI-compatible LLM (default: deepseek-v3) via LangChain. Parses structured JSON output across 17 visa field categories with auto-repair on JSON parse errors.

3. **`insert_browser.py`** — Entry point; calls `auto_fill_inis_form()` from `insert_function/main_flow.py` to drive Selenium.

### `insert_function/` Package Structure

| Module | Role |
|---|---|
| `main_flow.py` | Top-level orchestration (`auto_fill_inis_form`, `fill_application_form`) |
| `page_detection.py` | Detects current page state, handles errors/redirects/timeouts |
| `form_helpers.py` | Reusable helpers for dropdowns, radio buttons, text fields, dates |
| `page_fillers.py` | Dispatcher that routes to the correct `fill_page_N` module |
| `fill_page_1.py` – `fill_page_10.py` | Page-specific form-filling logic |
| `application_management.py` | Persists and retrieves application numbers across sessions |
| `utils.py` | Logging setup, configurable delays (`OPERATION_DELAY`, `POSTBACK_DELAY`, etc.) |

### Key Design Patterns

- **Page-per-module:** Each of the 10 INIS form pages has its own dedicated `fill_page_N.py`.
- **State persistence:** `application_management.py` saves application numbers so long-running sessions can resume.
- **Error resilience:** `page_detection.py` handles page redirects, error pages, and postback timing issues.
- **Mock-friendly tests:** The test suite uses `unittest.mock` to mock Selenium WebDriver, so tests run without a browser.

## Environment Variables (`.env`)

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | LLM API key |
| `OPENAI_API_BASE` | LLM API base URL (supports OpenAI-compatible endpoints) |
| `MODEL` | LLM model name (e.g., `deepseek-v3`) |
| `TENCENTCLOUD_SECRET_ID` | Tencent Cloud OCR credentials |
| `TENCENTCLOUD_SECRET_KEY` | Tencent Cloud OCR credentials |
