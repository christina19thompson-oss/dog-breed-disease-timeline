"""Shared writer: one breed per block, one condition per line.

Keeps data/*.json diffable and hand-editable, matching the original layout.
"""
import json
from collections import OrderedDict

NL = "\n"


def dump_file(d):
    blocks = []
    for b in d["breeds"]:
        head = OrderedDict()
        for k in ("name", "size", "life", "ofa"):
            if k in b:
                head[k] = b[k]
        for k in b:
            if k not in head and k not in ("dz", "group"):
                head[k] = b[k]
        h = json.dumps(head, ensure_ascii=False, separators=(",", ":"))[1:-1]
        dz = ("," + NL + " ").join(
            json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in b["dz"])
        blocks.append("{" + h + ',"dz":[' + NL + " " + dz + NL + "]}")
    return ("{" + NL
            + '"group": ' + json.dumps(d["group"], ensure_ascii=False) + "," + NL
            + '"breeds": [' + NL
            + ("," + NL).join(blocks) + NL
            + "]}" + NL)


def write(path, d):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dump_file(d))
