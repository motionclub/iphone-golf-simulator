"""Wireframe of the Micro1g head topology (front, side). blender -b --factory-startup --python viewwire0.py -- <blend> <outdir>"""
import sys
from pathlib import Path
import numpy as np
import bpy, bmesh
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e')
import wire

blend, out = sys.argv[sys.argv.index('--') + 1:][:2]
out = Path(out); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
me = bpy.data.objects['Body_M'].data
V = np.array([v.co[:] for v in me.vertices], float)
E = np.array([e.vertices[:] for e in me.edges])
bm = bmesh.new(); bm.from_mesh(me)
nm = [e for e in bm.edges if not e.is_manifold]
for e in nm:
    print('NONMANIFOLD', e.index, [tuple(round(c, 4) for c in v.co) for v in e.verts], 'faces', len(e.link_faces))
sel = (V[:, 2] > 1.42) & (np.abs(V[:, 0]) < 0.14)
# front view: u=x, v=z ; keep only front-facing half (y < -0.045) for readability
front = sel & (V[:, 1] < -0.045)
wire.plot(V, E, front, (0, 2), (-0.13, 0.13, 1.42, 1.72), 1200, str(out / 'wire_front.png'), pts=False)
wire.plot(V, E, front, (0, 2), (-0.075, 0.075, 1.44, 1.64), 1400, str(out / 'wire_front_zoom.png'), pts=True)
side = sel & (V[:, 0] > 0.0)
wire.plot(V, E, side, (1, 2), (-0.12, 0.08, 1.42, 1.72), 1200, str(out / 'wire_side.png'), pts=False)
print('done')
