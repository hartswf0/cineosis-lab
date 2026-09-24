#!/bin/bash
# fetch.sh <list> <outdir> <ext> : download url<TAB>id lines, skip existing, 6 at a time
list=$1; out=$2; ext=$3
awk -F'\t' -v o="$out" -v e="$ext" '{print $1" "o"/"$2"."e}' "$list" | \
  xargs -P 6 -n 2 sh -c '[ -s "$1" ] || curl -sfL --retry 3 -A cineosis-lab -o "$1" "$0" || echo "FAIL $0"'
echo "DONE $(ls "$out" | wc -l) files in $out"
