import bpy,bmesh,pathlib,json
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/characters';out={}
for sex in ('male','female'):
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_reference_expression2.blend'));h=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('GEO-') and not any(t in o.name for t in ('.iris.','.sclera.','.eye.')));co=[v.co.copy() for v in h.data.shape_keys.key_blocks['Reference_Expression2'].data];bm=bmesh.new();bm.from_mesh(h.data);bm.verts.ensure_lookup_table();boundary=set(e for e in bm.edges if e.is_boundary);parts=[]
 while boundary:
  e=boundary.pop();edges={e};vs=set(e.verts);pending=list(e.verts)
  while pending:
   v=pending.pop()
   for e2 in v.link_edges:
    if e2 not in boundary:continue
    boundary.remove(e2);edges.add(e2)
    for v2 in e2.verts:
     if v2 not in vs:vs.add(v2);pending.append(v2)
  center=sum((co[v.index] for v in vs),Vector())/len(vs);pts=[co[v.index] for v in vs];parts.append({'count':len(vs),'center':list(center),'bounds':[[min(p[a] for p in pts),max(p[a] for p in pts)] for a in range(3)],'indices':[v.index for v in vs]})
 out[sex]=parts;bm.free()
(O/'eye-loop-audit.json').write_text(json.dumps(out,indent=2));print('LOOPS',[(s,[(p['count'],p['center']) for p in ps]) for s,ps in out.items()])
