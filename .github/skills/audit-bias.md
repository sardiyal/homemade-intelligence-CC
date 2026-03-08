# Skill: audit-bias

Audit a candidate source list for ideological balance, geographic diversity, and analytical
failure modes before any drafting begins.

## Input

Source list produced by `select-sources`.

## Action

Answer every question below.
For each "No", either add the missing source or record a named gap under **Source gaps** in
the report.

- [ ] Does the collection span ≥ 2 distinct ideological perspectives?
- [ ] Is ≥ 1 non-Anglophone, non-Western source included?
- [ ] Are leading indicators (VIX, CDS, PMI, tanker flows) represented alongside lagging ones?
- [ ] Have all six Analytical Failure Modes been checked?
  - Anglophone epistemic capture
  - Negotiation optimism bias
  - Monocausal attribution
  - Recency bias
  - Confirmation bias
  - Energy market blindspot
- [ ] Are state-media sources (RT, Xinhua, Global Times) used only as narrative trackers,
      never as factual claims?
- [ ] Are all sources present in Intelligence Stack v2.0, or explicitly flagged if unlisted?
- [ ] **Economic school balance:** Does the collection include ≥ 1 demand-side/Keynesian source
      AND ≥ 1 supply-side/monetarist/Austrian source? If only one school is represented, flag
      the gap under **Source gaps** and note which theoretical perspectives are absent.
- [ ] **Economic policy bias balance:** Does the collection include both progressive-leaning and
      market-oriented sources? State-directed sources (Global Times, TASS, Arab News) are noted
      but do not count toward this balance. Flag if only one policy direction is represented.
- [ ] **IR theory balance (for geopolitical/security topics):** Does the collection represent
      ≥ 2 distinct IR analytical frameworks? Minimum: at least one realist source (power/security
      focus, e.g. War on the Rocks, RAND military) AND one non-realist source (liberal/institutionalist
      e.g. Foreign Affairs, Brookings; or constructivist; or critical/post-colonial e.g. Al Jazeera,
      The Hindu). If only one framework is represented, flag the gap under **Source gaps**.
- [ ] **Incentive check:** For any economic or financial claim, has the material incentive of
      the actor making the claim been identified? Incentives should be stated before conclusions.
- [ ] **Social↔Economic interconnection:** For hybrid topics, are sources present that illuminate
      both the political/social dimension AND the economic dimension? A source set that only covers
      military movements without economic implications, or only covers markets without political
      context, is incomplete.

## Output

A pass/fail audit result with gap notes, ready to include as the **Source collection and bias
audit summary** section of the report.
