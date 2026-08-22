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
