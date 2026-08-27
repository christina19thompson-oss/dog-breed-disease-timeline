#!/usr/bin/env python3
"""Coverage report: how much OFA data maps onto the breeds in data/*.json.

Prints matched / unmatched breeds so aliases can be added deliberately rather
than guessed. Run before wiring prevalence into the dataset.

Usage:  python tools/map_ofa.py
"""
import json, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# OFA name -> our name. Only where a plain normalised match fails.
ALIASES = {
    "COCKER SPANIEL": "Cocker Spaniel (American)",
    "COLLIE": "Rough Collie",
    "POODLE, STANDARD": "Standard Poodle",
    "POODLE, MINIATURE": "Miniature Poodle",
    "SCHNAUZER, MINIATURE": "Miniature Schnauzer",
    "SCHNAUZER, STANDARD": "Standard Schnauzer",
    "SCHNAUZER, GIANT": "Giant Schnauzer",
    "DACHSHUND, MINIATURE SMOOTH": "Dachshund",
    "PINSCHER, MINIATURE": "Miniature Pinscher",
    "GREYHOUND, ITALIAN": "Italian Greyhound",
    "WELSH CORGI, PEMBROKE": "Pembroke Welsh Corgi",
    "SHEPHERD, GERMAN": "German Shepherd Dog",
    "GERMAN SHEPHERD": "German Shepherd Dog",
    "MASTIFF, BULLMASTIFF": None,
    "CHINESE SHAR-PEI": "Chinese Shar-Pei",
    "SHAR-PEI": "Chinese Shar-Pei",
    "ST. BERNARD": "Saint Bernard",
    "PARSON RUSSELL TERRIER": "Parson Russell Terrier",
    "JACK RUSSELL TERRIER": "Parson Russell Terrier",
    "STAFFORDSHIRE BULL TERRIER": "Staffordshire Bull Terrier",
    "AMERICAN STAFFORDSHIRE TERRIER": "American Staffordshire Terrier",
    "WEST HIGHLAND WHITE TERRIER": "West Highland White Terrier",
    "SOFT COATED WHEATEN TERRIER": "Soft Coated Wheaten Terrier",
    "NOVA SCOTIA DUCK TOLLING RETRIEVER": "Nova Scotia Duck Tolling Retriever",
    "PEMBROKE WELSH CORGI": "Pembroke Welsh Corgi",
    "OLD ENGLISH SHEEPDOG": "Old English Sheepdog",
    "GREAT PYRENEES": "Great Pyrenees",
    "PORTUGUESE WATER DOG": "Portuguese Water Dog",
    "FLAT COATED RETRIEVER": "Flat-Coated Retriever",
    "FLAT-COATED RETRIEVER": "Flat-Coated Retriever",
    "GERMAN SHORTHAIRED POINTER": "German Shorthaired Pointer",
    "ENGLISH SPRINGER SPANIEL": "English Springer Spaniel",
    "CAVALIER KING CHARLES SPANIEL": "Cavalier King Charles Spaniel",
    "RHODESIAN RIDGEBACK": "Rhodesian Ridgeback",
    "CHESAPEAKE BAY RETRIEVER": "Chesapeake Bay Retriever",
    "DOBERMAN PINSCHER": "Doberman Pinscher",
    "BERNESE MOUNTAIN DOG": "Bernese Mountain Dog",
    "AUSTRALIAN CATTLE DOG": "Australian Cattle Dog",
    "NORWEGIAN ELKHOUND": "Norwegian Elkhound",
    "BOSTON TERRIER": "Boston Terrier",
    "SHETLAND SHEEPDOG": "Shetland Sheepdog",
}


def norm(x):
    x = x.upper().strip()
    x = re.sub(r"\(.*?\)", " ", x)
    x = x.replace("-", " ").replace(".", " ").replace(",", " ")
    return re.sub(r"\s+", " ", x).strip()


def load_breeds():
    out = {}
    for f in glob.glob(os.path.join(DATA, "*.json")):
        if os.path.basename(f).startswith("ofa"):
            continue
        d = json.load(open(f, encoding="utf-8"))
        if "breeds" not in d:
            continue
        for b in d["breeds"]:
            out[b["name"]] = b
    return out


def main():
    ours = load_breeds()
    ofa = json.load(open(os.path.join(DATA, "ofa_stats.json"), encoding="utf-8"))

    by_norm = {norm(n): n for n in ours}
    alias_norm = {norm(k): v for k, v in ALIASES.items() if v}

    def resolve(ofa_name):
        n = norm(ofa_name)
        if n in alias_norm:
            return alias_norm[n]
        if n in by_norm:
            return by_norm[n]
        return None

    matched_breeds = set()
    hits = 0
    per_test = {}
    ofa_names = set()
    for code, t in ofa.items():
        c = 0
        for row in t["rows"]:
            ofa_names.add(row[0])
            r = resolve(row[0])
            if r:
                matched_breeds.add(r)
                hits += 1
                c += 1
        if c:
            per_test[code] = (t["test"], c)

    print("OFA tests parsed         : %d" % len(ofa))
    print("OFA distinct breed names : %d" % len(ofa_names))
    print("our breeds               : %d" % len(ours))
    print("our breeds with OFA data : %d" % len(matched_breeds))
    print("matched breed-test rows  : %d" % hits)
    print()
    missing = sorted(set(ours) - matched_breeds)
    print("our breeds with NO OFA match (%d):" % len(missing))
    for m in missing:
        print("   -", m)
    print()
    print("richest tests by matched rows:")
    for code, (name, c) in sorted(per_test.items(), key=lambda kv: -kv[1][1])[:22]:
        print("   %-5s %-34s %3d of our breeds" % (code, (name or "?")[:34], c))


if __name__ == "__main__":
    main()
