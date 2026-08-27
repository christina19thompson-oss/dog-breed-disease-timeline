#!/usr/bin/env python3
"""Write OMIA gene assignments onto data/*.json, and audit our `inh` against theirs.

Two jobs, deliberately asymmetric:

**`gene` is written, but only on breed-level evidence.** A condition name can
match a whole family of OMIA phenes -- progressive retinal atrophy alone splits
into 36 gene-specific records -- so name matching cannot say *which* gene this
breed's version is. The variant table can: it lists the breeds each mutation
was reported in. A gene is written only where OMIA links that gene to that
mutation in that breed. Anything less and a Labrador's PRA would get labelled
with the Cocker Spaniel's locus, which is the exact class of error SOURCES.md
exists to prevent.

**`inh` is audited, not overwritten.** Our inheritance strings are curated
clinical text ("Autosomal recessive, immune-mediated acinar atrophy") and carry
more than OMIA's bare mode. Silently replacing them would lose information, so
disagreements are reported for a human to act on. `--apply-inh` will fill the
vague ones ("Breed predisposition") where OMIA states a specific mode, but that
is opt-in and it prints every change it makes.

Usage:
    python tools/merge_omia.py              # write genes, report inh audit
    python tools/merge_omia.py --dry        # report only, touch nothing
    python tools/merge_omia.py --apply-inh  # also fill vague inh from OMIA
"""
import sys, os, re, json, glob
from collections import OrderedDict, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _fmt import write as write_breed_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

SRC = "omia2026"
DRY = "--dry" in sys.argv
APPLY_INH = "--apply-inh" in sys.argv

# our `inh` values that say nothing about mode, and so may be filled from OMIA
VAGUE = re.compile(r"^(breed[- ]specific|breed predisposition|familial|"
                   r"heritable|congenital, heritable|unknown)\.?$", re.I)

# ...but only worth taking if OMIA is actually more specific than we are.
# "Familial" -> "Multifactorial" is a downgrade, not a fill.
SPECIFIC = re.compile(r"autosomal|x-linked|y-linked|mitochondrial|dominant|"
                      r"recessive|codominant|sex-linked", re.I)

# The two vocabularies say the same things in different words. Comparing raw
# strings reported 109 "disagreements", nearly all of them Polygenic vs
# Multifactorial or semi-dominant vs incomplete-dominant, which buried the
# handful that are real. Canonicalise, then compare.
EQUIV = [
    ("semi-dominant", r"semi[- ]dominant|incomplete(ly)? dominant|"
                      r"co[- ]?dominant|partial(ly)? dominant"),
    ("x-linked",      r"x[- ]linked|sex[- ]linked"),
    ("recessive",     r"recessive"),
    ("dominant",      r"dominant"),
    ("complex",       r"polygen|multifactor|complex|conformation|"
                      r"breed predisposition|breed physiology|quantitative"),
    ("mitochondrial", r"mitochondri|maternal"),
]


def canon(s):
    """Inheritance mode -> comparable token, or None if it says nothing."""
    s = (s or "").lower()
    for name, pat in EQUIV:
        if re.search(pat, s):
            return name
    return None


def norm_breed(x):
    """OMIA breed cells read 'Cocker Spaniel (Dog) American, Labrador (Dog)'."""
    x = re.sub(r"\(dog\)", " ", x, flags=re.I)
    x = re.sub(r"[^a-z0-9 ]", " ", x.lower())
    return re.sub(r"\s+", " ", x).strip()


# OMIA breed name -> our breed name, where normalisation cannot get there
BREED_ALIASES = {
    "german shepherd": "German Shepherd Dog",
    "alsatian": "German Shepherd Dog",
    "cocker spaniel american": "Cocker Spaniel (American)",
    "american cocker spaniel": "Cocker Spaniel (American)",
    "english cocker spaniel": "English Cocker Spaniel",
    "poodle miniature": "Miniature Poodle",
    "miniature poodle": "Miniature Poodle",
    "poodle standard": "Standard Poodle",
    "standard poodle": "Standard Poodle",
    "poodle toy": "Miniature Poodle",
    "dachshund miniature": "Dachshund",
    "miniature dachshund": "Dachshund",
    "miniature wire haired dachshund": "Dachshund",
    "collie rough": "Rough Collie",
    "rough collie": "Rough Collie",
    "collie": "Rough Collie",
    "shetland sheepdog": "Shetland Sheepdog",
    "welsh corgi pembroke": "Pembroke Welsh Corgi",
    "pembroke welsh corgi": "Pembroke Welsh Corgi",
    "jack russell terrier": "Parson Russell Terrier",
    "parson russell terrier": "Parson Russell Terrier",
    "staffordshire bull terrier": "Staffordshire Bull Terrier",
    "american staffordshire terrier": "American Staffordshire Terrier",
    "american pit bull terrier": "American Staffordshire Terrier",
    "shar pei": "Chinese Shar-Pei",
    "chinese shar pei": "Chinese Shar-Pei",
    "saint bernard": "Saint Bernard",
    "st bernard": "Saint Bernard",
    "labrador retriever": "Labrador Retriever",
    "golden retriever": "Golden Retriever",
    "flat coated retriever": "Flat-Coated Retriever",
    "nova scotia duck tolling retriever": "Nova Scotia Duck Tolling Retriever",
    "west highland white terrier": "West Highland White Terrier",
    "soft coated wheaten terrier": "Soft Coated Wheaten Terrier",
    "bernese mountain dog": "Bernese Mountain Dog",
    "great pyrenees": "Great Pyrenees",
    "pyrenean mountain dog": "Great Pyrenees",
    "doberman pinscher": "Doberman Pinscher",
    "dobermann": "Doberman Pinscher",
    "schnauzer miniature": "Miniature Schnauzer",
    "miniature schnauzer": "Miniature Schnauzer",
    "standard schnauzer": "Standard Schnauzer",
    "giant schnauzer": "Giant Schnauzer",
    "old english sheepdog": "Old English Sheepdog",
    "english springer spaniel": "English Springer Spaniel",
    "cavalier king charles spaniel": "Cavalier King Charles Spaniel",
    "italian greyhound": "Italian Greyhound",
    "miniature pinscher": "Miniature Pinscher",
    "portuguese water dog": "Portuguese Water Dog",
    "rhodesian ridgeback": "Rhodesian Ridgeback",
    "chesapeake bay retriever": "Chesapeake Bay Retriever",
    "german shorthaired pointer": "German Shorthaired Pointer",
    "australian cattle dog": "Australian Cattle Dog",
    "norwegian elkhound": "Norwegian Elkhound",
    "boston terrier": "Boston Terrier",
}


def load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        sys.exit("missing %s -- run tools/fetch_omia.sh first" % p)
    return json.load(open(p, encoding="utf-8"))


def breed_resolver(our_names):
    by_norm = {norm_breed(n): n for n in our_names}

    def resolve(cell):
        """One variant 'Breed(s)' cell -> the set of our breeds it names."""
        out = set()
        for part in re.split(r"[,;]", cell):
            n = norm_breed(part)
            if not n:
                continue
            if n in BREED_ALIASES:
                out.add(BREED_ALIASES[n])
            elif n in by_norm:
                out.add(by_norm[n])
            else:
                # 'labrador retriever english' -> longest our-name prefix match
                for k, v in by_norm.items():
                    if n.startswith(k) and len(k.split()) >= 2:
                        out.add(v)
                        break
        return out

    return resolve


def gene_of(phene, breed, resolve):
    """-> (symbol, variant) if OMIA links a gene to this breed, else (None, None)."""
    for v in phene.get("variants", []):
        if not v.get("gene"):
            continue
        if breed in resolve(v.get("breeds", "")):
            return v["gene"], v.get("c") or v.get("p") or None
    return None, None


def main():
    targets = load("omia_targets.json")
    phenes = load("omia_phenes.json")
    resolved = targets.get("resolved", {})

    files = [f for f in sorted(glob.glob(os.path.join(DATA, "*.json")))
             if not os.path.basename(f).startswith(("ofa", "omia", "_"))]

    docs = OrderedDict()
    our_names = []
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        if "breeds" not in d:
            continue
        docs[f] = d
        our_names += [b["name"] for b in d["breeds"]]
    resolve = breed_resolver(our_names)

    n_gene, n_amb, agree, disagree, vague_filled = 0, 0, 0, [], []
    detail, no_eviden = [], defaultdict(int)

    for f, d in docs.items():
        for b in d["breeds"]:
            for c in b["dz"]:
                c.pop("gene", None)
                r = resolved.get(c["n"])
                if not r:
                    continue
                cands = [phenes[i] for i in r["ids"] if i in phenes]
                if not cands:
                    continue

                # A locus qualifier in our name -- PRA (prcd), (rcd1), (rcd2) --
                # names the exact OMIA record and overrides everything else.
                # Without this, a breed that appears in several retinal phenes
                # takes whichever matched first: the smoke test handed Labrador
                # prcd the GTPBP2 locus. If the qualifier matches no fetched
                # phene, write nothing -- silent beats confidently wrong.
                hint = r.get("hint")
                if hint:
                    h = [w for w in re.split(r"[^a-z0-9]+", hint.lower()) if len(w) > 2]
                    named = [p for p in cands
                             if any(w in p.get("name", "").lower() for w in h)]
                    if named:
                        cands = named
                    elif h and any(w.startswith(("rcd", "prcd", "cord", "crd"))
                                   for w in h):
                        no_eviden["locus qualifier has no OMIA phene"] += 1
                        continue

                # --- gene: breed-level evidence only ---------------------
                hits = []
                for p in cands:
                    sym, var = gene_of(p, b["name"], resolve)
                    if sym:
                        hits.append((p, sym, var))

                if len({h[1] for h in hits}) > 1:
                    n_amb += 1
                    no_eviden["ambiguous (>1 gene for this breed)"] += 1
                elif hits:
                    p, sym, var = hits[0]
                    g = OrderedDict(sym=sym, omia=p["id"], phene=p.get("name", ""))
                    if p.get("inh"):
                        g["inh"] = p["inh"]
                    if var:
                        g["var"] = var
                    g["src"] = SRC
                    c["gene"] = g
                    n_gene += 1
                    detail.append((b["name"], c["n"][:34], sym, p["id"]))
                else:
                    no_eviden["no variant lists this breed"] += 1

                # --- inh: audit only ------------------------------------
                modes = {p["inh"] for p in cands if p.get("inh")}
                if len(modes) != 1:
                    continue
                omia_inh = modes.pop()
                ours = c.get("inh", "")
                mine, theirs = canon(ours), canon(omia_inh)
                if mine and mine == theirs:
                    agree += 1
                elif VAGUE.match(ours.strip()) and SPECIFIC.search(omia_inh):
                    if APPLY_INH and not DRY:
                        c["inh"] = omia_inh
                    vague_filled.append((b["name"], c["n"][:34], ours, omia_inh))
                elif mine and theirs:
                    disagree.append((b["name"], c["n"][:30], ours[:34], omia_inh))

        if not DRY:
            write_breed_file(f, d)

    print("OMIA phene records loaded    : %d" % len(phenes))
    print("condition names with candidates: %d" % len(resolved))
    print()
    print("genes written (breed-confirmed): %d%s"
          % (n_gene, "   (dry run)" if DRY else ""))
    for k, v in sorted(no_eviden.items(), key=lambda kv: -kv[1]):
        print("  not written, %-32s %d" % (k, v))
    print()
    print("inh agrees with OMIA         : %d" % agree)
    print("inh vague, OMIA specific     : %d%s"
          % (len(vague_filled), "   (filled)" if APPLY_INH and not DRY else "   (use --apply-inh)"))
    print("inh disagrees                : %d" % len(disagree))
    print()

    print("--- genes written (first 20) ---")
    for row in detail[:20]:
        print("   %-26s %-34s %-10s OMIA:%s" % row)
    if len(detail) > 20:
        print("   ... and %d more" % (len(detail) - 20))
    print()

    if vague_filled:
        print("--- our inh is vague, OMIA is specific (first 15) ---")
        for row in vague_filled[:15]:
            print("   %-24s %-34s %-22s -> %s" % row)
        if len(vague_filled) > 15:
            print("   ... and %d more" % (len(vague_filled) - 15))
        print()

    if disagree:
        print("--- DISAGREEMENTS, review by hand (first 20) ---")
        for row in disagree[:20]:
            print("   %-24s %-30s %-34s vs OMIA %s" % row)
        if len(disagree) > 20:
            print("   ... and %d more" % (len(disagree) - 20))


if __name__ == "__main__":
    main()
