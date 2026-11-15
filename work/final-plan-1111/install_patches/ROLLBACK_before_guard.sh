#!/bin/bash
# ROLLBACK.sh: put every file this plan changed back to how it was on 2026-11-11 before Phase 0 started.
# Files the plan added are moved into work/final-plan-1111/rolled_back/ (nothing is deleted).
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=$REPO/work/final-plan-1111/install_backup
cd "$B" || exit 1
find . -type f ! -name NEW_FILES.txt | sed 's|^\./||' | while read -r f; do cp -p "$B/$f" "$REPO/$f" && echo "restored $f"; done
if [ -f NEW_FILES.txt ]; then
  while read -r f; do
    for x in "$f" "$f.meta"; do
      [ -e "$REPO/$x" ] || continue
      mkdir -p "$REPO/work/final-plan-1111/rolled_back/$(dirname "$x")"; mv "$REPO/$x" "$REPO/work/final-plan-1111/rolled_back/$x" && echo "moved out $x"
    done
  done < NEW_FILES.txt
fi
