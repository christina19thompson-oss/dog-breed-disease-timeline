#!/usr/bin/env python3
"""Parse OFA breed statistics into structured JSON.

Source endpoint (the one behind ofa.org/diseases/disease-statistics/):
    https://api.ofa.org/api/ds.php

The response holds one <table class='ds_statistics' data-regcode='XX'> per test.
Markup is HTML4-loose: <tr> and <td> are frequently unclosed, and alternative
column sets are parked inside <!-- --> comments, so this parses by splitting on
open tags rather than assuming well-formed markup.

Usage:
    python tools/parse_ofa.py data/ofa_raw.html data/ofa_stats.json
"""
import sys, json, re, html
from collections import OrderedDict

raw_path = sys.argv[1] if len(sys.argv) > 1 else "data/ofa_raw.html"
out_path = sys.argv[2] if len(sys.argv) > 2 else "data/ofa_stats.json"

s = open(raw_path, encoding="utf-8", errors="replace").read()
s = re.sub(r"<!--.*?-->", "", s, flags=re.S)          # drop alternate column sets

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"[\s ]+")


def text(x):
    return WS.sub(" ", html.unescape(TAG.sub(" ", x))).strip()


def num(x):
    x = x.replace(",", "").replace("%", "").strip()
    if x in ("", "-", "--"):
        return None
    try:
        return int(x) if re.fullmatch(r"-?\d+", x) else float(x)
    except ValueError:
        return None


# split the document into per-table chunks (tables are not reliably closed)
starts = [(m.group(1), m.start(), m.end())
          for m in re.finditer(r"<table class='ds_statistics' data-regcode='([A-Z]+)'[^>]*>", s)]

out = OrderedDict()
for idx, (code, st, en) in enumerate(starts):
    end = starts[idx + 1][1] if idx + 1 < len(starts) else len(s)
    chunk = s[en:end]
    chunk = chunk.split("</table>")[0]

    rows_raw = re.split(r"<tr[^>]*>", chunk)
    title, header, rows = "", [], []
    for r in rows_raw:
        cells = [text(c) for c in re.split(r"<t[dh][^>]*>", r)[1:]]
        cells = [c for c in cells if c != ""]
        if not cells:
            continue
        is_header = "<th" in r
        if is_header:
            if len(cells) == 1 and not title:
                title = cells[0]
            elif len(cells) > 1:
                header = cells
        else:
            if len(cells) < 3:
                continue
            breed = cells[0]
            if not re.search(r"[A-Za-z]", breed):
                continue
            vals = [num(c) for c in cells[1:]]
            rows.append([breed] + vals)

    if rows:
        out[code] = {"test": title, "columns": header, "rows": rows}

json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

tot = sum(len(v["rows"]) for v in out.values())
print("tests: %d   breed-rows: %d   -> %s" % (len(out), tot, out_path))
print()
for code in ["HD", "EL", "PA", "EYE", "ACA", "BCA", "TH", "DM", "EIC", "VWD", "CEA"]:
    if code in out:
        v = out[code]
        print("%-5s %-26s cols=%s" % (code, (v["test"] or "?")[:26], v["columns"][:6]))
        for r in v["rows"][:2]:
            print("        ", r[:7])
