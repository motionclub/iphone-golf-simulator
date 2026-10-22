"""Scratch: digit model of a hand + debug render (components coloured, joints as spheres)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
from handlib import *
from handmodel import *
import render_setup_dl as RS
tag = args_after_dashes()[0]; out = args_after_dashes()[1]
h = HERO[tag]
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(SRC[h['body_src']], link=False) as (src, dst):
    dst.objects = [h['body']]
o = dst.objects[0]
bpy.context.scene.collection.objects.link(o)
co = mesh_co(o).astype(float)
me = o.data
E = edges_of(me); adj = adjacency(len(co), E)
hand = hand_region(co, adj, tag)
frame0 = pca_frame(co[hand])
ucut, digits = build_model(co, adj, tag, hand, frame0)
print(tag, 'ucut', ucut)
for nm, d in digits.items():
    print(nm, 'n', len(d['comp']), 'R %.1f mm' % (d['R']*1000), 'L %.3f' % d['L'], 'J', [np.round(j,3).tolist() for j in d['J']])
wrist, mid_mcp, u, v, p = landmark_frame(co, hand, digits, frame0)
print('landmark frame: wrist', np.round(wrist,4), 'mid_mcp', np.round(mid_mcp,4), 'u', np.round(u,3), 'v', np.round(v,3), 'p', np.round(p,3))
if tag == 'male':
    sj = json.load(open(SRC['socket_json']))['bodies']['male']['hand_frame_blender']
    uj, vj, pj = [np.array(sj[k]) for k in ('u_fingers', 'v_thumb', 'p_palm_normal')]
    ang = lambda a, b: np.degrees(np.arccos(np.clip(np.dot(a, b), -1, 1)))
    print('angle vs racket-chat male frame: u %.1f v %.1f p %.1f deg' % (ang(u, uj), ang(v, vj), ang(p, pj)))
    gc = np.array(json.load(open(SRC['socket_json']))['bodies']['male']['socket_bind_pose_blender']['position'])
    rel = gc - mid_mcp
    print('racket-chat male grip centre relative to my middle-MCP, in my frame (u,v,p):', np.round([rel@u, rel@v, rel@p], 4))
# debug colours: vertex colours per digit
cols = {'thumb': (1,0.3,0.3,1), 'index': (1,0.8,0.2,1), 'middle': (0.3,1,0.3,1), 'ring': (0.2,0.8,1,1), 'pinky': (0.7,0.3,1,1)}
col = np.tile(np.array([0.7,0.7,0.7,1.0]), (len(co),1))
for nm, d in digits.items():
    col[d['comp']] = cols[nm]
ca = me.color_attributes.new('dbg', 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set('color', col.ravel())
mat = bpy.data.materials.new('dbg'); mat.use_nodes = True
nt = mat.node_tree
for n_ in list(nt.nodes): nt.nodes.remove(n_)
a_ = nt.nodes.new('ShaderNodeVertexColor'); a_.layer_name = 'dbg'
b_ = nt.nodes.new('ShaderNodeBsdfPrincipled'); b_.inputs['Roughness'].default_value = 0.7
o_ = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(a_.outputs['Color'], b_.inputs['Base Color']); nt.links.new(b_.outputs['BSDF'], o_.inputs['Surface'])
me.materials.clear(); me.materials.append(mat)
# joints as small spheres
jm = bpy.data.materials.new('joint'); jm.use_nodes=True; jm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(1,0,0,1)
for nm, d in digits.items():
    for k, J in enumerate(d['J']):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0035 if k else 0.005, location=tuple(J), segments=12, ring_count=8)
        s_ = bpy.context.active_object; s_.data.materials.append(jm)
RS.studio(bg=(0.36, 0.37, 0.39), samples=24)
ctr = tuple(c for c in digits['middle']['J'][1])
for nm, az, el, dist in (('front', 0, 8, 0.55), ('side', -90, 8, 0.55), ('q', -45, 30, 0.55), ('back', 180, 8, 0.55)):
    RS.shot(f'{out}_{nm}.png', ctr, az=az, el=el, dist=dist, lens=70, res=(900, 900))
print('PROBE5_DONE')
