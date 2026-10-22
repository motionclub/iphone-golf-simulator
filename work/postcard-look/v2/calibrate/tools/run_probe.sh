#!/bin/bash
# usage: run_probe.sh <label>
# GolfLookProbe (play mode, the real HoleView.BuildFromModel path) on G's ground-library smoke FBXs (work/postcard-look/lib_ground/smoke_hole0N/look/hole_0N.fbx):
# real play surfaces + LK_ ground + cliff skin + graded ocean + thin shelf + WATER_SURF patches (+ lava + LAVA_LIGHT empties on hole 10), NO props. The real Resources/Course FBXs are NOT touched:
# the three FBXs are copied (with a fresh-GUID .meta of the real import settings) to Unity/Assets/_GolfLookProbe only while this script holds heavy.sh's lock, and removed on exit.
# Output: work/postcard-look/v2/calibrate/probe_<label>/ (JPG views + probe_report.txt), logs/probe_<label>.log
R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; PL="$1"
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT="$R/work/postcard-look/v2/calibrate/probe_$PL"; mkdir -p "$OUT" "$R/work/postcard-look/v2/calibrate/logs"
inner() {
  A="$R/Unity/Assets/_GolfLookProbe"
  trap 'rm -rf "$A" "$A.meta"' EXIT INT TERM
  rm -rf "$A" "$A.meta"; mkdir -p "$A"
  for n in 08 09 10; do
    src="$R/work/postcard-look/lib_ground/smoke_hole$n/look/hole_$n.fbx"
    [ "$n" = "10" ] && [ -n "$PROBE_FBX10" ] && src="$PROBE_FBX10"      # optional: another hole 10 look FBX (a scratch build, e.g. smoke_piece.py output)
    cp "$src" "$A/hole_$n.fbx"
    sed "s/^guid: .*/guid: $(uuidgen | tr -d - | tr 'A-Z' 'a-z')/" "$R/Unity/Assets/Resources/Course/hole_$n.fbx.meta" > "$A/hole_$n.fbx.meta"
  done
  GOLF_LOOK_PROBE_OUT="$OUT" GOLF_LOOK_PROBE_ASSETS=Assets/_GolfLookProbe "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.GolfLookProbe.Run -logFile "$R/work/postcard-look/v2/calibrate/logs/probe_$PL.log"
  rc=$?
  echo "probe $PL exit $rc; compile errors: $(grep -c 'error CS' "$R/work/postcard-look/v2/calibrate/logs/probe_$PL.log")"
  return $rc
}
export -f inner 2>/dev/null
export R PL U OUT PROBE_FBX10
"$R/work/postcard-look/heavy.sh" "K-probe-$PL" bash -c "$(declare -f inner); inner"
rc=$?
[ -e "$R/Unity/Assets/_GolfLookProbe" ] && echo "WARNING: _GolfLookProbe still present" || echo "temp assets removed"
exit $rc
