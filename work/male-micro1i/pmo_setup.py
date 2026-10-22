"""Real-plate PMO setup: zone, feature masks, stubble albedo field, contour freeze weights."""
import sys
sys.path.insert(0, '.')
from pmo import *
import sculpt as S                      # micro1h analytic helpers (numpy only): eye polygon, seam curve, ...

BROW_CL = [(214.0, 148.3), (206.0, 148.0), (198.0, 148.0), (190.0, 148.3), (184.0, 149.8), (180.0, 152.6), (177.0, 156.0), (175.6, 158.0)]
BROW_TH = [8.8, 9.0, 9.2, 8.8, 7.0, 5.0, 2.6, 0.8]


def seg_dist_pts(px, pz, pts):
    d = np.full(px.shape, np.inf)
    for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
        ex, ez = bx - ax, bz - az
        t = np.clip(((px - ax) * ex + (pz - az) * ez) / (ex * ex + ez * ez + 1e-18), 0, 1)
        d = np.minimum(d, np.hypot(px - (ax + t * ex), pz - (az + t * ez)))
    return d


def feature_masks(V):
    """returns dict of soft masks (0..1) on the vertices: eye, brow, lip, nostril (1 = feature, exclude from the photometric data term)"""
    x = np.abs(V[:, 0]); z = V[:, 2]; y = V[:, 1]
    front = V[:, 1] < -0.05
    poly = S.smooth_poly(S.eye_poly())
    de = S.poly_dist(x, z, poly)                                    # >0 outside the eye opening
    eye = 1.0 - sstep(0.002, 0.007, de)
    # brows: polyline in (|x|, z)
    pts = [((227.6 - c) * K, float(H.zrow(r))) for c, r in BROW_CL]
    th = np.array(BROW_TH) * K
    d = seg_dist_pts(x, z, pts)
    thv = np.interp(np.arange(len(pts)), np.arange(len(pts)), th)
    # distance minus half thickness at the nearest segment (use mean thickness weighted: simple, generous)
    brow = 1.0 - sstep(0.0045, 0.0085, d)
    # lips: seam +/- band along the smile arc, |x| < 40 mm
    zs = S.seam_z(x)
    lip = (1.0 - sstep(0.038, 0.044, x)) * sstep(zs - 0.0125, zs - 0.0095, z) * (1.0 - sstep(zs + 0.0065, zs + 0.0095, z))
    # nostrils / alar creases
    nz = float(H.zrow(S.PRM['nostril']['row']))
    nos = (1.0 - sstep(0.020, 0.026, np.abs(x - 0.0145))) * (1.0 - sstep(0.0035, 0.0065, np.abs(z - nz)))
    nostril = nos * front
    return dict(eye=eye * front, brow=brow * front, lip=lip * front, nostril=nostril)


def texture_energy_front():
    """stubble texture energy on the front panel (plate px), features not yet removed"""
    box = (5, 62, 433, 352)
    g = np.asarray(PLATE.crop(box).convert('L')).astype(float)
    hp = g - gauss_blur(g, 1.6)
    return np.sqrt(gauss_blur(hp ** 2, 3.0)), box


def stubble_field(V, masks):
    """S in [0,1] per vertex from the front-plate texture energy (features excluded, normalised convolution)"""
    en, box = texture_energy_front()
    col, row = colx(V[:, 0]), rowz(V[:, 2])
    e_v = bilinear(en, np.clip(col - box[0], 0, en.shape[1] - 1.01), np.clip(row - box[1], 0, en.shape[0] - 1.01))
    s0 = np.clip((e_v - 0.9) / (2.4 - 0.9), 0, 1)
    feat = np.maximum.reduce([masks['eye'], masks['brow'], masks['lip'], masks['nostril']])
    # region where stubble can exist: below the cheekbone line, not the nose block
    z = V[:, 2]; x = np.abs(V[:, 0])
    reg = (1.0 - sstep(1.540, 1.552, z)) * (1.0 - (1.0 - sstep(0.014, 0.022, x)) * sstep(1.527, 1.535, z))
    s0 = s0 * reg * (1.0 - feat)
    return s0


def build_zone(V, margin_z=(1.452, 1.625), xmax=0.082, ymax=-0.040):
    x = np.abs(V[:, 0]); z = V[:, 2]; y = V[:, 1]
    return (z > margin_z[0]) & (z < margin_z[1]) & (x < xmax) & (y < ymax)


def contour_freeze(pb, N0, views, thr=0.30, fz0=400.0):
    fz = np.zeros(pb.n)
    for v in views:
        Q, Nq = fold_pts(pb.V0, N0, v.fold)
        c = np.abs(Nq @ v.toward)
        fz = np.maximum(fz, fz0 * np.clip(1.0 - c / thr, 0, 1) ** 2)
    return fz
