import bpy,json
from pathlib import Path
root=Path(__file__).parent
rows={}
for ident in ['coastal_cliff_01','coastal_cliff_02']:
    bpy.ops.wm.open_mainfile(filepath=str(root/'vendor'/ident/(ident+'_2k.blend')))
    rows[ident]=[{'name':o.name,'type':o.type,'verts':len(o.data.vertices) if o.type=='MESH' else 0,
                 'dimensions':list(o.dimensions),'location':list(o.location),'rotation':list(o.rotation_euler),
                 'hide':o.hide_render,'collections':[c.name for c in o.users_collection],
                 'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []}
                for o in bpy.data.objects]
(root/'cliff-source-objects.json').write_text(json.dumps(rows,indent=2))
print('CLIFF_SOURCE_INSPECTED')
