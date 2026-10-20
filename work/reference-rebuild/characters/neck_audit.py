import bpy,pathlib,json
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/characters';out={}
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_ReferenceBody_Smooth.blend'));b=bpy.data.objects['Body'];me=b.data;c=b['ReferenceNeckCutZ'];faces=[]
 for p in me.polygons:
  center=p.center
  if c-.010<center.z<c+.045:
   radial=Vector((center.x,center.y,0));radial.normalize();faces.append({'i':p.index,'c':list(center),'n':list(p.normal),'radialDot':p.normal.dot(radial),'area':p.area})
 out[sex]={'faces':faces,'negative':sum(f['radialDot']<-.1 for f in faces),'aboveArea':[f for f in faces if f['area']>.0003],'customNormals':me.has_custom_normals}
(O/'neck-audit.json').write_text(json.dumps(out,indent=2));print('NECK_AUDIT',[(s,d['negative'],len(d['faces']),len(d['aboveArea'])) for s,d in out.items()])
