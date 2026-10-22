#!/bin/bash
# usage: run_importcheck_staged.sh <label> [dir-with-hole_08.fbx hole_09.fbx hole_10.fbx; default: each hole's v2/hole0N/stage/]
# AREA U (2026-10-04): PostcardImportCheck in PREVIEW mode (POSTCARD_IMPORT_ASSETS): the same ground-height (3000 samples), lie, marker, collider, material, foam, lava gates, but on the STAGED
# hole FBXs, copied (with a fresh-GUID .meta of the real import settings) to Unity/Assets/_GolfLookProbe only while heavy.sh's lock is held, removed on exit. Nothing is installed.
# Output: work/postcard-look/v2/unity_u/importcheck_<label>.txt, logs/importcheck_<label>.log, importcheck_<label>.staged_sha256.txt
# (the label variable is LBL, not L: heavy.sh keeps its lock path in L and runs the command in the same shell)
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; LBL="$1"; SRC="$2"
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT="$R/work/postcard-look/v2/unity_u"
mkdir -p "$OUT/logs"
inner() {
  A="$R/Unity/Assets/_GolfLookProbe"
  trap 'rm -rf "$A" "$A.meta"' EXIT INT TERM
  rm -rf "$A" "$A.meta"; mkdir -p "$A"
  for n in 08 09 10; do
    src="$R/work/postcard-look/v2/hole$n/stage/hole_$n.fbx"; [ -n "$SRC" ] && src="$SRC/hole_$n.fbx"
    cp "$src" "$A/hole_$n.fbx"
    sed "s/^guid: .*/guid: $(uuidgen | tr -d - | tr 'A-Z' 'a-z')/" "$R/Unity/Assets/Resources/Course/hole_$n.fbx.meta" > "$A/hole_$n.fbx.meta"
    shasum -a 256 "$A/hole_$n.fbx" >> "$OUT/importcheck_$LBL.staged_sha256.txt"
  done
  POSTCARD_IMPORT_ASSETS=Assets/_GolfLookProbe POSTCARD_IMPORT_REPORT="$OUT/importcheck_$LBL.txt" \
    "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.PostcardImportCheck.Run -logFile "$OUT/logs/importcheck_$LBL.log"
  rc=$?
  echo "importcheck (staged) $LBL exit $rc; compile errors: $(grep -c 'error CS' "$OUT/logs/importcheck_$LBL.log")"
  return $rc
}
export R LBL SRC U OUT
rm -f "$OUT/importcheck_$LBL.staged_sha256.txt"
"$R/work/postcard-look/heavy.sh" "U-importcheck-staged-$LBL" bash -c "$(declare -f inner); inner"
rc=$?
[ -e "$R/Unity/Assets/_GolfLookProbe" ] && echo "WARNING: _GolfLookProbe still present" || echo "temp assets removed"
exit $rc
