"""Clear the oversized racket from the resting left hand while retaining wrist position.
Search changes only Serve wrist rotation keys. Final proof still uses penetrate_dj.py.
"""
import bpy,sys,json,math,collections
import numpy as np
from mathutils import Quaternion,Vector
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:];tag=a[0]
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump'
sys.path.insert(0,W+'/scripts');import loco,kin
hero=loco.Hero(tag);rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.animation_data_clear();z=np.load(W+'/data/gen_serve_'+tag+'.npz');data={k:z[k] for k in z.files};q=data['quats'].copy()
for i,n in enumerate(hero.rig.names):
 p=rig.pose.bones[n];p.rotation_mode='QUATERNION';p.rotation_quaternion=q[0,i]
rig.pose.bones['Hips'].location=data['hips'][0]
bpy.data.objects['Racket_Classic'].scale=(1.3,)*3
obstacles=[('Body_M' if tag=='male' else 'Body_F'),('Face_M' if tag=='male' else 'Face_F'),'Kit_Top','Kit_Bottom','Kit_Sock_L','Kit_Sock_R','Kit_Shoe_L','Kit_Shoe_R']
def cost():
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();verts=[];tris=[];owners=[]
 for nm in obstacles:
  o=bpy.data.objects.get(nm)
  if not o:continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();base=len(verts)
  verts += [ev.matrix_world@v.co for v in me.vertices];me.calc_loop_triangles()
  tris += [tuple(base+i for i in t.vertices) for t in me.loop_triangles];owners += [nm]*len(me.loop_triangles);ev.to_mesh_clear()
 bvh=BVHTree.FromPolygons(verts,tris);who=collections.Counter()
 for nm in ['Racket_Classic','StringBed']:
  ev=bpy.data.objects[nm].evaluated_get(dg);me=ev.to_mesh()
  for v in me.vertices:
   p=ev.matrix_world@v.co;loc,nor,idx,dist=bvh.find_nearest(p)
   if loc and (loc-p).dot(nor)>.003:who[owners[idx]]+=1
  ev.to_mesh_clear()
 return sum(who.values()),dict(who)
i=hero.rig.idx['LeftHand'];original=Quaternion(q[0,i]);best=(10**9,None,None);trials=[]
axes=[(1,0,0),(0,1,0),(0,0,1),(1,0,1),(-1,0,1)]
for angle in [0,15,-15,30,-30,45,-45,60,-60,75,-75,90,-90]:
 for axis in axes:
  turn=Quaternion(Vector(axis).normalized(),math.radians(angle));rig.pose.bones['LeftHand'].rotation_quaternion=original@turn
  n,who=cost();trials.append(dict(angle=angle,axis=axis,inside=n,who=who))
  if (n,abs(angle)) < (best[0],abs(best[1] or 1e9)):best=(n,angle,axis)
  if n==0:break
 if best[0]==0:break
assert best[1] is not None
n,angle,axis=best
for f in range(14):
 strength=1 if f<=6 else max(0,1-(f-6)/7)
 turn=np.array(Quaternion(Vector(axis).normalized(),math.radians(angle*strength)))
 q[f,i]=kin.qmul(q[f,i],turn)
data['quats']=q;np.savez_compressed(W+'/data/gen_serve_'+tag+'.npz',**data)
open(W+'/r3/entry_clearance_'+tag+'.json','w').write(json.dumps(dict(best=dict(inside=n,angle=angle,axis=axis),trials=trials),indent=2))
print('ENTRY_CLEARANCE',tag,best,'wrist position unchanged')
