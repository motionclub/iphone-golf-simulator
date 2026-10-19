#!/bin/zsh
# versus_away.sh <label> [ENV=...]: a two-phone versus tennis match in two Unity clones (seat 0 windowed + recorded in
# ~/integration-UnityClone, seat 1 batch in ~/integration-UnityClone2) where one phone leaves the app mid-match (MP_AWAY_SEAT,
# MP_AWAY_AT, MP_AWAY_FOR). Both editors go through the heavy.sh gate and are booked on SCHEDULE.md. Muted.
HERE=${0:A:h}; REPO=${HERE:h:h:h}; DELEG=$REPO/work/delegation-2026-10-17
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
label=$1; shift
OUT=$REPO/work/integration-1018/away/$label; mkdir -p $OUT
F="GolfArcade.PlayTests.VersusPeerCapture.TennisVersusPeer"
LINE="| chat 12 integration | versus away test $label (2 editors) | unity x2 | $(date +%H:%M) | 8 |"
echo "$LINE" >> $DELEG/SCHEDULE.md
W=${WSEAT:-0}; B=$((1-W))   # seat W windowed + recorded, seat B batch
( env GOLF_MUTE=1 MP_VERSUS=1 MP_SEAT=$B MP_OUT=$OUT "$@" $DELEG/heavy.sh unity $UNITY -batchmode -projectPath $HOME/integration-work/Unity2 -runTests -testPlatform PlayMode -testFilter $F -testResults $OUT/seat$B.xml -logFile $OUT/seat$B.log ) &
P1=$!
env GOLF_MUTE=1 MP_VERSUS=1 MP_SEAT=$W MP_RECORD=1 MP_OUT=$OUT "$@" $DELEG/heavy.sh unity $UNITY -projectPath $HOME/integration-work/Unity1 -runTests -testPlatform PlayMode -testFilter $F -testResults $OUT/seat$W.xml -logFile $OUT/seat$W.log
wait $P1
python3 - "$DELEG/SCHEDULE.md" "$LINE" <<'PY'
import sys
p, line = sys.argv[1], sys.argv[2]
rows = open(p).read().split('\n'); out = []; removed = False
for r in rows:
    if not removed and r == line: removed = True; continue
    out.append(r)
open(p, 'w').write('\n'.join(out))
PY
for s in 0 1; do python3 - $OUT/seat$s.xml <<'PY'
import sys, xml.etree.ElementTree as E
try: r=E.parse(sys.argv[1]).getroot()
except Exception as e: print(sys.argv[1], "no results", e); sys.exit()
for t in r.iter('test-case'):
    m=t.find('.//message'); print(sys.argv[1].split('/')[-1], t.get('result'), t.get('duration'), (m.text or '').strip()[:300] if m is not None else '')
PY
done
