# Data schema

One JSON file per AKC group. Each file:

```
{ "group": "Sporting", "breeds": [ Breed, ... ] }
```

## Breed
| key | type | meaning |
|---|---|---|
| `name` | string | Breed name (AKC form) |
| `size` | toy\|small\|medium\|large\|giant | Adult size class |
| `life` | Lifespan | Longevity statistics |
| `dz` | Disease[] | Breed-associated conditions |

## Lifespan
| key | type | meaning |
|---|---|---|
| `mean` | number | Mean age at death, years |
| `mode` | number | Modal (most common) age at death, years |
| `modeEst` | bool | `true` = mode estimated from the death-age distribution, not directly published |
| `p25`,`p75` | number | Interquartile range of age at death, years |
| `src` | string[] | Source keys — see SOURCES.md |

## Disease
| key | type | meaning |
|---|---|---|
| `n` | string | Condition name |
| `sys` | string | Body system key (see `systems` in build) |
| `on` | [number,number] | Typical clinical onset window, **in months** |
| `sev` | mild\|moderate\|serious\|limiting | Clinical impact if untreated |
| `inh` | string | Inheritance / mode where known |
| `test` | string | Screening or diagnostic test, if one exists |
| `note` | string | Clinical note |

Ages are stored in **months** so that neonatal (0–6) and geriatric (120–200)
conditions share one axis.

## OFA screening (`ofa`)

Present at two levels, written by `tools/merge_ofa.py`.

`breed.ofa` — every OFA test held for that breed, keyed by test code.
`condition.ofa` — only where an OFA test is specific to that condition.

| key | meaning |
|---|---|
| `pct` | headline percent, from the column named in `metric` |
| `metric` | which column the percent came from (`Dysplastic %`, `Abnormal %`, `Autoimmune Thyroiditis %`) |
| `n` | dogs evaluated |
| `test` | OFA test code (condition level only) |
| `carrier` | carrier percent, DNA tests only |
| `pooled` | `true` where OFA pools breed varieties into one row |
| `src` | source key, `ofa2026` |

**This is not prevalence.** See SOURCES.md §1b before using these numbers.

## Gene assignment (`gene`)

Condition level only, written by `tools/merge_omia.py` from OMIA.

| key | meaning |
|---|---|
| `sym` | gene symbol (`SOD1`, `ABCB1`, `RPGRIP1`) |
| `omia` | OMIA phene id, so the claim stays checkable — `omia.org/OMIA000263/9615/` |
| `phene` | OMIA's name for the phene, which often differs from the clinical one |
| `inh` | OMIA's mode of inheritance **for that phene** — not merged into `inh` |
| `var` | the variant, in HGVS c. or p. form, where OMIA gives one |
| `src` | source key, `omia2026` |

**A gene is written only where OMIA links that mutation to that breed.** One
clinical entity often maps to many OMIA phenes — progressive retinal atrophy
splits into 36 gene-specific records — so a name match alone cannot say which
gene a given breed's version is. The breed column of OMIA's variant table can,
and nothing else is accepted as evidence. Where a locus qualifier appears in our
condition name (`PRA (prcd)`, `(rcd1)`), that qualifier decides the record and
overrides everything else.

`gene.inh` sits beside our `inh` rather than replacing it. Ours is curated
clinical text and frequently carries more ("Autosomal recessive, immune-mediated
acinar atrophy"); OMIA's is the bare mode for a phene that may be narrower than
the breed's clinical picture. See SOURCES.md §1c.

## Reserved fields

`prev` (true population prevalence), `freq` and `mst` are reserved for later
phases — see PLAN.md. `prev` is deliberately left unused so it cannot be
confused with an OFA screening result.
