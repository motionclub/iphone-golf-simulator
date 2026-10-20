import bpy,sys,math
from pathlib import Path
sys.path.insert(0,'Tools/HeroBase');from plate_profiles import MALE,FEMALE
D=Path('ArtDir/hero/base_lock').resolve()
for sex,pr in [('Male',MALE),('Female',FEMALE)]:
 path=D/'blender'/('HeroBase_'+sex+'.blend');bpy.ops.wm.open_mainfile(filepath=str(path));sp=1.7/pr['height']
 for view in ('front','back'):
  cx=pr['cx' if view=='front' else 'back_cx'];back=view=='back';ob=bpy.data.objects['LOCKED_PLATE_'+view];ob.location=(((cx-640) if back else (640-cx))*sp,-.55 if back else .55,(pr['sole']-360)*sp);ob.rotation_euler=(math.pi/2,0,math.pi if back else 0)
 for screen in bpy.data.screens:
  for area in screen.areas:
   if area.type=='VIEW_3D':
    region=area.spaces.active.region_3d;region.view_location=(0,0,.85);region.view_distance=2.7;region.view_rotation=bpy.data.objects['ProofCamera'].rotation_euler.to_quaternion();region.view_perspective='ORTHO';area.spaces.active.shading.color_type='MATERIAL'
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 print('AUTHORING_REFERENCES_ALIGNED',sex)
