"""A fitted cap crown above the existing female band and curved brim."""
import bpy,sys,math,shutil,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parents[1];rig=bpy.data.objects['Rig_Female'];body=bpy.data.objects['Body_F'];hair=bpy.data.objects['Hair_F']
for o in [hair]:o.hide_viewport=False;o.hide_set(False)
rig.animation_data.action=None;rig.data.pose_position='REST';bpy.context.view_layer.update()
for o in list(bpy.data.objects):
 if o.name.startswith('Golf_CapCrown') or o.name.startswith('Golf_CapPanelSeam'):bpy.data.objects.remove(o,do_unlink=True)
band=bpy.data.objects['Golf_VisorBand'];z0=min(v.co.z for v in band.data.vertices);cy=0.0;center=Vector((0,cy,z0));trees=[]
for o in [body,hair]:
 o.data.calc_loop_triangles();trees.append(BVHTree.FromPolygons([tuple(v.co) for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True))
def radius(d):
 hits=[]
 for tree in trees:
  cur=center.copy();travel=0
  for k in range(8):
   p,n,t,dist=tree.ray_cast(cur,d,.4-travel)
   if p is None:break
   travel+=dist;hits.append(travel);cur=p+d*.00001;travel+=.00001
 return max(hits,default=.13)+.004
# Conservative smooth rings contain every original scalp/hair point in the
# crown region. A 15 mm rounded top allows room for a structured fabric crown.
points=np.concatenate([np.array([tuple(v.co) for v in obj.data.vertices]) for obj in [body,hair]])
points=points[points[:,2]>=z0-.01];cy=float((points[:,1].max()+points[:,1].min())/2);center=Vector((0,cy,z0))
rx=float(abs(points[:,0]).max())+.005;ry=float(abs(points[:,1]-cy).max())+.005
rz=float(points[:,2].max())+.015;N=60;R=15;verts=[];faces=[]
radial=np.sqrt((points[:,0]/rx)**2+((points[:,1]-cy)/ry)**2)
for j in range(R):
 z=z0+(rz-z0)*j/(R-1)
 if j==R-1:r=.005
 else:
  near=abs(points[:,2]-z)<(rz-z0)/(R-1)*1.6
  r=float(radial[near].max())+.035 if near.any() else .05
 for i in range(N):
  a=i*2*math.pi/N;verts.append((rx*r*math.cos(a),cy+ry*r*math.sin(a),z))
for j in range(R-1):
 for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
faces.append(tuple((R-1)*N+i for i in range(N)))
def mesh(name,vs,fs,mat,thickness=0,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);me.materials.append(mat)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 if smooth:
  m=o.modifiers.new('Rounded structured crown','SUBSURF');m.levels=1;bpy.ops.object.modifier_apply(modifier=m.name)
 if thickness:
  m=o.modifiers.new('Turned crown edge','SOLIDIFY');m.thickness=thickness;m.offset=-1;bpy.ops.object.modifier_apply(modifier=m.name)
 for f in me.polygons:f.use_smooth=True
 group=o.vertex_groups.new(name='Head');group.add(list(range(len(me.vertices))),1,'REPLACE');m=o.modifiers.new('Existing Head bone','ARMATURE');m.object=rig;o.parent=rig;return o
mat=band.data.materials[0];o=mesh('Golf_CapCrown_F',verts,faces,mat,.002,smooth=True)
o.data.calc_loop_triangles();crownTree=BVHTree.FromPolygons([tuple(v.co) for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
seammat=bpy.data.objects.get('Golf_BrimStitch_0').data.materials[0]
for seam in range(6):
 ps=[]
 for j in range(R):
  loc,normal,_,_=crownTree.find_nearest(Vector(verts[j*N+seam*10]));ps.append(loc+normal*.0006)
 vs=[];fs=[]
 for j,p in enumerate(ps):
  tangent=(ps[min(j+1,len(ps)-1)]-ps[max(j-1,0)]).normalized();normal=(p-center).normalized();side=tangent.cross(normal).normalized()
  for k in range(4):a=k*math.pi/2;vs.append(tuple(p+normal*.0005+(normal*math.cos(a)+side*math.sin(a))*.0005))
 for j in range(len(ps)-1):
  for k in range(4):fs.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
 mesh('Golf_CapPanelSeam_F_'+str(seam),vs,fs,seammat)
rig.data.pose_position='POSE';a=bpy.data.actions['ReadyIdle'];rig.animation_data.action=a
if a.slots:rig.animation_data.action_slot=a.slots[0]
bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
path=Path(bpy.data.filepath);backup=W/'rollback/female_cap'/path.name;backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():shutil.copy2(path,backup)
bpy.ops.wm.save_as_mainfile(filepath=str(path));print('CAP_FITTED original hair mesh/weights untouched; existing Head bone only',flush=True)
