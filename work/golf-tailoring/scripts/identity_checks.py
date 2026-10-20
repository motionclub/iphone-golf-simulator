import bpy,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1];rows=[]
def snapshot(path,sex):
 bpy.ops.wm.open_mainfile(filepath=str(path));out={}
 for name in ['Body_'+sex[0],'Face_'+sex[0],'Hair_'+sex[0]]:
  o=bpy.data.objects.get(name)
  if not o:continue
  out[name]=hashlib.sha256(repr(([(v.co[:],[(o.vertex_groups[g.group].name,g.weight) for g in v.groups]) for v in o.data.vertices],[p.vertices[:] for p in o.data.polygons])).encode()).hexdigest()
 rig=bpy.data.objects['Rig_'+sex];out['restRig']=hashlib.sha256(repr([(b.name,[tuple(r) for r in b.matrix_local]) for b in rig.data.bones]).encode()).hexdigest();return out
for sex in ['Male','Female']:
 a=snapshot(W.parent/'golf-look/export'/f'Golf_{sex}_Draft.blend',sex);b=snapshot(W/'export'/f'Golf_{sex}_Draft.blend',sex);assert a==b,(sex,a,b);rows.append(dict(sex=sex,unchanged=list(a)))
(W/'data/identity_checks.json').write_text(json.dumps(rows,indent=2));print('IDENTITY_PASS',rows)
