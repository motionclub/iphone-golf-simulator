#!/bin/bash
# Install the rendered backgrounds into the real project and stage ONLY this chat's changes.
#   tools/install.sh            (run from anywhere; never commits)
# 1. own files (scripts, shaders, Editor/Test tools, Blender-rendered assets, their .meta GUIDs) -> Unity/Assets
# 2. the hooks in partly-owned files (tools/patch_shared.py) -> working tree
# 3. stage: own files with git add; partly-owned files as  index version + hook  (git update-index), so other
#    chats' unstaged edits in those files stay unstaged and untouched.
set -euo pipefail
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
RB=$REPO/work/rendered-backgrounds
cd "$REPO"
U=Unity/Assets; R=$U/Resources/Environment/RenderedSky
mkdir -p "$R"
rsync -a "$RB/unity/Assets/" "$U/"
cp "$RB/unity/Assets/Resources/Environment/RenderedSky.meta" "$U/Resources/Environment/RenderedSky.meta"
for f in clouds/CloudSixWay_A.png clouds/CloudSixWay_B.png clouds/clouds.json cloudsea/CloudSea_A.png cloudsea/CloudSea_B.png cloudsea/CloudSea_Tint.png \
         karst/KarstIslands.fbx karst/Karst_Albedo.png karst/Karst_Normal.png; do cp "$RB/blender/$f" "$R/"; done
python3 "$RB/tools/patch_shared.py" Unity
# stage own files
OWN=$(cd "$RB/unity" && find Assets -type f | sed 's#^#Unity/#')
ASSETS=$(for f in CloudSixWay_A.png CloudSixWay_B.png clouds.json CloudSea_A.png CloudSea_B.png CloudSea_Tint.png KarstIslands.fbx Karst_Albedo.png Karst_Normal.png; do echo "$R/$f"; done)
git add -- $OWN $ASSETS "$U/Resources/Environment/RenderedSky.meta"
# stage partly-owned files as index + hook
python3 - <<'EOF'
import subprocess, sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/rendered-backgrounds/tools')
from patch_shared import FILES, patch_text
for rel in FILES:
    path = 'Unity/' + rel
    idx = subprocess.run(['git', 'show', ':' + path], capture_output=True, text=True)
    if idx.returncode != 0: print('not in index, skipped:', path); continue
    new = patch_text(rel, idx.stdout)
    if new == idx.stdout: print('index already has the hook:', path); continue
    blob = subprocess.run(['git', 'hash-object', '-w', '--stdin'], input=new, capture_output=True, text=True, check=True).stdout.strip()
    mode = subprocess.run(['git', 'ls-files', '-s', '--', path], capture_output=True, text=True, check=True).stdout.split()[0]
    subprocess.run(['git', 'update-index', '--cacheinfo', f'{mode},{blob},{path}'], check=True)
    print('staged hook only:', path)
EOF
git status --short -- $OWN $ASSETS "$U/Resources/Environment/RenderedSky.meta" $(python3 -c "import sys;sys.path.insert(0,'$RB/tools');from patch_shared import FILES;print(' '.join('Unity/'+f for f in FILES))")
