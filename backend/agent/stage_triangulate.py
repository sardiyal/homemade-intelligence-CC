"""Stage 2 — Bias coverage check, economic school coverage, and narrative divergence scoring.

Two bias dimensions are tracked independently:

social_bias (bias_label):   left / center-left / center / center-right / right /
                            state-affiliated / independent
                            — captures social/political ideological lean

economic_bias:              progressive / center / market-oriented / state-directed
                            — captures economic POLICY direction, orthogonal to social bias
                            Examples: FT is socially center but economically market-oriented;
                            Cato is socially independent but economically market-oriented.

economic_school:            keynesian / monetarist / supply-side / austrian / neoclassical /
                            institutional / heterodox / empirical / mixed
                            — captures the theoretical FRAMEWORK used; reported to Stage 3
                            for analytical context but NOT used for the left/right check
                            (economic_bias handles that more directly).
"""

import logging

logger = logging.getLogger(__name__)

# Minimum requirements for unbiased analysis
MIN_NON_ANGLOPHONE_SOURCES = 1
ANGLOPHONE_LANGUAGES = {"en"}
REQUIRED_BIAS_POLES = 2  # At least 2 distinct social/political bias labels

# Economic policy bias vocabulary
ECON_BIAS_PROGRESSIVE = "progressive"
ECON_BIAS_MARKET = "market-oriented"
ECON_BIAS_CENTER = "center"
ECON_BIAS_STATE = "state-directed"  # state-capitalist systems; orthogonal to the progressive/market axis


def triangulate_sources(source_chunks: list[dict]) -> tuple[dict, str, float]:
    """Categorize sources by social bias, economic policy bias, economic school, and analytical framework.

    Enforces minimum coverage requirements and computes a narrative divergence score
    based on both social and economic dimensions independently.

    Args:
        source_chunks: List of ChromaDB result dicts (each with metadata).

    Returns:
        Tuple of:
        - bias_coverage: dict mapping social bias_label -> list of source names.
          Also contains reserved keys __econ_schools__, __econ_bias__, and
          __analytical_frameworks__ for Stage 3 context.
        - coverage_caveat: warning string if requirements not met (empty if OK)
        - divergence_score: float 0.0-1.0 measuring narrative divergence
    """
    bias_coverage: dict[str, list[str]] = {}
    econ_school_coverage: dict[str, list[str]] = {}
    econ_bias_coverage: dict[str, list[str]] = {}
    analytical_framework_coverage: dict[str, list[str]] = {}
    non_anglophone_count = 0
    seen_sources: set[str] = set()

    for chunk in source_chunks:
        meta = chunk.get("metadata", {})
        source_name = meta.get("source_name", "Unknown")
        social_bias = meta.get("bias_label", "unknown")
        language = meta.get("language", "en")
        econ_school = meta.get("economic_school") or "unlabeled"
        econ_bias = meta.get("economic_bias") or ECON_BIAS_CENTER
        analytical_framework = meta.get("analytical_framework") or "unlabeled"

        if source_name not in seen_sources:
            seen_sources.add(source_name)
            if language not in ANGLOPHONE_LANGUAGES:
                non_anglophone_count += 1

            # Social/political bias coverage
            if social_bias not in bias_coverage:
                bias_coverage[social_bias] = []
            if source_name not in bias_coverage[social_bias]:
                bias_coverage[social_bias].append(source_name)

            # Economic school coverage (theoretical framework — for Stage 3 context)
            if econ_school not in econ_school_coverage:
                econ_school_coverage[econ_school] = []
            if source_name not in econ_school_coverage[econ_school]:
                econ_school_coverage[econ_school].append(source_name)

            # Economic policy bias coverage (policy direction — for divergence check)
            if econ_bias not in econ_bias_coverage:
                econ_bias_coverage[econ_bias] = []
            if source_name not in econ_bias_coverage[econ_bias]:
                econ_bias_coverage[econ_bias].append(source_name)

            # IR/geopolitical analytical framework coverage — for Stage 3 context
            if analytical_framework not in analytical_framework_coverage:
                analytical_framework_coverage[analytical_framework] = []
            if source_name not in analytical_framework_coverage[analytical_framework]:
                analytical_framework_coverage[analytical_framework].append(source_name)

    # --- Build coverage caveats ---
    caveats = []

    if non_anglophone_count < MIN_NON_ANGLOPHONE_SOURCES:
        caveats.append(
            f"Analysis lacks non-Anglophone sources (found {non_anglophone_count}, "
            f"minimum {MIN_NON_ANGLOPHONE_SOURCES}). Perspective may be Western-centric."
        )

    # Social bias check
    meaningful_poles = [label for label in bias_coverage if label not in ("unknown", "center") and bias_coverage[label]]
    has_social_left = "left" in meaningful_poles
    has_social_right = "right" in meaningful_poles
    has_state_affiliated = "state-affiliated" in meaningful_poles

    pole_count = sum([has_social_left, has_social_right, has_state_affiliated])
    if pole_count < REQUIRED_BIAS_POLES and len(bias_coverage) < REQUIRED_BIAS_POLES:
        caveats.append(
            "Insufficient social/political bias diversity — only one ideological pole represented. "
            "Divergence score may be artificially low."
        )

    # Economic policy bias check — uses economic_bias, not economic_school
    has_econ_progressive = bool(econ_bias_coverage.get(ECON_BIAS_PROGRESSIVE))
    has_econ_market = bool(econ_bias_coverage.get(ECON_BIAS_MARKET))
    active_econ_biases = {b for b in econ_bias_coverage if b != ECON_BIAS_STATE}
    if active_econ_biases and not (has_econ_progressive and has_econ_market):
        missing_side = ECON_BIAS_MARKET if not has_econ_market else ECON_BIAS_PROGRESSIVE
        caveats.append(
            f"Economic policy bias is one-sided — {missing_side} perspectives absent. "
            "Analysis may lack full policy-direction balance."
        )

    coverage_caveat = " | ".join(caveats)

    # Compute narrative divergence score
    divergence_score = _compute_divergence_score(bias_coverage, econ_bias_coverage, source_chunks)

    labeled_schools = {s for s in econ_school_coverage if s != "unlabeled"}
    labeled_frameworks = {f for f in analytical_framework_coverage if f != "unlabeled"}
    logger.info(
        "Stage 2 triangulation: %d unique sources, %d social poles, %d econ schools, "
        "%d econ bias labels, %d IR frameworks, divergence=%.2f",
        len(seen_sources),
        len(bias_coverage),
        len(labeled_schools),
        len(econ_bias_coverage),
        len(labeled_frameworks),
        divergence_score,
    )

    # Attach all analytical dimensions to bias_coverage for Stage 3 context
    bias_coverage["__econ_schools__"] = [
        f"{school}: {', '.join(sources)}" for school, sources in econ_school_coverage.items() if school != "unlabeled"
    ]
    bias_coverage["__econ_bias__"] = [f"{bias}: {', '.join(sources)}" for bias, sources in econ_bias_coverage.items()]
    bias_coverage["__analytical_frameworks__"] = [
        f"{framework}: {', '.join(sources)}"
        for framework, sources in analytical_framework_coverage.items()
        if framework != "unlabeled"
    ]

    return bias_coverage, coverage_caveat, divergence_score


def _compute_divergence_score(
    bias_coverage: dict,
    econ_bias_coverage: dict,
    source_chunks: list[dict],
) -> float:
    """Estimate narrative divergence score based on social bias AND economic policy bias.

    Social bias score (max 0.50):
    - left + right present: 0.40
    - any 2 distinct poles: 0.20
    - state-affiliated present: +0.10

    Economic policy bias score (max 0.30):
    - progressive + market-oriented both present: +0.25
    - 2+ distinct non-state biases (without both sides): +0.10
    - center present alongside either: +0.05

    Source diversity bonus (max 0.20):
    - non-Anglophone source present: +0.10
    - 3+ non-Anglophone sources: +0.05
    - 3+ distinct intelligence stack layers: +0.05

    Cap at 1.0.

    Args:
        bias_coverage: Social bias label -> list of source names.
        econ_bias_coverage: Economic policy bias label -> list of source names.
        source_chunks: Raw source chunks for additional signals.

    Returns:
        Float divergence score 0.0-1.0.
    """
    reserved_keys = {"__econ_schools__", "__econ_bias__"}
    if not bias_coverage or sum(len(v) for k, v in bias_coverage.items() if k not in reserved_keys) <= 1:
        return 0.0

    pole_labels = set(bias_coverage.keys()) - reserved_keys
    score = 0.0

    # --- Social/political bias component (max 0.50) ---
    has_left = "left" in pole_labels
    has_right = "right" in pole_labels
    has_state = "state-affiliated" in pole_labels

    if has_left and has_right:
        score += 0.40
    elif len(pole_labels) >= 2:
        score += 0.20

    if has_state:
        score += 0.10

    # --- Economic policy bias component (max 0.30) ---
    has_progressive = bool(econ_bias_coverage.get(ECON_BIAS_PROGRESSIVE))
    has_market = bool(econ_bias_coverage.get(ECON_BIAS_MARKET))
    has_center = bool(econ_bias_coverage.get(ECON_BIAS_CENTER))
    active_biases = {b for b in econ_bias_coverage if b != ECON_BIAS_STATE}

    if has_progressive and has_market:
        score += 0.25
    elif len(active_biases) >= 2:
        score += 0.10
    if has_center and (has_progressive or has_market):
        score += 0.05

    # --- Source diversity bonus (max 0.20) ---
    non_anglophone = sum(
        1 for c in source_chunks if c.get("metadata", {}).get("language", "en") not in ANGLOPHONE_LANGUAGES
    )
    if non_anglophone >= 1:
        score += 0.10
    if non_anglophone >= 3:
        score += 0.05

    layers = {c.get("metadata", {}).get("layer", 0) for c in source_chunks}
    if len(layers) >= 3:
        score += 0.05

    return min(score, 1.0)
