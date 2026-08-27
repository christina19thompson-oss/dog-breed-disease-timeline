# Project direction

Reference document for the Canine Onset Atlas. What it is, what has been decided
and why, what is deliberately not being done, and where it goes next.

Companion documents: `PLAN.md` (data expansion phases), `SOURCES.md` (provenance
and the honesty rules), `data/_schema.md` (field definitions), `CHANGELOG.md`
(what shipped when).

---

## 1. What this is

A clinical reference that maps **breed-associated disease against the age it
appears**, and against **how long that breed actually lives**.

The question it exists to answer is the one asked in an exam room: *this breed,
this age — what belongs on my list?*

**Current state — v0.5.0**

| | |
|---|---|
| Breeds | 85, across all 7 AKC groups |
| Breed–disease pairs | 636 |
| OFA screening figures | 173 condition-level, 85 breed-level blocks |
| Repo | `~/dog-breed-disease-timeline`, private on GitHub |
| Published | Claude Artifact, private, republished from `dist/artifact.html` |

**What it contains per condition:** onset window in months, body system, clinical
impact, inheritance mode and gene where identified, the screening or diagnostic
test, a clinical note, and — where OFA runs a specific test — a screening figure
with its metric and sample size.

**Per breed:** mean lifespan, estimated modal lifespan, interquartile range of
age at death, size class, and the full block of OFA tests held for that breed.

---

## 2. The three views

1. **Burden matrix** — all 85 breeds and their whole life course on one screen.
   One row per breed, one column per four months, cell darkness = conditions
   inside their onset window at that age. Each row carries a rule at that
   breed's mean lifespan. Orderable by lifespan, peak burden, total burden,
   group, name, or by *similarity of burden shape* (agglomerative clustering on
   shape-normalised vectors, so breeds group by disease architecture rather than
   condition count).
2. **Lifespan strip** — mean, estimated mode, and IQR of age at death, against
   the all-breed mean.
3. **Onset timeline** — every condition as a bar spanning its onset window, over
   per-breed life-stage bands, with an age marker that dims everything not
   currently in play.

---

## 3. Decisions made, and why

These are the calls that would otherwise get re-litigated.

**Severity carries the colour, body system does not.**
Eleven body systems would need an eleven-colour legend that nobody can read.
Clinical impact is what matters at a glance, so severity gets the reserved
four-step status palette and body system became a filter chip plus a text label.

**The matrix uses a sequential single hue.**
Burden is magnitude, so it gets one hue light-to-dark. Never a rainbow. This
also keeps it visually separate from the severity encoding, which is the only
other colour on the page.

**Life stages are computed per breed, not fixed.**
Growth-plate closure by size class; senior at 75% of that breed's mean lifespan.
A Great Dane is senior at 6.3 years and a Dachshund is not senior until 10.
Fixed age bands would be clinically wrong.

**The page is a tool, not a designed site.**
An editorial treatment was built in v0.2.0 — full-bleed hero, oversized display
type, section framing — and reverted in v0.3.0. The ambition belongs in the
visualisations, not the page chrome. Do not reintroduce hero sections.

**Content never depends on JavaScript to become visible.**
Bars render at full size and animation applies a *temporary* start state.
The reverse — animating up from `scaleX(0)` — leaves a blank chart whenever a
frame is dropped, which happened and shipped once.

---

## 4. Data integrity rules

The display makes everything look equally certain. These rules exist so it
cannot mislead.

**Onset is not risk.** A bar says *when*, never *how likely*. Nothing in the
dataset encodes incidence. A condition absent from a breed's list means that
breed is not notably predisposed, not that the breed cannot get it.

**Modal lifespan is estimated, not published.** Sources report means and
medians. The mode is derived from the left-skew of canine age-at-death
distributions and is labelled *est.* everywhere it appears.

**OFA figures are not prevalence.** They describe voluntarily submitted breeding
candidates. Phenotypic screens read low; DNA results describe a population being
selected against the mutation. The field is `ofa`, never `prev`, and always
carries its metric label and sample size. `prev` is reserved and deliberately
unused until genuine population prevalence is entered. Full detail in
`SOURCES.md` §1b.

**Composite screens stay at breed level.** "Abnormal on a congenital cardiac
exam" belongs to no single condition.

**Every new number arrives with its population.** Whose dogs, how many, measured
how. A figure without that is not enterable.

---

## 5. Where it goes next

### Data — see `PLAN.md` for detail

| Phase | Source | Status |
|---|---|---|
| 1. OFA screening | `api.ofa.org` | **done, v0.5.0** |
| 2. Genotype frequency | OMIA, Embark, UC Davis VGL | next |
| 3. **True prevalence** | VetCompass, Agria | highest scientific value |
| 4. Survival / outcome | Oncology + cardiology literature | manual |
| 5. Local validation | Shepherd PIMS caseload | needs permission |
| 6. Coverage | ~120 more breeds, crosses, cats | mechanical |

Phase 3 is the one that fills the column OFA structurally cannot — OFA never
sees the pet population.

### Features

**Screening schedule generator — highest leverage, smallest build.**
Every condition already carries a `test` field. Invert it: breed in, age-ordered
checklist of what to screen and when. That is a wellness protocol generated from
data already entered, and it is the version that changes what happens in an exam
room rather than merely informing it. It is also the only feature with an
obvious commercial shape.

**Condition-first transpose.** Pick a disease, see every predisposed breed's
onset window ranked. Answers "which breeds should have had this on my radar",
which the breed-first view structurally cannot.

**Designer crosses.** An F1 cross inherits the union of both parents'
predispositions, but hybrid vigour applies to *recessive* conditions and not to
polygenic or conformational ones. That distinction is computable from `inh`, and
nobody has mapped it. It is also the question clients actually ask.

**Prevalence-weighted matrix.** Once Phase 3 lands, cells can encode expected
burden — probability × timing — instead of a count. Same chart, better number.

---

## 6. How to work on it

```bash
python build.py                  # data/*.json -> dist/index.html + dist/artifact.html
node tests/dom-checks.js         # 40 headless checks (needs jsdom)
bash tools/fetch_ofa.sh          # refresh the OFA snapshot, then parse + merge
```

Visual checks: render `dist/index.html` with headless Chrome and pass
`--force-prefers-reduced-motion`, or screenshots catch the load animation
mid-flight and the numbers read wrong.

Data files are plain JSON, one condition per line, deliberately hand-editable.
`tools/_fmt.py` preserves that layout when scripts write to them.

Versioning is semver: patch for corrected values, minor for new breeds,
conditions or fields, major for a schema change. Tag every release.

---

## 7. Open questions

- **Publication.** The dataset is publishable as it stands. RVC VetCompass
  group, veterinary informatics, or simply a public tool. Undecided.
- **Shepherd data.** Phase 5 is the most differentiating work available and the
  only source nobody else can replicate, but it is practice data. Permission and
  aggregation approach need settling before any extraction.
- **Scope of crosses.** Whether to model F1 only, or attempt multigenerational
  doodles where parentage is genuinely unknown.
- **Cats.** Same engine, entirely new dataset. Worth it only if the canine
  version proves itself first.
