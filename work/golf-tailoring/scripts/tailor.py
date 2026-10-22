import bpy,bmesh,json,math,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
W=Path(__file__).resolve().parents[1]
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def coords(o):return np.array([v.co[:] for v in o.data.vertices])
def blocks(o):return list(o.data.shape_keys.key_blocks) if o.data.shape_keys else []
def modify(o,delta):
 keys=blocks(o)
 if keys:
  for key in keys:
   for i,v in enumerate(key.data):v.co+=Vector(delta[i])
  for i,v in enumerate(o.data.vertices):v.co=keys[0].data[i].co
 else:
  for i,v in enumerate(o.data.vertices):v.co+=Vector(delta[i])
 o.data.update()
def fingerprint(o):return hashlib.sha256(repr(([(v.co[:],[(g.group,g.weight) for g in v.groups]) for v in o.data.vertices],[p.vertices[:] for p in o.data.polygons])).encode()).hexdigest()
def bvh(o,outer=False):
 p=[v.co.copy() for v in o.data.vertices];o.data.calc_loop_triangles();n=len(p)//2
 tri=[tuple(t.vertices) for t in o.data.loop_triangles if not outer or all(i<n for i in t.vertices)]
 return BVHTree.FromPolygons(p,tri,all_triangles=True),tri
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(W.parent/'golf-look/export'/f'Golf_{sex}_Draft.blend'))
 rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_'+sex[0]];identity=fingerprint(body)
 rig.data.pose_position='REST';rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();bodytree,bodytri=bvh(body)
 cy=-.035;waist=.990
 def radius(tree,a,z):
  direction=Vector((math.cos(a),math.sin(a),0));origin=Vector((0,cy,z));hit=tree.ray_cast(origin,direction,.6)
  if hit[0] is None:
   if tree is not bodytree:return radius(bodytree,a,z)+.018
   raise RuntimeError(('Missing body contour',sex,a,z))
  return float((hit[0]-origin).length)
 bottom=bpy.data.objects['Golf_Trousers' if sex=='Male' else 'Golf_PleatedSkort'];p=coords(bottom);delta=np.zeros_like(p)
 # Find the actual upper edge of the outer shell, including prior fit corrections.
 edgecounts={};half=len(p)//2
 for f in bottom.data.polygons:
  if sex=='Male' and not all(i<half for i in f.vertices):continue
  vs=list(f.vertices)
  for a,b in zip(vs,vs[1:]+vs[:1]):
   e=tuple(sorted((a,b)));edgecounts[e]=edgecounts.get(e,0)+1
 rim=sorted({i for e,n in edgecounts.items() if n==1 for i in e if p[i,2]>.91})
 if not rim:rim=[i for i in range(len(p)) if p[i,2]>p[:,2].max()-.005]
 ra=np.arctan2(p[rim,1]-cy,p[rim,0]);rz=p[rim,2]
 def rim_z(a):
  d=np.abs(np.arctan2(np.sin(ra-a),np.cos(ra-a)));sel=np.argsort(d)[:3];w=1/np.maximum(d[sel],.003)**2
  return float((rz[sel]*w).sum()/w.sum())
 # Fit the upper trouser/skort band to the actual body contour. Preserve lower ease.
 for i,(x,y,z) in enumerate(p):
  w=smooth(.905,.968,z)
  if w:
   a=math.atan2(y-cy,x);r=math.hypot(x,y-cy);desired=radius(bodytree,a,min(z,.990))+.018
   # Explicit lining remains 2.2 mm inside the outer construction.
   if sex=='Male' and i>=len(p)//2:desired-=.0022
   rr=r+(desired-r)*w;newz=z+(waist-rim_z(a))*smooth(.915,.955,z) if sex=='Male' else z-.005*w
   delta[i]=[rr*math.cos(a)-x,cy+rr*math.sin(a)-y,newz-z]
 modify(bottom,delta)
 # Turned trouser edge: one clean plane with a gentle shoe break, no frayed lobes.
 if sex=='Male':
  p=coords(bottom);delta=np.zeros_like(p)
  for i,(x,y,z) in enumerate(p):
   w=1-smooth(.137,.215,z)
   if w:
    target=.143-.009*smooth(.00,.15,-y)
    delta[i,2]=(target-z)*w
  modify(bottom,delta)
 # Tuck the polo beneath the waistband, using the same waist contour and a 6 mm
 # layer separation. Blend over 7 cm so the shirt keeps its natural upper ease.
 polo=bpy.data.objects['Golf_Polo'];p=coords(polo);delta=np.zeros_like(p)
 attr=polo.data.attributes.get('GolfOuterFace')
 outer={i for f in polo.data.polygons if attr and attr.data[f.index].value==1 for i in f.vertices}
 for i,(x,y,z) in enumerate(p):
  w=1-smooth(.976,1.055,z)
  if w and abs(x)<.27:
   a=math.atan2(y-cy,x);r=math.hypot(x,y-cy);desired=radius(bodytree,a,max(.95,min(z,1.055)))+(.010 if i in outer else .008)
   rr=r+(desired-r)*w;newz=z+.005*(1-smooth(.958,.98,z))
   delta[i]=[rr*math.cos(a)-x,cy+rr*math.sin(a)-y,newz-z]
 modify(polo,delta)
 # Belt and hardware inherit the nearest waistband triangle's bone weights and
 # every corrective delta, eliminating rigid-hip drift and loose circular fit.
 tree,tri=bvh(bottom,sex=='Male');bp=coords(bottom);bottomkeys=blocks(bottom);byname={k.name:k for k in bottomkeys}
 def attach(o,points):
  old=coords(o);keys=blocks(o)
  names={g.index:g.name for g in bottom.vertex_groups}
  for g in list(o.vertex_groups):o.vertex_groups.remove(g)
  groups={n:o.vertex_groups.new(name=n) for n in set(names.values())}
  for i,q in enumerate(points):
   loc,norm,idx,dist=tree.find_nearest(Vector(q));ids=tri[idx];a,b,c=[Vector(bp[k]) for k in ids]
   bary=barycentric_transform(loc,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
   ws={}
   for vi,w in zip(ids,bary):
    for g in bottom.data.vertices[vi].groups:ws[names[g.group]]=ws.get(names[g.group],0)+g.weight*max(0,w)
   ws=sorted(ws.items(),key=lambda t:-t[1])[:4];total=sum(v for _,v in ws)
   for n,v in ws:groups[n].add([i],v/total,'REPLACE')
   if keys:
    for key in keys:
     offset=Vector((0,0,0));source=byname.get(key.name)
     if source and key.name!='Basis':
      for vi,w in zip(ids,bary):offset+=(source.data[vi].co-bottomkeys[0].data[vi].co)*w
     key.data[i].co=Vector(q)+offset
   o.data.vertices[i].co=Vector(q)
  o.data.update()
 belt=bpy.data.objects['Golf_Belt'];points=[]
 # Original topology has 64 samples x upper/lower x inner/outer.
 for layer in range(4):
  z=.950 if layer%2==0 else .982
  for j in range(64):
   a=j*2*math.pi/64;r=radius(tree,a,z)+(.0038 if layer<2 else .0018)
   points.append((r*math.cos(a),cy+r*math.sin(a),z))
 attach(belt,points)
 for o in [x for x in bpy.data.objects if x.name.startswith('Golf_BeltLoop')]:
  p=coords(o);centre=p.mean(0);a=math.atan2(centre[1]-cy,centre[0]);z0=centre[2]
  rr=radius(tree,a,.966)+.006;target=np.array([rr*math.cos(a),cy+rr*math.sin(a),.966]);p+=target-centre
  attach(o,p)
 for o in [x for x in bpy.data.objects if x.name.startswith('Golf_Buckle')]:
  p=coords(o);p[:,1]=cy-radius(tree,-math.pi/2,.966)-.006+(p[:,1]-p[:,1].mean());p[:,2]+=.966-(.968-.018 if sex=='Male' else .985-.018)
  attach(o,p)
 assert fingerprint(body)==identity
 # Keep original animation data available for non-destructive pose proof.
 out=W/'export'/f'Golf_{sex}_Draft.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
 report=dict(sex=sex,bodyIdentityUnchanged=True,waistTopMetres=waist,beltHeightMetres=.032,beltClearanceMetres=.0038,poloLayerClearanceMetres=.008,topologyUnchanged=True)
 (W/'data'/f'tailoring_{sex}.json').write_text(json.dumps(report,indent=2));print('TAILOR_DONE',sex,flush=True)
