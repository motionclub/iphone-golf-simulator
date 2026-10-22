"""Measure the racket mesh objects of an open blend (racket local frame). Importable: measure(objs dict) or run directly.
blender -b <blend> --python measure_racket.py -- <out.json>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *


def tri_count(o):
    return int(sum(len(p.vertices) - 2 for p in o.data.polygons))


def vert_xyz(o):
    return mesh_co(o, world=False)


def measure(objs):
    """objs: dict name -> bpy object (Racket_Classic, StringBed, Grip, ButtCap, Collider_Racket)."""
    frame, strings, grip, cap, col = (objs[k] for k in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket'))
    F, Sg, Gr, Cp = vert_xyz(frame), vert_xyz(strings), vert_xyz(grip), vert_xyz(cap)
    vis = np.concatenate([F, Sg, Gr, Cp], axis=0)
    out = {}
    out['bbox_min'] = vis.min(0).tolist()
    out['bbox_max'] = vis.max(0).tolist()
    out['length_m'] = float(vis[:, 1].max() - vis[:, 1].min())
    out['width_m'] = float(vis[:, 0].max() - vis[:, 0].min())
    out['depth_m'] = float(vis[:, 2].max() - vis[:, 2].min())
    # head: frame verts above y=0.20; outer top = max y; outer bottom of the head loop = lowest frame vertex at |x|<0.015 above the window apex
    head_top = float(F[:, 1].max())
    bridge = F[(np.abs(F[:, 0]) < 0.012) & (F[:, 1] > 0.17) & (F[:, 1] < 0.30)]
    # the bridge underside is the lowest point of the head loop between the arms; the window apex region is below it, so use the
    # first big gap in y at x~0 (frame verts) to separate stem/apex from the bridge
    ys = np.sort(bridge[:, 1])
    gaps = np.diff(ys)
    k = np.argmax(gaps)
    head_bottom = float(ys[k + 1]) if gaps[k] > 0.01 else float(ys[0])
    out['head_top_y'] = head_top
    out['head_bottom_y'] = head_bottom
    out['head_outer_height_m'] = head_top - head_bottom
    hv = F[F[:, 1] > head_bottom + 0.02]
    out['head_outer_width_m'] = float(hv[:, 0].max() - hv[:, 0].min())
    out['head_outer_width_y'] = float(hv[np.argmax(hv[:, 0]), 1])
    out['frame_depth_max_m'] = float(F[:, 2].max() - F[:, 2].min())
    # grip sleeve diameter by slicing: radial distance from the Y axis for vertices in thin slabs
    ys_s = np.linspace(-0.090, 0.090, 37)
    diam = []
    for y in ys_s:
        sel = np.abs(Gr[:, 1] - y) < 0.0016
        if sel.sum() < 6:
            continue
        r = np.hypot(Gr[sel, 0], Gr[sel, 2])
        diam.append((float(y), float(2 * r.mean()), float(2 * r.min()), float(2 * r.max())))
    d = np.array(diam)
    out['grip_slices'] = len(d)
    out['grip_diameter_mean_m'] = float(d[:, 1].mean())
    out['grip_diameter_min_m'] = float(d[:, 2].min())
    out['grip_diameter_max_m'] = float(d[:, 3].max())
    out['grip_y_min'] = float(Gr[:, 1].min())
    out['grip_y_max'] = float(Gr[:, 1].max())
    out['grip_usable_length_m'] = float(Gr[:, 1].max() - Gr[:, 1].min())
    out['grip_center_y'] = float(0.5 * (Gr[:, 1].max() + Gr[:, 1].min()))
    rc = np.hypot(Cp[:, 0], Cp[:, 2])
    out['butt_cap_diameter_max_m'] = float(2 * rc.max())
    out['butt_end_y'] = float(Cp[:, 1].min())
    out['tris'] = {k: tri_count(o) for k, o in objs.items()}
    out['tris_visual'] = int(sum(out['tris'][k] for k in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap')))
    out['tris_total_with_collider'] = int(sum(out['tris'].values()))
    out['verts'] = {k: len(o.data.vertices) for k, o in objs.items()}
    out['materials'] = {k: [m.name if m else None for m in o.data.materials] for k, o in objs.items()}
    # symmetry of the frame about x=0 (nearest-vertex mirror distance)
    from mathutils.kdtree import KDTree
    kd = KDTree(len(F))
    for i, v in enumerate(F):
        kd.insert(v, i)
    kd.balance()
    sample = F[np.random.RandomState(1).choice(len(F), min(2000, len(F)), replace=False)]
    dm = [kd.find((-v[0], v[1], v[2]))[2] for v in sample]
    out['frame_mirror_x_max_mm'] = float(max(dm) * 1000)
    # logo / text / image checks
    out['text_objects'] = [o.name for o in bpy.data.objects if o.type in ('FONT', 'CURVE', 'GPENCIL')]
    out['images'] = [i.name for i in bpy.data.images]
    out['image_texture_nodes'] = int(sum(1 for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'))
    out['uv_layers'] = {k: len(o.data.uv_layers) for k, o in objs.items()}
    out['object_types'] = {o.name: o.type for o in bpy.data.objects}
    # closedness (edge manifold check) for the frame and grip/cap
    import bmesh
    man = {}
    for k in ('Racket_Classic', 'Grip', 'ButtCap'):
        bm = bmesh.new(); bm.from_mesh(objs[k].data)
        man[k] = dict(non_manifold_edges=int(sum(1 for e in bm.edges if not e.is_manifold)), loose_verts=int(sum(1 for v in bm.verts if not v.link_edges)))
        bm.free()
    out['manifold'] = man
    return out


if __name__ == '__main__':
    a = args_after_dashes()
    objs = {n: bpy.data.objects[n] for n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket')}
    res = measure(objs)
    Path(a[0]).write_text(json.dumps(res, indent=1))
    print('MEASURE_DONE', json.dumps({k: res[k] for k in ('length_m', 'head_outer_height_m', 'head_outer_width_m', 'grip_diameter_mean_m', 'grip_usable_length_m', 'butt_cap_diameter_max_m', 'tris_visual')}))
