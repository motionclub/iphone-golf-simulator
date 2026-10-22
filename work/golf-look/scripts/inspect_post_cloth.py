import bpy,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for sex in ['Male','Female']:
    bpy.ops.wm.open_mainfile(filepath=str(W.parents[1]/f'work/cloth-overhaul/export/Cloth_{sex}.blend'))
    rows=[]
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        o.data.calc_loop_triangles()
        rows.append({'name':o.name,'tris':len(o.data.loop_triangles),'matrix':list(map(list,o.matrix_world)),
                     'bounds':[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)],
                     'materials':[m.name for m in o.data.materials]})
    print(sex,json.dumps({'objects':rows,'rigs':[o.name for o in bpy.data.objects if o.type=='ARMATURE']}),flush=True)
    (W/f'data/post_cloth_meshes_{sex}.json').write_text(json.dumps(rows,indent=2))
