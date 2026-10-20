import sys
import numpy as np, bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, proxy as PX
P = np.load(H.W/'data/P_n4.npy'); V, F = PX.build_proxy(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
o = H.make_mesh_object('proxy', P, [f for f in F])
for sss, tag in ((0.0, 'sss0'), (0.12, 'sss12')):
    m = H.skin_material('m_'+tag, sss=sss)
    o.data.materials.clear(); o.data.materials.append(m)
    b = m.node_tree.nodes['Principled BSDF']
    print(tag, [ (k, b.inputs[k].default_value if not hasattr(b.inputs[k].default_value,'__len__') else tuple(b.inputs[k].default_value)) for k in ('Subsurface Weight','Subsurface Scale','Subsurface Radius')])
    H.setup_eevee(res=(700,700))
    H.shot(H.W/f'r/test_{tag}.png', (0,-0.1,1.55), 32.5, 0, 0.16, (700,700))
