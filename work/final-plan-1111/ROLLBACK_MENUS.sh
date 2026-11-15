#!/bin/bash
# ROLLBACK_MENUS.sh: put the iOS menu / locker / lobby heroes back to how they were before the 2026-11-12 re-export
# (work/final-plan-1111/sync_menus.sh). Only files that differ are copied back. The game project (Unity/) is not touched:
# that is ROLLBACK.sh. After this the menus show the old bodies and clothes again while the game shows the new ones.
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=$REPO/work/final-plan-1111/install_backup_menus
for pair in "CharacterAssets:GolfArcade/Unity/CharacterAssets" "VisualGolden:GolfArcadeTests/VisualGolden"; do
  src=$B/${pair%%:*}; dst=$REPO/${pair##*:}
  for f in "$src"/*; do t=$dst/$(basename "$f"); cmp -s "$f" "$t" || { cp -p "$f" "$t" && echo "restored ${pair##*:}/$(basename "$f")"; }; done
done
[ -f $REPO/work/final-plan-1111/install_backup/work/hero-sync/look_sources.txt ] && cp -p $REPO/work/final-plan-1111/install_backup/work/hero-sync/look_sources.txt $REPO/work/hero-sync/look_sources.txt && echo "restored work/hero-sync/look_sources.txt"
