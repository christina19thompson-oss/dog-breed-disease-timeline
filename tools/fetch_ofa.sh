#!/usr/bin/env bash
# Refresh the OFA breed statistics snapshot.
#
# ofa.org/diseases/disease-statistics/ renders its tables from this endpoint;
# a plain fetch of the page itself returns "Searching Database, Please wait".
# One request pulls every test at once (~5 MB), so this runs once, not per breed.
set -euo pipefail

cd "$(dirname "$0")/.."
OUT=data/ofa_raw.html

curl -sS --fail --max-time 120 \
  -A "Mozilla/5.0 (canine-onset-atlas; veterinary reference)" \
  -e "https://ofa.org/diseases/disease-statistics/" \
  "https://api.ofa.org/api/ds.php" \
  -o "$OUT"

printf 'fetched %s bytes -> %s\n' "$(wc -c < "$OUT")" "$OUT"
printf 'next: python tools/parse_ofa.py && python tools/merge_ofa.py && python build.py\n'
