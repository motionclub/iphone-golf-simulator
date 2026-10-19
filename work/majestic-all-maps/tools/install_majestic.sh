#!/bin/bash
# install_majestic.sh {install|rollback|dry-run} [Unity project dir]   (chat 10, Majestic on every golf map)
# Installs the golf Majestic layer of work/majestic-all-maps into a Unity project (default: <repo>/Unity), backing up every
# shared file it changes, and removes it again on rollback. Idempotent. Stages and commits nothing.
#   added   Assets/Scripts/Majestic/{MajesticBudget,MajesticCoastKit,MajesticCourseKit,MajesticCourses,MajesticHoleKit,
#           MajesticKit,MajesticLavaGround,MajesticScatter,MajesticShore}.cs
#           Assets/Resources/Majestic/{MajesticFX,MajesticFoam,MajesticImpostor,MajesticLavaGround,MajesticShadowOnly}.shader
#           Assets/Resources/Majestic/Kit/ (34 landmark FBX + impostor PNG, work/majestic-landmarks)
#           Assets/Editor/MajesticKitImport.cs (Read/Write on the 5 kit FBX the layer recolours)
#           [--tools] Assets/Editor/{MajesticHoleViews,MajesticGolfBudget,MajesticKitShots}.cs (proof tooling)
#   patched Assets/Scripts/Majestic/MajesticLook.cs, MajesticVenue.cs   (tools/patch_majestic_hooks.py: golf -> chat 10 courses)
#           Assets/Scripts/Course/GolfCoastalInstances.cs              (tools/patch_g0_instancers.py: tree shadow proxies)
#   replaced Assets/Resources/Course/Resort/{BotanicalKit,CoastalBotany}.fbx (g0/blender/lite: same objects, ~50 % triangles)
set -euo pipefail
MODE=${1:-dry-run}; TOOLS=0; [ "${3:-}" = "--tools" ] || [ "${2:-}" = "--tools" ] && TOOLS=1
SRC=$(cd "$(dirname "$0")/.." && pwd); ROOT=$(cd "$SRC/../.." && pwd)
PROJ=${2:-$ROOT/Unity}; [ "$PROJ" = "--tools" ] && PROJ=$ROOT/Unity
A="$PROJ/Assets"; BK="$SRC/install_backup"; L="$SRC/unity/Assets"
[ -d "$A" ] || { echo "no Assets in $PROJ"; exit 1; }
SCRIPTS="MajesticBudget MajesticCoastKit MajesticCourseKit MajesticCourses MajesticHoleKit MajesticKit MajesticLavaGround MajesticScatter MajesticShore"
SHADERS="MajesticFX MajesticFoam MajesticImpostor MajesticLavaGround MajesticShadowOnly"
PATCHED="Scripts/Majestic/MajesticLook.cs Scripts/Majestic/MajesticVenue.cs Scripts/Course/GolfCoastalInstances.cs Resources/Course/Resort/BotanicalKit.fbx Resources/Course/Resort/CoastalBotany.fbx"
added() {
  for s in $SCRIPTS; do echo "Scripts/Majestic/$s.cs"; done
  for s in $SHADERS; do echo "Resources/Majestic/$s.shader"; done
  (cd "$L" && find Resources/Majestic/Kit -type f ! -name '*.meta')
  echo "Editor/MajesticKitImport.cs"
  [ $TOOLS = 1 ] && for s in MajesticHoleViews MajesticGolfBudget MajesticKitShots; do echo "Editor/$s.cs"; done || true
}
case "$MODE" in
  dry-run)
    echo "project: $PROJ"; echo "would add:"; added | sed 's/^/  /'; echo "would back up + patch/replace:"; for f in $PATCHED; do echo "  $f"; done
    for f in $(added); do [ -e "$A/$f" ] && echo "  note: $f already present (would be overwritten)"; done; exit 0 ;;
  install)
    if [ -d "$BK" ]; then echo "backup already exists ($BK): installed already? rollback first"; exit 1; fi
    mkdir -p "$BK"; for f in $PATCHED; do mkdir -p "$BK/$(dirname "$f")"; cp -p "$A/$f" "$BK/$f"; done
    added > "$BK/ADDED.txt"
    for f in $(added); do mkdir -p "$A/$(dirname "$f")"; cp "$L/$f" "$A/$f"; done
    python3 "$SRC/tools/patch_majestic_hooks.py" "$A"; python3 "$SRC/tools/patch_g0_instancers.py" "$A"
    cp "$SRC/g0/blender/lite/BotanicalKit.fbx" "$A/Resources/Course/Resort/BotanicalKit.fbx"
    cp "$SRC/g0/blender/lite/CoastalBotany.fbx" "$A/Resources/Course/Resort/CoastalBotany.fbx"
    echo "installed into $PROJ ($(wc -l < "$BK/ADDED.txt") files added, 5 patched/replaced; backup $BK)" ;;
  rollback)
    [ -d "$BK" ] || { echo "no backup at $BK: nothing to roll back"; exit 1; }
    while read -r f; do rm -f "$A/$f" "$A/$f.meta"; done < "$BK/ADDED.txt"
    rmdir "$A/Resources/Majestic/Kit" 2>/dev/null || true
    for f in $PATCHED; do cp -p "$BK/$f" "$A/$f"; done
    rm -rf "$BK"; echo "rolled back $PROJ" ;;
  *) echo "usage: $0 {install|rollback|dry-run} [project] [--tools]"; exit 1 ;;
esac
