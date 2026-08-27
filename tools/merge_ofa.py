#!/usr/bin/env python3
"""Write OFA screening results onto data/*.json.

IMPORTANT — what this number is, and is not.

OFA statistics come from radiographs, exams and DNA tests that owners chose to
submit, overwhelmingly on breeding candidates. They are NOT breed prevalence:

  * phenotypic screens (hips, elbows, patella, eyes, cardiac, thyroid) are biased
    LOW, because obviously affected animals are frequently never submitted;
  * DNA test results describe the tested breeding population, where affected
    animals are actively selected against, not the pet population.

The field is therefore named `ofa`, never `prev`, and always carries the metric
label so the number can never be read as something it isn't.

Two levels are written:

  breed.ofa          every OFA test held for that breed, raw. Composite screens
                     (EYE, CA, ACA, BCA) live only here, because "abnormal on a
                     congenital cardiac exam" does not belong to any one condition.

  condition.ofa      only where an OFA test is specific to that condition
                     (hip dysplasia -> HD, degenerative myelopathy -> DM, ...).

Idempotent: re-running replaces both rather than accumulating.

Usage:  python tools/merge_ofa.py [--dry-run]
"""
import json, glob, os, re, sys, io
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DRY = "--dry-run" in sys.argv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from map_ofa import ALIASES, norm
from _fmt import write as write_breed_file

# Tests specific enough to attach to a single condition.
# (code, regex over our condition name, column to read as the headline number)
SPECIFIC = [
    ("HD",  r"\bhip dysplasia\b",                            "Dysplastic"),
    ("EL",  r"\belbow dysplasia\b",                          "Abnormal"),
    ("PA",  r"\bpatellar luxation\b",                        "Abnormal"),
    ("SH",  r"osteochondrosis of the shoulder",              "Abnormal"),
    ("TH",  r"\bhypothyroid",                                "Autoimmune Thyroiditis"),
    ("DM",  r"degenerative myelopathy",                      "Abnormal"),
    ("EIC", r"exercise[- ]induced collapse",                 "Abnormal"),
    ("CEA", r"collie eye anomaly",                           "Abnormal"),
    ("PRA", r"progressive retinal atrophy",                  "Abnormal"),
    ("NCL", r"neuronal ceroid lipofuscinosis",               "Abnormal"),
    ("CY",  r"cystinuria",                                   "Abnormal"),
    ("HU",  r"hyperuricosuria|urate urolithiasis",           "Abnormal"),
    ("VW",  r"von willebrand",                               "Abnormal"),
    ("CDY", r"intervertebral disc",                          "Abnormal"),
    ("CMR", r"multifocal retinopathy",                       "Abnormal"),
    ("BR",  r"congenital deafness|\bdeafness\b",             "Abnormal"),
    ("CMO", r"craniomandibular osteopathy",                  "Abnormal"),
    ("PLL", r"lens luxation",                                "Abnormal"),
    ("PFK", r"phosphofructokinase",                          "Abnormal"),
    ("CNM", r"centronuclear myopathy",                       "Abnormal"),
    ("SA",  r"sebaceous adenitis",                           "Abnormal"),
    ("CU",  r"copper-associated hepatopathy",                "Abnormal"),
]

# Composite screens: kept at breed level only.
COMPOSITE = {
    "EYE": "Abnormal", "CA": "Abnormal", "ACA": "Abnormal",
    "BCA": "Abnormal", "DE": "Abnormal",
}

POOLED = {"POODLE"}   # one OFA row covering more than one of our breeds


def col_index(columns, want):
    for i, c in enumerate(columns):
        if want.lower() in c.lower():
            return i
    return None


def pack(row, cols, metric, code, pooled):
    ci, ni = col_index(cols, metric), col_index(cols, "Evaluations")
    if ci is None or ni is None or ci >= len(row) or ni >= len(row):
        return None
    if row[ci] is None or row[ni] is None:
        return None
    o = OrderedDict()
    o["pct"] = row[ci]
    o["metric"] = cols[ci].strip()
    o["n"] = row[ni]
    o["test"] = code
    o["src"] = "ofa2026"
    cri = col_index(cols, "Carrier")
    if cri is not None and cri < len(row) and row[cri] is not None:
        o["carrier"] = row[cri]
    if pooled:
        o["pooled"] = True
    return o


def main():
    ofa = json.load(open(os.path.join(DATA, "ofa_stats.json"), encoding="utf-8"))
    alias_norm = {norm(k): v for k, v in ALIASES.items() if v}

    files = [f for f in glob.glob(os.path.join(DATA, "*.json"))
             if not os.path.basename(f).startswith("ofa")]
    breeds = {}
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        if "breeds" in d:
            for b in d["breeds"]:
                breeds[b["name"]] = b
    by_norm = {norm(n): n for n in breeds}

    def resolve(name):
        n = norm(name)
        if n in alias_norm:
            return [alias_norm[n]]
        if n in by_norm:
            return [by_norm[n]]
        if name.upper() in POOLED:
            return [x for x in breeds if x.endswith("Poodle")]
        return []

    lookup = {}
    for code, t in ofa.items():
        for row in t["rows"]:
            for ours in resolve(row[0]):
                lookup.setdefault(ours, {})[code] = (row, t["columns"], row[0].upper() in POOLED)

    n_breed, n_cond, bad = 0, 0, []
    detail = []
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        if "breeds" not in d:
            continue
        for b in d["breeds"]:
            b.pop("ofa", None)
            tests = lookup.get(b["name"], {})
            block = OrderedDict()
            for code in sorted(tests):
                row, cols, pooled = tests[code]
                metric = dict(COMPOSITE).get(code) or next(
                    (m for c, _p, m in SPECIFIC if c == code), "Abnormal")
                p = pack(row, cols, metric, code, pooled)
                if p:
                    p.pop("test", None)
                    block[code] = p
            if block:
                b["ofa"] = block
                n_breed += 1

            for dz in b["dz"]:
                dz.pop("prev", None)
                dz.pop("ofa", None)
                for code, pattern, metric in SPECIFIC:
                    if code not in tests or not re.search(pattern, dz["n"], re.I):
                        continue
                    row, cols, pooled = tests[code]
                    p = pack(row, cols, metric, code, pooled)
                    if not p:
                        bad.append((b["name"], dz["n"], code))
                        break
                    dz["ofa"] = p
                    n_cond += 1
                    detail.append((b["name"], dz["n"][:40], code, p["pct"], p["n"]))
                    break
        if not DRY:
            write_breed_file(f, d)

    print("breeds given an OFA block     : %d%s" % (n_breed, "   (dry run)" if DRY else ""))
    print("conditions given an OFA figure: %d" % n_cond)
    print("unusable matches              : %d" % len(bad))
    print()
    for row in detail[:16]:
        print("   %-28s %-40s %-4s %5s%%  n=%s" % row)
    if len(detail) > 16:
        print("   ... and %d more" % (len(detail) - 16))


if __name__ == "__main__":
    main()
