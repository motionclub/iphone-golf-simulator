#!/bin/bash
# utest.sh <label> <EditMode|PlayMode> [testFilter]: run tests in the plan's project copy (never the shared project), muted, through heavy.sh.
# EditMode runs in batch mode; PlayMode runs windowed (batch mode never renders a frame).
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
C=$HOME/unity-clones/${CLONE:-final-plan}/Unity
O=$REPO/work/final-plan-1111/logs; mkdir -p $O
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
label=$1; platform=$2; filter=$3
args=(-projectPath "$C" -runTests -testPlatform "$platform" -testResults "$O/$label.xml" -logFile "$O/$label.log")
[ "$platform" = EditMode ] && args=(-batchmode "${args[@]}")
[ -n "$filter" ] && args+=(-testFilter "$filter")
rm -f "$O/$label.xml" "$C/Temp/UnityLockfile"
start=$(date +%s)
env GOLF_MUTE=1 $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY "${args[@]}"
echo "unity exit $? after $(( $(date +%s) - start )) s"
python3 - "$O/$label.xml" <<'PY'
import sys, xml.etree.ElementTree as E
try: r = E.parse(sys.argv[1]).getroot()
except Exception as e: print("no results:", e); sys.exit()
print(f"total={r.get('total')} passed={r.get('passed')} failed={r.get('failed')} skipped={r.get('skipped')} duration={float(r.get('duration')):.0f}s")
for t in r.iter('test-case'):
    if t.get('result') != 'Passed':
        m = t.find('.//message'); print(' ', t.get('result'), t.get('fullname'), ((m.text or '').strip()[:500] if m is not None else ''))
PY
