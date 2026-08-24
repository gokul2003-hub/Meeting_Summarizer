# 🎙️ Enterprise AI Meeting Intelligence & Summarization Suite

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.0+-61dafb?style=for-the-badge&logo=react&logoColor=black)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)
![Whisper](https://img.shields.io/badge/Whisper-Audio_AI-ff6f00?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

A production-grade, full-stack AI Meeting Intelligence platform that converts Zoom, Microsoft Teams, Google Meet recordings, audio files, or raw transcripts into executive briefs, key decisions, structured action items with assigned owners + due dates, follow-up email drafts, and exported reports (PDF, Markdown, JSON, Linear, Slack).

---

## 📌 Project Requirements & Technical Fulfillment

| Requirement Category | Scope & Objective | Implementation Status |
|---|---|---|
| **Input** | Meeting audio files (`.mp3`, `.wav`, `.m4a`, `.mp4`) & transcripts (`.vtt`, `.srt`, `.txt`, `.json`) | ✅ **100% Fulfilled** (Multi-format parser & automatic audio format handling) |
| **Output** | Text transcript + executive summary + key decisions + action items table | ✅ **100% Fulfilled** (Full speaker attribution, multi-style recaps, task tracking) |
| **ASR Integration** | Speech Recognition API integration (OpenAI Whisper) | ✅ **100% Fulfilled** (Cloud `whisper-1` API + local fast Whisper `tiny` engine) |
| **Backend & Storage** | Backend REST API to process & store data | ✅ **100% Fulfilled** (FastAPI + SQLAlchemy ORM with SQLite / PostgreSQL models) |
| **LLM Summarization** | LLM for summary & task generation (GPT-4o) | ✅ **100% Fulfilled** (Custom prompts + first-person regex fallback engine) |
| **Frontend UI** | Web interface to upload audio & view summaries | ✅ **100% Fulfilled** (Modern React 18 + Tailwind CSS dashboard UI) |

---

## ✨ Features

- 🌐 **Full-Stack Web Dashboard (`frontend/` & `backend/`)**: FastAPI REST backend with React (Vite + Tailwind CSS) UI, JWT auth, database persistence, real-time polling, and export controls.
- 💻 **Rich CLI Application (`cli/` & `main.py`)**: Standalone terminal application with color-coded tables, panels, and export engines.
- 📄 **Multi-Format Transcript Parser**: Native parsing for **WebVTT** (`.vtt`), **SubRip** (`.srt`), **Plain Text** (`.txt`), and **Otter JSON** (`.json`) with automatic speaker attribution.
- 🎙️ **Audio Transcription**: Local & cloud Whisper transcription for audio recordings (`.mp3`, `.wav`, `.m4a`, etc.).
- 🤖 **Hybrid AI + Deterministic Engine**: GPT-4o LLM summarization with offline first-person regex fallback ("I'll / I will" -> current speaker mapping).
- 📊 **Multi-Format Report Exporter**: Styled PDF (via HTML/Jinja2/WeasyPrint), Markdown, JSON, and direct issue creation in **Linear** or notifications in **Slack**.
- 🧪 **Precision Quality Evaluation Suite (`evals/`)**: Automated quality rubric test harness verifying section completeness and 100% action item recall.

---

## 🏗️ Project Architecture

```
meeting/
├── backend/                             # Unified FastAPI Backend
│   ├── alembic/                         # Database migrations
│   ├── database.py                      # SQLAlchemy ORM Session & Setup (SQLite / Postgres)
│   ├── models.py                        # Database Models (Users, Meetings, Transcripts, Summaries, Actions, Emails)
│   ├── schemas.py                       # Pydantic v2 validation schemas
│   ├── services/                        # Core Engine & Business Logic
│   │   ├── parser.py                    # Multi-format transcript parser (.vtt, .srt, .txt, .json)
│   │   ├── regex_extractor.py           # First-person speaker attribution & fallback regex engine
│   │   ├── ai_processing.py             # GPT-4o LLM summarizer & multi-style recap generator
│   │   ├── exporter.py                  # Styled PDF, Markdown, and JSON exporter
│   │   ├── linear.py                    # Linear issue sync service
│   │   ├── transcriber.py               # OpenAI Whisper audio transcriber (cloud + local)
│   │   ├── auth.py                      # JWT authentication & native bcrypt security
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

### Option 1: Running via CLI (Instant, No Setup Required)

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

#### 1. Configure Environment
```bash
cp .env.example .env
# Set OPENAI_API_KEY=sk-... in .env (Optional: SQLite fallback works offline)
```

#### 2. Start Backend
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```
*Backend runs at: `http://localhost:8000` (API docs at `http://localhost:8000/docs`)*

#### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
*Open browser at **`http://localhost:5173`**.*

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

## 🔌 API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | No | Register new user account |
| POST | `/api/auth/login` | No | Authenticate user & return JWT token |
| GET | `/api/auth/me` | Yes | Get current authenticated user info |
| POST | `/api/meetings/upload` | Yes | Upload audio or transcript file for processing |
| POST | `/api/meetings/upload-url` | Yes | Import and transcribe YouTube URL |
| GET | `/api/meetings/` | Yes | List user's processed meetings |
| GET | `/api/meetings/{id}` | Yes | Get detailed meeting info (transcript, summary, action items) |
| GET | `/api/meetings/{id}/export` | Yes | Export meeting report as PDF, Markdown, or JSON |
| POST | `/api/meetings/{id}/export/linear` | Yes | Sync extracted action items to Linear issues |
| POST | `/api/meetings/{id}/regenerate` | Yes | Re-run AI processing pipeline |
| PATCH | `/api/meetings/{id}/action-items/{item_id}` | Yes | Toggle action item completion status |
| POST | `/api/chat/query` | Yes | Ask questions across meeting transcripts (RAG) |

---

## 🧠 LLM Prompts & Engineering

The platform uses structured JSON prompts for OpenAI GPT-4o:

- **Summarization Prompt**:
  > *"Summarize this meeting transcript into executive summary, key decisions, key discussion points, and open questions."*
- **Action Extraction Prompt**:
  > *"Extract all action items from the transcript, identifying task description, assignee, due date, and priority level."*
- **Follow-up Email Prompt**:
  > *"Draft a professional follow-up email summarizing the meeting decisions and next steps with assigned task owners."*

---

## 🧪 Benchmark Evaluation & Tests

Run the precision/recall evaluation harness and unit tests:

```bash
# 1. Run Unit Tests
pytest tests/ -v

# 2. Run Benchmark Evaluation Suite
python evals/run.py
```

Expected Benchmark Output:
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

Licensed under the [MIT License](LICENSE).
