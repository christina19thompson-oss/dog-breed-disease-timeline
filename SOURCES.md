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
| `ofa2026` | **Orthopedic Foundation for Animals**, breed statistics, retrieved 26 Aug 2026 from `api.ofa.org/api/ds.php`. 186 tests. See the warning below — these are screening results, not prevalence. |
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

## 1b. OFA screening statistics (`ofa` field)

**These are not prevalence figures, and must never be presented as such.**

OFA statistics describe dogs whose owners chose to submit them — overwhelmingly
breeding candidates, in breeds where health screening is a cultural norm.

- **Phenotypic screens** (hips, elbows, patella, eyes, cardiac, thyroid) are
  biased **low**. Obviously dysplastic or affected animals are frequently never
  submitted, so the reported abnormal rate is a floor, not an estimate.
- **DNA test results** describe the tested breeding population, which is being
  actively selected against the mutation. Two illustrations from the current
  snapshot: the Chihuahua merle locus reads 100% carrier (n=75) because only
  merle-looking dogs are tested at all; Cavalier degenerative myelopathy reads
  23.3% "abnormal" genotype, which is genotype frequency in breeding stock and
  not a clinical disease rate.
- **Sample sizes vary enormously** — Labrador hips carry n=324,731; some breeds
  have fewer than 100 evaluations. The `n` is stored alongside every figure and
  should always be read with it.
- **Composite screens** (eyes, congenital cardiac, basic and advanced cardiac,
  dentition) are stored only at breed level, because "abnormal on a congenital
  cardiac exam" does not belong to any one condition.
- **Breed varieties are pooled** where OFA pools them. OFA lists a single
  `POODLE` row, so Standard and Miniature Poodle share it and the figure is
  flagged `pooled: true`.

The interface always shows the metric label and sample size next to the number,
and repeats the caveat, precisely so the figure cannot be quoted out of context.

The field is named `ofa`. The field name `prev` is deliberately reserved and
unused until genuine population prevalence (VetCompass, Agria) is entered.

---

## 1c. Gene assignments (`gene` field)

| Key | Source |
|---|---|
| `omia2026` | **Online Mendelian Inheritance in Animals (OMIA)**, University of Sydney. Nicholas FW, Tammen I, & Sydney Informatics Hub (1995). <https://omia.org/>, doi:10.25910/2AMR-PV70. Dog records (taxon 9615) retrieved 27 Aug 2026. Data made available by software support from the Sydney Informatics Hub, funded from the Ronald Bruce Anstee bequest to the Sydney School of Veterinary Science for the Anstee Hub for Inherited Diseases in Animals (AHIDA). |

**A gene symbol is a claim about a specific mutation in a specific breed, and
it is recorded only where OMIA supports exactly that.**

- **One disease, many genes.** OMIA files by causal mutation, not by clinical
  entity. Progressive retinal atrophy is 36 separate dog records; cerebellar
  ataxia is 8; ichthyosis is a family of gene-specific entries. Matching our
  condition *name* to an OMIA phene therefore cannot establish which gene a
  given breed's version involves. What can is the breed column of OMIA's
  variant table, and that is the only evidence accepted here.
- **A locus qualifier wins.** Where the condition name carries one — PRA
  `(prcd)`, `(rcd1)`, `(rcd2)`, `(cord1)` — it names the exact record and
  overrides the breed search. Without this rule a Labrador's *prcd* picks up
  whichever retinal gene happens to list Labradors first, which is how a
  plausible and entirely wrong gene gets onto a breed page.
- **Silence is a valid answer.** Where the evidence does not reach that bar,
  nothing is written. Roughly half of the 636 pairs are polygenic,
  conformational or acquired — hip dysplasia, atopy, GDV, brachycephalic airway
  disease — and have no OMIA record because they are not Mendelian traits. An
  empty `gene` is usually correct, not a gap waiting to be filled.
- **A gene is not a diagnosis, and not a risk.** It says a mutation has been
  reported in this breed for this condition. It does not say this dog carries
  it, and it encodes nothing about how common it is. Carrier frequencies, where
  they exist at all, live in `ofa.carrier` and come with the §1b caveat.
- **Their inheritance is kept separate from ours.** `gene.inh` is OMIA's mode
  for the phene. Our `inh` is curated clinical text and often says more. The two
  are stored side by side and disagreements are reported by
  `tools/merge_omia.py` for a human to resolve; neither overwrites the other.

**Vocabulary note.** OMIA and the clinical literature name the same modes
differently — *Multifactorial* against *Polygenic*, *Autosomal incomplete
dominant* against *Autosomal semi-dominant*. These are treated as equivalent
when auditing, so the disagreement report shows substantive conflicts rather
than 100-odd differences of wording.

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
