"""Editable garment-only source weight refinement; positions/topology/UVs exact."""
import bpy,pathlib,sys,json,hashlib
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/golf/tailoring/source/Golf_{sex}.blend'))
name='Golf_PleatedSkort' if sex=='Female' else 'Golf_Trousers';o=bpy.data.objects.get(name)
if not o:raise RuntimeError('Garment source role missing '+name)
geometry=lambda:hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[[tuple(u.uv) for u in layer.data] for layer in o.data.uv_layers])).encode()).hexdigest()
before=geometry();hem=min(v.co.z for v in o.data.vertices);waist=max(v.co.z for v in o.data.vertices);changed=0

def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for v in o.data.vertices:
 weights={o.vertex_groups[g.group].name:g.weight for g in v.groups};original=dict(weights)
 if sex=='Female':
  amount=smooth(.06,.22,waist-v.co.z);removed=0
  for leg in ('LeftUpperLeg','RightUpperLeg'):
   mass=weights.get(leg,0);keep=mass*(1-.56*amount);removed+=mass-keep;weights[leg]=keep
  if removed<1e-6:continue
  weights['Hips']=weights.get('Hips',0)+removed
 else:
  amount=1-smooth(hem+.022,hem+.065,v.co.z)
  if amount<1e-6:continue
  weights={n:w*(1-amount) for n,w in weights.items()};shin=('Left' if v.co.x>0 else 'Right')+'LowerLeg';weights[shin]=weights.get(shin,0)+amount
 for group in o.vertex_groups:group.remove([v.index])
 rows=sorted(((n,w) for n,w in weights.items() if w>1e-6),key=lambda a:a[1],reverse=True)[:4];total=sum(w for n,w in rows)
 for n,w in rows:
  group=o.vertex_groups.get(n) or o.vertex_groups.new(name=n);group.add([v.index],w/total,'REPLACE')
 changed+=1
assert geometry()==before,'Garment geometry/UV drift'
out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_GolfHemMotionV3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
(R/f'proof/full-visual-overhaul/characters/golf-hem-motion-source-{sex}.json').write_text(json.dumps({'source':str(out),'piece':name,'changedWeightVertices':changed,'geometryUVTopologySHA256':before,'geometryExact':True,'gate':'UNVERIFIED staged source only; actual five-stroke clothed motion review required'},indent=2));print('GOLF_HEM_SOURCE',sex,changed,flush=True)
