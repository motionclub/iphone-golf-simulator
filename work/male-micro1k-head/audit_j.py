"""Micro1j blend-level audit.  blender -b --factory-startup --python audit_j.py -- <final.blend> <out.json> [outdir] [start.blend]
 - Body_M vs the START blend (bit-compare): moved set, outside-zone (z_start < 1.40) must be 0, hands 0, topology identical, vertex groups identical
 - Face_M identical to START; custom normals present; normals of vertices far from the edit unchanged
 - silhouette gate: bald_front / bald_back (Body_M only and with Face_M) vs the frozen target masks (<= 5.0 %)"""
import sys, json, hashlib, pickle
from pathlib import Path
from collections import defaultdict
import numpy as np
import bpy
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W = R / 'work/male-micro1k-head'
argv = sys.argv[sys.argv.index('--') + 1:]
blend = Path(argv[0]); outj = Path(argv[1]); outdir = Path(argv[2]) if len(argv) > 2 else W / 'final/audit'; outdir.mkdir(parents=True, exist_ok=True)
start_blend = Path(argv[3]) if len(argv) > 3 else W / 'baseline/HeroBase_Male_Silhouette.blend'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def grab(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects['Body_M']; me = body.data; n = len(me.vertices)
    V = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    F = [list(p.vertices) for p in me.polygons]
    face = bpy.data.objects.get('Face_M'); FV = None
    if face:
        FV = np.empty(len(face.data.vertices) * 3, np.float32); face.data.vertices.foreach_get('co', FV); FV = FV.reshape(-1, 3)
    groups = {vg.name: sorted(v.index for v in me.vertices if any(g.group == vg.index for g in v.groups)) for vg in body.vertex_groups}
    cn = None
    if me.has_custom_normals:
        cn = np.empty(len(me.loops) * 3, np.float32); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
        lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
    else: lv = None
    return dict(V=V, F=F, FV=FV, groups=groups, cn=cn, lv=lv, mats=[m.name if m else None for m in me.materials], fmats=[m.name if m else None for m in face.data.materials] if face else None)


S0 = grab(start_blend)
S1 = grab(blend)               # leaves the final blend open for the silhouette renders below
res = dict(blend=str(blend), blend_sha256=sha(blend), start_blend=str(start_blend), start_sha256=sha(start_blend))
V0, V1 = S0['V'], S1['V']; n = len(V0)
res['verts'] = int(n); res['verts_same_count'] = bool(len(V1) == n)
moved = np.any(V0 != V1, axis=1); zone = V0[:, 2] >= 1.40
d = np.linalg.norm(V1.astype(np.float64) - V0.astype(np.float64), axis=1)
res['moved_total'] = int(moved.sum()); res['moved_outside_zone_z_lt_1_40'] = int((moved & ~zone).sum())
res['min_z_of_moved_verts'] = float(V0[moved, 2].min()) if moved.any() else None; res['max_move_mm'] = float(d.max() * 1000); res['mean_move_mm_moved'] = float(d[moved].mean() * 1000) if moved.any() else 0.0
res['hands_moved'] = int((moved & (np.abs(V0[:, 0]) > 0.44) & (V0[:, 2] < 1.06)).sum())
res['arms_moved'] = int((moved & (np.abs(V0[:, 0]) > 0.14) & (V0[:, 2] >= 1.06)).sum())
res['torso_pelvis_legs_feet_moved'] = int((moved & (V0[:, 2] < 1.40)).sum())
res['weld_ring_moved'] = int((moved & (np.abs(V0[:, 2] - 1.43) < 0.0016) & (np.abs(V0[:, 0]) < 0.14)).sum())
res['topology_identical'] = bool(S0['F'] == S1['F']); res['tris'] = int(sum(len(f) - 2 for f in S1['F'])); res['quad_faces'] = int(sum(1 for f in S1['F'] if len(f) == 4))
res['vertex_groups_identical'] = bool(S0['groups'] == S1['groups']); res['vertex_groups'] = sorted(S1['groups'])
res['face_m_identical'] = bool(S0['FV'] is not None and np.array_equal(S0['FV'], S1['FV'])); res['face_m_materials_identical'] = bool(S0['fmats'] == S1['fmats'])
res['body_materials'] = S1['mats']
ec = defaultdict(int)
for p in S1['F']:
    for k in range(len(p)):
        a, b = p[k], p[(k + 1) % len(p)]; ec[(min(a, b), max(a, b))] += 1
res['boundary_edges'] = int(sum(1 for c in ec.values() if c == 1)); res['nonmanifold_edges'] = int(sum(1 for c in ec.values() if c > 2))
ec0 = defaultdict(int)
for p in S0['F']:
    for k in range(len(p)):
        a, b = p[k], p[(k + 1) % len(p)]; ec0[(min(a, b), max(a, b))] += 1
res['boundary_edges_start'] = int(sum(1 for c in ec0.values() if c == 1)); res['nonmanifold_edges_start'] = int(sum(1 for c in ec0.values() if c > 2))
res['height_m'] = float(V1[:, 2].max() - V1[:, 2].min()); res['nan_or_inf'] = bool(~np.isfinite(V1).all())
# custom normals: untouched vertices keep the START normals exactly (angle), edited ones are reported
res['custom_normals_present'] = bool(S1['cn'] is not None)
if S0['cn'] is not None and S1['cn'] is not None:
    ang = np.degrees(np.arccos(np.clip((S0['cn'] * S1['cn']).sum(1), -1, 1)))
    vmov = np.zeros(n, bool); vmov[moved] = True
    # vertices adjacent to a moved vertex also change (geometric normal)
    adjm = vmov.copy()
    for (a, b) in ec: 
        if vmov[a]: adjm[b] = True
        if vmov[b]: adjm[a] = True
    far = ~adjm[S1['lv']]
    res['normals_far_from_edit'] = dict(corners=int(far.sum()), max_angle_deg=float(ang[far].max()), changed_corners_gt_0_05deg=int((ang[far] > 0.05).sum()))
    near = adjm[S1['lv']]
    res['normals_edit_region'] = dict(corners=int(near.sum()), mean_rotation_deg=float(ang[near].mean()), max_rotation_deg=float(ang[near].max()))
# ---- silhouette gate (the final blend is still open)
sc = bpy.context.scene
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
face = bpy.data.objects.get('Face_M'); M = R / 'work/male-silhouette'


def alpha_of(path):
    img = bpy.data.images.load(str(path), check_existing=False)
    a = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4); bpy.data.images.remove(img); return a


sil = {}
for tag, show_face in (('body', False), ('withface', True)):
    if face: face.hide_render = not show_face
    for view in ('bald_front', 'bald_back'):
        sc.camera = bpy.data.objects['Locked_' + view]; sc.render.filepath = str((outdir / f'{tag}_{view}.png').resolve()); bpy.ops.render.render(write_still=True)
        r = alpha_of(outdir / f'{tag}_{view}.png')[:, :, 3] > 0.5
        t = alpha_of(M / f'{view}_target.png'); tm = (t[:, :, 3] > 0.5) if (t[:, :, 3].min() < 0.99) else (t[:, :, 0] > 0.5)
        diff = int((r != tm).sum()); uni = int((r | tm).sum()); sil[f'{tag}_{view}'] = dict(diff=diff, union=uni, pct=100.0 * diff / uni)
res['silhouette'] = sil
outj.write_text(json.dumps(res, indent=1))
print('AUDIT_JSON ' + json.dumps({k: res[k] for k in ('moved_total', 'moved_outside_zone_z_lt_1_40', 'min_z_of_moved_verts', 'hands_moved', 'topology_identical', 'tris', 'vertex_groups_identical', 'face_m_identical', 'boundary_edges', 'nonmanifold_edges')}))
print('SIL ' + json.dumps({k: round(v['pct'], 4) for k, v in sil.items()}))
