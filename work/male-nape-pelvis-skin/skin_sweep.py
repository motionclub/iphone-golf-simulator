"""Render the head in the Unity-like studio for a list of skin RGBs (sRGB 0..1) and measure the skinish S/V stats (hue 8-45, S>0.2, V>0.3).
python3 skin_sweep.py <tag> r,g,b [r,g,b ...]   (system python3: renders via blender subprocess, measures with Pillow+numpy if available, else blender python)"""
import sys, subprocess, os
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin')
tag = sys.argv[1]; cols = sys.argv[2:]
VIEWS = 'yaw0_0.50_1.56_0_700_700,yaw90_0.50_1.56_0_700_700,yaw180_0.50_1.56_0_700_700,yaw-90_0.50_1.56_0_700_700,yaw35_0.50_1.56_0_700_700,yaw-35_0.50_1.56_0_700_700'
env = dict(os.environ, PYTHONPATH='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
for i, c in enumerate(cols):
    subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'rig.py', '--', 'baseline/HeroBase_Male_Silhouette.blend', f'skin/{tag}_{i}', VIEWS, 'skin', c], cwd=W, env=env, capture_output=True)
print('rendered', len(cols))
