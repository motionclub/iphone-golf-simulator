import bpy, sys, json, hashlib, numpy as np
from pathlib import Path
ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
AUTH = ROOT / 'ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend'
PREV = ROOT / 'ArtDir/hero/base_lock/preview/outfit_example/HeroBase_Male_OutfitExample.blend'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(AUTH))
a = np.array([v.co[:] for v in bpy.data.objects['Body_M'].data.vertices], np.float32)
ta = sum(len(p.vertices) - 2 for p in bpy.data.objects['Body_M'].data.polygons)
bpy.ops.wm.open_mainfile(filepath=str(PREV))
b = np.array([v.co[:] for v in bpy.data.objects['Body_M'].data.vertices], np.float32)
res = dict(authority_sha256=sha(AUTH), preview_sha256=sha(PREV), body_coords_identical=bool(a.shape == b.shape and np.array_equal(a, b)), body_tris=ta)
parts = {}
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body_M':
        m = o.data
        parts[o.name] = dict(verts=len(m.vertices), tris=sum(len(p.vertices) - 2 for p in m.polygons), collections=[c.name for c in o.users_collection], hide_render=o.hide_render)
res['parts'] = parts
groups = {}
for n, d in parts.items():
    g = d['collections'][0] if d['collections'] else '?'
    groups.setdefault(g, 0)
    groups[g] += d['tris']
res['tris_by_collection'] = groups
res['materials'] = sorted(m.name for m in bpy.data.materials if m.users)
print('VERIFY_JSON ' + json.dumps(res))
