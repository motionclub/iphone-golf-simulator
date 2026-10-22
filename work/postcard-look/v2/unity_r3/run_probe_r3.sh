#!/bin/bash
# usage: run_probe_r3.sh <label> [tennis|studio]  -- GolfLookProbe against the INSTALLED Resources/Course holes (as proof/run_probe_installed.sh) but into v2/unity_r3/probe_<label>/
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; PL="$1"; PIPE="$2"
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT="$R/work/postcard-look/v2/unity_r3/probe_$PL"; mkdir -p "$OUT"
GOLF_LOOK_PROBE_OUT="$OUT" GOLF_LOOK_PROBE_ASSETS=Assets/_NoProbeAssets GOLF_LOOK_PROBE_PIPELINE="$PIPE" "$R/work/postcard-look/heavy.sh" "R3-probe-$PL" "$U" -batchmode -projectPath "$R/Unity" \
  -executeMethod GolfArcade.EditorTools.GolfLookProbe.Run -logFile "$OUT/probe.unity.log"
rc=$?; echo "probe $PL exit $rc; compile errors: $(grep -c 'error CS' "$OUT/probe.unity.log")"; exit $rc
