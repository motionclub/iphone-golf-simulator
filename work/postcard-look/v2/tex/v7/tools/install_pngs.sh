#!/bin/bash
# usage: install_pngs.sh <generated dir>   copies every generated PNG whose sha256 differs from the installed one into Unity/Assets/Resources/Course/Look/ (atomic: temp file + mv; never touches a .meta)
R="$(cd "$(dirname "$0")/../../../../../.." && pwd)"; SRC="$1"; DST="$R/Unity/Assets/Resources/Course/Look"
n=0
for f in "$SRC"/*.png; do
  b=$(basename "$f"); [ -f "$DST/$b" ] || { echo "skip (not a Look map): $b"; continue; }
  if [ "$(shasum -a 256 "$f" | cut -d' ' -f1)" != "$(shasum -a 256 "$DST/$b" | cut -d' ' -f1)" ]; then
    cp "$f" "$DST/.$b.tmp" && mv "$DST/.$b.tmp" "$DST/$b" && echo "installed $b" && n=$((n+1))
  fi
done
echo "installed $n file(s); Look/ = $(du -sk "$DST" | cut -f1) KB"
