# Skill: select-sources

Select the source set for a report using the Intelligence Stack v2.0 layer structure.

## Input

- Topic description
- Active geopolitical or market events
- Target audience (`english` | `zh-tw` | `zh-tw-elder`)

## Action

Select sources from the Intelligence Stack v2.0 layer structure.
For each report the minimum coverage is:

| Layer | Required sources (minimum) |
| ----- | -------------------------- |
| Layer II — Western Anglophone news | ≥ 2 ideologically distinct outlets (e.g., Reuters + FT) |
| Layer III — Economics & Policy | ≥ 1 institutional source (IMF / BIS / OECD) **AND** for economic topics: ≥ 1 demand-side school source (Keynesian/heterodox) + ≥ 1 supply-side school source (supply-side/monetarist/Austrian) |
| Layer IV — Energy & Commodities | ≥ 1 source if any Middle East, energy, or trade event is active |
| Layer V — Financial Markets | ≥ 2 leading indicators (VIX, CDS, PMI, BDTI, yield curve); primary data sources (BLS, BEA, Alpha Vantage) preferred over derived reporting |
| Layer VI — Non-Western Sources | ≥ 1 non-Anglophone outlet (e.g., Nikkei Asia, Al Jazeera, SCMP) |
| Layer VII — Early Warning Indexes | ≥ 2 quantitative signals |
| Layer VIII — Trump Behavior Stack | Required if any US executive action is a material risk factor |

### Economic School Coverage Rule

For any report that includes economic or financial analysis, the source set **must** represent at least two of the four recognized economic schools:

| School | Representative sources |
| ------ | ---------------------- |
| Keynesian / Post-Keynesian | Project Syndicate, Bruegel, PIIE, VoxEU/CEPR, Brookings |
| Monetarist / New Classical | Hoover Institution, OECD, IMF (macro stability lens) |
| Supply-Side / Neoliberal | AEI, Heritage Foundation, Wall Street Journal editorial |
| Heterodox (MMT / Austrian / Institutional) | Cato Institute, Marginal Revolution, NBER empirical |

If only one school is represented, record the gap in the **Source gaps** section and pass to `audit-bias` for flagging.

### Economic Policy Bias Coverage Rule

Separately from economic school, ensure both policy-direction perspectives are covered:

| Policy direction | Representative sources |
| ---------------- | ---------------------- |
| Progressive (government intervention, redistribution) | Brookings, PIIE, Guardian, The Hindu |
| Market-oriented (free markets, deregulation) | FT, Economist, AEI, Heritage, Hoover, Cato |
| State-directed (China, Russia, Gulf) | Global Times, TASS, Arab News — use as narrative sources only |

Note: A source can be economically market-oriented but socially centrist (FT) or socially conservative (Heritage). These are independent dimensions.

### IR / Analytical Framework Coverage Rule

For any report involving geopolitical, security, diplomatic, or military topics, the source set **must** represent ≥ 2 distinct IR analytical frameworks:

| Framework | Core assumptions | Representative sources |
| --------- | ---------------- | ---------------------- |
| Realist | Power, national interest, security dilemmas, balance of power | War on the Rocks, RAND (security), AEI (foreign policy), Heritage (defense) |
| Liberal / Institutionalist | Institutions, norms, interdependence, democratic peace | Foreign Affairs (CFR), Brookings, Lawfare, IMF, World Bank |
| Constructivist | Ideas, identities, norms, social construction of threats | Academic IR journals, analysis of narrative and identity politics |
| Critical / Post-Colonial | Power structures, hegemony, Global South agency, historical asymmetries | Al Jazeera, The Hindu, Rappler, non-Western outlets |
| Empirical | Data-driven; no dominant theory | ISW, Reuters, SCMP, GDELT signals |

If only realist sources are selected, note the gap. Constructivist and critical perspectives are especially important for Taiwan cross-strait analysis (identity narratives) and Global South topics.

**Note:** `economic_school` and `analytical_framework` are independent dimensions. A source can have both (e.g., Brookings: keynesian + liberal) or only one (e.g., War on the Rocks: realist only, no economic school).

## Output

A structured source list grouped by layer, ready as input for `audit-bias`.
