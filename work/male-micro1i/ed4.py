"""Edit e4: interior relief (no silhouette growth): cheek apples via hollows, lip/vermilion/seam definition, mentolabial + jaw grooves, infraorbital/temple hollows."""
import sys, json; sys.path.insert(0, '.')
from brushes import *

DEFAULT = dict(
    infraorb=dict(cx=31, cz=1.568, rx=13, rz=5.5, amp=-1.6),
    malar=dict(cx=46, cz=1.541, rx=15, rz=10, amp=1.6),
    buccal=dict(cx=50, cz=1.506, rx=11, rz=8, amp=-1.7),
    temple=dict(cx=66, cz=1.600, rx=9, rz=12, amp=-1.2),
    seam_depth=0.0, seam_sigma=2.4,
    vermil_up=dict(depth=0.0, sigma=2.4), vermil_lo=dict(depth=0.0, sigma=2.4),
    mentolabial=dict(depth=1.3, sigma=3.0, z_off=-0.0125),
    corner_pocket=dict(cx=37.5, dz=0.0, rx=3.2, rz=3.0, amp=-1.0),
    jaw_groove=dict(depth=2.0, sigma=4.0),
    ala_groove=dict(depth=1.4, sigma=2.4),
    ala_bump=dict(cx=22.0, cz=1.5415, rx=7.0, rz=6.2, amp=2.3),
)


def e4(V, F, M, loops, prm=None):
    p = json.loads(json.dumps(DEFAULT)); 
    if prm:
        for k, v in prm.items():
            if isinstance(v, dict): p[k].update(v)
            else: p[k] = v
    N = export_normals(V, F, M)
    fw = front_w(V)
    disp = np.zeros(len(V))
    for key in ('infraorb', 'malar', 'buccal', 'temple'):
        b = p[key]; disp += blob(V, b['cx'], b['cz'], b['rx'], b['rz'], b['amp'])
    disp *= fw
    # lips: seam + vermilion borders along the smile arc
    zs = lambda xmm: S.seam_z(np.asarray(xmm) * 1e-3)
    xs = np.linspace(0, 38, 40)
    seam_pts = [(float(a), float(zs(a))) for a in xs]
    hu = p.get('lip_up_h', 4.8) * 1e-3; hl = p.get('lip_lo_h', 8.8) * 1e-3
    up = [(float(a), float(zs(a)) + hu * max(0.0, 1 - (a / 36.0) ** 2.4) ** (1 / 2.4)) for a in xs]
    lo = [(float(a), float(zs(a)) - hl * max(0.0, 1 - (a / 32.5) ** 2.2) ** (1 / 2.2)) for a in xs]
    g = groove(V, seam_pts, p['seam_depth'], p['seam_sigma'], taper=lambda x: 1 - sstep(34, 40, x))
    g += groove(V, up, p['vermil_up']['depth'], p['vermil_up']['sigma'], taper=lambda x: 1 - sstep(30, 37, x))
    g += groove(V, lo, p['vermil_lo']['depth'], p['vermil_lo']['sigma'], taper=lambda x: 1 - sstep(26, 33, x))
    disp += g * fw
    # mentolabial groove under the lower lip (gentle arc)
    ml = p['mentolabial']
    ment = [(float(a), float(zs(0)) + ml['z_off'] + 0.0012 * (a / 25.0) ** 2) for a in np.linspace(0, 26, 20)]
    disp += groove(V, ment, ml['depth'], ml['sigma'], taper=lambda x: 1 - sstep(16, 28, x)) * fw
    # corner pockets
    c = p['corner_pocket']; disp += blob(V, c['cx'], float(zs(c['cx'])) + c['dz'] * 1e-3, c['rx'], c['rz'], c['amp'], q=2.0) * fw
    # jaw groove: along the jaw_ear loop, just below it
    jl = loops['LOOP_jaw_ear_R']
    jp = V[jl]; o = np.argsort(jp[:, 0]); jp = jp[o]
    pts = [(float(abs(a[0]) * 1000), float(a[2] - 0.004)) for a in jp]
    disp += groove(V, pts, p['jaw_groove']['depth'], p['jaw_groove']['sigma']) * sstep(-0.04, -0.08, V[:, 1]) * sstep(0.020, 0.030, np.abs(V[:, 0]))
    ab = p['ala_bump']; disp += blob(V, ab['cx'], ab['cz'], ab['rx'], ab['rz'], ab['amp']) * sstep(-0.10, -0.13, V[:, 1])        # rounded alar lobe
    # alar crease: groove along the carved ala chain (vertices sit on the crease) -> defined alar wing / nose side
    ag = p['ala_groove']
    if ag['depth'] > 0:
        al = loops['LOOP_ala_R']; ap = V[al]; ap = ap[np.argsort(-ap[:, 2])]
        pts = [(float(abs(a[0]) * 1000), float(a[2])) for a in ap]
        disp += groove(V, pts, ag['depth'], ag['sigma']) * sstep(-0.10, -0.13, V[:, 1])
    return apply_field(V, N, disp), disp


if __name__ == '__main__':
    tag_in = sys.argv[1]; tag_out = sys.argv[2]; prm = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    V0, F, loops = load(tag_in); M = Mesh(V0, F)
    V1, disp = e4(V0, F, M, loops, prm)
    d = np.linalg.norm(V1 - V0, axis=1)
    print('moved', int((d > 1e-6).sum()), 'max mm %.2f' % (d.max() * 1000), 'disp range %.2f..%.2f' % (disp.min(), disp.max()))
    np.save(f'data/V_{tag_out}.npy', V1)
