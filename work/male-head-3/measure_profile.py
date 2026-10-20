import bpy,bmesh,numpy as np,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock';ref=np.load(R/'work/male-head-2/profile-targets.npz')['reference']
def sample(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));bm=bmesh.new();bm.from_mesh(bpy.data.objects['Body_M'].data);tree=BVHTree.FromBMesh(bm);bm.free();samples=[]
 for z in np.arange(1.375,1.7044,.0007):
  f=tree.ray_cast(Vector((0,-1,float(z))),Vector((0,1,0)),2)[0];b=tree.ray_cast(Vector((0,1,float(z))),Vector((0,-1,0)),2)[0]
  if f is not None and b is not None:samples.append([z,f.y,b.y])
 return np.array(samples)
before=sample(W/'baseline/HeroBase_Male_Silhouette.blend');after=sample(D/'blender/HeroBase_Male_Silhouette.blend');rows=[]
for z in [1.395,1.410,1.425,1.440,1.455,1.470,1.485,1.500,1.590,1.605,1.620,1.650]:
 q={'height_metres':z}
 for k,prefix in [(1,''),(2,'rear_')]:
  t=float(np.interp(z,ref[:,0],ref[:,k]));o=float(np.interp(z,before[:,0],before[:,k]));a=float(np.interp(z,after[:,0],after[:,k]));q.update({prefix+'target_y':t,prefix+'before_y':o,prefix+'after_y':a,prefix+'before_difference_mm':1000*(o-t),prefix+'after_difference_mm':1000*(a-t)})
 rows.append(q)
report={'scope':'Fixed normalized head-detail central profile calipers; diagnostic only, not a silhouette/likeness gate.','source_sha256':hashlib.sha256((D/'blender/HeroBase_Male_Silhouette.blend').read_bytes()).hexdigest(),'baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'calibration':json.loads((R/'work/male-head-2/profile-calibration.json').read_text()),'landmarks':rows}
for label,prefix,count in [('jaw_throat','',8),('rear_neck','rear_',5)]:
 for when in ['before','after']:report[label+'_caliper_mean_absolute_error_mm_'+when]=float(np.mean([abs(q[prefix+when+'_difference_mm']) for q in rows[:count]]))
(W/'profile-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='landmarks'},indent=2))
