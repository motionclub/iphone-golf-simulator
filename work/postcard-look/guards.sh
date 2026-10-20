#!/bin/bash
# GATE lines for "what must not move". Run from anywhere. Exit 1 on any FAIL.
R="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$R"; rc=0
chk() { local want="$1" file="$2" got; got=$(shasum -a 256 "$file" | cut -d' ' -f1); if [ "$got" = "$want" ]; then echo "GATE: $file unchanged PASS"; else echo "GATE: $file unchanged FAIL ($got)"; rc=1; fi; }
chk a7842f25ca64a1a91be9d881611ff84de63eb1f2e1ad8111330b9834edc4c4af blender/hole_07.blend
chk 813850bff6d107c0424dd9ca22eeaedf1ba9d3fc7ef6e9f0eed54bc67856c6ed Unity/Assets/Resources/Course/hole_07.fbx
chk 18e346e0e2f4c02be07ea608bccca0d4391776165bab69b375819b67f8a0a216 Unity/Assets/Resources/Course/hole_07.fbx.meta
chk 5a5eed8e833815eabddce3efa431b453423c36ff9984bb0a358ae1a45eb3566b Unity/Assets/Scripts/Course/Hole.cs
if python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs >/dev/null 2>&1; then echo "GATE: Hole.cs Postcards() == design data (no drift) PASS"; else echo "GATE: Hole.cs Postcards() == design data (no drift) FAIL"; rc=1; fi
grep -q "course = Course.Course.Postcards();" Unity/Assets/Scripts/Game/GolfGame.cs && echo "GATE: GolfGame starts Course.Postcards() PASS" || { echo "GATE: GolfGame starts Course.Postcards() FAIL"; rc=1; }
grep -q "Cliffside()" Unity/Assets/Scripts/Course/Hole.cs && echo "GATE: Cliffside() still in Hole.cs PASS" || { echo "GATE: Cliffside() still in Hole.cs FAIL"; rc=1; }
exit $rc
