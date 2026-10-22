"""Scratch-only deterministic standing wall, doorway and arch fixture."""
import os, sys, json, random
sys.dont_write_bytecode = True
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(REPO, 'blender/scripts'))
import bpy
import numpy as np
from mathutils import Vector
import postcard_lib as P
import postcard_look_lib as L
import hole09_masonry as HM

variant = os.environ.get('POSTCARD_MASONRY_VARIANT', 'before')
out = os.path.join(os.path.dirname(__file__), variant)
os.makedirs(out, exist_ok=True)
D = P.start('hole09_design', out_dir=out)
ground = lambda X, Y: np.zeros(np.asarray(X).shape)
ss = HM.StoneSet(D, 'DRESS_RUIN', 918)
path = [(-9., -2.), (6., -2.), (6., 10.)]
wall = HM.build_wall_path(ss, path, [4., 5.6], 1.25, (0, 8., 2.4, 2.4), 904, ground, 0.)
HM.scatter_rubble(ss, path, 1.25, ground, lambda x,y: abs(x+1.) < 2.4 and abs(y+2.) < 3.6, 921)
ss.flush()
sa = HM.StoneSet(D, 'DRESS_ARCH', 922)
arch = HM.build_arch(sa, (-5., 9.), 0., ground, 0., r=2., t=.75, depth=1.3, pier_w=1.7,
                     spring=2.7, left_top=5.8, right_top=4.9, seed=911, missing=(), slip=(6,))
sa.flush()
me = bpy.data.meshes.new('fixture_ground')
me.from_pydata([(-20,-12,0), (20,-12,0), (20,24,0), (-20,24,0)], [], [(0,1,2,3)])
ob = bpy.data.objects.new('TERRAIN_fixture', me)
bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new('fixture_neutral_ground'); mat.diffuse_color=(.15,.17,.12,1)
me.materials.append(mat)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1600; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
if scene.world is None: scene.world=bpy.data.worlds.new('fixture_world')
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.38,.44,.52,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
scene.view_settings.view_transform='AgX'
for name,loc,power,size in [('key',(-8,-7,22),1800,12), ('fill',(9,10,15),1100,14)]:
    ld=bpy.data.lights.new(name, 'AREA'); ld.energy=power; ld.shape='DISK'; ld.size=size
    lo=bpy.data.objects.new(name,ld); scene.collection.objects.link(lo); lo.location=loc
    lo.rotation_euler=(Vector((-1,5,1))-lo.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('fixture_camera'); cam=bpy.data.objects.new('fixture_camera',cd)
scene.collection.objects.link(cam); scene.camera=cam; cd.type='ORTHO'; cd.ortho_scale=30
cam.location=(-22,-27,21); cam.rotation_euler=(Vector((-1,5,1.8))-cam.location).to_track_quat('-Z','Y').to_euler()
blend=os.path.join(out,'fixture.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend, relative_remap=False)
scene.render.filepath=os.path.join(out,'fixture.png'); bpy.ops.render.render(write_still=True)
for nm, loc, target, scale in [
    ('arch_front',(-5.,-8.,7.),(-5.,9.,2.9),13.),
    ('doorway_front',(-1.,-17.,5.),(-1.,-2.,1.6),19.),
    ('top_oblique',(16.,-9.,24.),(-1.,5.,1.5),29.)]:
    cam.location=loc; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler(); cd.ortho_scale=scale
    scene.render.filepath=os.path.join(out,nm+'.png'); bpy.ops.render.render(write_still=True)
with open(os.path.join(out,'construction.json'),'w') as f:
    json.dump({'wall':wall,'arch':arch,'wall_stones':ss.n_blocks,'arch_stones':sa.n_blocks},f,indent=2)
print('Fixture saved: '+out, flush=True)
