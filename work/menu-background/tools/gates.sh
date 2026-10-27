#!/bin/zsh
# Flicker numbers for one capture run (MenuBackgroundCapture output): every sequence, whole frame and building pixels only
# (mask_<shot>.png, eroded 2 px). Writes <run>/flicker.txt and the heat maps next to the sequences.
#   work/menu-background/tools/gates.sh <run dir>
TOOLS="$(cd "$(dirname "$0")" && pwd)"; R="$1"
: > "$R/flicker.txt"
for s in "$R"/seq_*; do
  b=$(basename "$s"); shot=${${b#seq_}%_*}
  python3 "$TOOLS/flicker.py" "$s" "$R/an_$b" >> "$R/flicker.txt"
  [ -f "$R/mask_$shot.png" ] && python3 "$TOOLS/flicker.py" "$s" "$R/an_${b}_buildings" --mask "$R/mask_$shot.png" | sed 's/^/BUILDINGS /' >> "$R/flicker.txt"
done
cat "$R/flicker.txt"
