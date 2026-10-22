"""Subdivide only the retained chest placket; preserve every other vertex/key."""
import bpy,bmesh,numpy as np,json,sys,shutil
from pathlib import Path
w=Path(__file__).resolve().parents[1];sex=sys.argv[-1];path=Path(bpy.data.filepath)
bk=w/'rollback/placket_grid_r35';bk.mkdir(exist_ok=True)
for p in [path,w/f'export/Golf_{sex}_SwingProof.blend']:shutil.copy2(p,bk/p.name)
o=bpy.data.objects['Golf_Polo'];me=o.data
adj=[set() for _ in me.vertices]
for e in me.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();parts=[]
for i in range(len(adj)):
 if i in seen:continue
 stack=[i];seen.add(i);ids=[]
 while stack:
  a=stack.pop();ids.append(a)
  for b in adj[a]:
   if b not in seen:seen.add(b);stack.append(b)
 if len(ids) in [48,56]:
  co=np.array([me.vertices[j].co[:] for j in ids])
  if abs(co.mean(0)[0])<.025:parts.append(ids)
assert len(parts)==1,(sex,[len(p) for p in parts])
selected=set(parts[0]);before={k.name:np.array([p.co[:] for p in k.data]) for k in me.shape_keys.key_blocks}
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
origin=bm.verts.layers.int.new('GolfGridOriginalIndex')
for v in bm.verts:v[origin]=v.index+1
flag=bm.verts.layers.float.new('GolfPlacketGridFlag')
for v in bm.verts:v[flag]=float(v.index in selected)
edges=[e for e in bm.edges if all(v.index in selected for v in e.verts)]
bmesh.ops.subdivide_edges(bm,edges=edges,cuts=7,use_grid_fill=True)
for v in bm.verts:
 if v[flag]>.5:v[origin]=0
bm.to_mesh(me);bm.free();me.update()
indices=me.attributes['GolfGridOriginalIndex']
checked=0
for v in me.vertices:
 old=indices.data[v.index].value-1
 # New edge vertices interpolate index values; compare only vertices outside
 # the original placket, whose connected components were untouched.
 if old>=0 and old not in selected:
  for k in me.shape_keys.key_blocks:
   assert np.max(np.abs(np.array(k.data[v.index].co)-before[k.name][old]))<1e-6,(sex,k.name,old)
  checked+=1
assert checked>=len(before['Basis'])-len(selected)
me.attributes.remove(indices)
me.attributes.remove(me.attributes['GolfPlacketGridFlag'])
bpy.ops.wm.save_as_mainfile(filepath=str(path))
bpy.ops.wm.save_as_mainfile(filepath=str(w/f'export/Golf_{sex}_SwingProof.blend'))
row=dict(sex=sex,oldVertices=len(before['Basis']),newVertices=len(me.vertices),unchangedOtherVertices=checked,shapeKeys=len(before),status='grid candidate; posed surface projection follows')
(w/f'data/placket_grid_{sex}_r35.json').write_text(json.dumps(row,indent=2));print(row,flush=True)
