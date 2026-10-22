import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from onhand import *
reset_scene()
body = load_body_copy('female')
prof = Profile('female', body)
sk = prof.socket(52.0, -0.02, 0.0, 45.0)
co3, co2, Mh, Qn, infos = prof.posed_body(sk)
rig = prof.rig
m = rig.member(prof.co)
moved = np.linalg.norm(co3 - prof.co, axis=1)
sel_set = set(prof.sel.tolist())
idx = np.where(moved > 0.003)[0]
print('moved verts', len(idx), 'of which in hand set', sum(1 for i in idx if i in sel_set))
# classify by rest position
rest = prof.co[idx]
print('rest x range', rest[:, 0].min().round(3), rest[:, 0].max().round(3), ' z range', rest[:, 2].min().round(3), rest[:, 2].max().round(3), ' y range', rest[:, 1].min().round(3), rest[:, 1].max().round(3))
# vertices with x > -0.185 that move (torso/leg side)
bad = [i for i in idx if prof.co[i, 0] > -0.185]
print('moved verts with rest x > -0.185 (torso/leg side):', len(bad))
for i in bad[:15]:
    print('   rest', prof.co[i].round(3), 'member', round(float(m[i]), 2), 'moved mm', round(float(moved[i] * 1000), 1))
# histogram of membership of moved verts
print('member>0.5:', int((m[idx] > 0.5).sum()), ' member in (0,0.5):', int(((m[idx] > 0) & (m[idx] <= 0.5)).sum()))
# longest edges after pose
e_all = np.concatenate([prof.tris[:, [0, 1]], prof.tris[:, [1, 2]], prof.tris[:, [2, 0]]])
L0 = np.linalg.norm(prof.co[e_all[:, 0]] - prof.co[e_all[:, 1]], axis=1)
L1 = np.linalg.norm(co3[e_all[:, 0]] - co3[e_all[:, 1]], axis=1)
order = np.argsort(-(L1 / np.maximum(L0, 1e-6)))[:8]
for i in order:
    a_, b_ = e_all[i]
    print('stretch x%.1f  L0 %.4f -> %.4f   rest %s %s member %.2f %.2f' % (L1[i] / L0[i], L0[i], L1[i], prof.co[a_].round(3), prof.co[b_].round(3), m[a_], m[b_]))
