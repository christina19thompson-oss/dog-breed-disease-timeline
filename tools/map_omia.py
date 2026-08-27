#!/usr/bin/env python3
"""Match our condition names to OMIA phene records, and report the coverage.

Run this before merging, the same way map_ofa.py is run before merge_ofa.py:
it prints what matched and what did not, so the residue gets resolved
deliberately rather than by a similarity threshold nobody audits.

Three things make this harder than the OFA breed match:

1. **OMIA is Mendelian.** Roughly half this dataset is polygenic, conformational
   or acquired -- hip dysplasia, atopy, GDV, brachycephalic airway signs. Those
   have no OMIA phene and never will. An unmatched row is usually correct, not
   a gap, so the report separates "no OMIA record expected" from "should match".

2. **One clinical entity, many phenes.** OMIA splits by causal gene:
   "Ataxia, cerebellar, KCNJ10-related", "Ataxia, cerebellar, RAB24-related",
   and 24 more. Our single "Cerebellar ataxia" maps to that whole family, and
   which member applies depends on the breed. So this stage returns a candidate
   *set* plus a `hint` (our parenthetical, e.g. "prcd", "rcd1"), and
   merge_omia.py narrows it using the breed column of the variant table.

3. **Clinical name vs database name.** Vets say "Collie eye anomaly"; OMIA
   files it as "Choroidal hypoplasia, NHEJ1-related". Guessing those from
   keywords is how you get a wrong gene onto a breed page, so the residue goes
   through OMIA's own search API, which indexes their synonyms. Results are
   cached in data/omia_raw/api_cache.json -- delete it to re-resolve.

Usage:
    python tools/map_omia.py              # coverage report
    python tools/map_omia.py --targets    # + write data/omia_targets.json
    python tools/map_omia.py --no-api     # local matching only, no network
"""
import sys, os, re, json, glob, time, urllib.parse, urllib.request
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "omia_raw")
CACHE = os.path.join(RAW, "api_cache.json")

API = "https://omia.org/api/search/phenes/"
UA = "Mozilla/5.0 (canine-onset-atlas; veterinary reference; +https://omia.org/)"
DOG = 9615

# Hand calls the API cannot make. None = checked, OMIA holds no such record.
ALIASES = {
    "Addison's disease": "Hypoadrenocorticism",
    "Cushing's disease": "Hyperadrenocorticism",
    "MDR1 drug sensitivity": "Multidrug resistance 1, ABCB1-related",
    "Border Collie collapse": "Exercise-induced collapse",
    "Lafora disease": "Myoclonus epilepsy of Lafora",
    "Hyperuricosuria and urate urolithiasis": "Urolithiasis",
    "Cervical spondylomyelopathy": "Cervical vertebral compressive myelopathy",
    "Cervical spondylomyelopathy (wobbler)": "Cervical vertebral compressive myelopathy",
    "Grey collie syndrome (cyclic neutropenia)": "Neutropenia, cyclic",
    "Idiopathic megaoesophagus": "Megaoesophagus, generic",
    "Pituitary dwarfism": "Dwarfism, growth-hormone deficiency",
    "Laryngeal paralysis (GOLPP)": "Laryngeal paralysis, generic",
    "Primary lens luxation and glaucoma": "Lens luxation",
    "Reactive systemic amyloidosis": "Amyloidosis, AA",
    # not single-gene entities; OMIA has no record and should not
    "Anaesthetic risk": None,
    "Anaesthetic sensitivity": None,
    "Anaesthetic and cold sensitivity": None,
    "Anaesthetic sensitivity (thiobarbiturate, propofol)": None,
    "Breed-specific clinicopathological ranges": None,
    "Aspiration pneumonia secondary to megaoesophagus": None,
    "Bloat and gastric dilatation-volvulus": None,
    "Brachycephalic airway signs": None,
    "Alopecia X": None,
}

STOP = set("""canine hereditary congenital inherited familial acquired
generic type form disease disorder syndrome deficiency related associated
primary secondary chronic acute juvenile adult onset early late progressive
of the and with in a an dog dogs""".split())


def norm(x):
    x = x.lower()
    x = re.sub(r"[(),;/]", " ", x)
    x = re.sub(r"[^a-z0-9 ]", " ", x)
    return re.sub(r"\s+", " ", x).strip()


def toks(x):
    return {t for t in norm(x).split() if t not in STOP and len(t) > 2}


def load_index():
    p = os.path.join(DATA, "omia_index.json")
    if not os.path.exists(p):
        sys.exit("missing %s -- run tools/fetch_omia.sh first" % p)
    return json.load(open(p, encoding="utf-8"))


def load_ours():
    rows = []
    for f in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        b = os.path.basename(f)
        if b.startswith(("ofa", "omia", "_")):
            continue
        d = json.load(open(f, encoding="utf-8"))
        if "breeds" not in d:
            continue
        for br in d["breeds"]:
            for c in br["dz"]:
                rows.append((br["name"], c))
    return rows


NOT_MENDELIAN = re.compile(
    r"polygenic|conformation|breed predisposition|breed physiology|"
    r"height-associated|pigment-associated|chondrodystroph|autoimmune|"
    r"immune-mediated|dla-associated|goniodysgenesis|multifactorial", re.I)


# --------------------------------------------------------------------------
class Api(object):
    """OMIA phene search, cached. Their index covers synonyms; ours does not."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.cache = {}
        if os.path.exists(CACHE):
            self.cache = json.load(open(CACHE, encoding="utf-8"))
        self.calls = 0

    def lookup(self, name):
        if name in self.cache:
            return self.cache[name]
        if not self.enabled:
            return None
        url = API + "?" + urllib.parse.urlencode({"q": name})
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as fh:
                d = json.loads(fh.read().decode("utf-8"))
        except Exception as e:
            sys.stderr.write("  api: %s -> %s\n" % (name, e))
            return None
        ids = ["%06d" % i["omia_id"] for i in d.get("items", [])
               if any(s.get("species") == DOG for s in i.get("in_species", []))]
        self.cache[name] = ids
        self.calls += 1
        time.sleep(0.3)
        return ids

    def save(self):
        if self.calls:
            if not os.path.isdir(RAW):
                os.makedirs(RAW)
            json.dump(self.cache, open(CACHE, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=0, sort_keys=True)


# --------------------------------------------------------------------------
def build_matcher(idx, api):
    phenes = idx["phenes"]
    by_id = {p["id"]: p for p in phenes}
    by_full = defaultdict(list)
    for p in phenes:
        by_full[norm(p["name"])].append(p)
    tokmap = [(p, toks(p["name"])) for p in phenes]

    alias_target = {norm(k): norm(v) for k, v in ALIASES.items() if v}

    def family(t):
        # two content tokens, or one distinctive one ("cystinuria", "ichthyosis").
        # A short single token ("cataract") would drag in half the eye records.
        if not t or (len(t) == 1 and len(next(iter(t))) < 7):
            return []
        return [p for p, pt in tokmap if t <= pt]

    def narrow(ps, hint):
        """Prefer family members naming our qualifier: (prcd) -> PRCD-related."""
        if not hint or len(ps) < 2:
            return ps
        h = [w for w in toks(hint) if len(w) > 2]
        if not h:
            return ps
        keep = [p for p in ps if any(w in norm(p["name"]).split() for w in h)]
        return keep or ps

    def match(name):
        """-> (kind, [phene, ...], hint)

        hint is our parenthetical qualifier (prcd, rcd1, Type A and B ...),
        carried through so merge_omia.py can prefer the right family member.
        """
        base = name.split("(")[0].strip()
        parens = re.findall(r"\(([^)]*)\)", name)
        hint = parens[0] if parens else None
        n = norm(name)

        if name in ALIASES and ALIASES[name] is None:
            return ("none-expected", [], None)
        if n in alias_target and alias_target[n] in by_full:
            return ("alias", by_full[alias_target[n]], hint)

        for k in [n, norm(base)] + [norm(p) for p in parens]:
            if k and k in by_full:
                return ("exact", by_full[k], hint)

        # family: full name first (more specific), then the base name
        for t in (toks(name), toks(base)):
            fam = family(t)
            if not fam:
                continue
            fam = narrow(fam, hint)
            # A qualifier can name an entity OMIA files elsewhere: our
            # "Progressive retinal atrophy (prcd)" is their "Progressive
            # rod-cone degeneration, PRCD-related", which shares no token with
            # the family. Look the qualifier up on its own and add what it finds.
            if hint and len(fam) > 1:
                extra = [by_id[i] for i in (api.lookup(hint) or []) if i in by_id]
                seen = {p["id"] for p in fam}
                fam = fam + [p for p in extra if p["id"] not in seen]
            return ("family", fam, hint)

        ids = api.lookup(name) or []
        ps = [by_id[i] for i in ids if i in by_id]
        if ps:
            return ("api", ps, hint)
        return ("miss", [], hint)

    return match


# --------------------------------------------------------------------------
def main():
    idx = load_index()
    ours = load_ours()
    api = Api(enabled="--no-api" not in sys.argv)
    match = build_matcher(idx, api)

    uniq = OrderedDict()
    for breed, c in ours:
        uniq.setdefault(c["n"], []).append((breed, c))

    kinds = defaultdict(list)
    targets = OrderedDict()
    resolved = OrderedDict()
    for name, rows in uniq.items():
        kind, ps, hint = match(name)
        mendelian = not NOT_MENDELIAN.search(
            " ".join(r[1].get("inh", "") for r in rows))
        if kind == "miss" and not mendelian:
            kind = "none-expected"
        kinds[kind].append((name, ps, len(rows)))
        if ps:
            resolved[name] = OrderedDict(
                kind=kind, hint=hint, ids=[p["id"] for p in ps])
        for p in ps:
            targets.setdefault(p["id"], p["name"])
    api.save()

    n_rows = len(ours)
    matched_rows = sum(n for k in ("exact", "alias", "family", "api")
                       for _, _, n in kinds[k])
    print("our conditions (rows)      : %d" % n_rows)
    print("distinct condition names   : %d" % len(uniq))
    print()
    for k, label in (("exact", "exact name match"),
                     ("alias", "matched via ALIASES"),
                     ("family", "matched a gene-split family"),
                     ("api", "resolved by OMIA synonym search"),
                     ("none-expected", "no OMIA record expected"),
                     ("miss", "UNMATCHED")):
        print("  %-32s %4d names" % (label, len(kinds[k])))
    print()
    print("rows reachable by OMIA     : %d of %d" % (matched_rows, n_rows))
    print("distinct OMIA phenes needed: %d" % len(targets))
    if api.calls:
        print("OMIA api calls this run    : %d" % api.calls)
    print()

    print("--- resolved by synonym search (clinical name -> OMIA name) ---")
    for name, ps, n in kinds["api"][:20]:
        print("  %-42s -> %s" % (name[:42], "; ".join(p["name"] for p in ps)[:60]))
    if len(kinds["api"]) > 20:
        print("  ... and %d more" % (len(kinds["api"]) - 20))
    print()

    print("--- families (our one name -> many OMIA phenes) ---")
    fam = sorted(kinds["family"], key=lambda x: -len(x[1]))
    for name, ps, n in fam[:10]:
        print("  %-46s %2d phenes" % (name[:46], len(ps)))
    if len(fam) > 10:
        print("  ... and %d more" % (len(fam) - 10))
    print()

    print("--- UNMATCHED, and the inheritance says single-gene (%d) ---"
          % len(kinds["miss"]))
    for name, _, n in kinds["miss"]:
        print("  %-52s (%d breed%s)" % (name[:52], n, "" if n == 1 else "s"))

    if "--targets" in sys.argv:
        p = os.path.join(DATA, "omia_targets.json")
        json.dump(OrderedDict(ids=list(targets), names=targets,
                              resolved=resolved),
                  open(p, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
        print()
        print("-> %s (%d phene pages to fetch)" % (p, len(targets)))


if __name__ == "__main__":
    main()
