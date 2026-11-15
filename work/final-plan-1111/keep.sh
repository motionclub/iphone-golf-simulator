#!/bin/bash
# keep.sh <repo-relative path>...: save the file as it was before this plan first touched it (once), so ROLLBACK.sh can put it back.
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=$REPO/work/final-plan-1111/install_backup
for f in "$@"; do
  if [ -e "$B/$f" ] || grep -qxF "$f" "$B/NEW_FILES.txt" 2>/dev/null; then continue; fi
  if [ -e "$REPO/$f" ]; then mkdir -p "$B/$(dirname "$f")"; cp -p "$REPO/$f" "$B/$f"; echo "kept $f"
  else echo "$f" >> "$B/NEW_FILES.txt"; echo "new  $f"; fi
done
