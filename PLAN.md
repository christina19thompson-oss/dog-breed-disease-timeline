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

## Phase 2 — Gene assignment from OMIA ✅ DONE (v0.7.0)

**Status: complete for OMIA.** 271 phene records parsed, 43 breed-confirmed gene
assignments written, 231 inheritance modes independently corroborated.

**Source:** OMIA (Online Mendelian Inheritance in Animals), University of
Sydney. The dog subset is reachable without the 198–262 MB full dumps:

| endpoint | what it gives |
|---|---|
| `results/?search_type=advanced&gb_species_id=9615` | 1,015 dog phenes: id, name, gene, year |
| `download/csv/genes/` | gene symbol → NCBI id |
| `download/causal_mutations/?format=X1` | traits with a known causal mutation |
| `OMIA<id>/9615/` | inheritance mode, gene table, **breed-level variant table** |
| `api/search/phenes/?q=` | synonym-aware name resolution |

**Pipeline** (all re-runnable; the phene fetch resumes where it stopped):

```bash
bash tools/fetch_omia.sh         # index + supporting tables + matched phenes
python tools/parse_omia.py       # -> data/omia_index.json, omia_phenes.json
python tools/map_omia.py         # coverage report; ALIASES for the residue
python tools/merge_omia.py       # write `gene`, audit `inh`
python build.py
```

**What we learned that changes how it must be handled:**

- **OMIA is Mendelian, so half this dataset is out of scope by construction.**
  Of 290 distinct condition names, 71 have no OMIA record and correctly never
  will — hip dysplasia, atopy, GDV, brachycephalic airway disease. Unmatched is
  usually right, so the coverage report separates "no record expected" from a
  genuine gap.
- **One clinical entity, many phenes.** PRA alone is 36 gene-specific dog
  records; cerebellar ataxia is 8. A name match therefore cannot establish which
  gene a breed's version involves. Only the breed column of the variant table
  can, and it is the sole evidence accepted. This is not a threshold that can be
  loosened: the first draft, matching on breed alone, gave Labrador *prcd* the
  GTPBP2 locus and Portuguese Water Dog *prcd* CCDC66. Both wrong, both entirely
  plausible-looking on the page.
- **A locus qualifier overrides everything.** `PRA (prcd)`, `(rcd1)`, `(rcd2)`
  name the exact record. Where the qualifier matches no fetched phene, nothing
  is written — 7 cases, and silence beats confidently wrong.
- **Clinical names are not database names.** "Collie eye anomaly" is filed as
  *Choroidal hypoplasia, NHEJ1-related*, "Musladin-Lueke syndrome" as
  *Geleophysic dysplasia, ADMATSL2-related*. Guessing those from keywords is how
  a wrong gene reaches a breed page, so the residue goes through OMIA's own
  synonym API, cached in `data/omia_raw/api_cache.json`.
- **The two vocabularies differ without disagreeing.** Raw string comparison
  reported 109 inheritance conflicts, nearly all *Polygenic* vs *Multifactorial*
  or *semi-dominant* vs *incomplete dominant*. Canonicalising leaves **9 real
  disagreements**, which are worth a look.
- **`inh` is audited, never overwritten.** Ours is curated clinical text and
  usually says more than OMIA's bare mode. `--apply-inh` exists for the 3 cases
  where ours is vague and theirs is specific, but it is opt-in and should not be
  run as things stand: all 3 are urolithiasis entries where OMIA's record is a
  narrower entity (cystinuria, hyperuricosuria), and "Autosomal recessive" would
  be wrong for struvite and calcium oxalate stones.

**Open, for a human:** the 9 inheritance disagreements from
`python tools/merge_omia.py --dry`. The most useful is Miniature Schnauzer PRA
Type A/B, which resolves to an X-linked OMIA phene — probably a wrong match
rather than a wrong mode.

### Phase 2b — genotype frequency, still open

**Embark / UC Davis VGL** breed pages hold allele frequencies for mutations
outside the OFA panel. Target field `freq`, still unused, under the Phase 1
honesty rule: record the tested population. Page-by-page, no bulk endpoint.

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
| `gene` | condition | **live** | gene symbol + OMIA record, breed-confirmed |
| `freq` | condition | planned | genotype frequency in a stated population (Phase 2b) |
| `prev` | condition | **reserved** | true population prevalence (Phase 3) — deliberately unused |
| `mst` | condition | planned | median survival, months (Phase 4) |
