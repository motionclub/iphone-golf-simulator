"""Socket diagram renders: coloured axis arrows parented to Hand_Racket (X red, Y green, Z blue), rendered as a transparent overlay
pass so they are visible through the grip. blender -b <on-hand blend> --python render_socket_diagram.py -- <out_prefix> <male|female> <apose|ready>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import render_lib as R

a = args_after_dashes()
prefix, tag, pose = a[0], a[1], a[2]
sock = bpy.data.objects['Hand_Racket']
body = [o for o in bpy.data.objects if o.name.startswith('Body_')][0]
col = bpy.data.objects.get('Collider_Racket')
if col:
    col.hide_render = True


def arrow(name, axis, rgb, length=0.13, r=0.0016):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=r, radius2=r, depth=length)
    cone = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=r * 3.2, radius2=0.0, depth=0.02)
    bmesh.ops.translate(bm, verts=cone['verts'], vec=(0, 0, length / 2 + 0.01))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, length / 2))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    # +Z of the primitive -> requested axis
    z = Vector((0, 0, 1))
    ax = Vector(axis)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = z.rotation_difference(ax)
    m = bpy.data.materials.new(name + '_mat')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*rgb, 1)
    em.inputs['Strength'].default_value = 3.0
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs[0])
    me.materials.append(m)
    o.parent = sock
    o.matrix_parent_inverse.identity()
    return o


gizmo = [arrow('Gizmo_X', (1, 0, 0), (1.0, 0.1, 0.1)), arrow('Gizmo_Y', (0, 1, 0), (0.1, 0.9, 0.2)), arrow('Gizmo_Z', (0, 0, 1), (0.15, 0.35, 1.0))]
bpy.context.view_layer.update()
ctr = tuple(np.array(sock.matrix_world)[:3, 3])
racket_names = ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap')
sc = bpy.context.scene
R.studio(bg=(0.36, 0.37, 0.39), samples=64)


def pass_base(path, hide_racket=False, **kw):
    for g in gizmo:
        g.hide_render = True
    for n in racket_names:
        bpy.data.objects[n].hide_render = hide_racket
    body.hide_render = False
    sc.render.film_transparent = False
    R.shot(path, **kw)


def pass_gizmo(path, **kw):
    for g in gizmo:
        g.hide_render = False
    for n in racket_names:
        bpy.data.objects[n].hide_render = True
    body.hide_render = True
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = 'RGBA'
    R.shot(path, **kw)
    sc.render.film_transparent = False
    sc.render.image_settings.color_mode = 'RGB'


views = {
    'close': dict(target=ctr, az=-55, el=14, dist=0.55, lens=70, res=(1100, 1100)),
    'wide': dict(target=ctr, az=-40, el=12, dist=1.5, lens=60, res=(1100, 1100)),
}
for nm, kw in views.items():
    pass_base(f'{prefix}_{nm}_base.png', hide_racket=False, **kw)
    pass_gizmo(f'{prefix}_{nm}_gizmo.png', **kw)
    pass_base(f'{prefix}_{nm}_empty_only.png', hide_racket=True, **kw)
print('SOCKET_DIAGRAM_DONE')
