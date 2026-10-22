#!/bin/bash
# PROTECTED_FILES: re-hash Unity/Assets/Scripts/Tennis, Unity/Assets/Resources/Tennis, Unity/Assets/Characters and Unity/ProjectSettings
# and compare with work/postcard-look/v3/protected_hashes_start.txt. Prints every difference (changed / new / missing).
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; cd "$R"
START=work/postcard-look/v3/protected_hashes_start.txt
NOW=$(mktemp)
find Unity/Assets/Scripts/Tennis Unity/Assets/Resources/Tennis Unity/Assets/Characters Unity/ProjectSettings -type f ! -name '.DS_Store' ! -name '*.meta' ! -name '*.jpg' ! -name '*.anim' -print0 | xargs -0 shasum -a 256 | sort -k2 > "$NOW"
sort -k2 "$START" > "$NOW.start"
echo "start lines: $(wc -l < "$NOW.start"), now lines: $(wc -l < "$NOW")"
diff "$NOW.start" "$NOW" && echo "PROTECTED_FILES: identical"
rm -f "$NOW" "$NOW.start"
