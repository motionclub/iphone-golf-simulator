"""Authored volume/knuckle corrective, inverse-skinned onto the same continuous hand.
Outside hand/wrist vertices stay exact. Exported absolute target is pre-skin geometry.
"""
import bpy,pathlib,sys,math,json
from mathutils import Vector,Matrix
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));bpy.context.view_layer.update()
rest=[v.co.copy() for v in body.data.vertices];groups={g.index:g.name for g in body.vertex_groups}
bodyToRig=rig.matrix_world.inverted()@body.matrix_world;rigToBody=bodyToRig.inverted()
skin={b.name:rigToBody@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@bodyToRig for b in rig.data.bones}
if not body.data.shape_keys:body.shape_key_add(name='Basis',from_mix=False)
report={}
def curve(points,k,u):
 a,b=points[k],points[k+1]
 d0=(points[min(k+1,3)]-points[max(0,k-1)])*.5 if k>0 else b-a
 d1=(points[min(k+2,3)]-points[k])*.5 if k<2 else b-a
 centre=(2*u**3-3*u*u+1)*a+(u**3-2*u*u+u)*d0+(-2*u**3+3*u*u)*b+(u**3-u*u)*d1
 tangent=(6*u*u-6*u)*a+(3*u*u-4*u+1)*d0+(-6*u*u+6*u)*b+(3*u*u-2*u)*d1
 return centre,tangent.normalized()
for side in ('Left','Right'):
 H=rig.data.bones[side+'Hand'].matrix_local.inverted()@bodyToRig;P=rig.pose.bones[side+'Hand'].matrix.inverted();toBody=rigToBody@rig.pose.bones[side+'Hand'].matrix
 fields={}
 for d in ('Index','Middle','Ring','Little','Thumb'):
  ns=[side+d+j for j in ('Proximal','Intermediate','Distal')]
  r=[H@rigToBody@rig.data.bones[n].head_local for n in ns]+[H@rigToBody@rig.data.bones[ns[-1]].tail_local]
  p=[P@rig.pose.bones[n].head for n in ns]+[P@rig.pose.bones[ns[-1]].tail]
  fields[d]=(ns,r,p)
 key=body.shape_key_add(name='Hero_Fist_'+side,from_mix=False);changed=0;maxDelta=0;maxPosed=0
 for i,v in enumerate(body.data.vertices):
  weights={groups[g.group]:g.weight for g in v.groups if g.weight>.000001};amounts={d:sum(weights.get(n,0) for n in ns) for d,(ns,_,_) in fields.items()};d=max(amounts,key=amounts.get)
  if amounts[d]<.025:continue
  ph=H@rest[i]
  if ph.y<.04:continue
  ns,r,p=fields[d];best=None
  for k,(a,b) in enumerate(zip(r,r[1:])):
   axis=b-a;u=max(0,min(1,(ph-a).dot(axis)/axis.length_squared));centre=a+u*axis;distance=(ph-centre).length
   if best is None or distance<best[0]:best=(distance,k,u,centre,axis.normalized())
  distance,k,u,centre,axis=best
  radius=([.0075,.008,.007,.0056,.0100] if sex=='Male' else [.005,.0052,.005,.0045,.0085])[('Index','Middle','Ring','Little','Thumb').index(d)]
  if distance>radius*1.8:continue
  posedCentre,tangent=curve(p,k,u);radial=ph-centre;radial=axis.rotation_difference(tangent)@radial;desired=toBody@(posedCentre+radial)
  m=Matrix(((0,0,0,0),)*4);sumw=0
  for n,w in weights.items():
   if n in skin:m+=w*skin[n];sumw+=w
  if sumw<.999 or abs(m.determinant())<.00001:continue
  actual=m@rest[i];strength=min(1,amounts[d]*1.8);desired=actual.lerp(desired,strength);point=m.inverted()@desired;delta=(point-rest[i]).length
  key.data[i].co=point;changed+=1;maxDelta=max(maxDelta,delta);maxPosed=max(maxPosed,(actual-desired).length)
 key.value=1;report[side]={'changed':changed,'maxBindDeltaMetres':maxDelta,'maxPosedCorrectionMetres':maxPosed}
bpy.context.view_layer.update();out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
(R/f'proof/full-visual-overhaul/characters/fist-surface-v3-{sex}.json').write_text(json.dumps(report,indent=2));print('FIST_SURFACE_V3',sex,report,flush=True)
