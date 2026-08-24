# 🎙️ Enterprise AI Meeting Intelligence & Summarization Suite

A production-ready, full-stack AI Meeting Intelligence platform that converts Zoom, Microsoft Teams, Google Meet recordings, audio files, or raw transcripts into executive recaps, structured action items with assigned owners, follow-up email drafts, and exported reports (PDF, Markdown, JSON, Linear, Slack).

---

## ✨ Unified Platform Highlights

This consolidated project combines three specialized meeting intelligence tools into a single repository:

- 🌐 **Full-Stack Web Dashboard (`frontend/` & `backend/`)**: FastAPI REST backend with React (Vite + TailwindCSS) UI, JWT auth, database persistence, and real-time processing status polling.
- 💻 **Rich CLI Application (`cli/` & `main.py`)**: Standalone terminal application with color-coded tables, panels, and export engines.
- 📄 **Multi-Format Transcript Parser**: Native parsing for **WebVTT** (`.vtt`), **SubRip** (`.srt`), **Plain Text** (`.txt`), and **Otter JSON** (`.json`) formats with automatic speaker attribution.
- 🎙️ **Audio Transcription**: Local & cloud Whisper transcription for audio recordings (`.mp3`, `.wav`, `.m4a`, etc.).
- 🤖 **Hybrid AI + Deterministic Engine**: GPT-4o LLM summarization with offline first-person regex fallback ("I'll / I will" -> current speaker mapping).
- 📊 **Multi-Format Report Exporter**: PDF (via WeasyPrint/HTML templates), Markdown, JSON, and direct issue creation in **Linear** or notifications in **Slack**.
- 🧪 **Precision Quality Evaluation Suite (`evals/`)**: Automated quality rubric test harness verifying section completeness and 100% action item recall.

---

## 🏗️ Project Architecture

```
meeting/
├── backend/                             # Unified FastAPI Backend
│   ├── alembic/                         # DB migrations
│   ├── database.py                      # SQLAlchemy ORM Session & Setup
│   ├── models.py                        # Database Models (Users, Meetings, Transcripts, Summaries, Actions, Emails)
│   ├── schemas.py                       # Pydantic v2 validation schemas
│   ├── services/                        # Core Engine & Business Logic
│   │   ├── parser.py                    # Multi-format transcript parser (.vtt, .srt, .txt, .json)
│   │   ├── regex_extractor.py           # First-person speaker attribution & fallback regex engine
│   │   ├── ai_processing.py             # GPT-4o LLM summarizer & multi-style recap generator
│   │   ├── exporter.py                  # Styled PDF, Markdown, and JSON exporter
│   │   ├── linear.py                    # Linear issue sync service
│   │   ├── transcriber.py               # OpenAI Whisper audio transcriber
│   │   ├── auth.py                      # JWT authentication & security
│   │   ├── slack.py                     # Slack webhook integration
│   │   └── rag.py                       # Vector search & transcript QA
│   ├── routers/                         # FastAPI Routers (/api/meetings, /api/auth, /api/chat, etc.)
│   └── templates/                       # HTML/Jinja2 templates for PDF reports
├── frontend/                            # React + Vite + Tailwind UI
│   ├── src/
│   │   ├── api/client.js                # Axios client & API hooks
│   │   ├── components/                  # UploadZone, SummaryPanel, ActionItemsList, ExportModal, etc.
│   │   ├── pages/                       # Dashboard, Login, Register, MeetingPage, Settings
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── cli/                                 # Rich Terminal Application
│   ├── cli.py                           # CLI implementation
│   └── main.py                          # CLI runner
├── evals/                               # Quality Evaluation Suite
│   ├── run.py                           # Benchmark runner
│   ├── action-items.json
│   └── recap-quality.json
├── fixtures/                            # Sample Transcripts (.txt, .vtt, .srt, .json)
├── tests/                               # Pytest unit tests
├── main.py                              # Root CLI entry point
├── docker-compose.yml                   # Docker orchestration (Postgres + FastAPI + React)
├── pyproject.toml                       # Python package configuration
└── requirements.txt                     # Dependencies
```

---

## 🚀 Quickstart Guide

### Option 1: Running via CLI (Instant, No Database Required)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run CLI on sample transcript fixture
python main.py --input fixtures/01-product-sync.txt --format all --style concise
```

Command-Line Options:
| Flag | Description | Values | Default |
|---|---|---|---|
| `-i, --input` | Path to transcript or audio file | `.vtt, .srt, .txt, .json, .mp3, .wav` | *required* |
| `-o, --output` | Output directory for reports | Filepath | `./output` |
| `-f, --format` | Export format | `markdown`, `json`, `pdf`, `all` | `markdown` |
| `-s, --style` | Summary style | `concise`, `detailed`, `executive`, `four_section` | `concise` |

---

### Option 2: Running Web Application (FastAPI + React)

#### 1. Setup Environment
```bash
cp .env.example .env
# Set OPENAI_API_KEY=sk-... in .env (Optional: SQLite fallback works offline)
```

#### 2. Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt

alembic upgrade head
uvicorn main:app --reload --port 8000
```

#### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173 in browser
```

---

### Option 3: Containerized Run (Docker Compose)

```bash
docker compose up --build
```
This launches:
- **PostgreSQL Database** on `localhost:5432`
- **FastAPI Backend** on `localhost:8000`
- **React Frontend Dashboard** on `http://localhost:3000`

---

## 🧪 Benchmark Evaluation Suite

Run the quality & recall evaluation harness across bundled fixtures:

```bash
python evals/run.py
```

Expected Output:
```
=== Recap-quality eval (5 cases) ===
  PASS  product-sync-has-all-sections
  PASS  product-sync-mentions-dashboard-decision
  PASS  zoom-recording-mentions-mfa-or-conditional-access
  PASS  customer-call-has-action-item-section
  PASS  otter-standup-mentions-deploy-or-migration

=== Action-item eval (4 cases) ===
  PASS  product-sync-extracts-five-items                    all 5 expected items found
  PASS  zoom-recording-davids-actions                       all 2 expected items found
  PASS  customer-call-account-manager-actions               all 1 expected items found
  PASS  otter-standup-diego-actions                         all 2 expected items found

  Overall action-item recall: 10/10 (100%)

Overall: recap-quality OK, action-items OK
```

---

## 📄 License

MIT License.
