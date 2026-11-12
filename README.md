# Lending Automation POC

Automated loan underwriting pipeline: OCR extraction from application forms and verification documents (paystubs), discrepancy analysis via a local LLM (Ollama), and an Angular UI for uploads and report display. Includes Behave BDD UI tests.

## Architecture

```
Angular UI (4200) ──► Spring Boot API (8081) ──► OCR Server (8000, PaddleOCR)
                            │
                            └──► Ollama LLM (11434) — discrepancy analysis → JSON report
```

- **`src/main/java`** — Spring Boot backend: `UnderwritingController` → `LoanUnderwritingEngine` → `OcrService` (HTTP) + `LlmService` (Ollama)
- **`ocr_server.py`** — FastAPI + PaddleOCR service (`/extract-text`, `/health`); auto-detects CUDA GPU
- **`lending-ui/`** — Angular standalone app (signals, zoneless)
- **`features/`** — Behave BDD tests with Selenium
- **`generate_mock_docs.py`** — generates mock application/paystub images for test scenarios

## Prerequisites

- Java 21+, Maven (or use `./mvnw`)
- Python 3.11+ with a virtualenv
- Node.js 20+ (for Angular UI)
- [Ollama](https://ollama.com) with an instruction model, e.g. `mistral` or `qwen2.5:7b`
- Optional: NVIDIA GPU + CUDA for fast OCR/LLM inference

## Setup

### 1. Python OCR server

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]" paddleocr paddlepaddle pillow numpy
```

For GPU OCR (recommended):

```powershell
pip uninstall -y paddlepaddle
pip install paddlepaddle-gpu==3.2.2 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
```

### 2. Ollama model

```powershell
ollama pull mistral
```

Avoid reasoning models (e.g. `deepseek-r1`) — they break the strict JSON output schema.

### 3. Angular UI

```powershell
cd lending-ui
npm install
```

## Running

Start all three services (order doesn't matter):

```powershell
# Terminal 1 — OCR server (GPU auto-detected on first request)
.\venv\Scripts\python.exe ocr_server.py        # http://127.0.0.1:8000

# Terminal 2 — Spring Boot backend
.\mvnw.cmd spring-boot:run                    # http://localhost:8081

# Terminal 3 — Angular UI
cd lending-ui; npm start                      # http://localhost:4200
```

Open http://localhost:4200, upload a loan application image and a verification document, click **Run Underwriting**.

## Configuration (`src/main/resources/application.yml`)

| Key | Default | Description |
|---|---|---|
| `ocr.provider` | `http` | `http` (OCR server) or `paddle` (shells out to Python) |
| `ocr.server-url` | `http://127.0.0.1:8000` | OCR server base URL |
| `slm.endpoint` | `http://localhost:11434/api/generate` | Ollama generate endpoint |
| `slm.model` | `mistral:latest` | Model name |
| `slm.prompts.*` | — | System/user prompt templates defining the JSON report schema |
| `cors.allowed-origins` | env `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins |

## Validations performed

The LLM compares the application form against the verification document and reports:

- **Applicant name** — MATCHED / MISMATCH
- **Employer** — MATCHED / MISMATCH
- **Income** — stated vs verified monthly income + variance %
- **Address** — MATCHED / MISMATCH
- **SSN last-4** — MATCHED / MISMATCH
- **Loan affordability** — requested loan vs verified income (max 5.0x LTI ratio)

Output: `APPROVE` / `REJECT` / `HOLD` plus a discrepancy list with severity (`CRITICAL` / `WARNING`).

## Observability

- **Correlation IDs** — UI generates `X-Request-Id` per request; propagated through Spring Boot (SLF4J MDC, shown in every log line), the OCR server, and Ollama headers
- **Structured timing logs** — per-step durations in engine, OCR client, SLM client, and OCR server
- **UI** — live elapsed timer during processing, final duration on the report, request/response details in browser console

## Mock documents & tests

```powershell
# Regenerate mock docs (clean, mismatch, address/SSN/affordability scenarios)
.\venv\Scripts\python.exe generate_mock_docs.py

# Run Behave UI tests (requires all services running)
.\venv\Scripts\behave.exe features/
```

Reports land in `reports/behave_report.html`.

## Project structure

```
├── ocr_server.py               # FastAPI + PaddleOCR service
├── generate_mock_docs.py       # Mock document generator
├── features/                   # Behave BDD tests
│   ├── underwriting.feature
│   ├── environment.py
│   └── steps/underwriting_steps.py
├── lending-ui/                 # Angular frontend
└── src/main/
    ├── java/com/lending/poc/
    │   ├── controller/         # REST endpoints
    │   ├── engine/             # Underwriting pipeline orchestration
    │   ├── service/impl/       # HttpOcrService, LocalSlmService, PaddleOcrService
    │   ├── model/              # Report records
    │   └── config/             # CORS, RequestIdFilter
    └── resources/
        ├── application.yml
        └── *.png               # Generated mock documents
```
