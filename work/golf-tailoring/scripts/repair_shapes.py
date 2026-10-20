import bpy,numpy as np,json
from pathlib import Path
W=Path(__file__).resolve().parents[1];rows=[]
for sex in ['Male','Female']:
 path=W/'export'/f'Golf_{sex}_Draft.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
 o=bpy.data.objects['Golf_Polo'];base=np.array([v.co[:] for v in o.data.shape_keys.key_blocks[0].data]);near=[set() for _ in base]
 for e in o.data.edges:a,b=e.vertices;near[a].add(b);near[b].add(a)
 groups={}
 for i,p in enumerate(base):groups.setdefault(tuple(np.round(p*100000).astype(int)),[]).append(i)
 for ids in groups.values():
  for i in ids:near[i].update(set(ids)-{i})
 for k in list(o.data.shape_keys.key_blocks)[1:]:
  delta=np.array([v.co[:] for v in k.data])-base;bad=(np.linalg.norm(delta,axis=1)>.12)|(~np.isfinite(delta).all(1));count=int(bad.sum())
  for _ in range(64):
   fixed=[]
   for i in np.where(bad)[0]:
    good=[j for j in near[i] if not bad[j]]
    if good:delta[i]=delta[good].mean(0);fixed.append(i)
   if not fixed:break
   bad[fixed]=False
  if bad.any():raise RuntimeError(('Unresolved correction component',sex,k.name,int(bad.sum())))
  for i,v in enumerate(k.data):v.co=base[i]+delta[i]
  rows.append(dict(sex=sex,shape=k.name,repaired=count,maxDelta=float(np.linalg.norm(delta,axis=1).max())))
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
(W/'data/correction_repairs.json').write_text(json.dumps(rows,indent=2));print('REPAIR_OK',sum(r['repaired'] for r in rows))
