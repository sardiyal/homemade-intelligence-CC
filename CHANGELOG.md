# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased — Theory-Based-Finance Branch]

### Added

- **Stage 2.5 — Topic-adaptive reasoning scaffold** (`backend/agent/stage_reason.py`): New pipeline stage between triangulate and analyze. Detects topic domain (economic/geopolitical/hybrid) and generates a schema-appropriate structured JSON scaffold: economic topics get per-school predictions (Keynesian/Monetarist/Supply-Side/Austrian/Heterodox); geopolitical topics get IR theory predictions (Realist/Liberal/Constructivist/Critical); hybrid topics get both. All scaffold types include `interconnection_vectors` (social→economic and economic→social transmission mechanisms).
- **Geopolitical / IR Theory Framework** in prompts (`backend/agent/prompts.py`): Mandatory 4-lens IR cross-analysis (Realist, Liberal/Institutionalist, Constructivist, Critical/Post-Colonial) for security and diplomatic topics; IR Theory Balance Rule enforces multi-lens coverage. Added `## Geopolitical Theory Analysis` and `## Social ↔ Economic Interconnection` to the report output template.
- **Economic Theory Framework** in prompts (`backend/agent/prompts.py`): Mandatory 4-school cross-analysis (Keynesian, Monetarist, Supply-Side, Heterodox), Incentive-First Analytical Chain (9-step), Economic School Balance Rule. All analyses must include demand-side and supply-side perspectives.
- **Source metadata — four independent bias/framework dimensions**: New columns on the `sources` table:
  - `economic_school` — theoretical economic framework (keynesian/monetarist/supply-side/austrian/institutional/heterodox/empirical/mixed)
  - `economic_bias` — economic policy direction (progressive/center/market-oriented/state-directed); independent of social/political bias
  - `analytical_framework` — IR/geopolitical theory framework (realist/liberal/constructivist/critical/empirical/mixed); 14 sources labeled in `rss_feeds.yaml`
  - `salience_domains` — comma-separated domain tags (geopolitics/markets/energy/taiwan/general)
  - All four fields auto-migrated via `_migrate_add_columns()` in `connection.py`; synced from `rss_feeds.yaml` via `registry.py`
- **Stage 2 triangulation** (`backend/agent/stage_triangulate.py`): Now tracks `analytical_framework` coverage alongside social bias, economic school, and economic policy bias; passes all four dimensions to Stage 3 via reserved keys (`__econ_schools__`, `__econ_bias__`, `__analytical_frameworks__`).
- **Topic-conditioned salience re-ranking** (`backend/vector_store/chroma.py`): `query_sources_with_salience()` oversamples 2×, applies −0.08 distance boost to domain-matching sources, re-ranks before returning.
- **Alpha Vantage ingestion** (`backend/ingestion/alpha_vantage.py`): Market signals for 8 equity ETFs and 4 forex pairs; 30-min schedule; requires `ALPHA_VANTAGE_API_KEY`.
- **BLS ingestion** (`backend/ingestion/bls.py`): CPI, Core CPI, PPI, unemployment, payrolls, average hourly earnings from Bureau of Labor Statistics; 6-hour schedule; free (optional `BLS_API_KEY`).
- **BEA ingestion** (`backend/ingestion/bea.py`): GDP, PCE, personal income, corporate profits from Bureau of Economic Analysis; 24-hour schedule; requires `BEA_API_KEY`.
- **World Bank ingestion** (`backend/ingestion/world_bank.py`): 5 macro indicators across 10 economies (US, CN, TW, JP, DE, IN, GB, EU, BR, KR); 24-hour schedule; fully free.
- **56 RSS feeds** in `sources/rss_feeds.yaml` (up from ~24): Added right-leaning economics think tanks (AEI, Cato, Heritage, Hoover, Marginal Revolution), centrist/empirical outlets (VoxEU/CEPR, NBER, World Bank Blogs, Econbrowser), Layer VI geographic diversity (Japan Times, Korea Herald, Dawn, Arab News, Rappler, Straits Times, China Dialogue, Caixin Global), and Layer VI markets (The Economist, MarketWatch, Reuters Finance, Seeking Alpha).
- **New config settings**: `alpha_vantage_api_key`, `bls_api_key`, `bea_api_key`, `reasoning_model` (defaults to `claude-haiku-4-5-20251001`).

### Changed

- Pipeline now emits `"reason"` SSE status stage between `"triangulate"` and `"analyze"`.
- `stage_triangulate.py`: Extended divergence scoring with economic policy bias component (max +0.25); uses `economic_bias` field directly (progressive/market-oriented) rather than mapping from school names; warns when progressive or market-oriented perspectives absent; now tracks and reports `analytical_framework` coverage per source.
- `stage_ingest.py`: `retrieve_relevant_content()` accepts `domain` parameter; uses salience-aware retrieval when domain is provided.
- All ingestion modules (`rss.py`, `fred.py`, `yahoo_finance.py`, `gdelt.py`, `manual.py`, `alpha_vantage.py`, `bls.py`, `bea.py`, `world_bank.py`): Now pass `economic_school`, `economic_bias`, `analytical_framework`, and `salience_domains` metadata to ChromaDB for triangulation and salience re-ranking.
- `bias_label` (social/political bias) and `economic_bias` (policy direction) are now fully independent dimensions; `state-directed` economies (China, Russia, Gulf states) are correctly excluded from the progressive/market-oriented balance check.
- `SourceStatus` schema (`backend/schemas/ingestion.py`) and `/api/sources` router now include all four metadata dimensions in API responses.
- Frontend sources page (`frontend/src/app/sources/page.tsx`): Added Social Bias, Econ Bias, IR Framework, and Econ School columns with color-coded badges; salience domains shown as sub-text under source name.
- `AGENTS.md`: Added economic theory expertise to Role; principles 8 & 9 (theory-before-conclusion, incentive-over-narrative); Economic Theory Framework; pipeline architecture diagram; full ingestion table.

---

## [Unreleased]

### Added

- AI instruction files for multi-agent compatibility:
  - `.github/copilot-instructions.md` — GitHub Copilot workspace instructions
  - `.claude/instructions.md` — Claude Code project instructions
  - `.claude/settings.json` — Claude Code permissions configuration
  - `AGENTS.md` — Shared agent instructions (cross-tool compatible)
- `.github/CODEOWNERS` — default reviewers for pull requests
- `.github/ISSUE_TEMPLATE/config.yml` — issue template chooser with Intelligence Stack link
- `.github/ISSUE_TEMPLATE/source_suggestion.md` — new template for intelligence source proposals
- VS Code setting `github.copilot.chat.codeGeneration.useInstructionFiles` enabled

### Changed

- Redesigned `.github/` directory structure aligned with README project goals
- Upgraded issue templates (bug report, feature request) with richer metadata
- Enhanced PR template with affected-area checkboxes and stronger checklist
- Improved `SECURITY.md` with security practices section
- Upgraded CI workflow: added concurrency control, AI instructions check job
- Updated Dependabot config with commit message prefixes and scheduled day
- CI workflow uses 2-space YAML indentation (standard)

### Previous

- Project foundation: README, intelligence source architecture, project structure
- Multi-audience report framework (English, Traditional Chinese, Elder-accessible)
- International Situation Intelligence Stack v2.0
- Prompt templates for pre-market analysis
- Project housekeeping: `.gitignore`, `LICENSE`, `pixi.toml`, EditorConfig, pre-commit, ruff
- GitHub CI workflow (lint + test via Pixi)
- Dependabot configuration for dependency updates
- Pull request template
- `Makefile` with convenience shortcuts (`make dev`, `make lint`, `make test`, etc.)
- `.python-version` file for pyenv compatibility
- `tests/` directory with placeholder smoke test
- `tools/__init__.py` Python package marker

---

*Maintained by Mike Shih*
