#!/usr/bin/env python3
"""Parse the OMIA snapshot into structured JSON.

Two stages, because the two things Phase 2 wants live in different places:

  --index   data/omia_raw/index.html          -> data/omia_index.json
            The dog phene list (taxon 9615). Carries OMIA id, phene name, gene
            symbol and year of first reported key mutation. ~1000 records.
            Enough to assign `gene`; says nothing about inheritance.

  --phenes  data/omia_raw/phene/OMIA*.html    -> data/omia_phenes.json
            Individual phene records, fetched only for matched conditions.
            Carries "Mode of inheritance", the gene table, and the variant
            table -- which is breed-level, the granularity this dataset uses.

Both pages are Django-rendered XHTML and well-formed, unlike the OFA source,
so this parses with straightforward regex over labelled spans and table rows.

Usage:
    python tools/parse_omia.py --index
    python tools/parse_omia.py --phenes
"""
import sys, os, re, json, glob, csv, io, html
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "omia_raw")

DOG_TAXON = "9615"

TAG = re.compile(r"(?s)<[^>]+>")
WS = re.compile(r"\s+")
SCRIPT = re.compile(r"(?is)<(script|style).*?</\1>")


def text(x):
    return WS.sub(" ", html.unescape(TAG.sub(" ", x))).strip()


def rows_of(table):
    for r in re.findall(r"(?is)<tr.*?</tr>", table):
        yield [text(c) for c in re.findall(r"(?is)<t[dh].*?</t[dh]>", r)]


def tables(s):
    return re.findall(r"(?is)<table.*?</table>", SCRIPT.sub(" ", s))


# --------------------------------------------------------------------------
def parse_index():
    src = os.path.join(RAW, "index.html")
    s = open(src, encoding="utf-8", errors="replace").read()

    biggest = max(tables(s), key=lambda t: t.count("<tr"))
    rs = list(rows_of(biggest))
    hdr = rs[0]
    col = {h: i for i, h in enumerate(hdr)}

    def cell(r, name):
        i = col.get(name)
        return r[i] if i is not None and i < len(r) else ""

    out = []
    for r in rs[1:]:
        oid = cell(r, "OMIA ID")                       # "OMIA:001129-9615"
        m = re.match(r"OMIA:(\d+)-(\d+)", oid)
        if not m or m.group(2) != DOG_TAXON:
            continue
        rec = OrderedDict()
        rec["id"] = m.group(1)
        rec["name"] = cell(r, "Phene")
        g = cell(r, "Gene")
        if g:
            rec["gene"] = g
        y = cell(r, "Year Key Mutation First Reported")
        if re.fullmatch(r"\d{4}", y):
            rec["year"] = int(y)
        rec["mod"] = cell(r, "Date Last Modified")
        out.append(rec)

    # gene id map: symbol -> NCBI id + description, restricted to dog
    genes = {}
    gp = os.path.join(RAW, "genes.csv")
    if os.path.exists(gp):
        for g in csv.DictReader(io.open(gp, encoding="utf-8", errors="replace")):
            if g.get("species") != DOG_TAXON:
                continue
            sym = (g.get("symbol") or "").strip()
            if sym:
                genes[sym] = OrderedDict(
                    ncbi=(g.get("ncbi_gene_id") or "").strip() or None,
                    desc=(g.get("gene_desc") or "").strip())

    # causal-mutation table S1: OMIA number -> gene symbol, traits listing dog
    causal = {}
    cp = os.path.join(RAW, "causal_s1.html")
    if os.path.exists(cp):
        s2 = open(cp, encoding="utf-8", errors="replace").read()
        big = max(tables(s2), key=lambda t: t.count("<tr"))
        rs2 = list(rows_of(big))
        h2 = {h: i for i, h in enumerate(rs2[0])}
        need = ("Species", "OMIA number", "Symbol")
        if all(k in h2 for k in need):
            for r in rs2[1:]:
                if len(r) <= max(h2[k] for k in need):
                    continue
                if "dog" not in [x.strip() for x in r[h2["Species"]].split(",")]:
                    continue
                causal[r[h2["OMIA number"]].lstrip("0")] = r[h2["Symbol"]]

    doc = OrderedDict(source="omia.org", taxon=DOG_TAXON,
                      phenes=out, genes=genes, causal=causal)
    p = os.path.join(DATA, "omia_index.json")
    json.dump(doc, open(p, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

    withgene = sum(1 for r in out if "gene" in r)
    print("dog phenes        : %d" % len(out))
    print("  with a gene     : %d" % withgene)
    print("dog genes (csv)   : %d" % len(genes))
    print("causal S1 (dog)   : %d traits" % len(causal))
    print("-> %s" % p)


# --------------------------------------------------------------------------
FIELD = re.compile(
    r'(?s)<span class="record_details_heading">\s*([^<:]+?)\s*:?\s*</span>(.*?)</p>')

WANT = {
    "Mode of inheritance": "inh",
    "Single-gene trait/disorder": "single",
    "Disease-related": "disease",
    "Key variant known": "keyVariant",
    "Year key variant first reported": "year",
    "Species-specific symbol": "symbol",
    "Species-specific name": "altName",
    "Categories": "cats",
}


def parse_phene(path):
    s = open(path, encoding="utf-8", errors="replace").read()
    oid = re.search(r"OMIA(\d+)\.html$", path.replace("\\", "/"))
    rec = OrderedDict(id=oid.group(1) if oid else None)

    t = re.search(r"(?s)<title>(.*?)</title>", s)
    if t:
        m = re.match(r"OMIA:\d+-\d+:\s*(.*?)\s+in\s+Canis", text(t.group(1)))
        if m:
            rec["name"] = m.group(1)

    body = SCRIPT.sub(" ", s)
    for label, val in FIELD.findall(body):
        key = WANT.get(label.strip())
        if not key:
            continue
        v = text(val)
        if not v:
            continue
        if key == "year" and re.fullmatch(r"\d{4}", v):
            rec[key] = int(v)
        elif key in ("single", "disease", "keyVariant"):
            rec[key] = v.lower().startswith("y")
        else:
            rec[key] = v

    for tb in tables(body):
        rs = list(rows_of(tb))
        if not rs:
            continue
        hdr = rs[0]
        if hdr[:2] == ["Symbol", "Description"]:
            rec["genes"] = [r[0] for r in rs[1:] if r and r[0]]
        elif hdr and hdr[0] == "OMIA Variant ID":
            h = {x: i for i, x in enumerate(hdr)}

            def c(r, k):
                i = h.get(k)
                return r[i].strip() if i is not None and i < len(r) else ""

            vs = []
            for r in rs[1:]:
                if not r or not c(r, "OMIA Variant ID"):
                    continue
                v = OrderedDict()
                for k, kk in (("Breed(s)", "breeds"), ("Gene", "gene"),
                              ("Variant Type", "type"), ("Variant Effect", "effect"),
                              ("c. or n.", "c"), ("p.", "p"),
                              ("Year Published", "year"), ("PubMed ID(s)", "pmid")):
                    val = c(r, k)
                    if val:
                        v[kk] = val
                if v:
                    vs.append(v)
            if vs:
                rec["variants"] = vs
    return rec


def parse_phenes():
    paths = sorted(glob.glob(os.path.join(RAW, "phene", "OMIA*.html")))
    out = OrderedDict()
    for p in paths:
        r = parse_phene(p)
        if r.get("id"):
            out[r["id"]] = r

    q = os.path.join(DATA, "omia_phenes.json")
    json.dump(out, open(q, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

    inh = sum(1 for r in out.values() if r.get("inh"))
    gen = sum(1 for r in out.values() if r.get("genes"))
    var = sum(len(r.get("variants", [])) for r in out.values())
    print("phene records     : %d" % len(out))
    print("  mode of inherit : %d" % inh)
    print("  with gene table : %d" % gen)
    print("  variants        : %d" % var)
    print("-> %s" % q)


if __name__ == "__main__":
    a = sys.argv[1:] or ["--index"]
    if "--index" in a:
        parse_index()
    if "--phenes" in a:
        parse_phenes()
