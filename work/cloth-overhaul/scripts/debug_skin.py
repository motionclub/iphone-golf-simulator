import bpy,sys
from pathlib import Path
R=Path(sys.argv[sys.argv.index('--')+1]);W=R/'work/cloth-overhaul'
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(W/f'export/Cloth_{sex}.blend'))
 print('SEX',sex,flush=True)
 for o in bpy.data.objects:
  if o.type=='MESH' and not o.name.endswith('_High'):
   print(o.name,'parent',o.parent.name if o.parent else None,'groups',len(o.vertex_groups),'members',sum(bool(v.groups) for v in o.data.vertices),'mods',[(m.type,m.object.name if m.type=='ARMATURE' and m.object else '') for m in o.modifiers],flush=True)
 print('rigs',[(o.name,len(o.data.bones)) for o in bpy.data.objects if o.type=='ARMATURE'],flush=True)
