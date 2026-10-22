import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
for m in bpy.data.materials:
    if m.use_nodes and 'Principled BSDF' in m.node_tree.nodes:
        n = m.node_tree.nodes['Principled BSDF']
        print(m.name, 'base', [round(x,3) for x in n.inputs['Base Color'].default_value[:3]], 'rough', round(n.inputs['Roughness'].default_value,2), 'users', m.users)
    else:
        print(m.name, 'diffuse', [round(x,3) for x in m.diffuse_color[:3]], 'nodes', m.use_nodes)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name in ('Body_M','Body_F'):
        me = o.data
        mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
        print(o.name, 'material slots', [m.name for m in me.materials], 'face counts', np.bincount(mi))
