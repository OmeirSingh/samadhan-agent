# Samadhan-Agent — Project Documentation

**AI First Hackathon · Summer School '26 · I3C – IIT Jammu × Techible**
**Track:** AI for Bharat — Governance & Social Impact
**Team:** Minchu Badmosh — Mishika Mittal · Xena Bandhu · Omeir Singh

- **Live prototype:** https://samadhan-agent.onrender.com
- **Source code:** https://github.com/OmeirSingh/samadhan-agent
- **Tagline:** *Turning public grievances into public solutions.*

---

## 1. The Problem — The Governance Bottleneck

Public grievance redressal in India is throttled by manual processing:

- **Unstructured inputs.** Citizens complain via handwritten letters, voice notes, images, and walk-ins. Staff must read, interpret, and re-type each one.
- **Slow, error-prone routing.** Complaints are manually sorted to departments — often the wrong one — adding days of delay before any action begins.
- **No prioritisation.** A life-threatening hazard (a live electric wire) sits in the same queue as a routine certificate request.
- **Erodes trust.** As digital adoption grows, the absence of responsive infrastructure undermines institutional credibility and lets backlogs compound into systemic inefficiency.

**Who is affected:** citizens awaiting resolution, and officials buried in high-volume manual document processing.

---

## 2. The Solution — Samadhan-Agent

An **autonomous, multi-modal interface** that digitises, interprets, and manages grievances from **submission to resolution**, split into two portals:

### 👥 Citizen Portal (public)
File a grievance through the channel that suits you, and track it by ID:

| Channel | Input method |
|---|---|
| **Web form** | Type the complaint |
| **Voice note** | Speak it — live browser speech-to-text transcription |
| **Image / scanned PDF** | Upload — AI vision OCR extracts the text |
| **Handwritten letter** | Upload a photo — AI vision reads the handwriting |

The **agentic pipeline** then, in one step:
1. **Extracts** a clean summary and the location,
2. **Classifies** the issue and **routes** it to the correct department,
3. Assigns a **priority** (Critical / High / Medium / Low) grounded in the department's SLA,
4. Reads **sentiment**, and
5. Drafts a **policy-grounded next action** citing the specific rule it relied on.

The citizen instantly sees the agent's decision and a tracking ID (e.g. `SAM-2026-0001`).

### 🏛 Government Portal (restricted)
Officials sign in with an access code to a live case-management dashboard:
- KPI stats (total, critical, pending, resolution rate),
- Cases sorted **critical-first**, filterable by status and department,
- One-click **status updates** (Submitted → Routed → In Progress → Resolved),
- Every case shows the AI's routing, sentiment, and the **policy basis** for accountability.

Officials-only API endpoints are gated **server-side**, not merely hidden in the UI.

---

## 3. How AI is Integrated

Samadhan-Agent is **AI-first**, not rules-first. Intelligence appears at three points:

1. **Multi-modal understanding.** Voice → text (browser Web Speech API). Images / scanned PDFs / handwriting → text (vision model OCR).
2. **Agentic reasoning.** A single LLM pass performs extraction, classification, routing, prioritisation, sentiment, and action-drafting — replacing rigid rules with intent-aware processing that handles the ambiguity of real complaints.
3. **RAG grounding.** Every AI decision is grounded in an **official policy corpus** (citizen charters, SLAs, safety norms). The agent must cite the specific policy behind each priority and action, so its output is auditable rather than a black box.

**Provider strategy (precedence):** `Gemini (free tier) → Anthropic Claude → deterministic rule-based fallback`. If no AI key is configured — or an API call fails — the system automatically falls back to a keyword engine, so **the demo never breaks**, even fully offline.

---

## 4. Why It's Different

- **End-to-end orchestration**, not passive ticket categorisation — the agent reasons through the whole submission-to-routing workflow.
- **Policy-grounded (RAG):** actions are validated against official policy, keeping automated resolutions compliant and contextually accurate.
- **Truly multi-modal intake** meets citizens where they are — voice, image, handwriting, or text.
- **Resilient by design:** graceful degradation guarantees a working demo regardless of connectivity or keys.

---

## 5. Architecture

```
Citizen (text / voice / image / scanned PDF / handwritten letter)
        │
        │  voice → browser Web Speech API (client-side transcription)
        │  image/PDF → POST /api/extract → vision OCR
        ▼
┌──────────────────────────────────────────────────────────────┐
│  FastAPI backend                                             │
│                                                              │
│   agent.analyze()   app/agent.py                             │
│     extract → classify → ROUTE → prioritise → sentiment →    │
│     policy-grounded action                                   │
│        ├─ provider: Gemini  (app/providers.py precedence)    │
│        ├─ provider: Claude                                   │
│        └─ provider: rule-based keyword engine (offline)      │
│                                                              │
│   RAG: retrieve_policy()   app/policies.py                   │
│   OCR: extract_text()      app/extract.py                    │
│   Auth: require_official()  (X-Official-Key gate)            │
│   Store: SQLAlchemy → SQLite (dev) / Postgres (prod)         │
└──────────────────────────────────────────────────────────────┘
        │  REST /api/*
        ▼
React SPA (frontend/, zero-build via CDN, served by FastAPI)
   • Citizen Portal: File Grievance · Track
   • Government Portal: login-gated Officials' Dashboard
```

---

## 6. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Backend | **FastAPI** (Python) | REST API + serves the frontend |
| Frontend | **React** | Zero-build (CDN + Babel); migratable to Vite |
| Database | **SQLAlchemy** → SQLite / **PostgreSQL** | `DATABASE_URL` swaps SQLite for hosted Postgres |
| AI reasoning + OCR | **Google Gemini** (default, free) / **Anthropic Claude** | provider-swappable via env keys |
| Voice | **Web Speech API** | in-browser, no key required |
| Knowledge | **RAG** over policy corpus | grounds every AI action |
| Deployment | **Render** (from GitHub) | auto-deploys on push |

---

## 7. Running It

### Local
```bash
./run.sh              # creates venv, installs deps, starts on :8000
```
Open http://127.0.0.1:8000. Runs in rule-based mode with no keys.

### Enable full AI (free)
1. Get a free key at https://aistudio.google.com/apikey
2. `cp backend/.env.example backend/.env` and set `GEMINI_API_KEY=...`
3. `./run.sh` — OCR and LLM reasoning now active.

### Government Portal
Access code defaults to `samadhan-admin` (override with `OFFICIAL_KEY`).

### Environment variables
| Var | Purpose | Default |
|---|---|---|
| `GEMINI_API_KEY` | Gemini (preferred, free) — enables OCR + LLM | _(unset)_ |
| `GEMINI_MODEL` | Gemini model | `gemini-flash-latest` |
| `ANTHROPIC_API_KEY` | Claude (paid alternative) | _(unset)_ |
| `OFFICIAL_KEY` | Government Portal access code | `samadhan-admin` |
| `DATABASE_URL` | Persistent Postgres URL | _(unset → SQLite)_ |

---

## 8. API Reference

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/grievances` | public | Submit a grievance (runs the agent) |
| `POST` | `/api/extract` | public | OCR an uploaded image / PDF / letter |
| `GET`  | `/api/track/{tracking_id}` | public | Citizen tracking |
| `POST` | `/api/official/login` | public | Government Portal login |
| `GET`  | `/api/grievances` | official | List cases (filterable, critical-first) |
| `PATCH`| `/api/grievances/{id}/status` | official | Update case status |
| `GET`  | `/api/stats` | official | Dashboard metrics |
| `GET`  | `/api/health` | public | Active AI provider + model |

---

## 9. Feasibility & Scalability

- **Technical viability:** industry-standard stack (FastAPI, SQLAlchemy, Postgres) that handles high-volume public-service data; the agent is stateless and horizontally scalable.
- **Operational integration:** an "AI-first overlay" — deployable alongside existing administrative workflows without an infrastructure overhaul.
- **Policy grounding:** RAG anchors resolutions in official policy, keeping automation compliant.
- **Data security:** designed for encryption in transit/at rest and adherence to government data-privacy standards.
- **Bias mitigation:** routing decisions are auditable (policy citation per action), enabling transparent review.

---

## 10. Current Scope vs. Roadmap

**Working today:** two-portal app; multi-modal intake (voice live, image/PDF/handwriting OCR with a key); agentic routing + prioritisation; RAG policy grounding; officials' auth + dashboard; tracking; IST timestamps; Gemini/Claude/rule-based providers; live cloud deployment.

**Prototype-level:** the policy corpus is a curated in-memory set (production = vector store over the full policy library); officials share a single access code (production = per-official accounts with role scoping).

**Roadmap:** vector DB (pgvector/Chroma) over real policy PDFs · per-official RBAC accounts · SMS/WhatsApp intake · analytics on department SLA compliance · Dockerised multi-service deploy on AWS/GCP.
