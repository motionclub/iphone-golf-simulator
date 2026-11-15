"""armio.py: read the hero export (ZHeroArmExport) with numpy, and the arm's own coordinates.
Hero frame (Unity): x right, y up, z forward. Arm coords for a point p on one side:
  u in [0,1] along shoulder->elbow (upper) or elbow->wrist (fore), rho = distance from that bone's axis,
  phi = angle about the axis, 0 = toward the front of the body (+z), +90 deg = up in the T pose."""
import json, struct, numpy as np

def read(path):
    b = open(path, 'rb').read(); nv, nt = struct.unpack_from('<ii', b, 0); o = 8
    pos = np.frombuffer(b, '<f4', nv * 3, o).reshape(nv, 3).astype(np.float64); o += nv * 12
    nrm = np.frombuffer(b, '<f4', nv * 3, o).reshape(nv, 3).astype(np.float64); o += nv * 12
    tri = np.frombuffer(b, '<i4', nt * 3, o).reshape(nt, 3); o += nt * 12
    uv = np.frombuffer(b, '<f4', nv * 2, o).reshape(nv, 2); o += nv * 8
    w = np.frombuffer(b, '<f4', nv * 8, o).reshape(nv, 8)
    return dict(pos=pos, nrm=nrm, tri=tri, uv=uv, w=w)

def full_tris(path):
    b = open(path, 'rb').read(); nt = struct.unpack_from('<i', b, 0)[0]
    return np.frombuffer(b, '<i4', nt * 3, 4).reshape(nt, 3)

def bones(path): return {k: np.array(v, float) for k, v in json.load(open(path)).items()}

def frame(a, b, fwd=np.array([0, 0, 1.0])):
    """Orthonormal frame of the bone a->b: axis, front (the body's forward made square to the axis), up = axis x front."""
    ax = (b - a) / np.linalg.norm(b - a)
    f = fwd - ax * (fwd @ ax); f /= np.linalg.norm(f)
    return ax, f, np.cross(ax, f)

def coords(p, a, b):
    ax, f, up = frame(a, b); L = np.linalg.norm(b - a)
    d = p - a; t = d @ ax
    r = d - np.outer(t, ax)
    return t / L, np.linalg.norm(r, axis=1), np.arctan2(r @ up, r @ f), L

def read_skin(path):
    """<name>.skin (ZHeroArmExport): bone names, their parents' names, and four (bone, weight) per vertex."""
    b = open(path, 'rb').read(); o = 0
    def s():
        nonlocal o
        n = 0; sh = 0
        while True:
            c = b[o]; o += 1; n |= (c & 127) << sh; sh += 7
            if c < 128: break
        t = b[o:o + n].decode(); o += n; return t
    nb = struct.unpack_from('<i', b, o)[0]; o += 4
    names, parents = [], []
    for _ in range(nb): names.append(s()); parents.append(s())
    nv = struct.unpack_from('<i', b, o)[0]; o += 4
    rec = np.frombuffer(b, np.dtype([('i', '<i4'), ('w', '<f4')]), nv * 4, o).reshape(nv, 4)
    return dict(names=names, parents=parents, idx=rec['i'].astype(int), w=rec['w'].astype(np.float64))

def arm_share(skin, body_skin, side):
    """Per bone of `skin`: how much of it belongs to the arm on `side` (0..1). The upper arm and everything under it is 1; a helper
    bone ArmBlend_<a>_<b>_<n> (HeroArmSkinning: the dual-quaternion blend of BODY bones a and b at n/8) is the mix of its two ends."""
    par = dict(zip(body_skin['names'], body_skin['parents'])); par.update(zip(skin['names'], skin['parents']))
    root = side + "UpperArm"
    def real(n):
        seen = 0
        while n and seen < 64:
            if n == root: return 1.0
            n = par.get(n, ""); seen += 1
        return 0.0
    out = []
    for n in skin['names']:
        if "ArmBlend_" in n:
            a, b, k = n[n.index("ArmBlend_"):].split("_")[1:4]; t = int(k) / 8
            out.append(((1 - t) * real(body_skin['names'][int(a)]), t * real(body_skin['names'][int(b)]), t))
        else:
            r = real(n); out.append((r, 0.0, 0.0) if True else None)
    return out   # (share from end a, share from end b, t); a real bone is (share, 0, 0)

def membership(skin, body_skin, side):
    sh = np.array([a + b for a, b, t in arm_share(skin, body_skin, side)])
    return (skin['w'] * sh[skin['idx']]).sum(1)

def swing(pos, skin, body_skin, S, side, deg):
    """The arm on `side` swung about the forward axis through the shoulder joint S by `deg` (linear blend skinning with the game's
    own weights; a helper bone turns by the dual-quaternion blend of its two ends, which for two turns about one axis is a turn
    about that axis)."""
    th = np.radians(deg); ang = []
    for (a, b, t), n in zip(arm_share(skin, body_skin, side), skin['names']):
        if "ArmBlend_" in n:
            ta = th if a > 0 else 0.0; tb = th if b > 0 else 0.0
            ang.append(2 * np.arctan2((1 - t) * np.sin(ta / 2) + t * np.sin(tb / 2), (1 - t) * np.cos(ta / 2) + t * np.cos(tb / 2)))
        else: ang.append(th * a)
    ang = np.array(ang)[skin['idx']]                       # (nv, 4)
    d = pos - S; c, s_ = np.cos(ang), np.sin(ang)
    x = (skin['w'] * (c * d[:, :1] - s_ * d[:, 1:2])).sum(1); y = (skin['w'] * (s_ * d[:, :1] + c * d[:, 1:2])).sum(1)
    tot = skin['w'].sum(1)
    out = pos.copy(); ok = tot > 1e-6
    out[ok, 0] = S[0] + x[ok] / tot[ok]; out[ok, 1] = S[1] + y[ok] / tot[ok]
    return out
