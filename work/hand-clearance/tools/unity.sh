#!/bin/zsh
# unity.sh <log> [extra args...]  - one batch Unity run on this job's clone: muted, through the machine-wide gate
# (work/delegation-2026-10-17/heavy.sh) and booked on SCHEDULE.md while it runs.
CLONE=${CLONE:-$HOME/hand-clearance-work/UnityClone}
DELEG=${0:A:h:h:h}/delegation-2026-10-17
LOG=$1; shift
LINE="| chat 3 hand-clearance | ${UNITY_WHAT:-batch Unity: $*} | unity | $(date +%H:%M) | ${UNITY_MINUTES:-?} |"
echo "$LINE" >> $DELEG/SCHEDULE.md
GOLF_MUTE=1 $DELEG/heavy.sh unity /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $CLONE -logFile $LOG "$@"
rc=$?
python3 - "$DELEG/SCHEDULE.md" "$LINE" <<'PY'
import sys
p, line = sys.argv[1], sys.argv[2]
rows = open(p).read().split('\n'); out = []; removed = False
for r in rows:
    if not removed and r == line: removed = True; continue
    out.append(r)
open(p, 'w').write('\n'.join(out))
PY
echo "exit $rc" >> $LOG
