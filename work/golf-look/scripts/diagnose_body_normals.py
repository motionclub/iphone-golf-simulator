import bpy,sys,numpy as np,json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,evaluated_co,activate_clip
from follow_lib import bvh_from,evaluated_normals
sex=sys.argv[-1];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];rig=bpy.data.objects['Rig_'+sex];activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg);N=evaluated_normals(body,dg);tree=bvh_from(B,mesh_tris(body.data))
def inside(p):
 votes=0
 for direction in [(1,.137,.347),(.219,1,.413),(.319,.179,1)]:
  origin=Vector(tuple(p));d=Vector(direction).normalized();count=0
  for _ in range(64):
   loc,n,k,dist=tree.ray_cast(origin,d,10)
   if loc is None:break
   count+=1;origin=loc+d*.00001
  votes+=count%2
 return votes>=2
plus=minus=both=neither=0
for i in range(0,len(B),15):
 a=inside(B[i]+N[i]*.003);b=inside(B[i]-N[i]*.003);plus+=a;minus+=b;both+=a and b;neither+=not(a or b)
print(sex,'world',list(map(list,body.matrix_world)),'samples',len(range(0,len(B),15)),'plusInside',plus,'minusInside',minus,'both',both,'neither',neither,flush=True)
# Compare evaluated normals to exact posed face winding normals.
T=mesh_tris(body.data);FN=np.cross(B[T[:,1]]-B[T[:,0]],B[T[:,2]]-B[T[:,0]]);FN/=np.maximum(np.linalg.norm(FN,axis=1)[:,None],1e-10);avg=N[T].mean(1);dot=np.einsum('ij,ij->i',FN,avg);print('vertex/face normal dots',np.percentile(dot,[0,10,50,90,100]),'negative',int((dot<0).sum()),flush=True)
