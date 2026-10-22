#!/bin/bash
# PROTECTED_FILES for calibration round 2.
# (a) the files the user named (QualitySettings.asset, the hero shaders, TennisURP / HeroBaseStudioURP assets + renderers, TennisWater / TennisSky / TennisPost, Serve / Locker scripts if present)
#     against the job-start hashes (v2/protected_hashes_start.txt): must be identical.
# (b) the whole protected tree against the snapshot taken at the start of THIS round (v2/calibrate/r2/protected_hashes_r2_snapshot1.txt, 16:23): must be identical,
#     i.e. nothing in it changed while this agent worked (other chats' edits since 09:28 are listed by the old protected_check.sh and are not ours).
R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; cd "$R"
START=work/postcard-look/v2/protected_hashes_start.txt
SNAP=work/postcard-look/v2/calibrate/r2/protected_hashes_r2_snapshot1.txt
NOW=$(mktemp)
find Unity/Assets/Scripts/Tennis Unity/Assets/Resources/Tennis Unity/Assets/Characters Unity/ProjectSettings -type f ! -name '.DS_Store' ! -name '*.meta' ! -name '*.jpg' ! -name '*.anim' -print0 | xargs -0 shasum -a 256 | sort -k2 > "$NOW"
echo "== (a) named files vs job start"
pat='ProjectSettings/QualitySettings.asset|Characters/.*\.shader|Resources/Tennis/Shaders/|TennisPost|TennisURP|HeroBaseStudio|Resources/Tennis/Rendering/'
grep -E "$pat" "$START" | sort -k2 > "$NOW.a_start"; grep -E "$pat" "$NOW" | sort -k2 > "$NOW.a_now"
echo "named files at start: $(wc -l < $NOW.a_start), now: $(wc -l < $NOW.a_now)"
if diff "$NOW.a_start" "$NOW.a_now"; then echo "NAMED_PROTECTED_FILES: identical"; else echo "NAMED_PROTECTED_FILES: DIFFERENT"; fi
echo "== (b) whole protected tree vs the round-2 start snapshot"
sort -k2 "$SNAP" > "$NOW.b_start"
if diff "$NOW.b_start" "$NOW"; then echo "PROTECTED_TREE_DURING_THIS_ROUND: identical ($(wc -l < $NOW) files)"; else echo "PROTECTED_TREE_DURING_THIS_ROUND: DIFFERENT (see lines above: another chat edited during this round)"; fi
rm -f "$NOW" "$NOW".*
