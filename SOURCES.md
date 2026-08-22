# Sources and how to read the numbers

This matters more than usual here, because the two kinds of numbers in this
dataset have very different evidentiary weight. Read this before using any of
it clinically.

---

## 1. Lifespan figures (`mean`, `mode`, `p25`, `p75`)

### Where they come from

| Key | Source |
|---|---|
| `mcm2024` | McMillan KM, Bielby J, Williams CL, Upjohn MM, Casey RA, Christley RM. **Longevity of companion dog breeds: those at risk from early death.** *Scientific Reports* 2024;14:531. Life tables built from 584,734 dogs across 155 breeds — the largest canine longevity dataset published, and the anchor for the `mean` column here. |
| `kc2014` | **Kennel Club / British Small Animal Veterinary Association Purebred Dog Health Survey**, 2004 and 2014 rounds. Owner-reported age and cause of death by breed. |
| `vc2017` | O'Neill DG et al. **Demography and disorders of German Shepherd Dogs under primary veterinary care in the UK.** *Canine Genetics and Epidemiology* 2017. |
| `vc2018` | O'Neill DG et al. **Labrador Retrievers under primary veterinary care in the UK: demography, mortality and disorders.** *Canine Genetics and Epidemiology* 2018;5:8. |
| `vc2021` | O'Neill DG et al. **Health of Pug dogs / English Bulldogs / French Bulldogs under primary veterinary care in the UK** (VetCompass series). *Canine Medicine and Genetics* 2021–2022. |
| `vc2022` | O'Neill DG et al. **Health of Pug dogs in the UK: disorder predispositions and protections.** *Canine Medicine and Genetics* 2022;9:4. |
| `glt2015` | **Golden Retriever Lifetime Study**, Morris Animal Foundation — prospective cohort of >3,000 Golden Retrievers, ongoing since 2012. |
| `bmd2016` | Bernese Mountain Dog histiocytic sarcoma cohort and heritability studies (Abadie, Shearin, Dobson series). |
| `ckcs2019` | Cavalier King Charles Spaniel mitral valve disease cohort studies and the MVD breeding-scheme literature. |

### How each statistic was derived — read this carefully

- **`mean`** — anchored to published breed life expectancy, primarily
  `mcm2024`. Where that paper reports median life expectancy at age 0 rather
  than an arithmetic mean, the value here is reconciled against the Kennel
  Club survey mean for the same breed. Treat as **±1 year**.
- **`p25` / `p75`** — the interquartile range of age at death. Where not
  directly published for a breed, it is modelled from the breed's mean and the
  characteristic left-skewed shape of canine death-age distributions.
- **`mode`** — **estimated, not published.** Almost no source reports a modal
  age at death by breed; medians and means are what get published. Because
  canine age-at-death distributions are left-skewed (a tail of early deaths
  from accident, congenital disease and early cancer pulls the mean down), the
  mode sits **above** the mean, typically by 1–1.5 years. Every mode in this
  dataset is flagged `modeEst: true` and the interface labels it *est.* Do not
  quote it as a published figure.

**What this means in practice:** the mean is a defensible number to give a
client. The mode is a useful shape-of-the-distribution intuition — "the most
common age to lose this breed" — and should be presented as an estimate.

---

## 2. Disease onset windows (`on`)

These are **clinical consensus ranges**, not extracts from a single dataset,
and no published source gives a tidy onset interval for most breed–disease
pairs. Each window was set from the standard reference literature:

- Gough A, Thomas A, O'Neill D. **Breed Predispositions to Disease in Dogs and
  Cats**, 3rd ed. Wiley-Blackwell, 2018. *(The backbone reference for which
  breed gets what.)*
- Ettinger SJ, Feldman EC, Côté E. **Textbook of Veterinary Internal
  Medicine**, 8th ed.
- **OFA / Canine Health Information Center (CHIC)** breed-specific screening
  requirements — the source for which tests exist and at what age they are valid.
- **UC Davis Veterinary Genetics Laboratory** and **OptiGen / Wisdom Panel**
  test catalogues — for mutation names, inheritance modes and gene symbols.
- **Online Mendelian Inheritance in Animals (OMIA)**, University of Sydney —
  for inheritance mode and gene assignment.
- **American College of Veterinary Ophthalmologists (ACVO) Blue Book** — for
  ocular condition onset and CAER examination timing.
- Primary literature for individual breed-specific entities (Doberman DCM
  screening intervals, CKCS MVD onset curves, Shar-Pei HAS2 autoinflammatory
  disease, Basenji Fanconi, Border Terrier CECS, and similar).

**Onset windows describe the interval in which clinical signs typically first
appear**, not the interval in which the disease exists. A dog can carry a
PRA genotype from conception and show nothing until seven years old; the bar
marks the seven, not the conception. Individual dogs fall outside these
windows regularly.

---

## 3. What this dataset is not

- **Not a prevalence dataset.** A bar on the timeline means "this breed is
  predisposed and this is when it shows up," not "this dog will get it."
  Nothing here encodes incidence.
- **Not a diagnostic tool.** Breed predisposition is one line of evidence in a
  differential, and a strong signal in a young animal, but it is not a
  diagnosis and it should never be used to exclude a condition in a breed
  that is not listed.
- **Not exhaustive.** 85 breeds and 636 breed–disease pairs at v0.1.0. Common
  conditions with no particular breed association (routine dental disease,
  most trauma, most infectious disease) are deliberately omitted except where
  a breed is genuinely overrepresented.
- **Population-specific.** Most of the underlying data is UK (VetCompass,
  Kennel Club) or US (OFA, Morris). Breed populations differ substantially
  between countries and between show and working lines, and so do their
  disease profiles.

---

## 4. Corrections

The dataset is plain JSON in `data/`, one file per AKC group, and every field
is documented in `data/_schema.md`. Corrections to onset windows or additions
of breed-specific conditions are the most valuable kind of edit. Bump the
minor version when adding breeds or conditions, and the patch version when
correcting a value.
