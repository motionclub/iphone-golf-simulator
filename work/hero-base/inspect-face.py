import bpy,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,'Tools/HeroBase');from plate_profiles import MALE,FEMALE
for sex,suf,pr in [('Male','M',MALE),('Female','F',FEMALE)]:
 bpy.ops.wm.open_mainfile(filepath=str(Path('ArtDir/hero/base_lock/blender/HeroBase_'+sex+'.blend').resolve()));ob=bpy.data.objects['Body_'+suf];tree=BVHTree.FromObject(ob,bpy.context.evaluated_depsgraph_get());sp=1.7/pr['height'];my=pr['mouth_y'];print(sex)
 for x in range(-14,15,2):
  y=my-2.7*(x/14)**2;hit,normal,idx,dist=tree.ray_cast(Vector((x*sp,-5,(pr['sole']-y)*sp)),Vector((0,1,0)));print(x,ob.data.materials[ob.data.polygons[idx].material_index].name,round(hit.y/sp,2),[round(f,2) for f in normal])
