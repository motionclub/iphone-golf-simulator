#!/bin/bash
# Character LOD install / rollback into a Unity project dir (default: the repo's Unity/). Only NEW files, all owned by character-lod.
#   install.sh install [UnityDir]   copy scripts, probe, tests, cache (+ the .meta files saved in install/meta so GUIDs stay stable)
#   install.sh remove  [UnityDir]   delete exactly those files again
set -eu
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
METAS=$ROOT/work/character-lod/install/meta
U=${2:-$ROOT/Unity}
FILES=(Assets/Scripts/CharacterLod Assets/Scripts/CharacterLod.meta
  Assets/Scripts/CharacterLod/HeroLod.cs Assets/Scripts/CharacterLod/HeroLod.cs.meta
  Assets/Scripts/CharacterLod/HeroLodSimplifier.cs Assets/Scripts/CharacterLod/HeroLodSimplifier.cs.meta
  Assets/Editor/CharacterLodProbe.cs Assets/Editor/CharacterLodProbe.cs.meta
  Assets/Tests/EditMode/CharacterLodTests.cs Assets/Tests/EditMode/CharacterLodTests.cs.meta
  Assets/Resources/CharacterLOD Assets/Resources/CharacterLOD.meta
  Assets/Resources/CharacterLOD/HeroLodCache.bytes Assets/Resources/CharacterLOD/HeroLodCache.bytes.meta)
case "${1:-}" in
install)
  mkdir -p "$U/Assets/Scripts/CharacterLod" "$U/Assets/Resources/CharacterLOD"
  cp "$ROOT"/work/character-lod/src/HeroLod.cs "$ROOT"/work/character-lod/src/HeroLodSimplifier.cs "$U/Assets/Scripts/CharacterLod/"
  cp "$ROOT"/work/character-lod/unity/Assets/Editor/CharacterLodProbe.cs "$U/Assets/Editor/"
  cp "$ROOT"/work/character-lod/unity/Assets/Tests/EditMode/CharacterLodTests.cs "$U/Assets/Tests/EditMode/"
  cp "$ROOT"/work/character-lod/install/HeroLodCache.bytes "$U/Assets/Resources/CharacterLOD/"
  for f in "${FILES[@]}"; do case "$f" in *.meta) [ -f "$METAS/$f" ] && cp "$METAS/$f" "$U/$f" || echo "missing meta (Unity will make one): $f";; esac; done
  shasum "$U"/Assets/Scripts/CharacterLod/*.cs "$U"/Assets/Resources/CharacterLOD/HeroLodCache.bytes ;;
remove)
  for f in "${FILES[@]}"; do [ -f "$U/$f" ] && rm "$U/$f"; done
  rmdir "$U/Assets/Scripts/CharacterLod" "$U/Assets/Resources/CharacterLOD" 2>/dev/null || true
  echo removed ;;
*) echo "usage: install.sh install|remove [UnityDir]"; exit 2 ;;
esac
