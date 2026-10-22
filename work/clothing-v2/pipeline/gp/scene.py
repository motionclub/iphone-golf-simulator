"""GARMENT PIPELINE: the worn set of one hero as skinnable items in ROOT space.
Every item (body, garments, accessories) is skinned with delta transforms D_g = M_g(frame) @ inv(M_g(rest)) over GLOBAL bone indices, so a
candidate garment and a dumped one are treated the same way. Correctives are root-space rest deltas added before skinning."""
import numpy as np
import rig


class Item:
    def __init__(self, tag, kind, P, tri, bi, bw, shapes=None, shape_names=(), drawn=None, sub=None, gidx=None, B=None):
        """bi index the palette gidx (global bone ids); B (nb,4,4) maps root-space rest points into each palette bone
        (skin_j = M[gidx_j] @ B_j). Without gidx / B: bi are global ids and B = inverse rest bone matrices."""
        self.tag, self.kind = tag, kind
        self.P = np.asarray(P, np.float64)            # rest, root space
        self.tri = np.asarray(tri, np.int64)
        self.bi = np.asarray(bi, np.int64); self.bw = np.asarray(bw, np.float64)
        self.gidx, self.B = gidx, B
        self.shapes = np.zeros((0, len(self.P), 3)) if shapes is None else shapes
        self.shape_names = list(shape_names)
        self.drawn = np.ones(len(self.tri), bool) if drawn is None else drawn   # triangles actually drawn (body cover)
        self.sub = np.zeros(len(self.tri), np.int32) if sub is None else sub
        self.corr = None       # optional corrective model: callable(features) -> weights over self.shapes

    @property
    def n(self): return len(self.P)


class Rig:
    def __init__(self, hero):
        self.hero = hero
        self.rest = hero.rest_mats()
        self.irest = np.linalg.inv(self.rest)

    def deltas(self, mats):
        return mats @ self.irest

    def skin(self, item, mats):
        """per-palette skinning matrices of an item for bone matrices `mats` (NB,4,4)."""
        if item.gidx is None: return mats @ self.irest
        return mats[item.gidx] @ item.B

    def posem(self, item, mats, shape_w=None, base=None):
        return self.pose(item, self.skin(item, mats), shape_w, base)

    def pose(self, item, D, shape_w=None, base=None):
        v = item.P if base is None else base
        if shape_w is not None and len(item.shapes):
            nz = np.nonzero(np.abs(shape_w) > 1e-6)[0]
            if len(nz): v = v + np.einsum('s,svk->vk', shape_w[nz] / 100.0, item.shapes[nz])
        out = np.zeros((len(v), 3))
        for k in range(item.bi.shape[1]):
            m = D[item.bi[:, k]]
            w = item.bw[:, k:k + 1]
            if not w.any(): continue
            out += w * (np.einsum('nij,nj->ni', m[:, :3, :3], v) + m[:, :3, 3])
        return out


def to_root(part, v):
    return v @ part.r2root[:3, :3].T + part.r2root[:3, 3]


def dir_to_root(part, d):
    return d @ part.r2root[:3, :3].T


def items_from_dump(hero, include=None):
    """body (drawn = the cover the game uses today) + every worn part, as root-space items with global weights."""
    out = []
    for p in hero.parts:
        if include is not None and p.tag != 'body' and p.tag not in include: continue
        P = to_root(p, p.pos)
        B = p.bind @ np.linalg.inv(p.r2root)
        shapes = np.einsum('svk,jk->svj', p.shapes, p.r2root[:3, :3]) if len(p.shapes) else None
        if p.tag == 'body':
            tri = hero.body_src_tri
            key = lambda t: np.sort(t, 1)
            cur = {tuple(x) for x in key(p.tri)}
            drawn = np.array([tuple(x) in cur for x in key(tri)])
            it = Item('body', 'body', P, tri, p.bi, p.bw, shapes, p.shape_names, drawn=drawn, gidx=p.gidx, B=B)
        else:
            it = Item(p.tag, p.kind, P, p.tri, p.bi, p.bw, shapes, p.shape_names, sub=p.sub_of_tri, gidx=p.gidx, B=B)
        out.append(it)
    return out


def frame_iter(hero, clips=None, step=1):
    """yields (clip_file, frame_index, mats, shape_weights_by_tag)"""
    for c in hero.clips:
        if clips is not None and c['file'] not in clips: continue
        mats, sw = hero.frames(c['file'])
        for f in range(0, len(mats), step):
            yield c['file'], f, mats[f], {k: v[f] for k, v in sw.items()}
