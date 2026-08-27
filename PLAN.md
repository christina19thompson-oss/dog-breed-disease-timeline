# Data expansion plan

The dataset currently answers **when** a condition appears. It does not answer
**how likely** it is, or **how bad** the outcome is. Almost everything worth
adding fills one of those two columns.

Phases are ordered by value per unit of effort. Each writes into `data/*.json`
behind a documented field, so partial progress is always usable.

---

## Phase 1 — OFA screening statistics ✅ DONE (v0.5.0)

**Status: complete.** 186 OFA tests parsed, 83 of 85 breeds matched, 173
condition-level figures and 85 breed-level blocks written.

**Source:** `https://api.ofa.org/api/ds.php` — the endpoint behind
ofa.org/diseases/disease-statistics/. Returns ~5 MB of HTML, one table per test.

**Pipeline** (all re-runnable):

```bash
bash tools/fetch_ofa.sh          # refresh data/ofa_raw.html
python tools/parse_ofa.py        # -> data/ofa_stats.json   (186 tests, 2189 rows)
python tools/map_ofa.py          # coverage report, add aliases if breeds are missed
python tools/merge_ofa.py        # write `ofa` onto data/*.json
python build.py
```

**What we learned that changes how it must be presented:** OFA numbers are *not*
prevalence. They describe dogs whose owners chose to submit them, overwhelmingly
breeding candidates. Phenotypic screens (hips, elbows, patella, eyes, cardiac,
thyroid) read **low** because obviously affected animals often go unsubmitted;
DNA test results describe a population actively selected against the mutation.
The field is therefore named `ofa`, never `prev`, and always carries its metric
label and sample size. Two live examples of why this matters:

- Chihuahua merle locus: 100% carrier, n=75 — because only merle-looking dogs
  get tested.
- Cavalier degenerative myelopathy: 23.3% "abnormal" genotype — genotype
  frequency in tested breeding stock, not clinical disease rate.

**Not attached to conditions:** the composite screens (`EYE`, `CA`, `ACA`,
`BCA`, `DE`) live only at breed level. "Abnormal on a congenital cardiac exam"
does not belong to any single condition, and attaching it to, say, patent ductus
arteriosus would be actively misleading.

---

## Phase 2 — Genotype frequencies beyond OFA

OFA already delivered carrier rates for the tests it hosts. This phase fills the
gaps for mutations OFA does not run.

- **OMIA** (`omia.org`, University of Sydney) — free, structured, downloadable:
  gene, phene, species, breed, inheritance mode. Use it to verify and complete
  the `inh` field across all 636 entries rather than to add new numbers.
- **Embark / UC Davis VGL** breed pages — allele frequencies for mutations
  outside the OFA panel.

Target field: `gene` (symbol), and `freq` where a defensible population figure
exists. Same honesty rule as Phase 1 — record the tested population.

**Effort:** moderate. OMIA is structured; the commercial labs are page-by-page.

---

## Phase 3 — True prevalence from primary-care populations

This is the column OFA cannot fill, because OFA never sees the pet population.

- **VetCompass** (Royal Veterinary College) — open-access papers reporting
  breed prevalence and odds ratios from UK primary-care records. Extraction is
  paper-by-paper, not a bulk download.
- **Agria** (Swedish insurance) — breed morbidity and mortality rates, published
  via Egenvall / Bonnett papers.
- **Nationwide / Trupanion** — aggregate claim summaries.

Target field: `prev` — reserved, deliberately still unused, so that when a real
prevalence figure arrives it cannot be confused with an OFA screening result.

**Effort:** high, and it is reading rather than engineering. Highest scientific
value of anything on this list.

---

## Phase 4 — Outcome and survival

Converts `sev` from a four-step judgement into a prognosis.

Median survival times, treatment response rates, and post-diagnosis quality of
life, entered by hand from the oncology, cardiology and neurology literature.
Splenic haemangiosarcoma with surgery alone (~4–6 months) and a completely
excised grade II mast cell tumour (years) are both "life-limiting" under the
current schema, which is a real loss of information.

Target fields: `mst` (median survival, months) and `mstNote`.

**Effort:** high, manual, but can be done condition-by-condition starting with
the ~90 entries marked `limiting`.

---

## Phase 5 — Coverage

- Remaining ~120 AKC breeds (the current 85 cover the high-volume ones).
- **Designer crosses.** An F1 cross inherits the union of both parents'
  predispositions, but hybrid vigour applies to *recessive* conditions and not
  to polygenic or conformational ones. That distinction is computable from data
  already in `inh`, and it is the question clients actually ask.
- Cat breeds.

---

## Field summary

| field | level | status | meaning |
|---|---|---|---|
| `ofa` | breed + condition | **live** | OFA screening result, with metric and n |
| `gene` | condition | planned | gene symbol (Phase 2) |
| `freq` | condition | planned | genotype frequency in a stated population (Phase 2) |
| `prev` | condition | **reserved** | true population prevalence (Phase 3) — deliberately unused |
| `mst` | condition | planned | median survival, months (Phase 4) |
