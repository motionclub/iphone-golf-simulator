#!/bin/bash
# Serialises Unity batch runs for the POSTCARD_LOOK job (and waits for any other chat's Unity / xcodebuild:
# overlapping Unity or xcodebuild processes crash Burst with SIGSEGV).
# usage: work/postcard-look/heavy.sh <label> <command> [args...]
HERE="$(cd "$(dirname "$0")" && pwd)"
L="$HERE/heavy.lock"
label="$1"; shift
others() { pgrep -f "^/Applications/Unity/Hub/Editor/[^ ]*/Unity.app/Contents/MacOS/Unity |^/Applications/Xcode[^ ]*/Contents/Developer/usr/bin/xcodebuild |^xcodebuild " >/dev/null 2>&1; }
while true; do
  if [ -d "$L" ] && [ $(( $(date +%s) - $(stat -f %m "$L") )) -gt 10800 ]; then rm -rf "$L"; fi
  if mkdir "$L" 2>/dev/null; then
    if others; then rmdir "$L" 2>/dev/null || rm -rf "$L"; sleep 15; continue; fi
    break
  fi
  sleep 10
done
echo "$label | $(date)" > "$L/owner"
trap 'rm -rf "$L"' EXIT INT TERM
"$@"
