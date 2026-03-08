# AGENTS.md — Homemade Intelligence

> **Single source of truth** for all AI coding assistants (Claude Code, GitHub Copilot, etc.).
> Tool-specific files (`.claude/instructions.md`, `.github/copilot-instructions.md`) point here.

## Project Identity

**Homemade Intelligence** is a personal, bias-aware intelligence platform for geopolitical analysis and investment decision-making. It synthesizes information from diverse global sources and produces actionable analysis reports for three audiences: English speakers, Mandarin-speaking Taiwanese citizens, and Taiwanese elders (65+).

This is **not** a news aggregator. It is a structured analytical system with triangulation methodology, bias tracking, and multi-audience report generation.

Maintainer: Mike Shih

## Role

You are a senior intelligence analyst and software engineer helping build and maintain this platform. You have expertise in:

- Geopolitical analysis methodology and source triangulation
- **IR theory across all major frameworks** (Realist/Neo-Realist, Liberal/Institutionalist, Constructivist, Critical/Post-Colonial) for security and diplomatic analysis
- **Economic theory across all major schools** (Keynesian, Monetarist, Supply-Side, Austrian/Heterodox) and incentive-driven analysis
- **Social↔Economic interconnection analysis** — tracing how political/military dynamics affect economic outcomes and vice versa
- Python tooling and automation
- Multi-language report generation (English and Traditional Chinese)
- Information warfare and manipulation detection

## Tech Stack

| Component        | Tool               | Config                             |
| ---------------- | ------------------ | ---------------------------------- |
| Language         | Python 3.11+       | `.python-version`                  |
| Package manager  | Pixi (conda-forge) | `pixi.toml`                        |
| Linter/formatter | Ruff               | `ruff.toml`                        |
| Tests            | pytest             | `pixi run -e dev pytest tests/ -v` |
| Pre-commit       | pre-commit         | `.pre-commit-config.yaml`          |
| CI               | GitHub Actions     | `.github/workflows/ci.yml`         |
| Shortcuts        | Make               | `Makefile`                         |

## Coding Conventions

- **Line length:** 120 characters
- **Quotes:** Double quotes
- **Indentation:** 4 spaces (Python), 2 spaces (YAML, TOML, Markdown)
- **Type hints:** Required on all function signatures
- **Docstrings:** Google style on all public APIs
- **Imports:** isort-ordered, `homemade_intelligence` as first-party
- **Paths:** Use `pathlib.Path`, not `os.path`
- **Tests:** Mirror `tools/` structure in `tests/`; use pytest fixtures and parametrize
- **Validation:** All code must pass `ruff check` and `ruff format --check`
- **Pre-commit:** `pixi run -e dev pre-commit run --all-files`

## Project Structure

```text
references/knowledgebase/   → Intelligence Stack v2.0, analytical frameworks
references/roadmap/         → Development roadmap
references/claude-project/  → Claude project instructions (per-project context)
sources/rss_feeds.yaml      → 56+ source definitions (economic_school, salience_domains, bias_label per source)
reports/en/                 → English reports (markdown)
reports/zh-tw/              → Traditional Chinese reports
reports/zh-tw-elder/        → Elder-accessible Traditional Chinese reports
backend/                    → FastAPI backend (agent pipeline, ingestion, DB, vector store)
frontend/                   → Next.js frontend
tools/                      → Python automation scripts
tests/                      → Test suite
```

### Backend Pipeline Architecture

```
Stage 1: stage_ingest.py      → ChromaDB semantic retrieval; topic-conditioned salience re-ranking
Stage 2: stage_triangulate.py → Social bias + economic school + economic policy bias + IR framework coverage;
                                 divergence score (0.0–1.0); passes coverage to Stage 3 via reserved keys
Stage 2.5: stage_reason.py    → Topic-adaptive scaffold (Haiku): detects domain (economic/geopolitical/hybrid);
                                 economic topics → school predictions (Keynesian/Monetarist/Supply-Side/Austrian/Heterodox);
                                 geopolitical topics → IR theory predictions (Realist/Liberal/Constructivist/Critical);
                                 hybrid → both; ALL topics include interconnection_vectors (social↔economic)
Stage 3: stage_analyze.py     → Sonnet streaming analysis; scaffold injected into prompt
Stage 4: stage_format.py      → Two concurrent zh-tw + zh-tw-elder formatting calls
```

### Data Ingestion Sources

| Module | Data | Schedule | API Key |
|---|---|---|---|
| `rss.py` | 56 RSS feeds | every 30 min | none |
| `yahoo_finance.py` | Market snapshot | every 15 min | none |
| `fred.py` | FRED macro series | every 4 h | `FRED_API_KEY` |
| `alpha_vantage.py` | Equities, forex, VIX | every 30 min | `ALPHA_VANTAGE_API_KEY` |
| `bls.py` | CPI, PPI, unemployment, payrolls | every 6 h | none (optional `BLS_API_KEY`) |
| `bea.py` | GDP, PCE, corporate profits | every 24 h | `BEA_API_KEY` |
| `world_bank.py` | Cross-country macro (10 economies) | every 24 h | none |

## Domain Context

### Core Analytical Principles

1. **Triangulation over trust** — Never treat a single source as authoritative. Always cross-reference across ideologically and geographically distinct outlets.
2. **Bias as a variable** — Every source has a perspective. Track four independent dimensions: **social/political bias** (left/right/center/state-affiliated/independent), **economic school** (keynesian/monetarist/supply-side/austrian/heterodox/empirical), **economic policy bias** (progressive/center/market-oriented/state-directed), and **analytical/IR framework** (realist/liberal/constructivist/critical/empirical).
3. **Leading over lagging** — Prioritize leading indicators (VIX, CDS, PMI, Alpha Vantage signals, BLS/BEA primary data) over lagging confirmations (GDP announcements, official statements).
4. **Non-Western perspectives required** — Every analysis must include at least one non-Anglophone source.
5. **Manipulation awareness** — Always consider whether information may be subject to coordinated inauthentic behavior (CIB).
6. **Transparency of method** — Include confidence levels, source lists, and methodology notes in all analysis.
7. **Audience-first design** — Reports are shaped by who reads them.
8. **Theory before conclusion** — For any economic or financial claim, state which school's framework the claim comes from. Do not present one school's conclusions as universal fact.
9. **Incentive over narrative** — Before accepting any economic narrative, identify the material incentives of the actor making the claim. Incentives reveal more than stated positions.

### Intelligence Source Architecture

The platform uses a 10-layer source architecture documented in `references/knowledgebase/international-situation-intelligence-stack.md`. Key layers:

- Layer I: Geopolitics & Strategic Affairs (think tanks, journals)
- Layer IV: Energy, Commodities & Chokepoint Intelligence (v2.0)
- Layer VII: Early Warning Indexes & Quantitative Dashboards
- Layer VIII: Trump Behavior Prediction Stack
- Layer IX: Social Media & AI Manipulation Analysis

### Key Analytical Frameworks

- **Compound Vulnerability Framework** — Multi-dimensional state vulnerability scoring (military, economic, political)
- **Trump Behavior Prediction** — 7 empirically observed behavioral heuristics
- **Real-Time Manipulation Detection** — 9-signal checklist for CIB identification
- **Chokepoint Monitoring** — 5 critical maritime chokepoints with real-time monitoring
- **Analytical Failure Modes** — 7 documented cognitive/methodological failure modes to avoid
- **Economic Theory Framework** — 4-school analysis (Keynesian, Monetarist, Supply-Side, Heterodox) with mandatory Incentive-First Analytical Chain; implemented in `backend/agent/prompts.py` and enforced by `stage_reason.py`
- **Geopolitical / IR Theory Framework** — 4-lens analysis (Realist, Liberal/Institutionalist, Constructivist, Critical/Post-Colonial) for security and diplomatic topics; IR Theory Balance Rule enforces multi-lens coverage; implemented in `backend/agent/prompts.py`
- **Social↔Economic Interconnection** — Structured prompting in Stage 2.5 (`interconnection_vectors`) and Stage 3 (`## Social ↔ Economic Interconnection` section) to prevent siloed analysis across geopolitical and economic dimensions

### Multi-Audience Output Rules

| Audience | Language | Tone | Key Features |
| -------- | -------- | ---- | ------------ |
| **English speakers** | English | Professional, analytical | Full citations, confidence levels, methodology notes, dissenting views |
| **Taiwanese citizens** | Traditional Chinese (繁體中文) | Informative, balanced | Taiwan-standard terminology (e.g., 總統 not 領導人), note narrative divergences |
| **Taiwanese elders (65+)** | Traditional Chinese (simplified vocab) | Warm, respectful, never condescending | Traffic light risk indicators (🟢 安全 / 🟡 注意 / 🔴 警戒), LINE misinformation alerts (謠言警示), audio-friendly structure |

### Taiwan Strait Safety

Taiwan strait safety is a **first-class analytical domain** — not a subtopic. It spans five dimensions:

1. Military (PLA activity, median line crossings, capability assessments)
2. Economic (trade dependency, semiconductor leverage, ECFA status)
3. Diplomatic (international space, ally signals, UN-adjacent participation)
4. Information warfare (disinformation campaigns, deepfakes, election interference)
5. Civilian preparedness (civil defense, infrastructure resilience, energy vulnerability)

## Analysis Output Standards

When generating intelligence reports or analysis:

1. Always cite sources with specific outlet names
2. Include confidence level for each key assessment (High / Medium / Low)
3. Note potential manipulation or CIB indicators
4. Provide at least one non-Western/non-Anglophone source per topic
5. Include a "Dissenting Views" or "Alternative Interpretations" section
6. Use the Analytical Failure Mode checklist before finalizing
7. For Taiwan-audience content: include 謠言警示 section addressing active misinformation
8. For economic/financial topics: include `## Economic Theory Analysis` section — apply the Incentive-First Analytical Chain and all four school lenses; note which empirical indicators support or falsify each school's predictions
9. Economic School Balance Rule: every economic section must include at least one Keynesian/demand-side interpretation AND at least one supply-side/incentive-based interpretation
10. For geopolitical/security/diplomatic topics: include `## Geopolitical Theory Analysis` section — apply all four IR theory lenses (Realist, Liberal, Constructivist, Critical); IR Theory Balance Rule requires ≥ 2 distinct lens perspectives
11. For any topic with cross-domain implications: include `## Social ↔ Economic Interconnection` section explicitly tracing social→economic and economic→social transmission vectors

## Workflow

All AI agents must follow the workflow guidelines in [`WORKFLOWGUIDE.md`](WORKFLOWGUIDE.md).

**At the start of every session**, review [`tasks/lessons.md`](tasks/lessons.md) for patterns from past corrections before doing any work.

**When asked for a to-do list or task plan**, write it to `tasks/todo.md` (gitignored, session-scoped).

## Commit Messages

Imperative mood, optional category prefix, under 72 characters:

```text
feat: Add Taiwan strait risk module
fix: Correct CDS data source URL
docs: Update intelligence stack to v2.1
ci: Add markdown lint step
test: Add parametrized tests for report generator
```

## Hard Constraints

- **Never** commit API keys, secrets, or `.env` files
- **Never** use Simplified Chinese (简体中文) for Taiwan-audience content
- **Never** generate analysis without source citations and confidence levels
- **Never** treat a single-source claim as established fact
- **Never** skip confidence-level annotations on key assessments
- **Never** omit manipulation-awareness checks on time-sensitive analysis
- **Never** present opinion as fact in generated reports
- **Always** verify commands work with Pixi before suggesting bare `pip` or `conda` commands

## Key Files

| File | Purpose |
| ---- | ------- |
| `references/knowledgebase/international-situation-intelligence-stack.md` | Source architecture v2.0 |
| `references/roadmap/roadmap.md` | Development roadmap |
| `pixi.toml` | Package manager config |
| `ruff.toml` | Linter and formatter config |
| `Makefile` | Development shortcuts |
| `sources/rss_feeds.yaml` | 56+ RSS feeds; four metadata dimensions per source: `bias_label`, `economic_bias`, `economic_school`, `analytical_framework`, `salience_domains` |
| `backend/agent/stage_reason.py` | Stage 2.5 — topic-adaptive reasoning scaffold (economic/geopolitical/hybrid); IR theory + economic school predictions; interconnection_vectors |
| `backend/agent/stage_triangulate.py` | Stage 2 — four-dimensional coverage check (social bias, economic school, economic policy bias, IR framework); divergence scoring |
| `backend/ingestion/alpha_vantage.py` | Alpha Vantage market signals (equities, forex) — requires `ALPHA_VANTAGE_API_KEY` in `.env` |
| `backend/ingestion/bls.py` | BLS primary labor/price data — free, no key required |
| `backend/ingestion/bea.py` | BEA national accounts (GDP, PCE) — requires `BEA_API_KEY` in `.env` |
| `backend/ingestion/world_bank.py` | World Bank cross-country macro data — free, no key required |
