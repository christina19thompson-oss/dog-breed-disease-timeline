#!/usr/bin/env bash
# Refresh the OMIA (Online Mendelian Inheritance in Animals) snapshot.
#
# Three stages, all resumable — rerun after an interruption and it picks up.
#
#   1. the dog phene index      one request, ~1000 records, carries gene + year
#   2. supporting tables        gene id map, causal-mutation table S1
#   3. per-phene pages          ONLY those map_omia.py matched, for `inh`
#
# Stage 3 is why this is not a single fetch: mode of inheritance appears on the
# individual phene record and nowhere in the index. Matching first keeps it to
# a few hundred requests instead of a thousand.
#
# The full MySQL/XML dumps at /static/omia.sql.gz are 198-262 MB and hold every
# species; the dog subset reachable through these pages is ~1 MB. Not worth it.
#
# Data: Nicholas FW, Tammen I, & Sydney Informatics Hub (1995). OMIA.
# https://omia.org/  doi:10.25910/2AMR-PV70   Cite it — see SOURCES.md.
set -euo pipefail

cd "$(dirname "$0")/.."
RAW=data/omia_raw
UA="Mozilla/5.0 (canine-onset-atlas; veterinary reference; +https://omia.org/)"
DELAY="${OMIA_DELAY:-0.4}"        # seconds between phene requests, be polite

mkdir -p "$RAW/phene"

get() {  # get <url> <out>
  curl -sS --fail --max-time 120 --retry 2 --retry-delay 3 \
    -A "$UA" -e "https://omia.org/" "$1" -o "$2"
}

# ---- stage 1: dog phene index (taxon 9615) --------------------------------
echo "[1/3] dog phene index"
get "https://omia.org/results/?search_type=advanced&gb_species_id=9615" \
    "$RAW/index.html"
printf '      %s bytes\n' "$(wc -c < "$RAW/index.html")"

# ---- stage 2: supporting tables -------------------------------------------
echo "[2/3] supporting tables"
get "https://omia.org/download/csv/genes/"              "$RAW/genes.csv"
get "https://omia.org/download/causal_mutations/?format=X1" "$RAW/causal_s1.html"
printf '      genes.csv %s bytes, causal_s1.html %s bytes\n' \
  "$(wc -c < "$RAW/genes.csv")" "$(wc -c < "$RAW/causal_s1.html")"

python tools/parse_omia.py --index

# ---- stage 3: phene records for matched conditions only -------------------
python tools/map_omia.py --targets            # writes data/omia_targets.json

echo "[3/3] phene records"
n=0; got=0; skip=0; fail=0
# tr -d '\r': python writes CRLF on Windows, and a stray CR inside the URL is
# rejected by curl before the request is ever made.
while read -r id; do
  [ -n "$id" ] || continue
  n=$((n+1))
  out="$RAW/phene/OMIA${id}.html"
  if [ -s "$out" ]; then skip=$((skip+1)); continue; fi
  # one phene that 404s must not abandon the other 270
  if get "https://omia.org/OMIA${id}/9615/" "$out"; then
    got=$((got+1))
    # not `[ ] && printf` -- a false test is a non-zero last command, and
    # `set -e` would take that as the loop body failing
    if [ $((got % 25)) -eq 0 ]; then printf '      %d fetched\n' "$got"; fi
  else
    fail=$((fail+1)); rm -f "$out"
    printf '      ! OMIA%s unavailable\n' "$id"
  fi
  sleep "$DELAY"
done < <(python -c "
import json;print('\n'.join(json.load(open('data/omia_targets.json',encoding='utf-8'))['ids']))
" | tr -d '\r')
printf '      %d targets: %d fetched, %d present, %d failed\n' "$n" "$got" "$skip" "$fail"

python tools/parse_omia.py --phenes

printf '\nnext: python tools/merge_omia.py && python build.py\n'
