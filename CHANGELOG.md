# Changelog

All notable changes to this project. Format follows [Keep a Changelog](https://keepachangelog.com/),
versioning follows [Semantic Versioning](https://semver.org/).

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
