# Homemade Intelligence

A personal, bias-aware geopolitical intelligence platform. Ingests from 56+ RSS feeds and primary economic data sources across ideologically diverse outlets, triangulates narratives across four independent bias dimensions, and generates theory-grounded analysis reports in three audience formats via Claude — all running locally.

---

## What It Does

1. **Ingests** from 56+ RSS feeds, GDELT, Yahoo Finance, FRED, Alpha Vantage, BLS, BEA, and World Bank in the background (or via manual text/URL injection)
2. **Triangulates** sources across four independent bias dimensions — social/political bias, economic school (Keynesian/Monetarist/Supply-Side/Heterodox), economic policy bias (progressive/market-oriented), and IR/geopolitical framework (Realist/Liberal/Constructivist/Critical) — then scores narrative divergence (0.0–1.0)
3. **Reasons** via a topic-adaptive Stage 2.5 scaffold: detects topic domain (economic/geopolitical/hybrid) and generates IR theory or economic school predictions plus social↔economic interconnection vectors before the main analysis call
4. **Analyzes** via Claude with a cached system prompt (~7,400 tokens, ~90% cost reduction on repeat calls)
5. **Formats** concurrently into three audiences: English · 繁體中文 · 長輩版 (elder-accessible TC with 🟢🟡🔴 risk indicators)
6. **Tracks predictions** with Brier scoring and calibration curves against Metaculus/Polymarket reference odds

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · SQLite · SQLAlchemy · ChromaDB |
| LLM | Anthropic Claude (`claude-sonnet-4-6`) with prompt caching |
| Ingestion | feedparser · GDELT v2 · yfinance · fredapi · Alpha Vantage · BLS · BEA · World Bank · trafilatura |
| Scheduling | APScheduler (RSS every 30 min, Alpha Vantage every 30 min, FRED every 4 h, BLS/World Bank every 6–24 h) |
| Frontend | Next.js 16 (App Router) · TypeScript · Tailwind CSS · Recharts |
| Package manager | Pixi (conda-forge) |

---

## Quick Start

### Prerequisites

- macOS arm64 (osx-arm64) or Linux x86-64
- [Pixi](https://pixi.sh) installed
- Node.js ≥ 20.9.0 (for frontend)
- Anthropic API key

### 1. Clone and configure

```bash
git clone https://github.com/eufmike/homemade-intelligence.git
cd homemade-intelligence
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY at minimum
```

### 2. Install dependencies

```bash
pixi install
```

### 3. Initialize the database

```bash
pixi run db-init
```

### 4. Start the backend

```bash
pixi run serve
# → http://localhost:8000
```

### 5. Start the frontend

```bash
cd frontend && npm install && npm run dev
# → http://localhost:3000
```

Open `http://localhost:3000/reports/new`, enter a topic, optionally paste an article, click **Analyze**.

---

## Project Structure

```
homemade-intelligence/
├── backend/
│   ├── main.py                     # FastAPI app (lifespan: DB init, source sync, scheduler)
│   ├── config.py                   # Settings from .env via pydantic-settings
│   ├── database/
│   │   ├── connection.py           # SQLAlchemy engine, SessionLocal, get_db()
│   │   ├── models.py               # ORM models: sources, ingested_content, reports, predictions, prediction_outcomes
│   │   └── migrations/001_initial_schema.sql
│   ├── vector_store/
│   │   └── chroma.py               # ChromaDB client; collections: sources + reports
│   ├── ingestion/
│   │   ├── rss.py                  # feedparser RSS poller (56+ feeds)
│   │   ├── gdelt.py                # GDELT v2 keyword query
│   │   ├── yahoo_finance.py        # yfinance market snapshot
│   │   ├── fred.py                 # FRED economic indicators
│   │   ├── alpha_vantage.py        # Alpha Vantage equities, forex, VIX (ALPHA_VANTAGE_API_KEY)
│   │   ├── bls.py                  # BLS CPI, PPI, unemployment, payrolls
│   │   ├── bea.py                  # BEA GDP, PCE, corporate profits (BEA_API_KEY)
│   │   ├── world_bank.py           # World Bank cross-country macro (10 economies)
│   │   ├── manual.py               # Raw text + URL (trafilatura) injection
│   │   ├── dedup.py                # SHA-256 content deduplication
│   │   └── scheduler.py            # APScheduler background jobs
│   ├── agent/
│   │   ├── pipeline.py             # Orchestration; asyncio.Task + Queue (survives client disconnect)
│   │   ├── prompts.py              # INTELLIGENCE_STACK_SYSTEM + IR theory/economic frameworks + cache_control
│   │   ├── stage_ingest.py         # Stage 1: ChromaDB semantic retrieval + salience re-ranking
│   │   ├── stage_triangulate.py    # Stage 2: four-dimensional bias coverage + divergence score
│   │   ├── stage_reason.py         # Stage 2.5: topic-adaptive scaffold (economic/geopolitical/hybrid)
│   │   ├── stage_analyze.py        # Stage 3: streaming English analysis
│   │   ├── stage_format.py         # Stage 4: concurrent TC general + elder formatting
│   │   └── token_tracker.py        # Per-stage token/cost logging
│   ├── predictions/
│   │   ├── crud.py                 # Prediction create/resolve
│   │   └── scoring.py              # Brier score, calibration curve, skill score
│   ├── routers/
│   │   ├── reports.py              # POST /generate, GET /, GET /{id}, GET /{id}/stream
│   │   ├── predictions.py          # CRUD + PATCH /{id}/resolve
│   │   ├── ingestion.py            # POST /inject/text, POST /inject/url, GET /sources
│   │   └── metrics.py              # GET /brier, /calibration, /accuracy-timeline
│   └── schemas/                    # Pydantic request/response models
├── frontend/src/
│   ├── app/
│   │   ├── page.tsx                # Dashboard
│   │   ├── reports/new/page.tsx    # Topic form + SSE streaming display
│   │   ├── reports/[id]/page.tsx   # Report viewer with audience toggle
│   │   ├── predictions/            # List, create, detail, resolve
│   │   ├── performance/page.tsx    # Brier score chart + calibration curve
│   │   └── sources/page.tsx        # Feed table + manual inject panel
│   └── components/
│       ├── report/                 # ReportViewer, AudienceToggle, BiasScoreBadge, StreamingOutput
│       ├── predictions/            # CreatePredictionForm, ResolutionModal, ReferenceOddsBar
│       ├── performance/            # BrierScoreChart, CalibrationCurve
│       └── sources/                # ManualInjectPanel
├── sources/
│   └── rss_feeds.yaml              # 56+ feeds; four metadata dimensions per source: bias_label, economic_bias, economic_school, analytical_framework
├── docs/
│   ├── methodology.md              # Vision, analytical principles, source architecture, audience standards
│   └── adr/                        # Architecture Decision Records (MADR format)
│       ├── 0001-sqlite-chromadb-for-storage.md
│       ├── 0002-anthropic-prompt-caching.md
│       └── 0003-background-task-pipeline.md
├── tests/
│   ├── conftest.py                 # In-memory SQLite + mock ChromaDB fixtures
│   ├── test_ingestion/test_dedup.py
│   ├── test_agent/test_pipeline.py
│   └── test_predictions/test_scoring.py
├── pixi.toml
├── .env.example
└── AGENTS.md                       # AI coding assistant instructions
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/reports/generate` | Generate report (SSE stream) |
| `GET` | `/api/reports` | List reports |
| `GET` | `/api/reports/{id}` | Get report with all 3 audience versions |
| `GET` | `/api/reports/{id}/stream` | SSE for in-progress report |
| `POST` | `/api/inject/text` | Inject raw article text |
| `POST` | `/api/inject/url` | Fetch + extract URL and inject |
| `GET` | `/api/sources` | List sources with article counts |
| `POST` | `/api/sources/ingest` | Trigger manual RSS poll |
| `POST` | `/api/predictions` | Create prediction |
| `GET` | `/api/predictions` | List predictions |
| `PATCH` | `/api/predictions/{id}/resolve` | Resolve with outcome + Brier score |
| `GET` | `/api/metrics/brier` | Brier scores overall + by domain |
| `GET` | `/api/metrics/calibration` | Calibration curve data |
| `GET` | `/api/metrics/accuracy-timeline` | Rolling accuracy by day/week |
| `GET` | `/health` | Health check |

---

## Common Tasks

```bash
# Run tests (31 tests)
pixi run -e dev pytest tests/ -v

# Lint
pixi run lint

# Trigger RSS ingestion manually
curl -X POST http://localhost:8000/api/sources/ingest

# Generate a report from the CLI (no frontend)
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Taiwan Strait military activity", "domain": "taiwan"}'

# Inject an article
curl -X POST http://localhost:8000/api/inject/text \
  -H "Content-Type: application/json" \
  -d '{"title": "Article title", "body": "Article text..."}'

# Check database tables
sqlite3 data/homemade_intelligence.db ".tables"
```

---

## Configuration

All settings are read from `.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required for report generation |
| `FRED_API_KEY` | — | Optional; enables FRED economic indicators |
| `ALPHA_VANTAGE_API_KEY` | — | Optional; enables equities, forex, VIX signals |
| `BEA_API_KEY` | — | Optional; enables BEA GDP/PCE national accounts |
| `BLS_API_KEY` | — | Optional; higher BLS rate limit (free without key) |
| `DATABASE_URL` | `sqlite:///./data/homemade_intelligence.db` | SQLite path |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB persistence directory |
| `FRONTEND_URL` | `http://localhost:3000` | CORS origin |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Architecture Notes

Key decisions are documented in [`docs/adr/`](docs/adr/):

- **ADR-0001** — SQLite + ChromaDB (zero-infrastructure, fully local)
- **ADR-0002** — Prompt caching via `cache_control: ephemeral` (~90% cost reduction on the static system block)
- **ADR-0003** — Pipeline as `asyncio.Task` + `Queue` (survives client disconnect; reports always complete)

For analytical methodology, source architecture, and audience standards, see [`docs/methodology.md`](docs/methodology.md).

---

*Maintainer: Mike Shih · March 2026*
