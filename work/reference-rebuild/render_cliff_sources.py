import bpy,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).parent
for ident in ['coastal_cliff_01','coastal_cliff_02']:
    bpy.ops.wm.open_mainfile(filepath=str(root/'vendor'/ident/(ident+'_2k.blend')))
    keep=bpy.data.objects.get(ident+'_LOD3')
    for o in list(bpy.data.objects):
        if o!=keep:bpy.data.objects.remove(o,do_unlink=True)
    # Relative packed source maps remain editable and are shipped with this evaluation.
    for image in bpy.data.images:
        if image.source=='FILE':
            p=root/'vendor'/ident/'textures'/Path(image.filepath).name
            if p.exists():image.filepath=str(p);image.reload()
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
    s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=1400;s.render.resolution_y=650;s.render.resolution_percentage=100
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0;s.view_settings.gamma=1
    s.use_nodes=False;s.render.film_transparent=False
    world=bpy.data.worlds.new('Source neutral sky');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.58,.74,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65
    light=bpy.data.lights.new('Source sun','SUN');light.energy=2.5;light.angle=.08;lo=bpy.data.objects.new('Source sun',light);s.collection.objects.link(lo);lo.rotation_euler=(.55,-.5,-.65)
    bounds=[keep.matrix_world@Vector(p) for p in keep.bound_box];centre=sum(bounds,Vector())/8
    cam=bpy.data.objects.new('Source camera',bpy.data.cameras.new('Source camera'));s.collection.objects.link(cam);s.camera=cam
    cam.data.type='ORTHO';cam.data.ortho_scale=keep.dimensions.x*1.06
    cam.location=centre+Vector((keep.dimensions.x*.04,-keep.dimensions.x*.75,keep.dimensions.x*.13))
    cam.rotation_euler=(centre-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(root/(ident+'-source.png'));bpy.ops.render.render(write_still=True)
print('COASTAL_SOURCE_PLATES_READY')
