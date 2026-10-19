import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft, sculpt_mouth as S
bpy.ops.wm.open_mainfile(filepath=ft.JAW + '/Female_JawSculpt.blend')
me = bpy.data.objects['Body'].data; base = ft.coords(me)
D = np.load(ft.WORK + '/eval/' + sys.argv[sys.argv.index('--') + 1] + '_delta.npy')
idx, tri, edges, nu = ft.topology_at(base, me)
P0 = np.zeros((nu, 3)); P0[idx] = base; P1 = np.zeros((nu, 3)); P1[idx] = base + D
e0, a0 = S.dihedral(P0, tri); e1, a1 = S.dihedral(P1, tri)
F = S.ctx(); G = S.to_face(ft.game_warp(base, True, True, F), F); U = np.zeros((nu, 3)); U[idx] = G
new = (a1 > 60) & (a0 <= 60)
lost = (a1 <= 60) & (a0 > 60)
print('LOST >60 edges', int(lost.sum()), [(np.round(U[e[0]],1).tolist(), np.round(U[e[1]],1).tolist(), round(float(x0),1), round(float(x1),1)) for e,x0,x1 in zip(e0[lost],a0[lost],a1[lost])][:6])
print('NEW >60 edges', int(new.sum()))
for e, aa, bb in zip(e0[new], a0[new], a1[new]): print('  game mm', np.round(U[e[0]], 1).tolist(), 'angle', round(float(aa), 1), '->', round(float(bb), 1))
