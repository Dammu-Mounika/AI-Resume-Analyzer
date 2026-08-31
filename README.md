# AI Resume Analyzer & Job Matcher

> Phase 3 complete — job description input UI and resume upload form are working.

## Quick Start

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

From the project root:

```bash
uvicorn backend.main:app --reload
```

### 4. Open the web UI

- **App UI:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **API health (JSON):** `curl http://127.0.0.1:8000/` or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Phase 3: Test the Input Form

1. Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
2. Upload a PDF resume (drag & drop or browse)
3. Paste a job description — or click **Load sample job description**
4. Click **Analyze Resume**
5. Confirm the **Extraction Preview** shows page count, character count, and resume text

### What to verify

| Action | Expected result |
|--------|-----------------|
| Submit without resume | "Please upload your resume PDF." |
| Submit with short job text | "Job description is too short..." |
| Upload non-PDF file | "Only PDF files are accepted." |
| Valid PDF + job description | Loading spinner, then extraction preview |
| Backend not running | Connection error message |

## Run Tests

```bash
pytest tests/ -v
```

Full documentation will be added in Phase 17.
