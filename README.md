# Samadhan-Agent 🇮🇳

**AI-first public grievance redressal — turning public grievances into public solutions.**

> AI First Hackathon (Summer School '26) · I3C – IIT Jammu × Techible
> Track: **AI for Bharat — Governance & Social Impact** · Team **Minchu Badmosh**

Samadhan-Agent is an autonomous, multi-modal interface that digitizes, interprets,
and manages public grievances from **submission to resolution**. A citizen describes
a civic problem in plain language (text now; voice / scanned letters / images as
channels); an **agentic pipeline** extracts the key facts, **routes** the case to the
correct department, assigns **priority** based on official SLA policy, and drafts a
**policy-grounded next action**. Officials get a live **dashboard** to triage, track,
and resolve.

### Two portals
- **👥 Citizen Portal** (public) — file a grievance (location required) and track it by id. No login.
- **🏛 Government Portal** (restricted) — officials sign in with an access code to reach the
  case-management dashboard: stats, filters, and status updates. The officials-only API
  endpoints are gated server-side via the `OFFICIAL_KEY`.

---

## Why this MVP maps to the evaluation criteria

| Criterion (weight) | How this build addresses it |
|---|---|
| **Technical Implementation (30%)** | Working FastAPI backend, SQLAlchemy persistence, REST API, React frontend, one-command run. |
| **AI Integration & Innovation (25%)** | Agentic pipeline (extract → classify → route → prioritize → draft) grounded in policy via **RAG**. LLM (Claude, provider-swappable) with a deterministic fallback. |
| **User Experience & Design (15%)** | Clean citizen intake, live "Agent Decision" panel, public tracking, officials' dashboard with stats and one-click status updates. |
| **Feasibility & Scalability (15%)** | Standard, production-grade stack. SQLite → PostgreSQL is a one-line swap; agent is stateless and horizontally scalable. |
| **Pitch & Demo (15%)** | Bulletproof demo: five realistic sample grievances built in; runs fully **offline** via the rule-based fallback so a dead Wi-Fi never kills the demo. |

---

## Architecture

```
Citizen (text / voice / image / letter)
        │
        ▼
┌─────────────────────────────────────────────┐
│  FastAPI backend  (app/main.py)              │
│                                              │
│   agent.analyze()  ── app/agent.py           │
│     1. extract summary + location            │
│     2. classify + ROUTE to department        │
│     3. prioritise via policy SLA             │
│     4. sentiment                             │
│     5. draft policy-grounded action          │
│           │                                  │
│           ├─ LLM mode  → Claude (if API key) │
│           └─ Rule mode → keyword engine      │
│                                              │
│   RAG: retrieve_policy() ── app/policies.py  │
│   Store: SQLAlchemy + SQLite ── models.py    │
└─────────────────────────────────────────────┘
        │  REST /api/*
        ▼
React frontend (frontend/, zero-build via CDN)
   • File Grievance   • Track   • Officials' Dashboard
```

**Stack** (deck-faithful): FastAPI · React · SQLAlchemy/SQLite (Postgres-ready) ·
Claude reasoning layer (deck lists "GPT-4o / Llama 3" — provider is swappable).

---

## Run it

```bash
./run.sh
```

Then open **http://127.0.0.1:8000**. First run creates a virtualenv and installs
dependencies automatically.

### Enable the live LLM agent (optional)
By default it runs in **rule-based fallback** mode (no key needed — great for demos).
To use the real LLM agent:

```bash
cp backend/.env.example backend/.env
# edit backend/.env → set ANTHROPIC_API_KEY=sk-ant-...
./run.sh
```

The header badge shows which mode is active (`LLM` vs `rule-based fallback`).

### Government Portal login
Default access code is `samadhan-admin` (set `OFFICIAL_KEY` to change it). Open the
**Government Portal** tab → enter the code → dashboard.

### Persistent database (production)
Local dev uses SQLite. On a host with an ephemeral disk (e.g. Render free tier),
set `DATABASE_URL` to a hosted Postgres connection string so grievances and their
status survive restarts and redeploys. `postgres://` / `postgresql://` URLs are
auto-normalised to the psycopg 3 driver.

### Environment variables
Provider precedence: **Gemini → Anthropic → rule-based**. Set one AI key.

| Var | Purpose | Default |
|---|---|---|
| `GEMINI_API_KEY` | Gemini (preferred, free tier) — enables OCR + LLM agent | _(unset → rule-based)_ |
| `GEMINI_MODEL` | Gemini model | `gemini-flash-latest` |
| `ANTHROPIC_API_KEY` | Claude (paid alternative) | _(unset)_ |
| `LLM_MODEL` | Claude model | `claude-haiku-4-5-20251001` |
| `OFFICIAL_KEY` | Government Portal access code | `samadhan-admin` |
| `DATABASE_URL` | Persistent Postgres URL | _(unset → SQLite)_ |

> **Model note:** use the `gemini-flash-latest` alias — some accounts have zero free-tier
> quota for pinned models like `gemini-2.0-flash`; the alias resolves to a currently
> available model with quota.

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/grievances` | Submit a grievance (runs the agent) |
| `GET`  | `/api/grievances` | List cases (filter `?status=`, `?department=`), critical-first |
| `GET`  | `/api/grievances/{id}` | Single case |
| `GET`  | `/api/track/{tracking_id}` | Public citizen tracking |
| `PATCH`| `/api/grievances/{id}/status` | Official updates status |
| `GET`  | `/api/stats` | Dashboard metrics |
| `GET`  | `/api/health` | Health + active AI mode |

---

## Demo script (for the video)

1. Open the app → **File Grievance** tab.
2. Click the **"A live electric wire…"** sample → **Submit**.
   → Agent returns **Electricity Board**, **Critical**, and cites the electrocution-hazard SLA.
3. Click the **"income certificate 20 days…"** sample → Submit.
   → Routes to **Revenue & Land Records** (routine priority).
4. Switch to **Officials' Dashboard** → cases are sorted **Critical-first**, with live stats.
5. Change the wire case to **In Progress** → stats update instantly.
6. Go to **Track**, paste `SAM-2026-0001` → citizen sees live status.

---

## What's mocked vs. real (honest scope)

- **Real:** end-to-end submit → agent → route → store → dashboard → status → track; RAG grounding; LLM + fallback; full REST API.
- **Prototype-level:** voice/image channels accept the metadata and text but transcription/OCR (Whisper) is stubbed for the thin slice; policy corpus is a small in-memory set (production = vector store over real policy PDFs); no auth (add JWT + role gating for officials).

## Roadmap to production
- Whisper transcription + vision OCR for true multi-modal intake
- Vector DB (pgvector / Chroma) over official policy documents
- Auth & department-scoped official accounts
- Migrate SQLite → PostgreSQL; Dockerize; deploy on AWS/GCP (per deck)
