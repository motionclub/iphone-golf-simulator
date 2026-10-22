import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
bpy.context.view_layer.update()
for n in ('Rig_Hand_R', 'Body_M', 'Chest_Top', 'Hip_Bottom', 'Foot_L_Shoe', 'Kit_Top_Polo_M_White', 'Kit_Shoe_L_White', 'Hand_Racket'):
    o = bpy.data.objects.get(n)
    if not o: continue
    print(n, 'parent', o.parent.name if o.parent else None, o.parent_type, 'loc', [round(x,4) for x in o.location], 'world_t', [round(x,4) for x in o.matrix_world.translation],
          'inv_t', [round(x,4) for x in o.matrix_parent_inverse.translation], 'basis_t', [round(x,4) for x in o.matrix_basis.translation])
