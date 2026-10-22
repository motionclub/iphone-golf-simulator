"""Export the finished racket blend to FBX (hero export flags: meters, scale 1, -Z forward / Y up) and verify by re-import.
blender -b <Racket_Classic.blend> --python export_racket.py -- <out_dir>"""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
from mathutils.kdtree import KDTree

out_dir = Path(args_after_dashes()[0])
out_dir.mkdir(parents=True, exist_ok=True)
blend = Path(bpy.data.filepath)
FLAGS = dict(use_selection=True, object_types={'MESH'}, global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
             axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True, mesh_smooth_type='OFF', add_leaf_bones=False, bake_anim=False, path_mode='COPY')
VISUAL = ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap')


def select_only(names):
    for o in bpy.data.objects:
        o.select_set(False)
    for n in names:
        bpy.data.objects[n].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[names[0]]


# sanity: identity transforms (origin = grip centre) and world == local
for n in VISUAL + ('Collider_Racket',):
    o = bpy.data.objects[n]
    mw = np.array(o.matrix_world)
    assert np.allclose(mw, np.eye(4), atol=1e-9), (n, mw)
src = {n: mesh_co(bpy.data.objects[n]) for n in VISUAL + ('Collider_Racket',)}
src_tris = {n: int(sum(len(p.vertices) - 2 for p in bpy.data.objects[n].data.polygons)) for n in src}
mats = sorted({m.name for n in VISUAL for m in bpy.data.objects[n].data.materials})
fbx_vis = out_dir / 'Racket_Classic.fbx'
fbx_col = out_dir / 'Racket_Classic_Collider.fbx'
select_only(VISUAL)
bpy.ops.export_scene.fbx(filepath=str(fbx_vis), **FLAGS)
select_only(('Collider_Racket',))
bpy.ops.export_scene.fbx(filepath=str(fbx_col), **FLAGS)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
res = dict(blend=str(blend), blend_sha256=sha(blend), fbx_visual=str(fbx_vis), fbx_visual_sha256=sha(fbx_vis), fbx_visual_bytes=fbx_vis.stat().st_size,
           fbx_collider=str(fbx_col), fbx_collider_sha256=sha(fbx_col), source_tris=src_tris, materials=mats,
           export_flags={k: (sorted(v) if isinstance(v, set) else v) for k, v in FLAGS.items()})
# ---- re-import in a clean session state and compare
for tag, fbx, names in (('visual', fbx_vis, VISUAL), ('collider', fbx_col, ('Collider_Racket',))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx))
    objs = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
    info = dict(objects=sorted(objs), parents={n: (o.parent.name if o.parent else None) for n, o in objs.items()})
    allco = []
    per = {}
    for n in names:
        o = objs[n]
        M = np.array(o.matrix_world)
        co = mesh_co(o) @ M[:3, :3].T + M[:3, 3]
        kd = KDTree(len(co))
        for i, c in enumerate(co):
            kd.insert(c, i)
        kd.balance()
        d = np.array([kd.find(tuple(c))[2] for c in src[n]])
        per[n] = dict(verts=len(co), tris=int(sum(len(p.vertices) - 2 for p in o.data.polygons)), max_err_mm=float(d.max() * 1000),
                      materials=[m.name if m else None for m in o.data.materials], dims_m=[float(x) for x in (co.max(0) - co.min(0))])
        allco.append(co)
    allco = np.concatenate(allco)
    info['per_object'] = per
    info['bbox_min'] = allco.min(0).tolist(); info['bbox_max'] = allco.max(0).tolist()
    info['extent_m'] = (allco.max(0) - allco.min(0)).tolist()
    info['scale_of_roots'] = {n: list(o.scale) for n, o in objs.items() if o.parent is None}
    res['reimport_' + tag] = info
(out_dir / 'export_report.json').write_text(json.dumps(res, indent=1))
print('EXPORT_DONE', json.dumps({k: res['reimport_visual']['per_object'][k]['max_err_mm'] for k in VISUAL}), res['reimport_visual']['extent_m'])
