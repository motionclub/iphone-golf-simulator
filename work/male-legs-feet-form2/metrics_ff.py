"""Fast metrics for the legs/feet job on arbitrary (V, F): sagittal near-foot contour error, foot placement, ground contact, silhouette XOR vs frozen plate masks.
numpy + PIL (PYTHONPATH=work/male-micro1i/pylib when run with Blender's python)."""
import sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-legs-feet-form2')
from edges_ref import CAMS, target_mask, cam, h_sign, VIEWS, spans

W_, H_ = 1280, 720
# near-foot contour read from both profile plates (previous chat, work/male-parallel-legs/metrics_legs.py C_NEW): (y, z) metres
C_NEW = np.array([(-0.2235, 0.030), (-0.2215, 0.045), (-0.2150, 0.054), (-0.2000, 0.061), (-0.1800, 0.067), (-0.1600, 0.0705), (-0.1400, 0.079),
                  (-0.1200, 0.0905), (-0.1000, 0.099), (-0.0850, 0.110), (-0.0720, 0.124), (-0.0640, 0.140), (-0.0620, 0.160), (-0.0640, 0.190),
                  (-0.0620, 0.220), (-0.0620, 0.250), (-0.0660, 0.300)])


def leg_faces(V, F, side=+1, zmax=0.40):
    sel = (side * V[:, 0] > 0.08) & (V[:, 2] < zmax)
    return [p for p in F if all(sel[i] for i in p)]


def sag_boundary(V, F, side=+1):
    """boundary pixels (y, z) of the sagittal silhouette of one leg (z < 0.40) at 0.5 mm/px"""
    faces = leg_faces(V, F, side)
    S = 2000.0; y0, z0 = -0.30, -0.01; Wd = int(0.45 * S); Hd = int(0.42 * S)
    img = Image.new('L', (Wd, Hd), 0); d = ImageDraw.Draw(img)
    for p in faces:
        d.polygon([((V[i, 1] - y0) * S, (V[i, 2] - z0) * S) for i in p], fill=1)
    m = np.array(img, bool)
    e = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    zs, ys = np.nonzero(e)
    return np.stack([ys / S + y0, zs / S + z0], 1)


def contour_error(V, F, side=+1):
    P = sag_boundary(V, F, side)
    t = np.linspace(0, 1, 400)
    seg = np.cumsum(np.r_[0, np.linalg.norm(np.diff(C_NEW, axis=0), axis=1)]); seg /= seg[-1]
    Q = np.stack([np.interp(t, seg, C_NEW[:, 0]), np.interp(t, seg, C_NEW[:, 1])], 1)
    # nearest boundary distance (chunked)
    d = np.empty(len(Q))
    for i, q in enumerate(Q):
        d[i] = np.sqrt(((P - q) ** 2).sum(1).min())
    d *= 1000
    inst = Q[:, 0] < -0.075
    cap = Q[:, 0] < -0.17
    return dict(mean_mm=float(d.mean()), max_mm=float(d.max()), instep_mean_mm=float(d[inst].mean()), instep_max_mm=float(d[inst].max()),
                cap_mean_mm=float(d[cap].mean()), cap_max_mm=float(d[cap].max()), behind_cap_mean_mm=float(d[~cap].mean()))


def foot_extents(V, side=+1):
    out = {}
    s_ = side * V[:, 0] > 0.10
    sel = s_ & (V[:, 2] < 0.12)
    # toe tip, heel back (y extremes of the sole region z<0.03)
    sole = s_ & (V[:, 2] < 0.03)
    out['toe_y_min'] = float(V[sole, 1].min()); out['heel_y_max'] = float(V[sole, 1].max())
    out['min_z'] = float(V[:, 2].min())
    for z in (0.16, 0.19, 0.22):
        s = s_ & (np.abs(V[:, 2] - z) < 0.006)
        out[f'ankle_y_z{z:.2f}'] = (float(V[s, 1].min()), float(V[s, 1].max()), float(0.5 * (V[s, 1].min() + V[s, 1].max())))
    return out


def mask(V, F, v):
    mpp, sole, cx = cam(v)
    u = V[:, 1] if v in ('left', 'right') else V[:, 0]
    px = cx + h_sign(v) * u / mpp; py = sole - V[:, 2] / mpp
    img = Image.new('L', (W_, H_), 0); d = ImageDraw.Draw(img)
    for p in F:
        d.polygon([(px[i], py[i]) for i in p], fill=1)
    return np.array(img, bool)


def xor_pct(m, t, rows=None):
    if rows is not None: m = m[rows]; t = t[rows]
    return 100.0 * (m != t).sum() / max(1, (m | t).sum())


def silhouettes(V, F, views=('bald_front', 'bald_back', 'sheet_front', 'sheet_back', 'left', 'right')):
    out = {}
    for v in views:
        m = mask(V, F, v); t = target_mask(v)
        mpp, sole, cx = cam(v)
        r_foot = slice(int(sole - 0.16 / mpp), H_)
        out[v] = dict(total=xor_pct(m, t), foot=xor_pct(m, t, r_foot), xor_px_foot=int((m[r_foot] != t[r_foot]).sum()))
    return out


if __name__ == '__main__':
    import pickle
    which = sys.argv[1] if len(sys.argv) > 1 else 'base'
    if which == 'base':
        V = np.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-legs-feet-form2/data/V_start.npy')
        F = pickle.load(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-legs-feet-form2/data/F.pkl', 'rb'))
    else:
        W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-legs-feet-form2/tmp/'
        V = np.load(W + f'V_{which}.npy'); F = pickle.load(open(W + f'F_{which}.pkl', 'rb'))['faces']
    print(json.dumps(contour_error(V, F), indent=1))
    print(json.dumps(foot_extents(V), indent=1))
    print(json.dumps(silhouettes(V, F), indent=1))
