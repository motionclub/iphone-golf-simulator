"""blender -b --factory-startup --python audit_ff.py -- <base.blend> <new.blend> <out.json> [--sil]
Audit for the legs/feet FORM2 job.  PYTHONPATH must contain work/male-micro1i/pylib (PIL) and the work dir.
Zone = Body_M vertices with ORIGINAL start z < 0.765 and |x| < 0.27 (8,745 verts).  The forefoot rebuild frees vertex slots inside the zone, reuses them and appends
extra vertices; every other vertex must be bit-identical (float32)."""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-legs-feet-form2')
from pathlib import Path
from collections import defaultdict
import numpy as np, bpy, bmesh
from mathutils.bvhtree import BVHTree
from ff_common import *

argv = sys.argv[sys.argv.index('--') + 1:]
base, new, outj = argv[:3]
do_sil = '--sil' in argv
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
ZONE_LIT = zone_mask_from_orig(); ZONE = zone_mask_eff()


def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    b = bpy.data.objects['Body_M']; me = b.data; n = len(me.vertices)
    V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    F = [tuple(p.vertices) for p in me.polygons]
    raw = np.zeros(len(me.loops) * 2, np.int32); me.attributes['custom_normal'].data.foreach_get('value', raw)
    ls = np.array([p.loop_start for p in me.polygons]); lt = np.array([p.loop_total for p in me.polygons])
    groups = defaultdict(list)
    for v in me.vertices:
        for g in v.groups: groups[b.vertex_groups[g.group].name].append((v.index, round(g.weight, 6)))
    f = bpy.data.objects.get('Face_M'); Vf = None
    if f:
        m2 = f.data; Vf = np.empty(len(m2.vertices) * 3); m2.vertices.foreach_get('co', Vf)
    return dict(V=V.astype(np.float32), V64=V, F=F, raw=raw.reshape(-1, 2), ls=ls, lt=lt, groups={k: sorted(v) for k, v in groups.items()}, Vf=Vf,
                vgnames=[vg.name for vg in b.vertex_groups], mats=[m.name if m else None for m in me.materials], has_cn=me.has_custom_normals,
                n_edges=len(me.edges), smooth=bool(all(p.use_smooth for p in me.polygons)))


A = load(base); B = load(new)
ZONE_LIT = zone_mask_from_orig(len(A['V'])); ZONE = zone_mask_eff(len(A['V']))
res = dict(base=base, base_sha256=sha(base), new=new, new_sha256=sha(new))
n0 = len(A['V']); n1 = len(B['V'])
res['verts'] = dict(base=n0, new=n1, appended=n1 - n0)
tris = lambda FF: int(sum(len(p) - 2 for p in FF))
res['faces'] = dict(base=len(A['F']), new=len(B['F']))
res['tris'] = dict(base=tris(A['F']), new=tris(B['F']), delta=tris(B['F']) - tris(A['F']))
res['topology_identical'] = bool(A['F'] == B['F'])
# --- zone isolation
V0 = A['V']; V1 = B['V'][:n0]
same = np.all(V0 == V1, axis=1)
res['zone_def'] = dict(start_z_lt=ZT, absx_lt=XMAX, literal_zone_verts=int(ZONE_LIT.sum()), effective_zone_verts=int(ZONE.sum()), extension='207 foot lateral-wall vertices (orig |x|>=0.27, z<0.15) unmoved by the earlier legs chat; the only |x|>=0.27 geometry below the crotch')
res['moved_outside_literal_zone'] = int((~same & ~ZONE_LIT).sum())
res['moved_inside_zone'] = int((~same & ZONE).sum()); res['moved_outside_zone'] = int((~same & ~ZONE).sum())
res['outside_zone_bit_identical'] = bool(res['moved_outside_zone'] == 0)
ap = B['V'][n0:]
res['appended_vertices_inside_zone_region'] = bool(len(ap) == 0 or ((ap[:, 2] < 0.15).all() and (np.abs(ap[:, 0]) < 0.30).all()))
res['appended_vertices_z_range'] = [float(ap[:, 2].min()), float(ap[:, 2].max())] if len(ap) else None
# faces: old faces untouched outside the foot -- every face of the new mesh that touches only unmoved-zone-outside vertices must exist in the old list
oldset = set(tuple(sorted(f)) for f in A['F']); newset_list = [tuple(sorted(f)) for f in B['F']]
kept = [f for f in B['F'] if tuple(sorted(f)) in oldset]
res['faces_kept_from_base'] = len(kept); res['faces_removed_from_base'] = len(A['F']) - len(kept); res['faces_added'] = len(B['F']) - len(kept)
# faces that were removed must lie entirely in the zone region
newset = set(newset_list)
removed = [f for f in A['F'] if tuple(sorted(f)) not in newset]
res['removed_faces_all_in_zone'] = bool(all(ZONE[list(f)].all() for f in removed))
# --- other objects / data
res['face_m_unchanged'] = bool(A['Vf'] is not None and np.array_equal(A['Vf'], B['Vf']))
res['vertex_groups_equal'] = bool(A['vgnames'] == B['vgnames'] and A['groups'] == B['groups'])
res['materials_equal'] = A['mats'] == B['mats']
res['all_faces_smooth'] = bool(B['smooth'])
res['has_custom_normals'] = bool(B['has_cn'])
# --- custom normals: unchanged corners identical
kept_idx = []
oldmap = {tuple(f): i for i, f in enumerate(A['F'])}
nm_same = 0; nm_diff = 0; nm_new = 0
for k, f in enumerate(B['F']):
    i = oldmap.get(tuple(f))
    if i is None:
        nm_new += B['lt'][k]; continue
    a = A['raw'][A['ls'][i]:A['ls'][i] + A['lt'][i]]; b = B['raw'][B['ls'][k]:B['ls'][k] + B['lt'][k]]
    if np.array_equal(a, b): nm_same += len(a)
    else: nm_diff += len(a)
res['custom_normal_corners'] = dict(unchanged_equal=int(nm_same), unchanged_but_different=int(nm_diff), new_corners=int(nm_new))
res['custom_normal_new_corners_all_zero'] = None
newfaces_mask = np.array([tuple(f) not in oldmap for f in B['F']])
if newfaces_mask.any():
    z = True
    for k in np.where(newfaces_mask)[0]:
        if B['raw'][B['ls'][k]:B['ls'][k] + B['lt'][k]].any(): z = False; break
    res['custom_normal_new_corners_all_zero'] = bool(z)
# --- manifold/boundary
def bnd(FF):
    ec = defaultdict(int)
    for p in FF:
        for k in range(len(p)):
            a, b = p[k], p[(k + 1) % len(p)]; ec[(min(a, b), max(a, b))] += 1
    return sum(1 for c in ec.values() if c == 1), sum(1 for c in ec.values() if c > 2)
res['boundary_nonmanifold'] = dict(base=bnd(A['F']), new=bnd(B['F']))
res['manifold_same_direction_pairs'] = dict(base=check_manifold(A['F'])[3], new=check_manifold(B['F'])[3])
res['nan_or_inf'] = bool(~np.isfinite(B['V']).all())
# --- geometry quality in the rebuilt region (new faces) vs the base zone
def face_normals(V, FF):
    V = V.astype(np.float64); out = np.zeros((len(FF), 3))
    for i, p in enumerate(FF):
        if len(p) == 4: n = np.cross(V[p[2]] - V[p[0]], V[p[3]] - V[p[1]])
        else: n = np.cross(V[p[1]] - V[p[0]], V[p[2]] - V[p[0]])
        out[i] = n / max(np.linalg.norm(n), 1e-18)
    return out
Fn = B['F']; Vn = B['V64']
fn = face_normals(Vn, Fn)
# flipped faces: compare each face normal with the mean of its edge-neighbours' normals
ef = defaultdict(list)
for i, p in enumerate(Fn):
    for k in range(len(p)):
        a, b = p[k], p[(k + 1) % len(p)]; ef[(min(a, b), max(a, b))].append(i)
flip = 0; flip_ids = []
for i, p in enumerate(Fn):
    nb = []
    for k in range(len(p)):
        a, b = p[k], p[(k + 1) % len(p)]
        nb += [j for j in ef[(min(a, b), max(a, b))] if j != i]
    if nb and fn[i] @ fn[nb].mean(0) < 0.0:
        flip += 1; flip_ids.append(i)
res['flipped_faces_vs_neighbours'] = int(flip)
newidx = np.where(newfaces_mask)[0]
def quad_angles(V, FF, idx):
    mn = 180.0; mx = 0.0; bad = 0
    for i in idx:
        p = FF[i]
        if len(p) != 4: continue
        a = []
        for k in range(4):
            u = V[p[(k - 1) % 4]] - V[p[k]]; v = V[p[(k + 1) % 4]] - V[p[k]]
            c = (u @ v) / max(np.linalg.norm(u) * np.linalg.norm(v), 1e-18); a.append(np.degrees(np.arccos(np.clip(c, -1, 1))))
        mn = min(mn, min(a)); mx = max(mx, max(a))
        if max(a) > 175 or min(a) < 5: bad += 1
    return mn, mx, bad
mn, mx, bad = quad_angles(Vn, Fn, newidx)
res['new_region_quad_angle_min_max_bad'] = [float(mn), float(mx), int(bad)]
E = np.array(sorted(set((min(p[k], p[(k + 1) % len(p)]), max(p[k], p[(k + 1) % len(p)])) for i in newidx for p in [Fn[i]] for k in range(len(p)))))
el = np.linalg.norm(Vn[E[:, 0]] - Vn[E[:, 1]], axis=1) * 1000
res['new_region_edge_mm'] = dict(mean=float(el.mean()), p01=float(np.percentile(el, 1)), p99=float(np.percentile(el, 99)), min=float(el.min()), max=float(el.max()))
tri_new = int(sum(len(Fn[i]) - 2 for i in newidx)); res['new_region_faces'] = int(len(newidx)); res['new_region_tris'] = tri_new
res['new_region_tri_count_faces'] = int(sum(1 for i in newidx if len(Fn[i]) == 3))
# --- self intersections (Body_M only) via BVH overlap
bpy.ops.wm.open_mainfile(filepath=new)
ob = bpy.data.objects['Body_M']
bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(bm, epsilon=0.0)
ov = tree.overlap(tree)
adj = defaultdict(set)
for f in bm.faces:
    for v in f.verts: adj[v.index].add(f.index)
real = 0; foot_real = 0
pairs = []
for a, b in ov:
    if a >= b: continue
    va = set(v.index for v in bm.faces[a].verts); vb = set(v.index for v in bm.faces[b].verts)
    if va & vb: continue
    real += 1
    cz = np.mean([bm.verts[i].co.z for i in va | vb]); cx = np.mean([abs(bm.verts[i].co.x) for i in va | vb])
    if cz < ZT and cx < XMAX: foot_real += 1; pairs.append((a, b))
res['self_intersecting_triangle_pairs'] = dict(total_nonadjacent=int(real), in_legs_zone=int(foot_real))
bm.free()
# base for comparison
bpy.ops.wm.open_mainfile(filepath=base)
bm = bmesh.new(); bm.from_mesh(bpy.data.objects['Body_M'].data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(bm, epsilon=0.0); ov = tree.overlap(tree); real0 = 0; foot0 = 0
for a, b in ov:
    if a >= b: continue
    va = set(v.index for v in bm.faces[a].verts); vb = set(v.index for v in bm.faces[b].verts)
    if va & vb: continue
    real0 += 1
    cz = np.mean([bm.verts[i].co.z for i in va | vb]); cx = np.mean([abs(bm.verts[i].co.x) for i in va | vb])
    if cz < ZT and cx < XMAX: foot0 += 1
res['self_intersecting_triangle_pairs_base'] = dict(total_nonadjacent=int(real0), in_legs_zone=int(foot0))
bm.free()
# --- ground contact / scale
res['ground'] = dict(min_z_base=float(A['V'][:, 2].min()), min_z_new=float(B['V'][:, 2].min()), min_z_equal=bool(A['V'][:, 2].min() == B['V'][:, 2].min()),
                     height_base=float(A['V'][:, 2].max() - A['V'][:, 2].min()), height_new=float(B['V'][:, 2].max() - B['V'][:, 2].min()))
sole = (B['V'][:, 2] < Z0 + 0.0006) & (np.abs(B['V'][:, 0]) < XMAX)
res['ground']['sole_vertices_on_plane'] = int(sole.sum())
if do_sil:
    R_ = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
    TD = R_ / 'work/male-legs-feet-form2/data/plates'
    sil = {}
    for tag, path in (('base', base), ('new', new)):
        bpy.ops.wm.open_mainfile(filepath=path)
        sc = bpy.context.scene; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.file_format = 'PNG'
        sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
        for o in bpy.data.objects:
            if o.type == 'EMPTY': o.hide_render = True
        fo = bpy.data.objects.get('Face_M')
        for fshow in (False, True):
            if fo: fo.hide_render = not fshow
            for view in ('bald_front', 'bald_back'):
                sc.camera = bpy.data.objects['Locked_' + view]
                p = R_ / f'work/male-legs-feet-form2/tmp/_sil_{tag}_{int(fshow)}_{view}.png'; sc.render.filepath = str(p); bpy.ops.render.render(write_still=True)
                img = bpy.data.images.load(str(p), check_existing=False); a = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)[:, :, 3] > 0.5; bpy.data.images.remove(img)
                timg = bpy.data.images.load(str(TD / f'{view}_target.png'), check_existing=False); t = np.array(timg.pixels[:], np.float32).reshape(timg.size[1], timg.size[0], 4); bpy.data.images.remove(timg)
                tm = (t[:, :, 3] > 0.5) if t[:, :, 3].min() < 0.99 else (t[:, :, 0] > 0.5)
                diff = int((a != tm).sum()); uni = int((a | tm).sum())
                sil[f'{tag}_{"withface" if fshow else "body"}_{view}'] = dict(pct=100.0 * diff / uni, xor_px=diff, union_px=uni)
    res['silhouette_native'] = sil
Path(outj).write_text(json.dumps(res, indent=1, default=float))
print('AUDIT', json.dumps({k: res[k] for k in ('moved_outside_zone', 'moved_inside_zone', 'outside_zone_bit_identical', 'appended_vertices_inside_zone_region', 'removed_faces_all_in_zone',
                                              'face_m_unchanged', 'vertex_groups_equal', 'flipped_faces_vs_neighbours', 'self_intersecting_triangle_pairs', 'self_intersecting_triangle_pairs_base')}, default=float))
print('NEWREGION', res['new_region_quad_angle_min_max_bad'], res['new_region_edge_mm'], 'tris delta', res['tris']['delta'])
if do_sil: print('SIL', json.dumps({k: round(v['pct'], 3) for k, v in res['silhouette_native'].items()}))
print('CUSTOM_NORMALS', res['custom_normal_corners'], res['custom_normal_new_corners_all_zero'])
