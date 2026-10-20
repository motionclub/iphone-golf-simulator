"""Edit e8: mouth modelled ON the carved loops (clean, no sawtooth): seam groove along LOOP_mouth_seam, vermilion borders along
LOOP_mouth_lip_upper / lower, lip volume (upper tubercle, fuller lower lip), stronger corner pockets.  Displacements along the smoothed normal."""
import sys, json; sys.path.insert(0, '.')
from brushes import *

DEFAULT = dict(seam=dict(depth=1.0, sigma=1.8), up_border=dict(depth=0.0, sigma=1.5), lo_border=dict(depth=0.0, sigma=1.7),
               lip_up=dict(cx=0.0, dz=0.0034, rx=15.0, rz=3.0, amp=0.7, q=2.2), lip_lo=dict(cx=0.0, dz=-0.0050, rx=17.0, rz=4.2, amp=1.1, q=2.2),
               pocket=dict(cx=37.8, dz=0.0, rx=3.0, rz=2.8, amp=-1.7), fold=dict(depth=0.9, sigma=2.6))


def chain_points(V, loop, both_sides=False):
    p = V[loop]; pts = [(float(abs(a[0]) * 1000), float(a[2])) for a in p]
    return sorted(pts)


def e8_mouth(V, F, M, loops, prm=None):
    p = json.loads(json.dumps(DEFAULT))
    for k, v in (prm or {}).items(): p[k].update(v)
    N = export_normals(V, F, M); fw = front_w(V)
    disp = np.zeros(len(V))
    zs = lambda xmm: S.seam_z(np.asarray(xmm) * 1e-3)
    seam = chain_points(V, loops['LOOP_mouth_seam'])
    up = chain_points(V, loops['LOOP_mouth_lip_upper']); lo = chain_points(V, loops['LOOP_mouth_lip_lower'])
    disp += groove(V, seam, p['seam']['depth'], p['seam']['sigma'], taper=lambda x: 1 - sstep(33, 39, x))
    disp += groove(V, up, p['up_border']['depth'], p['up_border']['sigma'], taper=lambda x: 1 - sstep(28, 35, x))
    disp += groove(V, lo, p['lo_border']['depth'], p['lo_border']['sigma'], taper=lambda x: 1 - sstep(24, 31, x))
    for key in ('lip_up', 'lip_lo'):
        b = p[key]; disp += blob(V, b['cx'], float(zs(0.0)) + b['dz'], b['rx'], b['rz'], b['amp'], q=b['q'])
    c = p['pocket']; disp += blob(V, c['cx'], float(zs(c['cx'])) + c['dz'] * 1e-3, c['rx'], c['rz'], c['amp'], q=2.0)
    disp *= fw
    return apply_field(V, N, disp), disp


if __name__ == '__main__':
    tag_in, tag_out = sys.argv[1], sys.argv[2]; prm = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    V0, F, loops = load(tag_in); M = Mesh(V0, F)
    V1, disp = e8_mouth(V0, F, M, loops, prm)
    d = np.linalg.norm(V1 - V0, axis=1); print('moved', int((d > 1e-9).sum()), 'max mm %.2f' % (d.max() * 1000), 'disp %.2f..%.2f' % (disp.min(), disp.max()))
    np.save(f'data/V_{tag_out}.npy', V1)
