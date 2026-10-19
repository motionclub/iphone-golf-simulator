#!/bin/zsh
# FRAME_RATE_60B asset install / rollback into Unity/ (only files chat 1 owns).
#   zsh install.sh install    backs the current files up to rollback/ (once), then copies the 60 Hz files in
#   zsh install.sh rollback   copies rollback/ back
# Code edits (SignatureShot.cs, FrameProbe.cs, TennisQuality.cs, MatchHeroLockerExport.cs, Swift) are made in place: see GATE_RESULTS.md.
set -e
W=${0:A:h:h}; U=${W:h:h}/Unity/Assets; R=$W/rollback
typeset -a PAIRS
for s in Male Female; do for c in Emote_Spike Emote_Scuba Emote_Thrust Intro_Wave Intro_BringIt Intro_Pushups; do
  PAIRS+=("$W/emotes60/fbx/${s}_$c.fbx" "$U/Characters/MatchHeroes/$s/${s}_$c.fbx"); PAIRS+=("$W/emotes60/fbx/${s}_$c.fbx.meta" "$U/Characters/MatchHeroes/$s/${s}_$c.fbx.meta"); done; done
for t in m f; do PAIRS+=("$W/golf/out/golfer_$t.fbx" "$U/Resources/Hero/golfer_$t.fbx" "$W/golf/out/golfer_${t}_clips.json" "$U/Resources/Hero/golfer_${t}_clips.json"); done
PAIRS+=("$W/hole12/hole_12_cinematic.fbx" "$U/Resources/Course/hole_12_cinematic.fbx")
case $1 in
  install)
    for ((i=1; i<=${#PAIRS}; i+=2)); do src=${PAIRS[i]}; dst=${PAIRS[i+1]}; rel=${dst#$U/}
      if [[ ! -e $R/$rel ]]; then mkdir -p ${R}/${rel:h}; cp $dst $R/$rel; fi
      cp $src $dst; print "installed $rel"; done ;;
  rollback)
    for ((i=1; i<=${#PAIRS}; i+=2)); do dst=${PAIRS[i+1]}; rel=${dst#$U/}; cp $R/$rel $dst; print "restored $rel"; done ;;
  *) print "usage: install.sh install|rollback"; exit 1 ;;
esac
