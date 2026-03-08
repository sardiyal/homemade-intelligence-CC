"""Stage 2.5 — Topic-adaptive reasoning scaffold via a fast LLM call.

Sits between triangulate (Stage 2) and analyze (Stage 3). Uses a cheaper/faster
model to extract a structured reasoning scaffold from source chunks, which Stage 3
then uses as an auditable foundation rather than reasoning from scratch.

The scaffold is topic-adaptive:

  ECONOMIC topics (inflation, trade, monetary policy, labor markets, etc.):
    - Maps each economic school's theoretical prediction (Keynesian / Monetarist /
      Supply-Side / Austrian / Heterodox)
    - Identifies actors and their economic incentive structures
    - Notes empirical data vs. theory divergences
    - Always includes social↔economic interconnection vectors

  GEOPOLITICAL topics (conflict, diplomacy, sanctions, elections, military, etc.):
    - Maps each IR theory's prediction (Realist / Liberal / Constructivist / Critical)
    - Identifies state and non-state actors with interests and identity narratives
    - Notes empirical signals vs. theory divergences
    - Always includes social↔economic interconnection vectors

  HYBRID topics (topics combining both dimensions):
    - Includes both economic school predictions AND IR theory predictions
    - Explicitly models cross-domain interconnection

The interconnection_vectors field appears in ALL scaffold types — it is the
structural mechanism for ensuring social↔economic analysis is never siloed.
"""

import json
import logging

import anthropic

from backend.agent.token_tracker import RunTokenTracker
from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

ReasoningScaffold = dict  # typed alias for clarity in other modules

# Economic topic keywords (lower-case)
_ECONOMIC_KEYWORDS = frozenset(
    [
        "inflation",
        "interest rate",
        "gdp",
        "unemployment",
        "recession",
        "fed",
        "federal reserve",
        "central bank",
        "monetary",
        "fiscal",
        "tariff",
        "trade",
        "market",
        "stock",
        "bond",
        "yield",
        "currency",
        "dollar",
        "euro",
        "cpi",
        "ppi",
        "jobs",
        "earnings",
        "ipo",
        "investment",
        "hedge",
        "portfolio",
        "equity",
        "debt",
        "deficit",
        "surplus",
        "tax",
        "regulation",
        "supply chain",
        "commodities",
        "oil price",
        "energy market",
        "labor market",
        "wage",
        "productivity",
        "export",
        "import",
        "balance of trade",
    ]
)

# Geopolitical topic keywords (lower-case)
_GEOPOLITICAL_KEYWORDS = frozenset(
    [
        "war",
        "military",
        "troops",
        "invasion",
        "conflict",
        "sanction",
        "missile",
        "nuclear",
        "alliance",
        "nato",
        "treaty",
        "election",
        "coup",
        "strait",
        "protest",
        "democracy",
        "taiwan",
        "china",
        "russia",
        "ukraine",
        "iran",
        "north korea",
        "pla",
        "navy",
        "geopolit",
        "diplomat",
        "sovereignty",
        "territorial",
        "regime",
        "government",
        "bilateral",
        "multilateral",
        "security council",
        "pentagon",
        "deterrence",
        "escalat",
        "ceasefire",
        "occupation",
        "annexation",
        "insurgency",
        "blockade",
    ]
)

# ---------------------------------------------------------------------------
# Prompt constants
# ---------------------------------------------------------------------------

_REASON_SYSTEM = """You are a geopolitical and economic reasoning assistant. Your task is to produce a structured reasoning scaffold from raw source material. This scaffold will be used by a senior analyst to write a rigorous multi-framework analysis.

Your output must be strict JSON. Do not add prose outside the JSON block."""


# ---------------------------------------------------------------------------
# Topic domain detection
# ---------------------------------------------------------------------------


def _detect_topic_domain(topic: str) -> str:
    """Heuristically detect topic domain from topic string.

    Args:
        topic: Analysis topic string.

    Returns:
        'economic', 'geopolitical', or 'hybrid'.
    """
    topic_lower = topic.lower()
    has_econ = any(kw in topic_lower for kw in _ECONOMIC_KEYWORDS)
    has_geo = any(kw in topic_lower for kw in _GEOPOLITICAL_KEYWORDS)

    if has_econ and has_geo:
        return "hybrid"
    if has_econ:
        return "economic"
    if has_geo:
        return "geopolitical"
    return "hybrid"  # default: comprehensive coverage for ambiguous topics


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def _build_source_block(source_chunks: list[dict]) -> str:
    """Format source chunks for inclusion in the reasoning prompt."""
    parts = []
    for i, chunk in enumerate(source_chunks, 1):
        meta = chunk.get("metadata", {})
        name = meta.get("source_name", "Unknown")
        bias = meta.get("bias_label", "unknown")
        econ_school = meta.get("economic_school", "unknown")
        framework = meta.get("analytical_framework", "unknown")
        text = chunk.get("document", "")[:600]
        parts.append(
            f"[Source {i}: {name} | political bias: {bias} | "
            f"econ school: {econ_school} | IR framework: {framework}]\n{text}"
        )
    return "\n\n".join(parts) if parts else "(no sources retrieved)"


def _interconnection_schema() -> str:
    """Return the interconnection_vectors schema fragment (shared across all domains)."""
    return """\
  "interconnection_vectors": {
    "social_to_economic": "How do political instability, sanctions, elections, military actions, or social movements in this situation affect economic outcomes (supply chains, capital flows, commodity prices, investment, trade)?",
    "economic_to_social": "How do economic conditions (inequality, unemployment, fiscal stress, inflation, commodity shocks) shape political stability, election outcomes, conflict risk, or social cohesion in this situation?"
  }"""


def _build_reason_prompt_economic(topic: str, source_chunks: list[dict]) -> str:
    """Build reasoning prompt for economic topics."""
    sources_block = _build_source_block(source_chunks)
    interconnection = _interconnection_schema()

    return f"""Topic: {topic}
Domain: ECONOMIC

Source material:
{sources_block}

---

Produce a JSON reasoning scaffold with EXACTLY this structure:

{{
  "topic_summary": "One sentence describing the economic situation at stake.",
  "domain": "economic",
  "actors": [
    {{
      "name": "actor name",
      "role": "their economic role (e.g., central bank, exporting state, labor unions)",
      "incentives": "what material incentives drive their behavior in this situation",
      "constraints": "what limits their options"
    }}
  ],
  "school_predictions": {{
    "keynesian": "What Keynesian/Post-Keynesian theory predicts about this situation. If not applicable, write 'N/A — not primarily a demand-side issue.'",
    "monetarist": "What Monetarist/New Classical theory predicts. If not applicable, write 'N/A'.",
    "supply_side": "What Supply-Side/Neoliberal theory predicts. If not applicable, write 'N/A'.",
    "austrian": "What Austrian School theory predicts. If not applicable, write 'N/A'.",
    "heterodox": "What Heterodox/MMT/Institutional theory predicts. If not applicable, write 'N/A'."
  }},
  "empirical_signals": [
    {{
      "indicator": "name of indicator or data point",
      "value": "value or description",
      "source": "source name",
      "favors_school": "which school's prediction this data supports, or 'ambiguous'"
    }}
  ],
  "theory_data_divergences": [
    {{
      "framework": "school or theory name",
      "prediction": "what it predicted",
      "data_finding": "what the data actually shows",
      "divergence_severity": "low / medium / high"
    }}
  ],
  "source_framework_detection": [
    {{
      "source_name": "source name",
      "detected_framework": "the economic school or IR theory this source argues from based on its content",
      "framework_type": "economic_school / ir_theory",
      "confidence": "high / medium / low",
      "evidence": "one sentence of evidence for this classification"
    }}
  ],
{interconnection},
  "key_uncertainties": ["list of 2-4 key unknowns that would change the analysis"]
}}

Rules:
- Every field is required. Use "N/A" or empty arrays if genuinely not applicable.
- actors: list 2-5 key economic actors, not countries as monoliths.
- empirical_signals: list only signals present in the source material.
- Be specific — cite figures, dates, and source names where available.
- Output ONLY the JSON object, nothing else."""


def _build_reason_prompt_geopolitical(topic: str, source_chunks: list[dict]) -> str:
    """Build reasoning prompt for geopolitical/security topics."""
    sources_block = _build_source_block(source_chunks)
    interconnection = _interconnection_schema()

    return f"""Topic: {topic}
Domain: GEOPOLITICAL

Source material:
{sources_block}

---

Produce a JSON reasoning scaffold with EXACTLY this structure:

{{
  "topic_summary": "One sentence describing the geopolitical situation at stake.",
  "domain": "geopolitical",
  "actors": [
    {{
      "name": "actor name (state, armed group, institution, or key individual)",
      "role": "their role in this situation (e.g., regional hegemon, occupying force, mediator)",
      "interests": "material and strategic interests driving their behavior",
      "identity_narrative": "the identity, historical, or ideological narrative that shapes their position",
      "constraints": "what limits their options (domestic, military, diplomatic, economic)"
    }}
  ],
  "ir_theory_predictions": {{
    "realist": "What Realist/Neo-Realist theory predicts: focus on power, security dilemmas, balance of power, deterrence. If not clearly applicable, write 'N/A'.",
    "liberal": "What Liberal/Institutionalist theory predicts: focus on institutions, norms, interdependence, democratic constraints. If not applicable, write 'N/A'.",
    "constructivist": "What Constructivist theory predicts: focus on identity, norms, narrative, threat perception construction. If not applicable, write 'N/A'.",
    "critical": "What Critical/Post-Colonial theory highlights: focus on power asymmetries, historical injustices, Global South agency, hegemonic interest in the framing. If not applicable, write 'N/A'."
  }},
  "empirical_signals": [
    {{
      "indicator": "name of military, diplomatic, or economic signal",
      "value": "value, description, or observed behavior",
      "source": "source name",
      "favors_theory": "which IR theory this signal supports, or 'ambiguous'"
    }}
  ],
  "theory_data_divergences": [
    {{
      "framework": "IR theory name",
      "prediction": "what it predicted",
      "data_finding": "what the empirical signals actually show",
      "divergence_severity": "low / medium / high"
    }}
  ],
  "source_framework_detection": [
    {{
      "source_name": "source name",
      "detected_framework": "the IR theory or economic school this source argues from based on its content",
      "framework_type": "economic_school / ir_theory",
      "confidence": "high / medium / low",
      "evidence": "one sentence of evidence for this classification"
    }}
  ],
{interconnection},
  "key_uncertainties": ["list of 2-4 key unknowns that would change the analysis"]
}}

Rules:
- Every field is required. Use "N/A" or empty arrays if genuinely not applicable.
- actors: list 2-5 key actors. Do not treat countries as monoliths — distinguish governments, militaries, populations, diaspora.
- empirical_signals: list only signals present in the source material.
- Be specific — cite observable events, troop movements, diplomatic statements, economic actions.
- Output ONLY the JSON object, nothing else."""


def _build_reason_prompt_hybrid(topic: str, source_chunks: list[dict]) -> str:
    """Build reasoning prompt for hybrid topics (geopolitical + economic)."""
    sources_block = _build_source_block(source_chunks)
    interconnection = _interconnection_schema()

    return f"""Topic: {topic}
Domain: HYBRID (geopolitical + economic)

Source material:
{sources_block}

---

Produce a JSON reasoning scaffold with EXACTLY this structure:

{{
  "topic_summary": "One sentence describing the situation, covering both geopolitical and economic dimensions.",
  "domain": "hybrid",
  "actors": [
    {{
      "name": "actor name",
      "role": "their role (economic and/or geopolitical)",
      "interests": "material and strategic interests driving their behavior",
      "identity_narrative": "identity or ideological narrative shaping their position (if relevant)",
      "constraints": "what limits their options"
    }}
  ],
  "ir_theory_predictions": {{
    "realist": "Realist prediction for the geopolitical dimension. If not applicable, write 'N/A'.",
    "liberal": "Liberal/Institutionalist prediction. If not applicable, write 'N/A'.",
    "constructivist": "Constructivist prediction on identity/norms. If not applicable, write 'N/A'.",
    "critical": "Critical/Post-Colonial lens on power asymmetries. If not applicable, write 'N/A'."
  }},
  "school_predictions": {{
    "keynesian": "Keynesian prediction for the economic dimension. If not applicable, write 'N/A'.",
    "monetarist": "Monetarist prediction. If not applicable, write 'N/A'.",
    "supply_side": "Supply-Side prediction. If not applicable, write 'N/A'.",
    "austrian": "Austrian School prediction. If not applicable, write 'N/A'.",
    "heterodox": "Heterodox/MMT/Institutional prediction. If not applicable, write 'N/A'."
  }},
  "empirical_signals": [
    {{
      "indicator": "name of signal",
      "value": "value or description",
      "source": "source name",
      "favors_framework": "which theory or school this signal supports, or 'ambiguous'"
    }}
  ],
  "theory_data_divergences": [
    {{
      "framework": "IR theory or economic school name",
      "prediction": "what it predicted",
      "data_finding": "what the data actually shows",
      "divergence_severity": "low / medium / high"
    }}
  ],
  "source_framework_detection": [
    {{
      "source_name": "source name",
      "detected_framework": "the IR theory or economic school this source argues from",
      "framework_type": "economic_school / ir_theory",
      "confidence": "high / medium / low",
      "evidence": "one sentence of evidence"
    }}
  ],
{interconnection},
  "key_uncertainties": ["list of 2-4 key unknowns that would change the analysis"]
}}

Rules:
- Every field is required. Use "N/A" or empty arrays if genuinely not applicable.
- actors: list 2-5 key actors, not countries as monoliths.
- empirical_signals: list only signals present in the source material.
- Be specific — cite figures, dates, events, and source names where available.
- Output ONLY the JSON object, nothing else."""


def _build_reason_prompt(topic: str, source_chunks: list[dict]) -> tuple[str, str]:
    """Select and build the appropriate reasoning prompt based on topic domain.

    Args:
        topic: Analysis topic string.
        source_chunks: Retrieved source chunks from Stage 1.

    Returns:
        Tuple of (domain, prompt_string).
    """
    domain = _detect_topic_domain(topic)
    logger.info("Stage 2.5: detected topic domain '%s' for topic: %s", domain, topic[:80])

    if domain == "economic":
        return domain, _build_reason_prompt_economic(topic, source_chunks)
    if domain == "geopolitical":
        return domain, _build_reason_prompt_geopolitical(topic, source_chunks)
    return domain, _build_reason_prompt_hybrid(topic, source_chunks)


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------


def build_reasoning_scaffold(
    topic: str,
    source_chunks: list[dict],
    tracker: RunTokenTracker,
) -> ReasoningScaffold:
    """Run the reasoning scaffold extraction using the fast reasoning model.

    Uses settings.reasoning_model (defaults to claude-haiku) for cost efficiency.
    Falls back to an empty scaffold on any failure so the pipeline continues.

    Args:
        topic: Analysis topic string.
        source_chunks: Retrieved source chunks from Stage 1.
        tracker: Token tracker for cost accounting.

    Returns:
        Parsed ReasoningScaffold dict, or a minimal fallback scaffold on error.
    """
    if not source_chunks:
        logger.info("Stage 2.5: no source chunks; returning empty scaffold")
        return _empty_scaffold(topic, "hybrid")

    domain, prompt = _build_reason_prompt(topic, source_chunks)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    try:
        response = client.messages.create(
            model=settings.reasoning_model,
            max_tokens=2048,
            system=_REASON_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        tracker.record_usage("reason", response.usage)

        raw_text = response.content[0].text.strip()

        # Strip markdown code fences if the model wrapped the JSON
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        scaffold = json.loads(raw_text)
        logger.info(
            "Stage 2.5 scaffold built (domain=%s): %d actors, %d signals, %d divergences",
            domain,
            len(scaffold.get("actors", [])),
            len(scaffold.get("empirical_signals", [])),
            len(scaffold.get("theory_data_divergences", [])),
        )
        return scaffold

    except json.JSONDecodeError as exc:
        logger.warning("Stage 2.5: JSON parse failed (%s); using empty scaffold", exc)
        return _empty_scaffold(topic, domain)
    except Exception as exc:
        logger.warning("Stage 2.5: scaffold extraction failed (%s); using empty scaffold", exc)
        return _empty_scaffold(topic, domain)


def format_scaffold_for_prompt(scaffold: ReasoningScaffold) -> str:
    """Render the reasoning scaffold as a structured markdown block for Stage 3 prompt injection.

    Args:
        scaffold: The reasoning scaffold dict from build_reasoning_scaffold.

    Returns:
        Markdown-formatted string ready for injection into the Stage 3 user message.
    """
    if not scaffold or scaffold.get("_empty"):
        return "_Reasoning scaffold unavailable — proceeding from source material directly._"

    parts: list[str] = []
    domain = scaffold.get("domain", "hybrid")

    topic_summary = scaffold.get("topic_summary", "")
    if topic_summary:
        parts.append(f"**Topic Summary ({domain}):** {topic_summary}")

    # Actors and incentives
    actors = scaffold.get("actors", [])
    if actors:
        parts.append("\n### Key Actors & Incentive Structures")
        for actor in actors:
            interests = actor.get("interests") or actor.get("incentives", "")
            identity = actor.get("identity_narrative", "")
            constraints = actor.get("constraints", "")
            line = f"- **{actor.get('name', 'Unknown')}** ({actor.get('role', '')}): Interests — {interests}."
            if identity:
                line += f" Identity/Narrative — {identity}."
            if constraints:
                line += f" Constraints — {constraints}."
            parts.append(line)

    # IR theory predictions (geopolitical and hybrid domains)
    ir_preds = scaffold.get("ir_theory_predictions", {})
    if ir_preds:
        parts.append("\n### IR Theory Predictions")
        ir_labels = {
            "realist": "Realist/Neo-Realist",
            "liberal": "Liberal/Institutionalist",
            "constructivist": "Constructivist",
            "critical": "Critical/Post-Colonial",
        }
        for key, label in ir_labels.items():
            val = ir_preds.get(key, "N/A")
            parts.append(f"- **{label}:** {val}")

    # Economic school predictions (economic and hybrid domains)
    school_preds = scaffold.get("school_predictions", {})
    if school_preds:
        parts.append("\n### Economic School Predictions")
        school_labels = {
            "keynesian": "Keynesian/Post-Keynesian",
            "monetarist": "Monetarist/New Classical",
            "supply_side": "Supply-Side/Neoliberal",
            "austrian": "Austrian School",
            "heterodox": "Heterodox/MMT/Institutional",
        }
        for key, label in school_labels.items():
            val = school_preds.get(key, "N/A")
            parts.append(f"- **{label}:** {val}")

    # Empirical signals
    signals = scaffold.get("empirical_signals", [])
    if signals:
        parts.append("\n### Empirical Signals from Sources")
        for sig in signals:
            favors = sig.get("favors_school") or sig.get("favors_theory") or sig.get("favors_framework", "ambiguous")
            parts.append(
                f"- {sig.get('indicator', '')} = {sig.get('value', '')} "
                f"(source: {sig.get('source', '')} | favors: {favors})"
            )

    # Theory-data divergences
    divergences = scaffold.get("theory_data_divergences", [])
    if divergences:
        parts.append("\n### Theory ↔ Data Divergences")
        for div in divergences:
            severity = div.get("divergence_severity", "")
            parts.append(
                f"- **{div.get('framework', '')}** [{severity}]: "
                f"Predicted — {div.get('prediction', '')}. "
                f"Found — {div.get('data_finding', '')}."
            )

    # Source framework detection
    detected = scaffold.get("source_framework_detection", [])
    if detected:
        parts.append("\n### Detected Analytical Framework per Source")
        for src in detected:
            ftype = src.get("framework_type", "")
            parts.append(
                f"- {src.get('source_name', '')}: {src.get('detected_framework', '')} "
                f"[{ftype}] (confidence: {src.get('confidence', '')})"
            )

    # Social↔Economic interconnection vectors — always rendered
    interconnection = scaffold.get("interconnection_vectors", {})
    if interconnection:
        parts.append("\n### Social ↔ Economic Interconnection")
        s2e = interconnection.get("social_to_economic", "")
        e2s = interconnection.get("economic_to_social", "")
        if s2e:
            parts.append(f"- **Social→Economic:** {s2e}")
        if e2s:
            parts.append(f"- **Economic→Social:** {e2s}")

    # Uncertainties
    uncertainties = scaffold.get("key_uncertainties", [])
    if uncertainties:
        parts.append("\n### Key Uncertainties")
        for u in uncertainties:
            parts.append(f"- {u}")

    return "\n".join(parts)


def _empty_scaffold(topic: str, domain: str = "hybrid") -> ReasoningScaffold:
    """Return a minimal empty scaffold that signals Stage 3 to proceed without it."""
    return {
        "_empty": True,
        "topic_summary": topic,
        "domain": domain,
        "actors": [],
        "ir_theory_predictions": {},
        "school_predictions": {},
        "empirical_signals": [],
        "theory_data_divergences": [],
        "source_framework_detection": [],
        "interconnection_vectors": {},
        "key_uncertainties": [],
    }
