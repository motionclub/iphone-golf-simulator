#!/bin/bash
# ROLLBACK.sh: put every file this plan changed back to how it was on 2026-11-11 before Phase 0 started.
# Files the plan added are moved into work/final-plan-1111/rolled_back/ (nothing is deleted).
#
# GUARDED since 2026-11-12 22:30: other chats now edit some of the same files (the "Emotes and sports animations" chat added
# its empty-hands call to HubHeroAnimator.cs). A whole-file restore would silently delete their work, so:
#   - a file is restored only if it is still exactly as this plan left it (install_patches/MANIFEST.sha256);
#   - HubHeroAnimator.cs is not restored whole: only this plan's own lines are taken out (install_patches/HubHeroAnimator.mine.patch);
#   - anything else that changed since is SKIPPED and listed at the end, to be undone by hand or with its switch
#     (switches: work/final-plan-1111/GATE_RESULTS.md, "INSTALLED in the game project").
# FORCE=1 restores every file whole, as the script did before (this DELETES other chats' edits in those files).
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$REPO/work/final-plan-1111; B=$W/install_backup; P=$W/install_patches
cd "$B" || exit 1
skipped=()
while read -r f; do
  if [ "$FORCE" = 1 ]; then cp -p "$B/$f" "$REPO/$f" && echo "restored $f (forced)"; continue; fi
  if [ "$f" = "Unity/Assets/Scripts/Hub/HubHeroAnimator.cs" ]; then
    if cmp -s "$B/$f" "$REPO/$f"; then echo "already as before: $f"
    elif patch -R --dry-run -s "$REPO/$f" "$P/HubHeroAnimator.mine.patch" >/dev/null 2>&1; then patch -R -s "$REPO/$f" "$P/HubHeroAnimator.mine.patch" && echo "took this plan's lines out of $f (other chats' lines kept)"
    else skipped+=("$f (this plan's lines no longer come out cleanly: use PLAZA_ELBOW=0 PLAZA_WRIST=0 FEMALE_WALK_CURL=0 CLEARANCE_FreeArmShare=1, or edit by hand)"); fi
    continue
  fi
  want=$(grep -F "  $f" "$P/MANIFEST.sha256" | head -1 | cut -d' ' -f1)
  have=$( [ -f "$REPO/$f" ] && shasum -a 256 "$REPO/$f" | cut -d' ' -f1 )
  if [ -n "$want" ] && [ "$want" = "$have" ]; then cp -p "$B/$f" "$REPO/$f" && echo "restored $f"
  elif cmp -s "$B/$f" "$REPO/$f"; then echo "already as before: $f"
  else skipped+=("$f (changed by someone else since this plan's install)"); fi
done < <(find . -type f ! -name NEW_FILES.txt | sed 's|^\./||' | sort)
if [ -f NEW_FILES.txt ]; then
  while read -r f; do
    for x in "$f" "$f.meta"; do
      [ -e "$REPO/$x" ] || continue
      mkdir -p "$REPO/work/final-plan-1111/rolled_back/$(dirname "$x")"; mv "$REPO/$x" "$REPO/work/final-plan-1111/rolled_back/$x" && echo "moved out $x"
    done
  done < NEW_FILES.txt
fi
if [ ${#skipped[@]} -gt 0 ]; then echo; echo "NOT RESTORED (${#skipped[@]}):"; for s in "${skipped[@]}"; do echo "  $s"; done; echo "FORCE=1 restores them whole and deletes the other chats' edits in them."; fi
