"""export the racket's vertices (Racket_Classic + Grip + ButtCap + StringBed, no collider) in the racket's own frame -> data/racket_pts.npz  (blender -b <blend> --python this)"""
import bpy, numpy as np
rk = bpy.data.objects['Racket_Classic']
pts = []
for n in ('Racket_Classic', 'Grip', 'ButtCap', 'StringBed'):
    o = bpy.data.objects[n]
    M = rk.matrix_world.inverted() @ o.matrix_world
    me = o.data
    pts += [np.array(M @ v.co) for v in me.vertices]
pts = np.array(pts)
np.savez_compressed('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emotes/data/racket_pts.npz', pts=pts)
print('RACKET_PTS', pts.shape, pts.min(0).round(3), pts.max(0).round(3))
