import bpy,sys,json,os, numpy as np
from pathlib import Path
A=sys.argv[sys.argv.index('--')+1:]; R=Path(A[0]); out=R/'work/cloth-overhaul'
all_stats={}
for sex in ['Male','Female']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(R/f'Unity/Assets/Characters/MatchHeroKit/{sex}_Kit.fbx'))
 stats=[]
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  m=o.data;m.calc_loop_triangles(); P=np.array([o.matrix_world@v.co for v in m.vertices]); N=np.array([v.normal for v in m.vertices]); uv=np.array([x.uv[:] for x in m.uv_layers[0].data]);
  adj=[[] for _ in P]
  for e in m.edges:
   a,b=e.vertices; adj[a].append(b);adj[b].append(a)
  seen=set();cs=[]
  for i in range(len(P)):
   if i in seen:continue
   q=[i];seen.add(i);ids=[]
   while q:
    v=q.pop();ids.append(v)
    for j in adj[v]:
     if j not in seen:seen.add(j);q.append(j)
   ids=np.array(ids);cs.append({'verts':len(ids),'min':P[ids].min(0).tolist(),'max':P[ids].max(0).tolist()})
  s={'name':o.name,'verts':len(P),'tris':len(m.loop_triangles),'min':P.min(0).tolist(),'max':P.max(0).tolist(),'materials':[x.name for x in m.materials],'components':sorted(cs,key=lambda s:-s['verts'])[:40],'matrix':[list(x) for x in o.matrix_world]};stats.append(s)
  np.savez(out/f'{sex}_{o.name}_mesh.npz',P=P,N=N,uv=uv,loopverts=np.array([l.vertex_index for l in m.loops]),tri=np.array([t.vertices[:] for t in m.loop_triangles]),triloops=np.array([t.loops[:] for t in m.loop_triangles]),material=np.array([t.material_index for t in m.loop_triangles]))
 all_stats[sex]=stats
(out/'kit_geometry_before.json').write_text(json.dumps(all_stats,indent=2))
print(json.dumps({s:[{'piece':o['name'],'tris':o['tris'],'components':len(o['components']),'min':o['min'],'max':o['max']} for o in all_stats[s]] for s in all_stats},indent=2))
