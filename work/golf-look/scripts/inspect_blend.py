import bpy,json,sys
from pathlib import Path
sex=sys.argv[-1]; r=Path(__file__).resolve().parents[1]
rows=[]
for o in bpy.data.objects:
 if o.type=='MESH':
  o.data.calc_loop_triangles()
  v=[o.matrix_world @ x.co for x in o.data.vertices]
  rows.append(dict(name=o.name,verts=len(v),tris=len(o.data.loop_triangles),bbox=[[min(x[i] for x in v) for i in range(3)],[max(x[i] for x in v) for i in range(3)]],groups=[g.name for g in o.vertex_groups],mats=[m.name if m else None for m in o.data.materials],mods=[(m.name,m.type) for m in o.modifiers]))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
d=dict(objects=rows,rig=rig.name,bones=[dict(name=b.name,head=list(b.head_local),tail=list(b.tail_local)) for b in rig.data.bones],actions=[dict(name=a.name,frames=list(a.frame_range)) for a in bpy.data.actions])
(r/f'data/inspect_{sex}.json').write_text(json.dumps(d,indent=2))
print(json.dumps({'sex':sex,'objects':[(o['name'],o['tris'],o['bbox']) for o in rows],'bones':len(d['bones']),'actions':[a['name'] for a in d['actions']]}))
