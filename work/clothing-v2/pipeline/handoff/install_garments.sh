#!/bin/zsh
# GARMENT PIPELINE -> a Unity project (integration, chat 6). Installs fitted garment runs into <project>: new meshes + maps
# (ClothingV2Install) and the pipeline's weights / GP_Pose correctives / skin-cover hide lists / offsets (GarmentPipelineInstall).
#   install_garments.sh <unity project path> <Hero>:<run>[:<out_gp dir with new meshes>] [...]
# e.g. female tennis K12:  install_garments.sh ~/integration-UnityClone MatchHero_Female:K12_FT:../out_gp
# Needs in the project (staged in the repo by chat 5): Assets/Editor/GarmentPipelineInstall.cs, Assets/Editor/ClothingV2Install.cs,
# Assets/Scripts/Tennis/GarmentPoseCorrectives.cs, KitV2PoseCorrectives.cs (Attach + gp-rbf skip), HeroGarmentHemWeights.cs ([gp] skip).
# ALSO NEEDED for the female tennis top: HeroShoulderDeformation must skip "[gp]" Kit_Top meshes (request in
# work/delegation-2026-10-17/REQUESTS.md; chat 5's clone uses the one-line patch at its line 60).
# Unity runs through heavy.sh, batch, muted. Nothing is committed.
set -e
P=${0:A:h:h}; cd $P
PROJ=${1:A}; shift
HV=${GP_HEAVY:-$P/../../delegation-2026-10-17/heavy.sh}
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUTD=$P/out/_handoff_$(date +%m%d_%H%M); CV2=$OUTD/_cv2; mkdir -p $OUTD $CV2
HEROES=(); NEWH=()
for j in $@; do
  parts=(${(s.:.)j}); HERO=$parts[1]; RUN=$parts[2]; NS=${parts[3]:-}; HEROES+=$HERO
  [[ -n $NS ]] && { ln -sfn ${NS:A}/$HERO $CV2/$HERO; NEWH+=$HERO; }
  mkdir -p $OUTD/$HERO
  GP_OUT_DIR=$OUTD python3 gp/export.py $HERO runs/$RUN
  python3 -c "import sys; sys.path.insert(0,'gp'); import rig, cover; cover.export_cover(rig.Hero('$HERO'), 'runs/$RUN', '$OUTD/$HERO')"
  python3 -c "import sys; sys.path.insert(0,'gp'); import offsets; offsets.write('$HERO', 'runs/$RUN', '$OUTD/$HERO/garment_offsets.json')"
done
H=${(j:,:)HEROES}
if (( ${#NEWH} )); then
  GOLF_MUTE=1 CV2_SRC=$CV2 CV2_HEROES=${(j:,:)NEWH} $HV unity $U -batchmode -quit -projectPath $PROJ -executeMethod GolfArcade.EditorTools.ClothingV2Install.Run -logFile $OUTD/cv2install.log > /dev/null 2>&1 \
    || { grep -E "error CS|Exception" $OUTD/cv2install.log | head; exit 1; }
fi
GOLF_MUTE=1 GP_OUT=$OUTD GP_HEROES=$H $HV unity $U -batchmode -quit -projectPath $PROJ -executeMethod GolfArcade.EditorTools.GarmentPipelineInstall.Run -logFile $OUTD/gpinstall.log > /dev/null 2>&1 \
  || { grep -E "error CS|Exception" $OUTD/gpinstall.log | head; exit 1; }
cat $OUTD/install_report.txt
echo "installed $H into $PROJ (logs + export in $OUTD). Lobby: regenerate the garment .ktx (work/clothing-v2/lobby/compress_maps.py) and run work/hero-sync/sync_heroes.sh."
