import bpy,json,pathlib
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/characters';out={}
for sex in ('male','female'):
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_reference_expression2.blend'));head=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('GEO-') and all(t not in o.name for t in ('.iris.','.sclera.','.eye.')))
 ev=head.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[{'i':v.index,'p':[float(c) for c in v.co]} for v in me.vertices if abs(v.co.x)<.004 and -.14<v.co.z<-.04 and v.co.y<0];vs.sort(key=lambda v:v['p'][2]);out[sex]={'centralProfile':vs,'materials':[m.name for m in me.materials],'vertexCount':len(me.vertices)};ev.to_mesh_clear()
(O/'anatomy-landmarks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
