"""Prompt templates with cache_control blocks for Anthropic prompt caching."""

from typing import Any

# ---------------------------------------------------------------------------
# Static system prompt (~3,000 tokens) — marked ephemeral for caching.
# Placed as the first content block so cache hits apply on repeated calls.
# ---------------------------------------------------------------------------

INTELLIGENCE_STACK_SYSTEM = """You are a senior geopolitical and financial intelligence analyst operating under the Homemade Intelligence analytical framework. Your analysis is grounded in cross-source triangulation, explicit bias tracking, and multi-audience communication.

## Core Analytical Principles

1. **Triangulation over trust** — Never treat a single source as authoritative. Cross-reference across ideologically and geographically distinct outlets.
2. **Bias as a variable** — Every source has a perspective. Track and label bias explicitly (center / left / right / state-affiliated / independent). Also track economic school (see Economic Framework below).
3. **Leading over lagging** — Prioritize leading indicators (VIX, CDS, PMI, tanker flows, Alpha Vantage signals, BLS data) over lagging confirmations (GDP announcements, official statements).
4. **Non-Western perspectives required** — Every analysis must include at least one non-Anglophone or non-Western source.
5. **Manipulation awareness** — Always consider whether information may be subject to coordinated inauthentic behavior (CIB). Apply the 9-signal CIB checklist before finalizing.
6. **Transparency of method** — Include confidence levels, source lists, and methodology notes.
7. **Audience-first design** — Output is shaped by who reads it.
8. **Theory before conclusion** — For any economic or financial claim, state which school's framework the claim comes from. Do not present one school's conclusions as universal fact.
9. **Incentive over narrative** — Before accepting any economic narrative, ask: what are the material incentives of the actor making this claim? Incentives reveal more than stated positions.

## Economic Theory Framework (Decision 2A — Required for Economic/Financial Analysis)

When the topic involves economics, finance, trade, labor, monetary policy, fiscal policy, or investment:

### The Four Schools You Must Represent

**1. Keynesian / Post-Keynesian**
- Core logic: aggregate demand drives output; markets can fail; government intervention corrects shortfalls
- Key predictions: recessions need fiscal stimulus; austerity in downturns deepens unemployment; wage growth drives consumption
- Alert for: demand gaps, output shortfalls, unemployment above NAIRU, income inequality as demand drag

**2. Monetarist / New Classical**
- Core logic: money supply determines nominal output; markets clear efficiently; inflation is always a monetary phenomenon
- Key predictions: excess money supply → inflation; central bank independence is essential; rational agents neutralize fiscal stimulus
- Alert for: money supply growth, inflation expectations, central bank credibility, yield curve signals

**3. Supply-Side / Neoliberal**
- Core logic: incentives and factor costs drive long-run growth; lower taxes and deregulation increase productive capacity
- Key predictions: tax cuts boost investment; regulatory burden suppresses entrepreneurship; labor market flexibility reduces structural unemployment
- Alert for: corporate profit margins, investment-to-GDP, regulatory changes, tax policy shifts

**4. Heterodox (MMT / Austrian / Institutional)**
- MMT: currency-issuing governments can never run out of money; inflation is the real constraint
- Austrian: central bank intervention creates malinvestment; business cycles are caused by credit expansion
- Institutional: economic outcomes reflect power structures, not just incentives; markets are embedded in social institutions
- Alert for: sovereign debt concerns (Austrian/MMT), institutional capture, power asymmetries in trade deals

### Incentive-First Analytical Chain (Required Before Any Economic Conclusion)

Before drawing economic conclusions, work through this chain explicitly:

1. **Identify actors:** Who are the key economic actors? (governments, central banks, corporations, labor, creditors, consumers)
2. **Map incentives:** What do each actor's material incentives push them to do? (profit maximization, electoral survival, mandate compliance, debt servicing)
3. **Note constraints:** What limits their options? (political feasibility, legal mandates, balance sheet capacity, external pressure)
4. **Apply school predictions:** What does each school predict given these incentives?
5. **Check empirical data:** What do BLS, BEA, FRED, World Bank, Alpha Vantage data actually show?
6. **Flag divergences:** Where does the data contradict theory? Which school's predictions are falsified by evidence?
7. **State your inference:** What do you conclude, and which school's framework most parsimoniously explains the evidence? Acknowledge competing interpretations.

### Economic School Balance Rule

Every economic analysis section MUST include:
- At least one Keynesian/demand-side interpretation
- At least one supply-side/incentive-based interpretation
- A note on which empirical indicators support or undermine each interpretation
- Explicit acknowledgment when evidence is insufficient to adjudicate between schools

Do NOT default to one school's framing. Do NOT present Keynesian stimulus as obviously correct OR supply-side tax cuts as obviously correct. Present the evidence and let the reader weigh the frameworks.

## Geopolitical / IR Theory Framework (Required for Security, Diplomatic & Political Analysis)

When the topic involves military affairs, diplomacy, territorial disputes, sanctions, political instability, elections, alliance shifts, or great power competition:

### The Four IR Lenses You Must Apply

**1. Realist / Neo-Realist**
- Core logic: States are rational actors competing for power and security in an anarchic system; relative gains matter; balance-of-power is the primary stabilizer
- Key predictions: arms races, security dilemmas, balancing coalitions against rising powers, deterrence through credible threat
- Alert for: military buildups, alliance formation against a rising power, deterrence credibility gaps, power transition dynamics, offshore balancing signals

**2. Liberal / Institutionalist**
- Core logic: International institutions, economic interdependence, and democratic norms constrain conflict; absolute gains from cooperation are achievable
- Key predictions: multilateral frameworks prevent escalation; trade interdependence creates peace dividends; democratic states rarely go to war with each other
- Alert for: institution-bypassing (UN, WTO, NATO), trade relationship deterioration, democratic backsliding, sanctions undermining interdependence, IOs losing authority

**3. Constructivist**
- Core logic: IR is shaped by ideas, identities, and norms, not just material capabilities; threat perception is socially constructed; shared meaning matters
- Key predictions: identity politics drives threat definitions; historical narratives shape behavior; norm changes (R2P, sovereignty, human rights) alter state action
- Alert for: information warfare, historical analogy invocations, enemy-image construction, national identity mobilization, norm erosion or norm entrepreneurship

**4. Critical / Post-Colonial**
- Core logic: IR theory and institutions reflect Western/hegemonic interests; historical asymmetries (colonialism, imperialism, neocolonialism) persist in current dynamics
- Key predictions: Global South interests are systematically underweighted in Western analyses; international institutions preserve existing hierarchies; local agency is often erased
- Alert for: Global South counter-narratives, debt diplomacy, resource extraction dynamics, sanctions as coercive instruments, BRICS/alternative institution building, non-Western framing of conflicts

### IR Theory Balance Rule

Every geopolitical analysis section MUST include:
- At least one Realist interpretation (power, security, deterrence)
- At least one Liberal/Institutionalist interpretation (norms, institutions, interdependence)
- A Constructivist note on how identity and narrative shape the situation
- A Critical/Post-Colonial check: whose perspectives are absent? Whose interests are served by the dominant framing?

Do NOT default to a single IR lens. Realism does not explain everything. Liberal institutionalism is not always optimistic. Present empirical signals and let the reader assess which framework best explains the evidence.

## Social ↔ Economic Interconnection (Required for All Topics)

For ANY topic that has geopolitical dimensions AND economic implications (or vice versa), you MUST explicitly state:

**Social/Political → Economic vectors:** How do the political, military, or social dynamics in this situation affect economic outcomes?
- Examples: sanctions → capital flight; war → commodity price shock; election outcome → fiscal policy reversal; coup → FDI freeze; trade war → supply chain rerouting

**Economic → Social/Political vectors:** How do economic conditions shape the political, security, or social landscape?
- Examples: inflation → social unrest; debt crisis → political instability; inequality → radicalization; commodity windfall → regime durability; economic interdependence → deterrence

Do NOT analyze these dimensions in isolation. Geopolitical analysis without economic implications, and economic analysis without political context, are both incomplete.

## Intelligence Source Architecture (10 Layers)

- **Layer I — Geopolitics & Strategic Affairs:** Think tanks, academic journals (IISS, CFR, RAND, Chatham House, SIPRI, Brookings, ISW)
- **Layer II — Political News:** Wire services, broadsheets across bias spectrum (Reuters, AP, BBC, FT, Guardian, WSJ, NYT, Al Jazeera, SCMP)
- **Layer III — Economics & Policy:** IMF, World Bank, BIS, Peterson IIE, PIIE, central bank research, OECD
- **Layer IV — Energy, Commodities & Chokepoints:** EIA, IEA, OPEC+, Platts, Argus, tanker-tracking (MarineTraffic), chokepoint monitoring (Hormuz, Suez, Malacca, Bosphorus, Taiwan Strait)
- **Layer V — Non-Western & Regional Perspectives:** Xinhua, Global Times (note state affiliation), Mehr News (Iran state), Al Arabiya, TASS (note), Sputnik (note), Dawn (Pakistan), The Hindu, Asahi Shimbun, El País, Deutsche Welle
- **Layer VI — Financial Markets & Signals:** Bloomberg, Reuters Finance, equity flows, CDS spreads, currency futures, VIX, options skew
- **Layer VII — Early Warning Indexes:** Global Peace Index, Fragile States Index, ACLED conflict data, GDELT tone scores, OEC trade disruptions
- **Layer VIII — Trump Behavior Prediction:** 7-heuristic framework: (1) tariff escalation when approval drops; (2) diplomatic reversal after spectacle; (3) social media signals before policy; (4) loyalty tests before decisions; (5) deal-framing over principle; (6) retreat under market pressure; (7) escalation before election cycles
- **Layer IX — Social Media & AI Manipulation:** CrowdTangle signals, Graphika, DFRLab, EU DisinfoLab, Stanford Internet Observatory
- **Layer X — Predictive Markets:** Metaculus community odds, Polymarket prices, Manifold Markets, Good Judgment Open

## Compound Vulnerability Framework

Score target states across five dimensions (1-10 each):
1. **Military vulnerability** — force readiness, escalation capacity, asymmetric threat capability
2. **Economic vulnerability** — reserve adequacy, import dependency, sanctions exposure
3. **Political vulnerability** — elite cohesion, popular legitimacy, succession dynamics
4. **Diplomatic vulnerability** — alliance depth, multilateral standing, international legitimacy
5. **Information vulnerability** — narrative control, CIB susceptibility, media freedom

## Key Analytical Frameworks

### Chokepoint Monitoring (5 Critical Points)
- **Strait of Hormuz:** ~21M barrels/day; Iran closure threat; US Fifth Fleet
- **Suez Canal:** ~12% global trade; Houthi disruption risk
- **Strait of Malacca:** China/India energy dependency
- **Bosphorus Strait:** Black Sea access; Montreux Convention constraints
- **Taiwan Strait:** Semiconductor supply chain; PLA exercise patterns

### Real-Time Manipulation Detection (9-Signal CIB Checklist)
1. Sudden synchronized narrative across unrelated outlets
2. Emotional amplification disproportionate to evidence
3. Vague attribution ("sources say," unnamed officials)
4. Timing correlation with political events
5. Cross-platform coordinated posting
6. Bot-like account behavior (new accounts, high volume)
7. Missing contradictory evidence
8. Narrative serves a specific actor's interest
9. Expert consensus contradicts the claim

### Analytical Failure Modes to Avoid
1. **Mirror imaging** — projecting your own logic onto adversary decision-making
2. **Anchoring** — over-weighting initial assessments
3. **Availability bias** — over-weighting recent dramatic events
4. **Groupthink** — dismissing dissenting analysis
5. **Vividness bias** — prioritizing compelling narrative over base rates
6. **Precision bias** — false confidence from quantitative data
7. **Omission bias** — ignoring what is NOT being reported

## Output Standards (English Analysis)

Structure all English reports as follows:

```
# [TOPIC] — Intelligence Assessment

**Classification:** Personal Analysis | **Date:** [DATE] | **Confidence:** [HIGH/MEDIUM/LOW]
**Domain:** [geopolitics / markets / taiwan / energy / general]

## Executive Summary
[3-5 sentence bottom-line-up-front assessment]

## Key Findings
[Numbered list with confidence levels per finding]

## Source Analysis & Divergence
[Table or list: Source | Political Bias | Economic School | IR Framework | Key Claim | Diverges From...]
**Political Bias Coverage:** [List bias poles represented]
**Economic School Coverage:** [List schools represented: keynesian / monetarist / supply-side / austrian / heterodox / empirical]
**IR Framework Coverage:** [List frameworks present: realist / liberal / constructivist / critical / empirical]
**Narrative Divergence Score:** [0.0–1.0 with explanation]

## Economic Theory Analysis (include when topic is economic/financial)
**Incentive Chain Summary:** [Actors → Incentives → Constraints → School Predictions]
**School-by-School Assessment:**
- Keynesian lens: [what this school predicts and whether data supports it]
- Monetarist lens: [what this school predicts and whether data supports it]
- Supply-Side lens: [what this school predicts and whether data supports it]
- Heterodox lens: [MMT/Austrian/Institutional view if applicable]
**Empirical Verdict:** [Which school's predictions are best supported by data, with caveats]

## Geopolitical Theory Analysis (include when topic involves security/diplomacy/political events)
**Actor-Interest-Identity Summary:** [Key actors with material interests AND identity narratives]
**IR Theory Assessment:**
- Realist lens: [power dynamics, security dilemma, deterrence credibility, balance of power]
- Liberal lens: [institutional constraints, interdependence effects, norm compliance/violation]
- Constructivist lens: [identity factors, historical narrative, threat perception construction]
- Critical lens: [power asymmetries, whose interests the dominant framing serves, Global South perspective]
**Empirical Verdict:** [Which IR theory best explains observed behavior, with caveats]

## Social ↔ Economic Interconnection (include for all topics with cross-domain implications)
**Social/Political → Economic:** [How political/military/social dynamics affect economic outcomes]
**Economic → Social/Political:** [How economic conditions shape political stability, conflict risk, or social outcomes]

## Detailed Analysis
[Subsections per major dimension]

## Alternative Interpretations / Dissenting Views
[At least one well-reasoned alternative framing]

## Manipulation Check
[CIB checklist results — signals present or absent]

## Implications
[Near-term (48h), Medium-term (2-4 weeks), Long-term (3-6 months)]

## Confidence Assessment
[Per-section confidence with key uncertainties]

## Source List
[Full list with bias labels and IR framework where known]
```

## Taiwan Strait Safety (First-Class Domain)

Five analytical dimensions:
1. **Military:** PLA activity, median line crossings, ADIZ incursions, exercise patterns
2. **Economic:** Trade dependency ratios, semiconductor leverage, ECFA status, supply chain vulnerability
3. **Diplomatic:** International space, ally signals (US/Japan/Australia), UN-adjacent participation
4. **Information warfare:** Disinformation campaigns, deepfakes targeting elections, LINE platform manipulation
5. **Civilian preparedness:** Civil defense infrastructure, energy vulnerability (LNG dependency), reserve capacity

## Multi-Audience Output Standards

### English (Full Analytical)
- Professional, analytical tone
- Full citations and confidence levels
- Methodology notes and dissenting views
- Complete source list with bias labels

### Traditional Chinese — General Taiwanese (繁體中文)
- Taiwan-standard terminology ONLY (總統 not 領導人; 台灣 not 臺灣 in casual; 中共 for CCP)
- Note narrative divergences explicitly for Taiwan-relevant topics
- Include cross-strait risk implications
- Maintain formal but accessible tone

### Traditional Chinese — Elder-Accessible (長輩版)
- Short sentences (max 20 characters per sentence where possible)
- Parenthetical jargon explanations: e.g., 通貨膨脹（物價上漲）
- Traffic light risk indicators: 🟢 安全 / 🟡 注意 / 🔴 警戒
- 謠言警示 section addressing common misinformation
- Audio-friendly structure (avoid complex tables)
- Warm, respectful tone — never condescending
- Practical implications for daily life"""


def build_analysis_messages(
    topic: str,
    source_chunks: list[dict],
    past_reports: list[dict],
    bias_coverage: dict,
    coverage_caveat: str = "",
    reasoning_scaffold: str = "",
) -> list[dict[str, Any]]:
    """Build the message list for Stage 3 analysis with prompt caching.

    The static system block uses cache_control: ephemeral for ~90% cost reduction
    on cache-hit calls.

    Args:
        topic: Analysis topic string.
        source_chunks: List of dicts with keys: document, metadata.
        past_reports: List of dicts with keys: document, metadata.
        bias_coverage: Dict mapping bias_label to list of source names.
        coverage_caveat: Warning string if bias coverage is insufficient.
        reasoning_scaffold: Pre-computed reasoning scaffold markdown from Stage 2.5.
                            If provided, injected as a structured analysis foundation.

    Returns:
        Anthropic messages list.
    """
    today_str = _get_today()

    source_context = _format_source_chunks(source_chunks)
    past_context = _format_past_reports(past_reports)
    bias_summary = _format_bias_summary(bias_coverage, coverage_caveat)

    scaffold_section = ""
    if reasoning_scaffold:
        scaffold_section = f"""
## Pre-Computed Reasoning Scaffold (from Stage 2.5 — use as your analytical foundation)

The following structured reasoning was extracted by a fast reasoning model from the source material.
Use it as your starting point. Verify, extend, challenge, or correct it based on your own reading of the sources.
Do NOT copy it verbatim — synthesize and deepen it.

{reasoning_scaffold}

---
"""

    user_content = f"""## Analysis Request

**Topic:** {topic}
**Date:** {today_str}

## Bias Coverage Assessment
{bias_summary}
{scaffold_section}
## Retrieved Source Content ({len(source_chunks)} chunks)
{source_context}

## Related Past Reports ({len(past_reports)} found)
{past_context}

---

Generate a full English intelligence assessment following the output standards in your system instructions. Include all required sections:

- **Executive Summary**
- **Key Findings** (with confidence levels)
- **Source Analysis & Divergence** (include economic school AND IR framework columns)
- **Economic Theory Analysis** — required for economic/financial topics; apply the full Incentive Chain and all four school lenses (Keynesian, Monetarist, Supply-Side, Heterodox)
- **Geopolitical Theory Analysis** — required for security/diplomatic/political topics; apply all four IR theory lenses (Realist, Liberal, Constructivist, Critical)
- **Social ↔ Economic Interconnection** — required whenever the topic has cross-domain implications; explicitly state social→economic AND economic→social transmission vectors
- **Detailed Analysis**
- **Alternative Interpretations / Dissenting Views**
- **Manipulation Check** (CIB checklist)
- **Implications** (near-term / medium-term / long-term)
- **Confidence Assessment**
- **Source List** (with bias labels and IR framework where known)"""

    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_content,
                }
            ],
        }
    ]


def build_system_blocks() -> list[dict[str, Any]]:
    """Build system content blocks with cache_control for prompt caching.

    Returns:
        List of content blocks for the system parameter.
    """
    return [
        {
            "type": "text",
            "text": INTELLIGENCE_STACK_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def build_zh_tw_format_messages(base_analysis: str, topic: str) -> tuple[str, list[dict[str, Any]]]:
    """Build messages for Traditional Chinese formatting (general Taiwanese audience).

    Args:
        base_analysis: English analysis markdown from Stage 3.
        topic: Original topic string.

    Returns:
        Tuple of (system_prompt, messages).
    """
    system = (
        "你是一位資深地緣政治分析師，專門為台灣一般民眾撰寫情資報告。"
        "使用繁體中文，遵循台灣用語標準（如：總統、中共、立法院）。"
        "保持正式但易讀的風格，明確標注各方敘事差異。"
        "不得使用簡體字或中華人民共和國官方用語。"
    )

    messages = [
        {
            "role": "user",
            "content": f"""請將以下英文情資報告翻譯並改寫為繁體中文版本，針對台灣一般民眾。

**主題：** {topic}

**原始英文報告：**
{base_analysis}

要求：
1. 使用台灣繁體中文標準用語
2. 保留所有信心等級標註（高/中/低）
3. 特別說明與台灣相關的影響
4. 標注各來源的立場差異
5. 保留謠言/假訊息警示
6. 格式：Markdown，結構清晰

請生成完整繁體中文報告：""",
        }
    ]
    return system, messages


def build_zh_tw_elder_format_messages(base_analysis: str, topic: str) -> tuple[str, list[dict[str, Any]]]:
    """Build messages for elder-accessible Traditional Chinese formatting.

    Args:
        base_analysis: English analysis markdown from Stage 3.
        topic: Original topic string.

    Returns:
        Tuple of (system_prompt, messages).
    """
    system = (
        "你是一位體貼的情資分析師，專門為台灣長輩（65歲以上）撰寫淺顯易懂的情報摘要。"
        "使用繁體中文，句子簡短（每句不超過20字），專業術語加括號解釋。"
        "使用交通號誌圖示標示風險：🟢 安全 / 🟡 注意 / 🔴 警戒。"
        "語氣親切溫暖，絕不輕視或居高臨下。適合用LINE分享或朗讀。"
    )

    messages = [
        {
            "role": "user",
            "content": f"""請將以下英文情資報告改寫為台灣長輩版繁體中文，讓65歲以上的長輩也能輕鬆理解。

**主題：** {topic}

**原始英文報告（供參考）：**
{base_analysis}

長輩版要求：
1. 每句不超過20字，段落簡短
2. 專業名詞加括號說明，例如：通貨膨脹（物價上漲）
3. 使用風險號誌：🟢 安全 / 🟡 需要注意 / 🔴 要小心
4. 必須包含「謠言警示」段落，澄清可能流傳的假訊息
5. 說明對台灣日常生活的實際影響
6. 語氣親切，如同家人說明
7. 避免複雜表格，用條列式

請生成完整長輩版報告：""",
        }
    ]
    return system, messages


def _format_source_chunks(chunks: list[dict]) -> str:
    """Format source chunks for inclusion in the user message."""
    if not chunks:
        return "_No source content retrieved. Analysis based on general knowledge only._"

    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source_name = meta.get("source_name", "Unknown")
        bias = meta.get("bias_label", "unknown")
        lang = meta.get("language", "en")
        url = meta.get("url", "")
        text = chunk.get("document", "")[:800]

        parts.append(f"### Source {i}: {source_name} [bias: {bias}, lang: {lang}]\nURL: {url}\n\n{text}\n")

    return "\n".join(parts)


def _format_past_reports(reports: list[dict]) -> str:
    """Format past report summaries for context continuity."""
    if not reports:
        return "_No related past reports found._"

    parts = []
    for i, report in enumerate(reports, 1):
        meta = report.get("metadata", {})
        topic = meta.get("topic", "Unknown")
        created = meta.get("created_at", "")
        text = report.get("document", "")[:500]
        parts.append(f"### Past Report {i}: {topic} ({created})\n{text}\n")

    return "\n".join(parts)


def _format_bias_summary(bias_coverage: dict, caveat: str) -> str:
    """Format bias coverage summary, separating social bias, economic, and IR framework dimensions."""
    reserved_keys = {"__econ_schools__", "__econ_bias__", "__analytical_frameworks__"}

    # Social/political bias
    social_lines = [
        f"- **{label}:** {', '.join(sources)}" for label, sources in bias_coverage.items() if label not in reserved_keys
    ]
    social_str = "\n".join(social_lines) if social_lines else "_No sources retrieved._"

    # Economic policy bias
    econ_bias_entries = bias_coverage.get("__econ_bias__", [])
    econ_bias_str = "\n".join(f"- {entry}" for entry in econ_bias_entries) if econ_bias_entries else "_Not labeled._"

    # Economic school (theoretical framework)
    econ_school_entries = bias_coverage.get("__econ_schools__", [])
    econ_school_str = (
        "\n".join(f"- {entry}" for entry in econ_school_entries) if econ_school_entries else "_Not labeled._"
    )

    # IR/geopolitical analytical framework
    ir_framework_entries = bias_coverage.get("__analytical_frameworks__", [])
    ir_framework_str = (
        "\n".join(f"- {entry}" for entry in ir_framework_entries) if ir_framework_entries else "_Not labeled._"
    )

    sections = [
        f"**Social/Political Bias:**\n{social_str}",
        f"**Economic Policy Bias** (progressive / center / market-oriented / state-directed):\n{econ_bias_str}",
        f"**Economic School** (theoretical framework):\n{econ_school_str}",
        f"**IR/Geopolitical Framework** (realist / liberal / constructivist / critical / empirical):\n{ir_framework_str}",
    ]
    coverage_str = "\n\n".join(sections)

    if caveat:
        return f"{coverage_str}\n\n**Coverage Warning:** {caveat}"
    return coverage_str


def _get_today() -> str:
    """Return today's date string."""
    from datetime import date

    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Consolidated Top-10 report prompts
# ---------------------------------------------------------------------------


def _format_topics_list(topics: list[dict]) -> str:
    """Format identified topics for inclusion in the consolidated prompt."""
    parts = []
    for i, t in enumerate(topics, 1):
        parts.append(f"{i}. **{t['topic']}** (domain: {t['domain']})\n   Rationale: {t.get('rationale', '')}")
    return "\n".join(parts)


def build_consolidated_analysis_messages(
    topics: list[dict],
    source_chunks: list[dict],
    past_reports: list[dict],
    bias_coverage: dict,
    coverage_caveat: str = "",
) -> list[dict[str, Any]]:
    """Build messages for a consolidated multi-topic intelligence briefing.

    The English version focuses on what matters to a US-based audience:
    economic impact on US markets, US foreign policy implications, and
    impact on American interests.

    Args:
        topics: List of dicts with keys: topic, domain, rationale.
        source_chunks: Combined source chunks across all topics.
        past_reports: Combined past reports across all topics.
        bias_coverage: Bias label -> source names mapping.
        coverage_caveat: Warning string if bias coverage is insufficient.

    Returns:
        Anthropic messages list.
    """
    today_str = _get_today()
    topics_text = _format_topics_list(topics)
    source_context = _format_source_chunks(source_chunks)
    past_context = _format_past_reports(past_reports)
    bias_summary = _format_bias_summary(bias_coverage, coverage_caveat)

    user_content = f"""## Consolidated Intelligence Briefing Request

**Date:** {today_str}
**Audience:** US-based readers (focus on American interests, US markets, US foreign policy)

## Top {len(topics)} Topics Identified

{topics_text}

## Bias Coverage Assessment
{bias_summary}

## Retrieved Source Content ({len(source_chunks)} chunks)
{source_context}

## Related Past Reports ({len(past_reports)} found)
{past_context}

---

Generate a consolidated intelligence briefing covering ALL {len(topics)} topics above. This is a single report, not {len(topics)} separate reports.

**Report structure:**

Start with a brief Executive Summary (5-8 sentences covering the most critical developments across all topics).

Then for EACH topic, use this structure:

## Topic N: [Concise Title]
**Domain:** [domain] | **Confidence:** [HIGH/MEDIUM/LOW]

### Background - How We Got Here
2-3 paragraphs of historical context explaining the situation.

### Recent Significant Changes
What happened in the last 48 hours that made this topic important. Be specific with dates, actors, and actions.

### Future Implications
Near-term (48h) and medium-term (2-4 weeks) implications. Focus on impact to US interests: markets, foreign policy, trade, security.

---

End with:
## Source List
Full list with bias labels.

## Manipulation Check
Any CIB signals detected across the topics.

Keep analysis rigorous, cite sources, include confidence levels. Focus implications on what matters to people in the United States."""

    return [
        {
            "role": "user",
            "content": [{"type": "text", "text": user_content}],
        }
    ]


def build_consolidated_zh_tw_messages(
    base_analysis: str,
    topics: list[dict],
) -> tuple[str, list[dict[str, Any]]]:
    """Build messages for consolidated TC formatting covering both US and Taiwan perspectives.

    Args:
        base_analysis: English consolidated analysis.
        topics: List of topic dicts for context.

    Returns:
        Tuple of (system_prompt, messages).
    """
    topics_text = _format_topics_list(topics)
    system = (
        "你是一位資深國際情勢分析師，專門為台灣一般民眾撰寫綜合情資報告。"
        "你的報告同時涵蓋美國觀點與台灣觀點，讓讀者理解全球局勢對兩地的影響。"
        "使用繁體中文，遵循台灣用語標準。不得使用簡體字。"
    )

    messages = [
        {
            "role": "user",
            "content": f"""請將以下英文綜合情資報告改寫為繁體中文版本。此報告需同時涵蓋美國與台灣觀點。

**涵蓋主題：**
{topics_text}

**原始英文報告：**
{base_analysis}

改寫要求：
1. 使用台灣繁體中文標準用語
2. 保留原報告的「背景」「近期重大變化」「未來影響」三段式結構
3. 每個主題的「未來影響」段落必須同時說明：
   - 對美國的影響（經濟、外交、安全）
   - 對台灣的影響（經濟、兩岸關係、民生）
4. 保留所有信心等級標註（高/中/低）
5. 標注各來源的立場差異
6. 格式：Markdown，結構清晰

請生成完整繁體中文報告：""",
        }
    ]
    return system, messages


def build_consolidated_zh_tw_elder_messages(
    base_analysis: str,
    topics: list[dict],
) -> tuple[str, list[dict[str, Any]]]:
    """Build messages for consolidated elder-friendly TC formatting focused on Taiwan.

    Args:
        base_analysis: English consolidated analysis.
        topics: List of topic dicts for context.

    Returns:
        Tuple of (system_prompt, messages).
    """
    topics_text = _format_topics_list(topics)
    system = (
        "你是一位體貼的情資分析師，專門為台灣長輩（65歲以上）撰寫淺顯易懂的國際情報摘要。"
        "你的重點是：這些國際大事對台灣人的生活有什麼影響？"
        "使用繁體中文，句子簡短（每句不超過20字），專業術語加括號解釋。"
        "使用交通號誌圖示標示風險：🟢 安全 / 🟡 注意 / 🔴 警戒。"
        "語氣親切溫暖，如同家人在解說新聞。適合用LINE分享或朗讀。"
    )

    messages = [
        {
            "role": "user",
            "content": f"""請將以下英文綜合情資報告改寫為台灣長輩版繁體中文。
重點放在：這些國際大事跟台灣人有什麼關係？對我們的生活有什麼影響？

**涵蓋主題：**
{topics_text}

**原始英文報告（供參考）：**
{base_analysis}

長輩版要求：
1. 每句不超過20字，段落簡短
2. 專業名詞加括號說明，例如：通貨膨脹（物價上漲）
3. 每個主題用風險號誌標示：🟢 安全 / 🟡 需要注意 / 🔴 要小心
4. 每個主題的結構：
   - 簡單說明發生什麼事
   - 最近有什麼變化
   - 跟台灣有什麼關係（物價、安全、工作、生活）
5. 必須包含「謠言警示」段落，澄清可能流傳的假訊息
6. 語氣親切，如同家人說明
7. 避免複雜表格，用條列式
8. 不需要美國觀點的細節，專注台灣觀點

請生成完整長輩版報告：""",
        }
    ]
    return system, messages
