import bpy,sys,numpy as np
from pathlib import Path
W=Path(sys.argv[sys.argv.index('--')+1])/'work/cloth-overhaul';sys.path.insert(0,str(W/'scripts'));from surface_field import field
for sex in ['Male','Female']:
 p=W/f'export/Cloth_{sex}.blend';bpy.ops.wm.open_mainfile(filepath=str(p));col=bpy.data.collections['Construction_High_BakeOnly']
 for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
 for o in list(bpy.data.objects):
  if o.type!='MESH' or not o.name.startswith('Kit_'):continue
  h=o.copy();h.data=o.data.copy();h.name=o.name+'_High';col.objects.link(h)
  for mod in list(h.modifiers):h.modifiers.remove(mod)
  sub=h.modifiers.new('High construction subdivision','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=1
  bpy.context.view_layer.objects.active=h;bpy.ops.object.modifier_apply(modifier=sub.name)
  P=np.array([v.co[:] for v in h.data.vertices]);N=np.array([v.normal[:] for v in h.data.vertices]);heights=field(P,o.name,sex)[0];h.data.vertices.foreach_set('co',(P+N*heights[:,None]).ravel());h.hide_render=True;h.hide_set(True)
 bpy.ops.wm.save_as_mainfile(filepath=str(p))
