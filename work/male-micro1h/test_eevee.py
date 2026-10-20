import sys, math
import numpy as np, bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
P = np.load(H.W/'data/P_n3.npy')
import proxy as PX
V, F = PX.build_proxy(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
o = H.make_mesh_object('proxy', P, [f for f in F])
# material
m = bpy.data.materials.new('skin'); m.use_nodes = True
b = m.node_tree.nodes['Principled BSDF']
def lin(c): return ((c+0.055)/1.055)**2.4 if c>0.04045 else c/12.92
b.inputs['Base Color'].default_value = (lin(0.74), lin(0.555), lin(0.435), 1)
b.inputs['Roughness'].default_value = 0.55
try: b.inputs['Subsurface Weight'].default_value = 0.15
except Exception as e: print('sss?', e)
o.data.materials.append(m)
s = bpy.context.scene
print('engines', [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items])
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        s.render.engine = eng; print('engine ok', eng); break
    except Exception as e:
        print('engine fail', eng, e)
s.render.resolution_x = 900; s.render.resolution_y = 900
s.render.film_transparent = False
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.22, 0.23, 0.26, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
def light(name, kind, loc, rot, energy, size=1.0, color=(1,1,1)):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind == 'SUN': d.angle = math.radians(25)
    ob = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot; return ob
light('key', 'SUN', (-1,-2,2.5), (math.radians(55), 0, math.radians(-35)), 3.2, color=(1.0,0.96,0.92))
light('fill', 'SUN', (1.5,-2,1.5), (math.radians(70), 0, math.radians(40)), 1.0, color=(0.85,0.9,1.0))
light('rim', 'SUN', (0,2,2.5), (math.radians(-120), 0, 0), 1.6)
cam = H.camera(); bpy.context.scene.camera = cam
H.shot(H.W/'r/eevee_test.png', (0,-0.1,1.55), 32.5, 0, 0.16, (900,900))
