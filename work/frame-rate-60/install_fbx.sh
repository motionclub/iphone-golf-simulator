#!/bin/zsh
# install_fbx.sh [install|rollback] : copy the 60 Hz clips (this folder) over the installed FBXs, or put the 30 Hz originals back (their source job folders hold them byte for byte).
# Match clips (Forehand ... Overhead, 14 per hero) are installed by Unity's FrameRate60Wire.Run, which also moves the prefab slot times; this script does the rest:
#   Serve (serve/), Walk + RunForward/Left/Right (feet/), the 7 standard emotes (tennis + Free), Free Walk / Run (emotes/).
# Afterwards run:  Unity -batchmode -nographics -quit -projectPath Unity -executeMethod GolfArcade.EditorTools.FrameRate60Wire.Reimport
R=$(cd "$(dirname "$0")/../.." && pwd); W=$R/work; U=$R/Unity/Assets
mode=${1:-install}
pick() { # <new> <old> <dest>
  if [ $mode = install ]; then src=$1; else src=$2; fi
  [ -f $src ] || { echo "MISSING $src"; exit 1; }
  cp $src $3 && echo "$mode $(basename $3)"
}
for s in Male Female; do
  pick $W/frame-rate-60/serve/export/fbx/${s}_Serve.fbx $W/serve-dip-jump/export/fbx/${s}_Serve.fbx $U/Characters/MatchHeroes/$s/${s}_Serve.fbx
  for n in Walk RunForward RunLeft RunRight; do
    pick $W/frame-rate-60/feet/export/fbx/${s}_$n.fbx $W/serve-and-feet/export/fbx/${s}_$n.fbx $U/Characters/MatchHeroes/$s/${s}_$n.fbx
  done
  for n in Emote_Defeat Emote_FistPump Emote_JumpJoy Emote_Shock Emote_Slump Emote_Stomp Emote_Victory; do
    pick $W/frame-rate-60/emotes/fbx/${s}_$n.fbx $W/emote-standard/fbx/${s}_$n.fbx $U/Characters/MatchHeroes/$s/${s}_$n.fbx
    pick $W/frame-rate-60/emotes/fbx/${s}_${n}_Free.fbx $W/emote-standard/fbx/${s}_${n}_Free.fbx $U/Resources/HeroMoves/$s/$n.fbx
  done
  for n in Walk Run; do
    pick $W/frame-rate-60/emotes/fbx/${s}_${n}_Free.fbx $W/emote-standard/fbx/${s}_${n}_Free.fbx $U/Resources/HeroMoves/$s/$n.fbx
  done
done
# The HeroMoves FBXs carry explicit clip ranges in their .meta (frames at the FBX's rate): 30 Hz last frames, doubled for the 60 Hz files.
python3 - $mode $U <<'PY'
import re, sys
mode, U = sys.argv[1], sys.argv[2]
last30 = dict(Emote_Defeat=99, Emote_FistPump=47, Emote_JumpJoy=62, Emote_Shock=65, Emote_Slump=77, Emote_Stomp=65, Emote_Victory=95, Run=20, Walk=32)
for s in ('Male', 'Female'):
    for n, l in last30.items():
        p = f'{U}/Resources/HeroMoves/{s}/{n}.fbx.meta'
        t = open(p).read()
        want = 2 * l if mode == 'install' else l
        t2 = re.sub(r'lastFrame: \d+', f'lastFrame: {want}', t, count=1)
        open(p, 'w').write(t2)
print('metas', mode)
PY
