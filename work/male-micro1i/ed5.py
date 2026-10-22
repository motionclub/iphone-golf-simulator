"""Edit e5: stronger cheek/smile modelling on top of e4 (malar apple, smile bunching, lower-lid puff).  All amplitudes in mm along the smoothed normal."""
import sys, json; sys.path.insert(0, '.')
from brushes import *

DEFAULT = dict(
    apple=dict(cx=43.0, cz=1.541, rx=13.0, rz=10.5, amp=3.4),
    bunch=dict(cx=42.0, dz=0.0066, rx=6.5, rz=5.0, amp=1.6),
    lidpuff=dict(cx=35.0, cz=1.5705, rx=13.0, rz=3.2, amp=1.2),
    cheek_soft=dict(cx=52.0, cz=1.525, rx=20.0, rz=14.0, amp=1.4),
)


def e5(V, F, M, prm=None):
    p = json.loads(json.dumps(DEFAULT))
    if prm:
        for k, v in prm.items(): p[k].update(v)
    N = export_normals(V, F, M); fw = front_w(V)
    a = p['apple']; disp = blob(V, a['cx'], a['cz'], a['rx'], a['rz'], a['amp'])
    b = p['bunch']; disp += blob(V, b['cx'], float(S.seam_z(np.array([b['cx'] * 1e-3]))[0]) + b['dz'], b['rx'], b['rz'], b['amp'])
    l = p['lidpuff']; disp += blob(V, l['cx'], l['cz'], l['rx'], l['rz'], l['amp'])
    c = p['cheek_soft']; disp += blob(V, c['cx'], c['cz'], c['rx'], c['rz'], c['amp'])
    disp *= fw
    return apply_field(V, N, disp), disp


if __name__ == '__main__':
    tag_in, tag_out = sys.argv[1], sys.argv[2]; prm = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    V0, F, loops = load(tag_in); M = Mesh(V0, F)
    V1, disp = e5(V0, F, M, prm)
    d = np.linalg.norm(V1 - V0, axis=1); print('moved', int((d > 1e-6).sum()), 'max mm %.2f' % (d.max() * 1000))
    np.save(f'data/V_{tag_out}.npy', V1)
