#!/bin/bash
# usage: run_probe_scratch.sh <label>
# GolfLookProbe (Unity play mode, the real HoleView.BuildFromModel path, Game-view 900x1600 RenderTexture) on SCRATCH hole FBXs: work/postcard-look/v2/libs_r2/h08|h09|h10/hole_NN.fbx
# (built by the live hole scripts against the repaired props / look libs). The real Resources/Course FBXs are NOT touched: the three FBXs are copied (fresh-GUID .meta of the real
# import settings) to Unity/Assets/_GolfLookProbe only while this script holds heavy.sh's lock, and removed on exit (same pattern as v2/calibrate/tools/run_probe.sh).
# Output: work/postcard-look/v2/libs_r2/probe_<label>/ (JPG views + probe_report.txt), logs/probe_<label>.log
R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; PL="$1"
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT="$R/work/postcard-look/v2/libs_r2/probe_$PL"; mkdir -p "$OUT" "$R/work/postcard-look/v2/libs_r2/logs"
inner() {
  A="$R/Unity/Assets/_GolfLookProbe"
  trap 'rm -rf "$A" "$A.meta"' EXIT INT TERM
  rm -rf "$A" "$A.meta"; mkdir -p "$A"
  for n in 08 09 10; do
    src="$R/work/postcard-look/v2/libs_r2/h$n/hole_$n.fbx"; ov="PROBE_FBX_$n"; [ -n "${!ov}" ] && src="${!ov}"      # optional override: another FBX for hole n (e.g. the hole fixer's stage, as a control)
    cp "$src" "$A/hole_$n.fbx"
    sed "s/^guid: .*/guid: $(uuidgen | tr -d - | tr 'A-Z' 'a-z')/" "$R/Unity/Assets/Resources/Course/hole_$n.fbx.meta" > "$A/hole_$n.fbx.meta"
  done
  GOLF_LOOK_PROBE_OUT="$OUT" GOLF_LOOK_PROBE_ASSETS=Assets/_GolfLookProbe "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.GolfLookProbe.Run -logFile "$R/work/postcard-look/v2/libs_r2/logs/probe_$PL.log"
  rc=$?
  echo "probe $PL exit $rc; compile errors: $(grep -c 'error CS' "$R/work/postcard-look/v2/libs_r2/logs/probe_$PL.log")"
  return $rc
}
export R PL U OUT PROBE_FBX_08 PROBE_FBX_09 PROBE_FBX_10
"$R/work/postcard-look/heavy.sh" "libs-r2-probe-$PL" bash -c "$(declare -f inner); inner"
rc=$?
[ -e "$R/Unity/Assets/_GolfLookProbe" ] && echo "WARNING: _GolfLookProbe still present" || echo "temp assets removed"
exit $rc
