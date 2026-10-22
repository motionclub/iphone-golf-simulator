"""Experiment: raw SDF frame mesh -> (a) collapse decimate + surface projection, (b) quadriflow. Writes variants to tmp/ as blends + renders."""
import sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import racket_geom as G, sdf_tools as S
import render_lib as R

p = dict(G.P)
t0 = time.time()
V, T, info = G.build_frame_sdf(p, h=0.0015, k=p['sdf_k'])
F, grid = info['F'], info['gridobj']
print('raw', len(V), len(T), 'sdf time', round(time.time() - t0, 1))
np.savez(WORK / 'tmp' / 'frame_raw.npz', V=V, T=T)


def project(V, iters=3):
    for _ in range(iters):
        d = S.sample(F, grid, V)
        g = S.gradient(F, grid, V)
        gl = np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)
        V = V - d[:, None] * g / gl
    return V


def make_obj(name, V, T):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(int(i) for i in t) for t in T])
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def evaluated_copy(o):
    bpy.context.view_layer.update()
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return bpy.data.meshes.new_from_object(ev)


def finish(o, me, mat):
    old = o.data
    if old is not me:
        o.data = me
        bpy.data.meshes.remove(old)
    me.materials.clear(); me.materials.append(mat)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    co = mesh_co(o)
    co = project(co)
    me.vertices.foreach_set('co', co.ravel())
    g = S.gradient(F, grid, co)
    g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)
    me.normals_split_custom_set_from_vertices([tuple(x) for x in g])
    me.update()


reset_scene()
mat = bpy.data.materials.new('W'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.85, 0.85, 0.84, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.5
variants = {}
# (a) collapse decimate at 4200 / 6500
for tag, tgt in (('dec4k', 4200), ('dec6k', 6500)):
    o = make_obj(tag, V, T)
    m = o.modifiers.new('D', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = tgt / len(T)
    m.use_collapse_triangulate = True; m.use_symmetry = True; m.symmetry_axis = 'X'
    me = evaluated_copy(o); o.modifiers.remove(m)
    finish(o, me, mat)
    variants[tag] = o
    print(tag, len(o.data.polygons))
# (b) quadriflow
for tag, tgt in (('qf2k', 2400), ('qf3k', 3200)):
    o = make_obj(tag, V, T)
    for ob in bpy.data.objects: ob.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    try:
        t1 = time.time()
        r = bpy.ops.object.quadriflow_remesh(target_faces=tgt, use_mesh_symmetry=True, use_preserve_sharp=False, use_preserve_boundary=False, smooth_normals=True, mode='FACES', seed=1)
        print(tag, r, 'quads', len(o.data.polygons), 'tris', sum(len(q.vertices) - 2 for q in o.data.polygons), round(time.time() - t1, 1), 's')
        finish(o, o.data, mat)
        variants[tag] = o
    except Exception as e:
        print(tag, 'FAILED', e)
for ob in variants.values():
    ob.hide_render = True
R.studio(bg=(0.36, 0.37, 0.39), samples=48)
for i, (tag, ob) in enumerate(variants.items()):
    for o2 in variants.values(): o2.hide_render = True
    ob.hide_render = False
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.location = (0, 0, 0.60)
    R.shot(str(WORK / 'tmp' / f'exp_{tag}_throat.png'), (0, 0, 0.60 + 0.20), az=38, el=18, dist=0.8, lens=85, res=(900, 900))
    R.shot(str(WORK / 'tmp' / f'exp_{tag}_head.png'), (-0.07, 0, 0.60 + 0.30), az=-35, el=12, dist=0.6, lens=85, res=(900, 900))
print('EXP_DONE')
