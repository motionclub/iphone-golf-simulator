"""Replace the head zone of the START blend by the new head patch (welded to the 30-vertex collar ring), build Face_F, loops as vertex groups, UVs.
blender -b --factory-startup --python assemble.py -- <patch tag> <out.blend>"""
import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, bpy
import fl, facef
argv = sys.argv[sys.argv.index('--') + 1:]
tag, out = argv[0], argv[1]
START = fl.W / 'baseline/HeroBase_Female_start.blend'
bpy.ops.wm.open_mainfile(filepath=str(START))
ob = bpy.data.objects['Body_F']; me = ob.data
V0, F0 = fl.mesh_arrays(me)
mi0 = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi0)
mats0 = [m.name for m in me.materials]
ringd = np.load(fl.W / 'data/ring.npz'); zone_faces = set(int(i) for i in ringd['zone_faces'])
pd = np.load(fl.W / f'data/{tag}_patch.npz'); pj = json.load(open(fl.W / f'data/{tag}_patch.json'))
P = pd['P']; off = pd['Foff']; Fp = [pd['F'][off[i]:off[i + 1]] for i in range(len(off) - 1)]
collar_map = {int(k): int(v) for k, v in pj['collar_map'].items()}
# ---- body faces kept
keep = [i for i in range(len(F0)) if i not in zone_faces]
used = np.zeros(len(V0), bool)
for i in keep: used[list(F0[i])] = True
for v in collar_map.values(): used[v] = True
old2new = -np.ones(len(V0), np.int64); old2new[used] = np.arange(used.sum())
Vk = V0[used]
# patch vertices: collar -> body ring vertex; others appended
nb = len(Vk); pmap = {}; newV = []
for i in range(len(P)):
    if i in collar_map: pmap[i] = int(old2new[collar_map[i]])
    else: pmap[i] = nb + len(newV); newV.append(P[i])
Vall = np.vstack([Vk, np.array(newV)]) if newV else Vk
Fkeep = [[int(old2new[v]) for v in F0[i]] for i in keep]
Fhead = [[pmap[int(v)] for v in f] for f in Fp]
# materials: Base_Grey_F (0), Skin_F (1)
grey = mats0.index('Base_Grey_F'); skin = mats0.index('Skin_F')
mkeep = np.array([0 if mi0[i] == grey else 1 for i in keep], np.int32)
collar_set = set(collar_map.keys())
mhead = np.array([0 if any(int(v) in collar_set for v in f) else 1 for f in Fp], np.int32)      # the 60->30 transition strip at the collar is grey (clean horizontal collar top)
Fall = Fkeep + Fhead; Mall = np.concatenate([mkeep, mhead])
print('body verts', len(Vall), 'faces', len(Fall), 'tris', sum(len(f) - 2 for f in Fall), '| dropped zone faces', len(zone_faces))
# ---- UVs: keep old loop UVs for kept faces; spherical/cylindrical UVs for the head faces
uv0 = np.array([l.uv[:] for l in me.uv_layers['UVMap'].data]) if 'UVMap' in me.uv_layers else None
ls0 = np.empty(len(me.polygons), np.int64); me.polygons.foreach_get('loop_start', ls0)
uvs = []
for i in keep:
    n = len(F0[i]); uvs.append(uv0[ls0[i]:ls0[i] + n] if uv0 is not None else np.zeros((n, 2)))
def head_uv(p):
    C = np.array([0.0, -0.010, 1.575]); d = p - C; th = math.atan2(d[1], d[0]); ph = math.acos(max(-1, min(1, d[2] / (np.linalg.norm(d) + 1e-12))))
    return [0.5 + 0.5 * th / math.pi * 0.5, 0.5 + 0.5 * (ph / math.pi)]               # packed in the upper-right quadrant of UV space
for f in Fhead:
    uvs.append(np.array([head_uv(Vall[v]) for v in f]))
# ---- rebuild Body_F mesh
for o in list(bpy.data.objects):
    if o.name == 'Body_F': bpy.data.objects.remove(o, do_unlink=True)
nm = bpy.data.meshes.new('Body_F')
nm.vertices.add(len(Vall)); nm.vertices.foreach_set('co', Vall.astype(np.float32).ravel())
lens = np.array([len(f) for f in Fall]); nm.loops.add(int(lens.sum())); nm.polygons.add(len(Fall))
nm.loops.foreach_set('vertex_index', np.concatenate([np.asarray(f, np.int64) for f in Fall]))
nm.polygons.foreach_set('loop_start', np.concatenate([[0], np.cumsum(lens)[:-1]])); nm.polygons.foreach_set('loop_total', lens)
nm.polygons.foreach_set('material_index', Mall); nm.polygons.foreach_set('use_smooth', [True] * len(Fall))
nm.update(calc_edges=True)
uvl = nm.uv_layers.new(name='UVMap'); uvl.data.foreach_set('uv', np.concatenate(uvs).ravel())
mg = bpy.data.materials['Base_Grey_F']; ms = bpy.data.materials['Skin_F']
nm.materials.append(mg); nm.materials.append(ms)
body = bpy.data.objects.new('Body_F', nm); bpy.context.scene.collection.objects.link(body)
# ---- loops as vertex groups (indices in the patch -> assembled)
for name, verts in pj['loops'].items():
    vg = body.vertex_groups.new(name='LOOP_' + name)
    ids = sorted({pmap[int(v)] for v in verts if int(v) in pmap and int(v) not in collar_map} | {pmap[int(v)] for v in verts if int(v) in collar_map})
    vg.add(ids, 1.0, 'REPLACE')
# ---- Face_F
LV = pd['LV']; foffs = pd['LFoff']; LF = [pd['LF'][foffs[i]:foffs[i + 1]] for i in range(len(foffs) - 1)]
fo = fl.make_mesh_object('Face_F', LV, LF)
for nm_ in pj['mats']: fo.data.materials.append(bpy.data.materials.new('Face_' + nm_))
fo.data.polygons.foreach_set('material_index', pd['LM'])
# ---- old hair mesh is fitted to the old head: keep it in the file but hidden (not part of the base)
h = bpy.data.objects.get('Hair_F')
if h: h.hide_viewport = True; h.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=str(out))
json.dump(dict(old2new=old2new.tolist(), n_body_kept=int(nb), pmap={str(k): int(v) for k, v in pmap.items()}), open(str(out).replace('.blend', '_vmap.json'), 'w'))
print('saved', out)
