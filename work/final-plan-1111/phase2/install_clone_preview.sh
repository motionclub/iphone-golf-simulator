#!/bin/bash
# install_clone_preview.sh [clone name]: puts the studio preview hook into a PROJECT COPY (never the shared project):
# HeroStudio.cs + three one-line calls. Idempotent. Remove with: install_clone_preview.sh <clone> off  (re-syncs the three files from the repo).
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
C=$HOME/unity-clones/${1:-final-plan-dev}/Unity/Assets/Scripts; H=$REPO/work/final-plan-1111/phase2
[ -d "$C" ] || { echo "no clone at $C"; exit 1; }
case "$C" in "$REPO"*) echo "refusing: that is the shared project"; exit 1;; esac
if [ "$2" = off ]; then
  rm -f $C/Tennis/HeroStudio.cs $C/Tennis/HeroStudio.cs.meta
  for f in Tennis/HeroBuild.cs Tennis/MatchHeroLook.cs; do cp $REPO/Unity/Assets/Scripts/$f $C/$f; done; echo "preview hook removed"; exit 0
fi
cp $H/HeroStudio.cs.txt $C/Tennis/HeroStudio.cs
python3 - "$C" <<'PY'
import sys
c = sys.argv[1]
def patch(f, a, b):
    s = open(f).read()
    if b in s: print("already patched:", f.split("/")[-1]); return
    assert s.count(a) == 1, (f, a); open(f, "w").write(s.replace(a, b)); print("patched:", f.split("/")[-1])
patch(c + "/Tennis/HeroBuild.cs", "            if (!On || !look || !smr || !source || !source.isReadable) return source;\n",
      "            if (HeroStudio.On && look && !look.female) { HeroGarmentLOD.ForceFullDetail = true; return HeroStudio.Override(look, smr, source); }   // PROJECT-COPY PREVIEW\n            if (!On || !look || !smr || !source || !source.isReadable) return source;\n")
patch(c + "/Tennis/MatchHeroLook.cs", "                    if (!tag.StartsWith(\"Shoe\")) r.sharedMesh = HeroBuild.Prepare(this, r, r.sharedMesh, true);\n",
      "                    if (!tag.StartsWith(\"Shoe\")) { r.sharedMesh = HeroBuild.Prepare(this, r, r.sharedMesh, true); if (female) r.sharedMesh = HeroStudio.Override(this, r, r.sharedMesh, true); }   // PROJECT-COPY PREVIEW: her refitted tops\n                    else r.sharedMesh = HeroStudio.Override(this, r, r.sharedMesh);   // PROJECT-COPY PREVIEW: the rounded toe\n")
PY
