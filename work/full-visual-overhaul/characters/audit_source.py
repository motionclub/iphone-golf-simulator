import bpy,json,os,hashlib
from pathlib import Path
out=Path(os.environ['CHAR_AUDIT_OUT']);out.parent.mkdir(parents=True,exist_ok=True)
rows=[]
for o in bpy.data.objects:
 if o.type=='ARMATURE':
  rows.append({'name':o.name,'type':o.type,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'matrix':[list(r) for r in b.matrix_local]} for b in o.data.bones]})
 elif o.type=='MESH':
  rows.append({'name':o.name,'type':o.type,'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'shapeKeys':[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],'materials':[m.name if m else '' for m in o.data.materials],'armature':[m.object.name if m.object else '' for m in o.modifiers if m.type=='ARMATURE'],'dimensions':list(o.dimensions),'hidden':o.hide_render})
content={'source':bpy.data.filepath,'objects':rows,'actions':[a.name for a in bpy.data.actions]}
out.write_text(json.dumps(content,indent=2))
print('CHAR_AUDIT '+str(out)+' meshes='+str(sum(r['type']=='MESH' for r in rows)))
