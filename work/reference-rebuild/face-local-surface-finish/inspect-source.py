import bpy,json,pathlib
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-local-surface-finish'
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/original-blink-finish/{sex}_OriginalSeamBlinkFinish1.blend'))
 b=bpy.data.objects['Body'];me=b.data
 groups={g.name:[[v.index,*v.co] for v in me.vertices if any(w.group==g.index and w.weight>.25 for w in v.groups)] for g in b.vertex_groups if any(s in g.name.lower() for s in ('loop','lip','nostril','seam'))}
 out={'groups':groups,'headBounds':[[min(v.co[k] for v in me.vertices if v.co.z>1.4),max(v.co[k] for v in me.vertices if v.co.z>1.4)] for k in range(3)],'vertices':len(me.vertices),'shapes':[(k.name,sum((p.co-me.vertices[i].co).length>1e-7 for i,p in enumerate(k.data))) for k in me.shape_keys.key_blocks]}
 (O/f'{sex.lower()}-inspection.json').write_text(json.dumps(out,indent=2))
 print(sex,{k:(len(v),[sum(p[j] for p in v)/len(v) for j in (1,2,3)] if v else []) for k,v in groups.items()},out['headBounds'],out['shapes'])
