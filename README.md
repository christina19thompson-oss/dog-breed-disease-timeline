# Canine Onset Atlas

A breed-by-breed reference that plots inherited and breed-associated disease
against **the age it typically first shows up**, alongside longevity statistics
for each breed.

The question it answers is the one you actually ask in the exam room: *this
breed, this age — what should be on my list?*

**v0.1.0 — 85 breeds, 636 breed–disease pairs, 7 AKC groups.**

---

## What it does

- **Burden matrix.** All 85 breeds and their whole life course on one screen:
  one row per breed, one column per four months, cell darkness = how many
  conditions are inside their onset window at that age. Each row carries a rule
  at that breed's mean lifespan. Order it by lifespan, peak or total burden,
  group, name, or by **similarity of burden shape** — agglomerative clustering on
  shape-normalised burden vectors, which groups breeds with comparable disease
  architecture regardless of how many conditions they carry. Hover a cell for the
  conditions in play; click a row to open that breed.
- **Onset timeline.** Every condition is a bar spanning the window in which
  clinical signs typically first appear, on an age axis scaled to that breed's
  own lifespan. Bars are coloured by clinical impact, not by body system, so
  the life-limiting conditions read at a glance.
- **Life-stage bands.** The background is shaded puppy / adult / senior / past
  mean lifespan, and the boundaries are computed **per breed** — growth-plate
  closure by size class, senior at 75% of mean lifespan. A Great Dane is senior
  at 6.3 years; a Dachshund is not senior until 10.
- **Age marker.** Drag it to the patient's age and everything not in its onset
  window dims. Toggle *Only what is live at this age* to strip the list down to
  the differential that actually applies.
- **Lifespan panel.** Mean, estimated mode, and the interquartile range of age
  at death, with the all-breed mean drawn in for comparison.
- **Per-condition detail.** Click any bar for inheritance mode, gene where one
  is identified, the screening or diagnostic test, and a clinical note.
- **Filters.** By body system, by free-text search across breeds and conditions.
  Table view for anything you would rather read than scan.

## Layout

```
data/*.json        one file per AKC group — the actual dataset
data/_schema.md    field-by-field schema
build.py           renders the data into a self-contained page
dist/index.html    standalone page, open it in any browser
dist/artifact.html same page as a fragment, for publishing as an Artifact
SOURCES.md         sources, and how each number was derived
```

## Building

```bash
python build.py
```

No dependencies. Reads `data/*.json`, writes both files in `dist/`.

## Testing

`tests/dom-checks.js` runs the built page in a headless DOM and exercises it:
breed selection from the spectrum and the dropdown, the age scrubber, filters,
table view, the detail panel, search, and a sweep that renders all 85 breeds
checking for NaN geometry and bars that overflow their track.

```bash
npm i jsdom          # anywhere; point the script at dist/index.html
node tests/dom-checks.js
```

For visual checks, render `dist/index.html` with headless Chrome. Pass
`--force-prefers-reduced-motion`, otherwise screenshots capture the load
animation mid-flight and the numbers read wrong.

## Reading it correctly

Three things worth being explicit about, because the display makes them look
more certain than they are:

1. **Bars are onset, not risk.** A bar says *when*, never *how likely*. Nothing
   in this dataset encodes incidence or prevalence.
2. **Modal lifespan is estimated.** Published sources give means and medians,
   not modes. Every mode here is derived from the left-skewed shape of canine
   age-at-death distributions and is labelled *est.* throughout.
3. **Absence is not exclusion.** A condition missing from a breed's list means
   that breed is not notably predisposed — not that the breed cannot get it.

Full derivation notes in [SOURCES.md](SOURCES.md).

## Extending it

The data is plain JSON and deliberately easy to edit by hand. Adding a breed
means appending one object to the right group file; adding a condition means one
line. Re-run `build.py`.

Versioning is semver: patch for corrections to existing values, minor for new
breeds or conditions, major for a schema change.

## Roadmap

- Remaining AKC breeds, plus common designer crosses (doodles, cavapoos) where
  they inherit both parent breeds' risks
- Cross-breed view: pick a condition, see every predisposed breed on one axis
- Screening-schedule export: a per-breed wellness plan by age
- Cat breeds

---

*Clinical reference for veterinary professionals. Not a diagnostic tool and not
a substitute for examination.*
