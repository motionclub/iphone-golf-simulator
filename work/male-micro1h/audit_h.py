"""Regression + gate audit of a final blend.  blender -b --factory-startup --python audit_h.py -- <final.blend> <out.json> [outdir]
 - original-index vertices: unchanged outside the head zone? hands bit-identical? chin band displacement
 - silhouette gate: bald_front / bald_back (Body_M only and with Face_M) vs the frozen target masks (<= 5.0 %)
 - topology stats: tris, quads, tri faces, boundary/non-manifold edges, head edge-length stats"""
import sys, json, hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
import bpy
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W = R / 'work/male-micro1h'
argv = sys.argv[sys.argv.index('--') + 1:]
blend = Path(argv[0]); outj = Path(argv[1]); outdir = Path(argv[2]) if len(argv) > 2 else W / 'final/audit'
outdir.mkdir(parents=True, exist_ok=True)
LOCK = np.load(W / 'data/V_micro1g.npy')            # the verified start blend's Body_M (c6b66ede...)
K5 = np.load(W / 'data/V_micro1f.npy')
bpy.ops.wm.open_mainfile(filepath=str(blend))
body = bpy.data.objects['Body_M']; face = bpy.data.objects.get('Face_M')
me = body.data
n = len(me.vertices)
Vc = np.empty(n * 3, np.float64); me.vertices.foreach_get('co', Vc); Vc = Vc.reshape(-1, 3)
N0 = len(LOCK)
res = dict(blend=str(blend), blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(), verts=n, polys=len(me.polygons))
polys = [list(p.vertices) for p in me.polygons]
res['tris'] = int(sum(len(p) - 2 for p in polys)); res['quad_faces'] = int(sum(1 for p in polys if len(p) == 4)); res['tri_faces'] = int(sum(1 for p in polys if len(p) == 3))
res['ngon_faces'] = int(sum(1 for p in polys if len(p) > 4))
if face:
    res['face_m'] = dict(verts=len(face.data.vertices), tris=int(sum(len(p.vertices) - 2 for p in face.data.polygons)), materials=[m.name if m else None for m in face.data.materials])
# ---- original-index regression vs the lock blend (Micro1g)
z = LOCK[:, 2]; x = LOCK[:, 0]
head = (z > 1.43) & (np.abs(x) < 0.14)
hands = (np.abs(x) > 0.44) & (z < 1.06)
same = np.all(Vc[:N0] == LOCK, axis=1)
res['original_vertices'] = N0
res['moved_total'] = int((~same).sum())
res['moved_outside_head_zone'] = int((~same & ~head).sum())
res['moved_in_hands'] = int((~same & hands).sum())
res['body_below_neck_bit_identical'] = bool((~same & ~head).sum() == 0)
d = np.linalg.norm(Vc[:N0] - LOCK, axis=1)
chin_band = head & (z < 1.47)
res['chin_band_orig_verts'] = int(chin_band.sum()); res['chin_band_moved'] = int((~same & chin_band).sum()); res['chin_band_max_mm'] = float(d[chin_band].max() * 1000)
# new vertices (appended) in the chin band: distance to the lock surface (nearest lock vertex is a lower bound only) -> report count
newv = Vc[N0:]
res['new_vertices'] = int(len(newv))
# ---- topology audit
ec = defaultdict(int)
for p in polys:
    for k in range(len(p)):
        a, b = p[k], p[(k + 1) % len(p)]; ec[(min(a, b), max(a, b))] += 1
res['boundary_edges'] = sum(1 for c in ec.values() if c == 1); res['nonmanifold_edges'] = sum(1 for c in ec.values() if c > 2)
res['height_m'] = float(Vc[:, 2].max() - Vc[:, 2].min()); res['nan_or_inf'] = bool(~np.isfinite(Vc).all())
vol = 0.0
for p in polys:
    for k in range(1, len(p) - 1):
        vol += float(np.dot(Vc[p[0]], np.cross(Vc[p[k]], Vc[p[k + 1]]))) / 6.0
res['signed_volume_m3'] = vol
# head edge stats (edges with both verts in the head zone, face zone)
head_now = (Vc[:, 2] > 1.43) & (np.abs(Vc[:, 0]) < 0.14)
E = np.array(sorted(ec.keys()))
sel = head_now[E[:, 0]] & head_now[E[:, 1]]
el = np.linalg.norm(Vc[E[sel, 0]] - Vc[E[sel, 1]], axis=1) * 1000
zc = 0.5 * (Vc[E[sel, 0], 2] + Vc[E[sel, 1], 2]); yc = 0.5 * (Vc[E[sel, 0], 1] + Vc[E[sel, 1], 1])
fz = (zc > 1.47) & (zc < 1.63) & (yc < -0.02)
res['head_edge_mm'] = dict(mean=float(el.mean()), median=float(np.median(el)), p5=float(np.percentile(el, 5)), p95=float(np.percentile(el, 95)), max=float(el.max()), n=int(len(el)))
res['face_zone_edge_mm'] = dict(mean=float(el[fz].mean()), median=float(np.median(el[fz])), p5=float(np.percentile(el[fz], 5)), p95=float(np.percentile(el[fz], 95)), max=float(el[fz].max()), n=int(fz.sum()))
# ---- silhouette gate (blend's own locked workbench setup)
sc = bpy.context.scene
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
M = R / 'work/male-silhouette'


def alpha_of(path):
    img = bpy.data.images.load(str(path), check_existing=False)
    a = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)
    bpy.data.images.remove(img)
    return a


sil = {}
for tag, show_face in (('body', False), ('withface', True)):
    if face: face.hide_render = not show_face
    for view in ('bald_front', 'bald_back'):
        sc.camera = bpy.data.objects['Locked_' + view]
        sc.render.filepath = str((outdir / f'{tag}_{view}.png').resolve()); bpy.ops.render.render(write_still=True)
        r = alpha_of(outdir / f'{tag}_{view}.png')[:, :, 3] > 0.5
        t = alpha_of(M / f'{view}_target.png')
        tm = (t[:, :, 3] > 0.5) if (t[:, :, 3].min() < 0.99) else (t[:, :, 0] > 0.5)
        diff = int((r != tm).sum()); uni = int((r | tm).sum())
        sil[f'{tag}_{view}'] = dict(diff=diff, union=uni, pct=100.0 * diff / uni)
res['silhouette'] = sil
outj.write_text(json.dumps(res, indent=1))
print('AUDIT_JSON ' + json.dumps({k: res[k] for k in ('tris', 'moved_outside_head_zone', 'moved_in_hands', 'chin_band_max_mm', 'boundary_edges', 'nonmanifold_edges')}))
print('SIL ' + json.dumps({k: round(v['pct'], 4) for k, v in sil.items()}))
