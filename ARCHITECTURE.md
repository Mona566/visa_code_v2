# ARCHITECTURE.md

High-level design documentation for the Irish INIS Visa Application Auto-Filler.

---

## System Overview

The system automates end-to-end filling of the Irish INIS online visa application form. It is composed of three loosely coupled stages that run in sequence:

```
PDF Documents
    │
    ▼
[pdf_to_markdown.py]  ──  Tencent Cloud OCR
    │
    ▼  Markdown text
[llm_analysis.py]  ──  OpenAI-compatible LLM
    │
    ▼  Structured JSON (17 field categories)
[insert_browser.py]
[insert_function/]  ──  Selenium Chrome
    │
    ▼
INIS Online Form (pages 1–10)
```

Each stage is independently runnable. The `insert_function/` package consumes the JSON produced by `llm_analysis.py` and drives the browser.

---

## Stage 1 — PDF to Markdown (`pdf_to_markdown.py`)

- Renders each PDF page to JPEG using **PyMuPDF** at a configurable DPI (default 150).
- Sends the JPEG as base64 to **Tencent Cloud OCR** (`GeneralAccurateOCR`, with auto-fallback to `GeneralBasicOCR` on failure).
- If the base64 payload exceeds 7 MB, DPI and JPEG quality are progressively reduced before retrying.
- Returns a single Markdown string with `<!-- Page N -->` delimiters between pages.

---

## Stage 2 — Field Extraction (`llm_analysis.py`)

- Sends the Markdown to an **OpenAI-compatible LLM** (configured via `MODEL` and `OPENAI_API_BASE`) using LangChain.
- The prompt instructs the model to return a single JSON object with **17 top-level keys**, one per field category (Application Info, Personal Info, Passport, Employment, Family, Financial Support, etc.). All missing values are `null`.
- On JSON parse failure: tries regex extraction, then asks the LLM to repair the malformed JSON.
- All dates are normalized to `YYYY-MM-DD`.

---

## Stage 3 — Browser Automation (`insert_function/`)

This package contains all Selenium automation logic, split by responsibility.

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `main_flow.py` | Top-level orchestration; page loop (pages 1–10) |
| `page_detection.py` | Detect which page is currently shown; error recovery |
| `form_helpers.py` | Low-level field interaction (text, dropdown, radio, date) |
| `page_fillers.py` | Thin dispatcher that re-exports `fill_page_1` … `fill_page_10` |
| `fill_page_1.py` – `fill_page_10.py` | Page-specific field mapping logic |
| `application_management.py` | Save/retrieve application numbers; resume interrupted sessions |
| `utils.py` | Logging, delay constants, PostBack helper, page-state verifier |

### Main Flow (`main_flow.py`)

`auto_fill_inis_form()` is the single public entry point:

1. Opens Chrome (`detach=True` — browser stays open after the script exits).
2. Navigates to the INIS homepage and checks for an immediate error page.
3. If a saved application number exists (`application_number.txt`), calls `retrieve_application()` to resume it; otherwise starts a new application.
4. Calls `fill_application_form()`, which loops through pages 1–10, calling the appropriate `fill_page_N()` then clicking **Next**, re-detecting the resulting page, and handling any errors or redirects at each step.

### Page Detection (`page_detection.py`)

Page identity is determined without refreshing (a refresh can lose ASP.NET form state). Each page is identified by a unique DOM element ID present only on that page (e.g., page 1: `ctl00_ContentPlaceHolder1_ddlCountryOfNationality`; page 2: `ctl00_ContentPlaceHolder1_txtSurname`). For more ambiguous pages (3, 6, etc.) the page source text is scanned for unique strings.

Error detection uses a multi-strategy approach:
- URL pattern checks (`ApplicationError.aspx`, `Error.aspx`)
- Page source keyword scan ("error has occured", "Please try again")
- DOM element search (`MainHeadersText` class)

Recovery: auto-refresh up to 50 times. After 5 consecutive failures the browser navigates to the homepage. If a homepage redirect is detected at any point, `retrieve_application()` is called using the saved application number.

### Form Helpers (`form_helpers.py`)

Four primary helpers, each implementing a multi-strategy fallback chain so that minor label-wording differences in the live form do not cause hard failures:

- **`fill_text_by_label`** — Finds the `<input>` associated with a label via `for` attribute, sibling traversal, or table-row context.
- **`fill_dropdown_by_label`** — Locates the `<select>`, tries to select by visible text → value → partial match.
- **`select_radio_by_label`** — Groups radio buttons by `name`; selects by proximity if multiple groups match; clicks via standard Selenium, then JS click, then direct `checked` + `onchange()` as fallbacks.
- **`fill_date_by_label`** — Distinguishes Issue vs. Expiry date fields by label keyword and position.

**PostBack handling**: ASP.NET PostBack causes a full-page DOM replacement. After any dropdown or button interaction that has an `onchange`/`onclick` handler, the helpers wait for `document.readyState === "complete"` and re-locate elements rather than holding stale references.

### Timing (`utils.py`)

```
OPERATION_DELAY      = 1.5 s   # between normal field fills
POSTBACK_DELAY       = 2.0 s   # pause before triggering a PostBack
POSTBACK_WAIT_DELAY  = 3.0 s   # pause after PostBack resolves
POSTBACK_BETWEEN_DELAY = 2.5 s # between consecutive PostBack operations
```

`safe_postback_operation()` wraps any PostBack-triggering call: verifies pre-state, waits for ready, verifies post-state, and returns `bool`.

### Session Persistence (`application_management.py`)

On successful page 10 submission, the application number is written to `application_number.txt`. On the next run, `auto_fill_inis_form()` reads this file and calls `retrieve_application()` — which fills the retrieval form (application number, passport number, country, date of birth) and re-enters the in-progress application at whatever page the server returns.

---

## Target URLs

| Purpose | URL |
|---|---|
| Start / Homepage | `https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx` |
| Intermediate page | `https://www.visas.inis.gov.ie/AVATS/OnlineHome2.aspx` |
| Form entry | `https://www.visas.inis.gov.ie/AVATS/VisaTypeDetails.aspx` |

---

## Error Recovery Summary

```
Error detected on any page
    │
    ├─ Auto-refresh (up to 50×, 6-second intervals)
    │       └─ Resolved → continue filling
    │
    ├─ 5+ failures → navigate to homepage
    │
    └─ Homepage detected at any time
            ├─ Saved app number exists → retrieve_application()
            └─ No saved number → restart_from_homepage() (new application)
```

---

## Key Design Decisions

- **No hard failures in form helpers.** If a field cannot be filled, it is logged and skipped; the next field is attempted. This prevents one unrecognized label from aborting the entire run.
- **No stale element references.** Elements are re-located after every PostBack rather than cached.
- **Browser stays visible and open.** Allows human inspection and manual correction if automation stalls.
- **LLM model is configurable.** `OPENAI_API_BASE` supports any OpenAI-compatible endpoint (the default uses deepseek-v3 via a third-party gateway).
