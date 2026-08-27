# Changelog

All notable changes to this project. Format follows [Keep a Changelog](https://keepachangelog.com/),
versioning follows [Semantic Versioning](https://semver.org/).

## [0.7.0] — 2026-08-27

Gene assignment from OMIA — phase 2 of the data expansion plan. The dataset now
names the causal gene where one is known *for that breed*, and every symbol
carries the OMIA record it was read from.

### Added
- Re-runnable pipeline: `tools/fetch_omia.sh` (dog phene index, gene table,
  causal-mutation table, then only the phene pages the mapper matched — and it
  resumes where it stopped), `tools/parse_omia.py` → `data/omia_index.json`
  (1,015 dog phenes) and `data/omia_phenes.json` (271 records),
  `tools/map_omia.py` (coverage report and name resolution),
  `tools/merge_omia.py` (writes `gene`, audits `inh`).
- `gene` field on conditions: symbol, OMIA phene id and name, OMIA's inheritance
  mode for that phene, and the variant in HGVS form. 43 breed-confirmed
  assignments.
- Gene symbol surfaced inline on timeline rows, in the table view's inheritance
  column, and as a sourced row in the detail panel.
- `SOURCES.md` §1c and a fifth data-integrity rule in `DIRECTION.md`.
- 5 DOM checks covering the gene surfacing, including one asserting that every
  symbol on the page names the OMIA record behind it. 55 checks total.

### Notes
- **A gene is written only where OMIA links that mutation to that breed.** One
  clinical entity maps to many OMIA phenes — progressive retinal atrophy alone
  is 36 gene-specific records — so a name match cannot establish which gene a
  breed's version involves. Only the breed column of the variant table can. The
  first draft matched on breed alone and produced two confident, wrong, entirely
  plausible-looking results: Labrador *prcd* → GTPBP2, Portuguese Water Dog
  *prcd* → CCDC66. A locus qualifier in our own name now overrides everything,
  and where it matches no record, nothing is written.
- **Half this dataset is out of OMIA's scope by construction.** 71 of 290
  condition names have no phene and correctly never will — hip dysplasia, atopy,
  GDV, brachycephalic airway disease are not Mendelian traits. An empty `gene`
  is usually right, so the coverage report separates "no record expected" from a
  real gap.
- **Clinical names are not database names**, and guessing between them from
  keywords is how a wrong gene reaches a breed page. "Collie eye anomaly" is
  filed as *Choroidal hypoplasia, NHEJ1-related*. The residue is resolved
  through OMIA's own synonym API rather than by similarity scoring.
- **`inh` is audited, not overwritten.** Ours is curated clinical text that
  usually says more than OMIA's bare mode; 231 modes corroborate, 9 genuinely
  disagree and are listed for review by `merge_omia.py --dry`. Filling the vague
  ones is opt-in behind `--apply-inh` and should stay off for now — all 3
  candidates are urolithiasis entries where OMIA's record is a narrower entity.
- Comparing inheritance strings raw reported 109 conflicts, almost all
  *Polygenic* vs *Multifactorial* and *semi-dominant* vs *incomplete dominant*.
  The two vocabularies are canonicalised before comparison so the report shows
  substance rather than wording.
- OMIA's full MySQL and XML dumps are 198–262 MB and cover every species; the
  dog subset used here is ~1.6 MB, so the dumps are deliberately not fetched.
  `data/omia_raw/` is gitignored, matching how `data/ofa_raw.html` is handled.

### Fixed
- Backfilled the changelog for 0.5.0 through 0.6.0, which shipped and were
  tagged without entries.

## [0.6.0] — 2026-08-26

Surfaced the OFA data in the interface. 1,045 figures across 140 tests were
stored but displayed nowhere; only the 173 condition-level ones were reachable,
and only by clicking a bar.

### Added
- **Breed-level OFA screening panel**: every test held for the selected breed,
  split into phenotypic screens and genetic tests, each sorted by sample size.
  The split is derived from the data — a test is genetic exactly when it reports
  a carrier rate — rather than from a hardcoded list.
- Inline OFA percentage on timeline rows, which doubles as the marker for which
  conditions have a hard number behind them (173 of 636).
- OFA column in table view, with sample size.
- Test codes resolved to readable names, acronyms preserved (CDDY/IVDD, CDPA,
  BAER, MCADD).

### Notes
- Rows under 100 evaluations are greyed and footnoted; OFA itself requires 100
  evaluations before publishing a breed figure.
- The panel repeats the caveat in full: voluntarily submitted breeding
  candidates, not breed prevalence.
- `tests/dom-checks.js` extended to 50 checks, including a sweep confirming no
  breed is left with an empty panel.

## [0.5.2] — 2026-08-26

### Removed
- The local-caseload validation phase, from both `PLAN.md` and `DIRECTION.md`,
  along with its open question and the wellness-tier framing on the screening
  generator. The data source is not available, so the phase is deleted rather
  than left in as blocked. Coverage renumbered 6 → 5.

## [0.5.1] — 2026-08-26

### Added
- `DIRECTION.md` — the standing project reference: what this is, the decisions
  already made and why, the data integrity rules, and where it goes next.
  Written so the settled calls (severity carries colour, life stages computed
  per breed, no hero sections, OFA is not prevalence, content never depends on
  JS to be visible) do not get re-litigated.

## [0.5.0] — 2026-08-26

OFA screening statistics — phase 1 of the data expansion plan.

### Added
- Re-runnable pipeline: `tools/fetch_ofa.sh` → `data/ofa_raw.html` (~5 MB, one
  request, every test), `tools/parse_ofa.py` → `data/ofa_stats.json` (186 tests,
  2,189 breed-rows), `tools/map_ofa.py` (coverage report and breed-name
  aliases), `tools/merge_ofa.py` (writes `ofa` onto `data/*.json`).
- 83 of 85 breeds matched: 173 condition-level figures, 85 breed-level blocks.

### Notes
- **These are not prevalence figures and the code refuses to call them that.**
  OFA data comes from voluntarily submitted breeding candidates: phenotypic
  screens read low because affected animals go unsubmitted, and DNA results
  describe a population selected against the mutation. The field is `ofa`, it
  carries its metric label and sample size everywhere, and the detail panel
  repeats the caveat. `prev` stays reserved and deliberately unused until real
  population prevalence is entered.

## [0.4.0] — 2026-08-22

Added the breed × age burden matrix — the whole dataset on one screen.

### Added
- **Burden matrix**: 85 breeds down, 48 four-month bins across (birth to 16 years).
  Cell darkness encodes how many conditions are inside their onset window at that
  age, on a sequential single-hue ramp. Every row carries a rule at that breed's
  mean lifespan, so the matrix shows disease against the life it actually has.
- **Ordering** by mean lifespan, peak burden, total burden, AKC group, breed name,
  or **similarity of burden shape** — average-linkage agglomerative clustering
  (Lance-Williams update) over burden vectors normalised to sum 1, so breeds group
  by the *shape* of their disease across life rather than by how many conditions
  they carry. Runs in ~60 ms for all 85 breeds.
- **Severity weighting** toggle: count of conditions, or weighted mild 1 to
  life-limiting 4.
- **Population profile** above the matrix: total burden across all breeds at each
  age, showing the two-wave structure at population level.
- Hover any cell for the conditions in play for that breed at that age; click any
  row to load it into the breed panel below.

### Fixed
- Population profile bars used percentage heights inside an auto-sized grid track,
  which collapses to zero. Now computed in pixels.
- `var(--ink-4)` was referenced but never defined after the v0.3.0 revert, so the
  profile bars were transparent. Added a CSS-variable audit to catch this class of
  bug: every `var(--x)` used is now checked against the defined set.

### Notes
- The matrix includes lifelong constitutional traits (MDR1 sensitivity, sighthound
  clinicopathological ranges), which is why a few rows read as uniformly loaded
  across life. That is accurate — they are in play at every age.
- `tests/dom-checks.js` extended to 40 checks covering the matrix, its orderings,
  the clustering, and severity weighting.

## [0.3.0] — 2026-08-22

Reverted the v0.2.0 editorial redesign. The page is a clinical tool again, not a
designed site.

### Removed
- Full-bleed hero, oversized display typography, "Figure 1 / Figure 2" section
  framing, and the Big Shoulders Display typeface.
- Mortality spectrum and burden curve, which shipped as part of that treatment.

### Restored
- The v0.1.0 shell: breed rail, lifespan strip, onset timeline, filters, table
  view, per-condition detail.

### Kept
- `tests/dom-checks.js` and the defensive fixes it surfaced are unaffected by the
  revert and remain worth having.

### Note
The next round targets the visualisations themselves rather than page chrome.

## [0.2.0] — 2026-08-22

Editorial redesign. Same data, rebuilt as a kinetic data-first page.

### Added
- **Mortality spectrum** (Figure 1): all 85 breeds on one axis ranked by mean
  lifespan, showing the full 7.4–13.9 year spread at a glance. Click any line to
  open that breed. Selective direct labels on the extremes plus the current breed.
- **Burden curve** (per breed): how many conditions sit inside their onset window
  at each age, with a second area for serious and life-limiting conditions only.
  Makes the two-wave shape of canine disease visible — developmental in the first
  two years, then cancer and degeneration.
- Oversized display numerals for mean, modal, IQR and condition count, with a
  count-up on breed change.
- Staggered left-to-right bar draw on the timeline, so the animation enacts the
  time axis it sits on.
- Sticky breed bar with search and a grouped breed selector, replacing the rail.

### Changed
- Typeface pairing to Big Shoulders Display / Source Sans 3 / IBM Plex Mono.
- Palette to a near-monochrome ground with a single structural accent, so the only
  saturated colour on the page is the severity encoding.
- Filter chips: "on" is now the quiet state and "off" is marked, since every
  system is enabled by default.

### Fixed
- Timeline bars no longer default to `scaleX(0)`. Content was relying on JS to
  become visible, so a dropped frame or interrupted script left the chart blank.
  Bars now render at full size and the animation applies a temporary start state.
- Spectrum bars get the same treatment, plus a timeout fallback.
- `window.matchMedia` is now feature-detected. Its absence threw at module scope
  and killed the entire page script.
- `scrollIntoView` is feature-detected.
- Burden curve no longer destroys its own anchor element on re-render, which
  broke every breed change after the first.
- Spectrum reserves the right 28% of its width for direct labels, so a label can
  no longer be drawn on top of its own bar and disappear.
- Final year tick on the timeline axis no longer clipped by the scroll container.
- Burden "peak" label clamped so it cannot be clipped at either edge.
- Mastiff modal lifespan corrected 9 → 10 years (it must exceed the mean).

## [0.1.0] — 2026-08-22

First release.

### Added
- Dataset of **85 breeds** across all 7 AKC groups, **636 breed–disease pairs**,
  as one JSON file per group in `data/`.
- Per-condition fields: onset window in months, body system, clinical impact,
  inheritance mode and gene where identified, screening/diagnostic test, and a
  clinical note.
- Per-breed longevity statistics: mean, estimated modal, and interquartile range
  of age at death, with source keys.
- `build.py` — dependency-free renderer producing a self-contained page.
- Interactive onset timeline with per-breed life-stage bands, an age marker that
  filters to conditions live at a given age, body-system filters, search, a table
  view, and a per-condition detail panel.
- `SOURCES.md` documenting every source and, importantly, how each statistic was
  derived — including explicit disclosure that modal lifespan is estimated rather
  than published.
- `data/_schema.md` documenting the schema field by field.

### Notes
- Severity is encoded with a reserved four-step status palette and always paired
  with a text label, so colour never carries meaning alone.
- Onset windows are clinical consensus ranges, not extracts from a single
  dataset. See `SOURCES.md`.
