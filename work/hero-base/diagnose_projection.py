import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
R=Path.cwd();D=R/'ArtDir/hero/base_lock';O=R/'work/hero-base/projection-tests';O.mkdir(exist_ok=True)
for sex,suf,height,sole in [('Male','M',658,680),('Female','F',598,676)]:
 bpy.ops.wm.open_mainfile(filepath=str(D/'blender'/('HeroBase_'+sex+'.blend')))
 sc=bpy.context.scene;cam=sc.camera;sc.render.engine='BLENDER_EEVEE';cam.data.type='ORTHO'
 sc.render.resolution_percentage=100
 h=(sole-360)*1.7/height
 for deg in [0,4,8,12]:
  p=math.radians(deg)
  for view,ang in [('front',0),('back',math.pi)]:
   cam.location=(math.sin(ang)*5*math.cos(p),-math.cos(ang)*5*math.cos(p),h+5*math.sin(p));cam.rotation_euler=(Vector((0,0,h))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{suf}_{view}_{deg}.png');bpy.ops.render.render(write_still=True)
print('PROJECTION_DIAGNOSTICS_DONE')
