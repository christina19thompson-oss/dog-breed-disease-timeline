# Changelog

All notable changes to this project. Format follows [Keep a Changelog](https://keepachangelog.com/),
versioning follows [Semantic Versioning](https://semver.org/).

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
