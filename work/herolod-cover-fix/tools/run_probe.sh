#!/bin/zsh
# tools/run_probe.sh <out_dir> : HeroLodCoverProbe in the clone ~/unity-clones/herolod-fix (APFS clone of bowling-ship), batch mode, muted,
# through heavy.sh. Copies this worktree's HeroLod sources (HLF_SRC, default: the worktree's Unity/Assets/Scripts/CharacterLod) and the probe in first.
# The clone keeps the bowling worktree's HeroLodExempt class (BowlingHero.cs references it): the probe removes the component instead.
set -u
W=${0:A:h:h}; WT=${W:h:h}; C=$HOME/unity-clones/herolod-fix
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
HEAVY=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/delegation-2026-10-17/heavy.sh
OUT=${1:A}; mkdir -p $OUT
SRC=${HLF_SRC:-$WT/Unity/Assets/Scripts/CharacterLod}
cp $SRC/HeroLod.cs $SRC/HeroLodSimplifier.cs $C/Assets/Scripts/CharacterLod/
# keep the bowling worktree's HeroLodExempt (+ boot skip) in the clone's copy
grep -q "class HeroLodExempt" $C/Assets/Scripts/CharacterLod/HeroLod.cs || python3 - $C/Assets/Scripts/CharacterLod/HeroLod.cs <<'PY'
import sys; p=sys.argv[1]; s=open(p).read()
s=s.replace("if (!look.GetComponent<HeroLod>()) look.gameObject.AddComponent<HeroLod>();","if (!look.GetComponent<HeroLod>() && !look.GetComponentInParent<HeroLodExempt>()) look.gameObject.AddComponent<HeroLod>();")
i=s.rstrip().rfind("}"); s=s[:i]+"    public sealed class HeroLodExempt : MonoBehaviour { }\n}\n"; open(p,"w").write(s)
PY
[[ -f ${HLF_CACHE:-/nonexistent} ]] && cp $HLF_CACHE $C/Assets/Resources/CharacterLOD/HeroLodCache.bytes
cp $W/unity/Assets/Editor/HeroLodCoverProbe.cs $C/Assets/Editor/
env GOLF_MUTE=1 BOWL_VENUE=${BOWL_VENUE:-tiki} HLF_OUT=$OUT $HEAVY unity $UNITY -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.HeroLodCoverProbe.Run -logFile $OUT/unity.log
echo "unity exit $?"
grep -E "error CS|Exception" $OUT/unity.log | sort -u | head -20
cat $OUT/report.txt 2>/dev/null | head -80
