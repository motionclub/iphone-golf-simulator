import bpy,bmesh,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(W/'depth/candidate.blend'));bm=bmesh.new();bm.from_mesh(bpy.data.objects['Body_M'].data);tree=BVHTree.FromBMesh(bm);bm.free()
p=np.load(W/'profile-targets.npz');ref=p['reference'];before=p['current'];samples=[]
for z in np.arange(1.375,1.7044,.0007):
 f=tree.ray_cast(Vector((0,-1,float(z))),Vector((0,1,0)),2)[0];b=tree.ray_cast(Vector((0,1,float(z))),Vector((0,-1,0)),2)[0]
 if f is not None and b is not None:samples.append([z,f.y,b.y])
after=np.array(samples);np.save(W/'depth/profile-after.npy',after);rows=[]
for z in [1.395,1.410,1.425,1.440,1.455,1.470,1.485,1.500,1.590,1.605,1.620,1.650]:
 t=float(np.interp(z,ref[:,0],ref[:,1]));o=float(np.interp(z,before[:,0],before[:,1]));a=float(np.interp(z,after[:,0],after[:,1]));tb=float(np.interp(z,ref[:,0],ref[:,2]));ob=float(np.interp(z,before[:,0],before[:,2]));ab=float(np.interp(z,after[:,0],after[:,2]));rows.append({'height_metres':z,'target_y':t,'before_y':o,'after_y':a,'before_difference_mm':1000*(o-t),'after_difference_mm':1000*(a-t),'rear_target_y':tb,'rear_before_y':ob,'rear_after_y':ab,'rear_before_difference_mm':1000*(ob-tb),'rear_after_difference_mm':1000*(ab-tb)})
report={'scope':'Fixed normalized head-detail left-profile central calipers; diagnostic only, not a silhouette gate.','calibration':json.loads((W/'profile-calibration.json').read_text()),'landmarks':rows,'jaw_throat_caliper_mean_absolute_error_mm_before':float(np.mean([abs(r['before_difference_mm']) for r in rows[:8]])),'jaw_throat_caliper_mean_absolute_error_mm_after':float(np.mean([abs(r['after_difference_mm']) for r in rows[:8]])),'rear_neck_caliper_mean_absolute_error_mm_before':float(np.mean([abs(r['rear_before_difference_mm']) for r in rows[:5]])),'rear_neck_caliper_mean_absolute_error_mm_after':float(np.mean([abs(r['rear_after_difference_mm']) for r in rows[:5]]))}
(W/'depth/profile-comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
