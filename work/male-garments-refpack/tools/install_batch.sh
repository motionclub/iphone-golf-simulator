#!/bin/zsh
# male-garments: garment_install_batch with a PRIVATE install source (install_out/) and clone (~/male-garments-UnityClone).
#   install_batch.sh <Hero>:<run>[:<new_src dir>] ... [film=<clips>] [look=target] [steps=cv2,install,perf,film]
set -e
ME=${0:A:h:h}; P=$ME/../clothing-v2/pipeline; cd $P
HV=$ME/../delegation-2026-10-17/heavy.sh
U=($HV unity /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity)
CL=$HOME/male-garments-UnityClone; OUT=$ME/install_out
JOBS=(); FILM=""; LOOK=""; STEPS=""
for a in "$@"; do case $a in film=*) FILM=${a#film=};; look=*) LOOK=${a#look=};; steps=*) STEPS=${a#steps=};; *) JOBS+=$a;; esac; done
TAG=mg_$(date +%m%d_%H%M); mkdir -p $ME/logs $ME/perf $ME/film/$TAG $OUT
mkdir -p $CL/Assets/Editor/GarmentPipeline; cp unity/*.cs $CL/Assets/Editor/GarmentPipeline/
for f in Assets/Editor/GarmentPipelineInstall.cs Assets/Scripts/Tennis/GarmentPoseCorrectives.cs Assets/Scripts/Tennis/KitV2PoseCorrectives.cs Assets/Scripts/Tennis/HeroGarmentHemWeights.cs Assets/Editor/ClothingV2Install.cs; do
  cp ../../../Unity/$f $CL/$f; done
HEROES=(); NEWH=(); CV2=$OUT/_cv2src_$TAG; mkdir -p $CV2
for j in $JOBS; do
  parts=(${(s.:.)j}); HERO=$parts[1]; RUN=$parts[2]; NS=${parts[3]:-}
  HEROES+=$HERO
  if [[ -n $NS ]]; then ln -sfn ${NS:A}/$HERO $CV2/$HERO; NEWH+=$HERO; fi
  rm -rf $OUT/$HERO; mkdir -p $OUT/$HERO
  GP_OUT=$OUT python3 gp/export.py $HERO runs/$RUN
  [[ -f runs/$RUN/$HERO/body.npz ]] && python3 -c "import sys; sys.path.insert(0,'gp'); import rig, cover; cover.export_cover(rig.Hero('$HERO'), 'runs/$RUN', '$OUT/$HERO')"
  python3 -c "import sys; sys.path.insert(0,'gp'); import offsets; offsets.write('$HERO', 'runs/$RUN', '$OUT/$HERO/garment_offsets.json')"
done
[[ -z $STEPS ]] && { STEPS=install,perf; (( ${#NEWH} )) && STEPS=cv2,$STEPS; [[ -n $FILM ]] && STEPS=$STEPS,film; }
H=${(j:,:)HEROES}
echo "[mg install] $H steps $STEPS ($(date +%H:%M:%S))"
GOLF_MUTE=1 FEMALE_ALIVE=0 GP_STEPS=$STEPS CV2_SRC=$CV2 CV2_HEROES=${(j:,:)NEWH} GP_INSTALL_OUT=$OUT GP_INSTALL_HEROES=$H GP_PERF_OUT=$ME/perf GP_PERF_HEROES=$H \
  GP_FILM_OUT=$ME/film/$TAG GP_FILM_HEROES=$H GP_CLIPS=$FILM GP_STEP=${GP_STEP:-.2} GP_LOOK=$LOOK \
  $U -batchmode -projectPath $CL -executeMethod GolfArcade.EditorTools.GarmentPipelineBatch.Run -logFile $ME/logs/${TAG}.log > /dev/null 2>&1 \
  || { grep -E "error CS|Exception|GP-BATCH" $ME/logs/${TAG}.log | head -20; exit 1; }
grep -E "GP-BATCH|\[ClothingV2\]" $ME/logs/${TAG}.log | head -30
cat $OUT/install_report.txt 2>/dev/null; cp $ME/perf/perf.json $ME/perf/${TAG}_perf.json 2>/dev/null; cat $ME/perf/perf.json 2>/dev/null
echo "[mg install] done -> logs/${TAG}.log, perf/${TAG}_perf.json, film/$TAG"
