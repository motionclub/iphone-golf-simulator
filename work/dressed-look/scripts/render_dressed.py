"""Render proof cells of a dressed hero blend (headless EEVEE).

  blender -b export/HeroBase_<Sex>_Dressed.blend --python render_dressed.py -- <male|female> <White|Black> <out_dir> [--body source|skin] [--only name,name] [--res fast]

Cells: full_front, full_q3, full_side, full_back (full figure), waist_front, waist_back (waist closeups), hand_a, hand_b (racket-hand closeups).
The dressed blend itself is never saved from here; the scene is only modified in memory (other colour hidden, studio lights, proof camera)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
import studio as ST
from preview_common import material

a_ = args_after_dashes()
tag, color, outdir = a_[0], a_[1], a_[2]
opt = lambda k, d=None: (a_[a_.index(k) + 1] if k in a_ else d)
body_mode = opt('--body', 'source')
only = opt('--only')
fast = opt('--res') == 'fast'
os.makedirs(outdir, exist_ok=True)
H = HERO[tag]
body = bpy.data.objects[H['body']]
other = 'Black' if color == 'White' else 'White'
for o in bpy.data.objects:
    if o.type in ('LIGHT', 'CAMERA'):
        o.hide_render = True
bpy.data.collections[f'Kit_{other}'].hide_render = True
bpy.data.collections[f'Kit_{other}'].hide_viewport = True
bpy.data.collections[f'Kit_{color}'].hide_render = False
bpy.data.collections[f'Kit_{color}'].hide_viewport = False
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == f'Kit_{other}':
        lc.hide_viewport = True
    if lc.name == f'Kit_{color}':
        lc.hide_viewport = False
if body_mode == 'skin':
    skin = material('Proof_Skin', (0.80, 0.60, 0.46), .55, .3)
    body.data.materials.clear()
    body.data.materials.append(skin)
    # all polygons use slot 0
    mi = np.zeros(len(body.data.polygons), np.int32)
    body.data.polygons.foreach_set('material_index', mi)
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
shoe_min = min(mesh_co(o, world=True)[:, 2].min() for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Kit_Shoe') and color in o.name)
# world bounding box of everything visible (evaluated) for framing
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.hide_render and o.visible_get() and o.name not in ('Collider_Racket',):
        ev = o.evaluated_get(dg)
        m = ev.to_mesh()
        a = np.empty(len(m.vertices) * 3, np.float32); m.vertices.foreach_get('co', a)
        ev.to_mesh_clear()
        a = a.reshape(-1, 3)
        M = np.array(o.matrix_world)
        pts.append(a[::7] @ M[:3, :3].T + M[:3, 3])
pts = np.concatenate(pts)
bb_min, bb_max = pts.min(0), pts.max(0)
print('bbox', np.round(bb_min, 3), np.round(bb_max, 3))
ctr_full = (0.5 * (bb_min[0] + bb_max[0]), 0.5 * (bb_min[1] + bb_max[1]), 0.5 * (bb_min[2] + bb_max[2]))
cam = ST.setup(samples=32 if fast else 64)
ST.set_floor_z(shoe_min)

hr = bpy.data.objects['Hand_Racket'].matrix_world.translation
RES_F = (520, 760) if fast else (780, 1140)
RES_C = (520, 520) if fast else (780, 780)
cells = {
    'full_front': dict(target=ctr_full, az=0, el=3, dist=7.2, lens=105, res=RES_F),
    'full_q3': dict(target=ctr_full, az=-38, el=4, dist=7.2, lens=105, res=RES_F),
    'full_side': dict(target=ctr_full, az=-90, el=3, dist=7.2, lens=105, res=RES_F),
    'full_back': dict(target=ctr_full, az=180, el=3, dist=7.2, lens=105, res=RES_F),
    'waist_front': dict(target=(0, -0.03, H.get('waist_z', 0.96 if tag == 'male' else 0.975)), az=0, el=5, dist=2.8, lens=85, res=RES_C),
    'waist_back': dict(target=(0, -0.03, H.get('waist_z', 0.96 if tag == 'male' else 0.975)), az=180, el=5, dist=2.8, lens=85, res=RES_C),
    'hand_a': dict(target=tuple(hr), az=-55, el=12, dist=0.62, lens=70, res=RES_C),
    'hand_b': dict(target=tuple(hr), az=-135, el=14, dist=0.62, lens=70, res=RES_C),
}
for nm, c in cells.items():
    if only and nm not in only.split(','):
        continue
    ST.shot(f'{outdir}/{tag}_{color}_{nm}.png', c['target'], az=c['az'], el=c['el'], dist=c['dist'], lens=c['lens'], res=c['res'])
    print('cell', nm)
print('RENDER_DONE', tag, color)
