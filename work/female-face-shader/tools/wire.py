"""Blender: dump game-frame coords + triangles of Body for a blend -> ../eval/<tag>_mesh.npz"""
import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft, sculpt_mouth as S
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data; F = S.ctx()
G = S.to_face(ft.game_warp(ft.coords(me), True, True, F), F)
me.calc_loop_triangles(); t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', t)
np.savez(ft.WORK + f'/eval/{argv[1]}_mesh.npz', G=G, tri=t.reshape(-1, 3))
print('WIRE DONE')
