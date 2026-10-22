#!/bin/zsh
# GOLF SWING SPEED install / rollback (the phone paces the golfer's downswing).
#   install.sh [<repo root>]            patch the working tree + stage ONLY these edits (no commit)
#   install.sh --rollback [<repo root>] take exactly these edits back out of the working tree and the index
#   install.sh --check [<repo root>]    report what would happen
# Touches (exact-line edits, other sessions' edits in the same files are left alone, staged or not):
#   Unity/Assets/Scripts/Game/GolferView.cs, Game/GolfGame.Native.cs, Swing/MotionSwingDetector.cs
# Adds: Unity/Assets/Tests/EditMode/GolfSwingPaceTests.cs (+ .meta)
set -e
W=${0:A:h}; MODE=install
[[ ${1:-} == --rollback ]] && { MODE=rollback; shift; }
[[ ${1:-} == --check ]] && { MODE=check; shift; }
REPO=${1:-${W:h:h}}
cd $REPO
P=$W/scripts/pace_patch.py
FILES=(Swing/MotionSwingDetector.cs Game/GolfGame.Native.cs Game/GolferView.cs)
TEST=Unity/Assets/Tests/EditMode/GolfSwingPaceTests.cs

if [[ $MODE == check ]]; then python3 $P Unity --check; ls -la $TEST 2>/dev/null || echo "$TEST: not installed"; exit 0; fi

# the index copy of each file gets the same edit (or revert) as the working tree, so staging takes only these lines
stage() {   # stage <path in repo> [--revert]
  local f=$1 tmp=$(mktemp -d)/${1:t}
  if git cat-file -e :$f 2>/dev/null; then
    git show :$f > $tmp
    python3 $P $tmp ${2:-} > /dev/null
    local h=$(git hash-object -w $tmp)
    local m=$(git ls-files -s -- $f | awk '{print $1}')
    git update-index --cacheinfo $m,$h,$f
  fi
  rm -f $tmp
}

if [[ $MODE == install ]]; then
  python3 $P Unity
  for f in $FILES; do stage Unity/Assets/Scripts/$f; done
  cp $W/src/Tests/EditMode/GolfSwingPaceTests.cs $TEST
  cp $W/src/Tests/EditMode/GolfSwingPaceTests.cs.meta $TEST.meta
  git add -- $TEST $TEST.meta
  echo "installed + staged (no commit)"
else
  python3 $P Unity --revert
  for f in $FILES; do stage Unity/Assets/Scripts/$f --revert; done
  git rm -q --cached --ignore-unmatch -- $TEST $TEST.meta
  rm -f $TEST $TEST.meta
  echo "rolled back (working tree + index)"
fi
git status --short -- Unity/Assets/Scripts/Game/GolferView.cs Unity/Assets/Scripts/Game/GolfGame.Native.cs Unity/Assets/Scripts/Swing/MotionSwingDetector.cs $TEST $TEST.meta
