import bpy, sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/scripts')
import render_setup as rs
from preview_common import material
ROOT='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
which = sys.argv[sys.argv.index('--')+1]
if which=='male':
    bpy.ops.wm.open_mainfile(filepath=ROOT+'/ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend')
    body = bpy.data.objects['Body_M']
else:
    bpy.ops.wm.open_mainfile(filepath=ROOT+'/ArtDir/hero/base_lock/blender/HeroBase_Female.blend')
    body = bpy.data.objects['Body_F']
skin = material('Skin_proof', (0.80,0.60,0.46), .55, .3)
body.data.materials.clear(); body.data.materials.append(skin)
for o in list(bpy.data.objects):
    if o.type in ('LIGHT','CAMERA') or o.name.startswith(('Face_','Hair_')):
        pass
cam = rs.setup(samples=32)
t0=time.time()
for nm, az in (('front',0),('side',90)):
    rs.shot(f'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/tmp/body_{which}_{nm}.png', (0,-0.05,0.86), az, 3, dist=6.4, lens=105, res=(500,700))
print("render time", time.time()-t0)
