#!/bin/bash
# Type-check the character-LOD scripts against the Unity engine/editor DLLs and the project's last compiled GolfArcade.dll (no Editor launch).
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
C=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/Resources/Scripting; M=$C/MonoBleedingEdge
O=${TMPDIR:-/tmp}/clod_check; mkdir -p "$O"
REFS=(); for d in "$C"/Managed/UnityEngine/UnityEngine*.dll "$C"/Managed/UnityEngine/UnityEditor*.dll; do REFS+=("-r:$d"); done
REFS+=("-r:$C/NetStandard/ref/2.1.0/netstandard.dll" "-r:$ROOT/Unity/Library/ScriptAssemblies/GolfArcade.dll")
CSC=("$M/bin/mono" "$M/lib/mono/4.5/csc.exe" -nologo -langversion:9 -nowarn:0168,0219,0414 -target:library -nostdlib+ -noconfig)
"${CSC[@]}" -out:"$O/rt.dll" "${REFS[@]}" "$ROOT"/work/character-lod/src/*.cs 2>&1 | grep -E "error" ; r1=${PIPESTATUS[0]}
"${CSC[@]}" -define:UNITY_EDITOR -out:"$O/ed.dll" "${REFS[@]}" -r:"$O/rt.dll" "$ROOT"/work/character-lod/unity/Assets/Editor/*.cs 2>&1 | grep -E "error"; r2=${PIPESTATUS[0]}
N=$(find "$C/../../" -name nunit.framework.dll -path "*nunit*" 2>/dev/null | head -1)
"${CSC[@]}" -define:UNITY_EDITOR -out:"$O/tests.dll" "${REFS[@]}" -r:"$O/rt.dll" -r:"$N" -r:"$C/NetStandard/compat/2.1.0/shims/netfx/mscorlib.dll" "$ROOT"/work/character-lod/unity/Assets/Tests/EditMode/*.cs 2>&1 | grep -E "error"; r3=${PIPESTATUS[0]}
echo "runtime rc=$r1 editor rc=$r2 tests rc=$r3"
