"""Editable counterpart of real Body aperture closure; Basis/open identity exact.
The same continuous rim-segment/depth construction is used by HeroActualLidFit.
This writes editable Blender sources only, not production FBX or Unity resources.
"""
import bpy,bmesh,pathlib,sys,math,json
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ContinuousHandsV2.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST';body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'))
bm=bmesh.new();bm.from_mesh(body.data);boundary={e for e in bm.edges if e.is_boundary};loops=[]
while boundary:
 start=next(iter(boundary));todo=list(start.verts);visited=set();edges=set()
 while todo:
  v=todo.pop()
  if v in visited:continue
  visited.add(v)
  for e in v.link_edges:
   if e.is_boundary:edges.add(e);todo.extend(e.verts)
 boundary-=edges
 loop=[body.matrix_world@v.co for v in visited]
 if len(loop)>20 and sum(p.z for p in loop)/len(loop)>1.2:loops.append(loop)
assert len(loops)==2,[len(l) for l in loops]
basis=body.shape_key_add(name='Basis');blink=body.shape_key_add(name='Hero_Blink');inverse=body.matrix_world.inverted();maximum=0;count=0;apertures=[]
for contour in loops:
 cx=sum(p.x for p in contour)/len(contour);cy=sum(p.z for p in contour)/len(contour);hx=(max(p.x for p in contour)-min(p.x for p in contour))*.5;hy=(max(p.z for p in contour)-min(p.z for p in contour))*.5
 contour.sort(key=lambda p:math.atan2(p.z-cy,p.x-cx))
 def nearest(p):
  best=None;distance=1e30
  for a,b in zip(contour,contour[1:]+contour[:1]):
   d=b-a;t=min(1,max(0,(p-a).dot(d)/max(1e-12,d.length_squared)));q=a+d*t;e=(p-q).length_squared
   if e<distance:best=q;distance=e
  return best
 def depth(x):
  cut=[]
  for a,b in zip(contour,contour[1:]+contour[:1]):
   if (a.x<=x<b.x) or (b.x<=x<a.x):cut.append(a.lerp(b,(x-a.x)/(b.x-a.x)))
  if len(cut)<2:return nearest(Vector((x,0,cy))).y
  lo=min(cut,key=lambda p:p.z);hi=max(cut,key=lambda p:p.z);return lo.y*.725+hi.y*.275
 for v in body.data.vertices:
  p=body.matrix_world@v.co
  if abs(p.x-cx)>hx+.018:continue
  near=nearest(p);d=(p-near).length
  if d>.018:continue
  t=min(1,d/.018);w=1-t*t*(3-2*t);u=min(1,max(-1,(near.x-cx)/max(.001,hx)));crease=cy+hy*(-.45+.22*u*u);y=depth(min(cx+hx-1e-6,max(cx-hx+1e-6,near.x)))
  next=p+Vector((0,(y-near.y-.0012)*w,(crease-near.z)*w));blink.data[v.index].co=inverse@next;maximum=max(maximum,(blink.data[v.index].co-v.co).length);count+=1
 apertures.append({'rimVertices':len(contour),'centreWorld':[cx,sum(p.y for p in contour)/len(contour),cy],'halfWidth':hx,'halfHeight':hy})
blink.value=0;body['face_contract']='physical Body Hero_Blink with exact open Basis; local aperture region only'
out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_HandsAndFaceV2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'sex':sex,'source':str(out),'shape':'Hero_Blink','openBasisPositionDriftMetres':max((a.co-b.co).length for a,b in zip(body.data.vertices,basis.data)),'affectedVertices':count,'maxTravelMetres':maximum,'apertures':apertures,'nativeContract':'exported Body morph target; performFace applies named morpher weight after skeletal correctives','gate':'SOURCE COMPLETE; actual Unity/native0/50/100 visual gate required'}
(R/f'proof/full-visual-overhaul/characters/body-blink-source-{sex}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
