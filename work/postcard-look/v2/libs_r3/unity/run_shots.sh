#!/bin/bash
# usage: run_shots.sh <label>
# Game-view stills of the SCRATCH hole FBXs (work/postcard-look/v2/libs_r3/h08|h09|h10/hole_NN.fbx, built by the live hole scripts against the repaired libs) through the real
# GolfGame / HoleView.BuildFromModel / GolfAtmosphere / CameraRig, 900x1600, TennisURP. The real Resources/Course FBXs are NOT touched. Everything temporary lives in
# Unity/Assets/_LibsR3Probe (FBX copies with fresh-GUID metas + the LibsR3Shots editor script + asmdef) ONLY while heavy.sh's lock is held; removed on exit.
# Output: work/postcard-look/v2/libs_r3/shots_<label>/ (PNG per shot + shots_report.txt), logs/shots_<label>.log
R="$(cd "$(dirname "$0")/../../../../.." && pwd)"; PL="$1"
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
H="$R/work/postcard-look/v2/libs_r3"; OUT="$H/shots_$PL"; mkdir -p "$OUT" "$H/logs"
inner() {
  A="$R/Unity/Assets/_LibsR3Probe"
  trap 'rm -rf "$A" "$A.meta"' EXIT INT TERM
  rm -rf "$A" "$A.meta"; mkdir -p "$A/Editor"
  for n in 08 09 10; do
    src="$H/h$n/hole_$n.fbx"; ov="PROBE_FBX_$n"; [ -n "${!ov}" ] && src="${!ov}"
    cp "$src" "$A/hole_$n.fbx"
    sed "s/^guid: .*/guid: $(uuidgen | tr -d - | tr 'A-Z' 'a-z')/" "$R/Unity/Assets/Resources/Course/hole_$n.fbx.meta" > "$A/hole_$n.fbx.meta"
  done
  cp "$H/unity/LibsR3Shots.cs" "$H/unity/LibsR3Shots.asmdef" "$A/Editor/"
  LIBS_R3_OUT="$OUT" LIBS_R3_CFG="${LIBS_R3_CFG:-$H/unity/cfg.json}" LIBS_R3_ASSETS=Assets/_LibsR3Probe "$U" -batchmode -projectPath "$R/Unity" -executeMethod LibsR3.LibsR3Shots.Run -logFile "$H/logs/shots_$PL.log"
  rc=$?
  echo "shots $PL exit $rc; compile errors: $(grep -c 'error CS' "$H/logs/shots_$PL.log")"
  return $rc
}
export R PL U OUT H PROBE_FBX_08 PROBE_FBX_09 PROBE_FBX_10 LIBS_R3_CFG
"$R/work/postcard-look/heavy.sh" "libs-r3-shots-$PL" bash -c "$(declare -f inner); inner"
rc=$?
[ -e "$R/Unity/Assets/_LibsR3Probe" ] && echo "WARNING: _LibsR3Probe still present" || echo "temp assets removed"
exit $rc
