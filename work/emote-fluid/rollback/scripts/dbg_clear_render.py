"""dbg_clear_render.py <male|female> <clip> <t> : render the clearance violators (blue = R samples, red = L samples) on the dressed hero (run on the DRESSED blend)."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np
import bpy
from mathutils import Matrix, Vector
import emo_hero as EH
import emo_clips2 as EC
import preview as PV
a_ = sys.argv[sys.argv.index('--') + 1:]
tag, clip, t, outdir = a_[0], a_[1], float(a_[2]), a_[3]
views = a_[4].split(',') if len(a_) > 4 else ['front', 'q_front', 'side', 'top']
os.makedirs(outdir, exist_ok=True)
H = EH.EmoHero(tag)
C = EC.build(clip, H)
clr = C.clr
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
rk = bpy.data.objects['Racket_Classic']
rk.scale = (1, 1, 1)
cam = PV.setup_scene(rig_o, samples=10)
import studio
d = C.solve(t)
P0 = C.P(t)
b0, h0, info0 = H.solve(P0)
prev = PV.apply_pose(rig_o, H.rig, d['basis'] if os.environ.get('SHOW_CLEARED', '0') == '1' else b0, d['hips'] if os.environ.get('SHOW_CLEARED', '0') == '1' else h0, None)
info = d['info'] if os.environ.get('SHOW_CLEARED', '0') == '1' else info0
rkw = d.get('racket')
if rkw is not None:
    rk.matrix_world = Matrix.Translation(Vector(rkw['pos'].tolist())) @ Matrix(rkw['R'].tolist()).to_4x4()
bpy.context.view_layer.update()
marks = []
for side, col in (('L', (1.0, 0.1, 0.1)), ('R', (0.1, 0.3, 1.0))):
    ex = C.grip_exempt(t)
    trees = clr.obstacles(info, side, False, True, ex)
    rk_obs = None
    if side == 'L' and not ex and not clr.holding(info, 'L'):
        rk_obs = info['rk_origin'] + (clr.rko @ info['rk_R'].T)
    pts, kind = clr.arm_samples(info, side, side == 'R')
    viol, nrm = clr.violations(pts, kind, trees, rk_obs=rk_obs)
    print(side, 'exempt', ex, 'max viol', float(viol.max()), 'n', int((viol > 0).sum()), 'layers', list(trees))
    for i in np.where(viol > 0)[0][:200]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=tuple(float(x) for x in pts[i]), segments=8, ring_count=6)
        ob = bpy.context.active_object
        m = bpy.data.materials.new('dbg'); m.use_nodes = True
        bsdf = m.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (*col, 1.0); bsdf.inputs['Emission Color'].default_value = (*col, 1.0); bsdf.inputs['Emission Strength'].default_value = 4.0
        ob.data.materials.append(m)
    print(side, 'violators', int((viol > 0).sum()), 'max', float(viol.max()))
VIEWS = {'front': (0.0, 6.0, 2.2, 50, 1.05), 'q_front': (35.0, 10.0, 2.2, 50, 1.05), 'side': (90.0, 6.0, 2.2, 50, 1.05), 'top': (0.0, 70.0, 2.4, 50, 0.95), 'behind': (180.0, 8.0, 2.4, 50, 1.0)}
for v in views:
    az, el, dist, lens, tz = VIEWS[v]
    studio.shot(f'{outdir}/{clip}_{tag}_{int(round(t*30)):03d}_{v}.png', (H.O[0], H.O[1] - 0.05, tz), az=az, el=el, dist=dist, lens=lens, res=(420, 520), turn_lights=True)
print('DONE')
