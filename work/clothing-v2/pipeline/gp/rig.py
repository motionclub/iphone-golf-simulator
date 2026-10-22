"""GARMENT PIPELINE: read a hero dump (unity/GarmentPipelineDump.cs) and rebuild any part at any frame exactly like Unity
(blend shapes, then Bone4 linear blend skinning). Root space = Unity hero root (Y up, hero faces +Z). numpy only, so it runs in
Blender's python and in the system python."""
import json, os
import numpy as np

PIPE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DUMP = os.path.join(PIPE, 'dump')
HEROES = ['MatchHero_Male', 'MatchHero_Female', 'GolfKitHero_Male', 'GolfKitHero_Female']


def rm(a):
    return np.array(a, np.float64).reshape(4, 4)        # dumped row-major


def _rd(path, dt, k):
    return np.fromfile(path, dtype=dt).reshape(-1, k) if os.path.exists(path) else None


class Part:
    def __init__(self, d, info):
        self.info = info
        self.tag, self.name, self.kind = info['tag'], info['name'], info['kind']
        f = lambda s, dt, k: _rd(os.path.join(d, f"{self.tag}_{s}"), dt, k)
        self.pos = f('pos.f32', np.float32, 3).astype(np.float64)
        self.nrm = f('nrm.f32', np.float32, 3).astype(np.float64)
        self.tri = f('tri.i32', np.int32, 3)
        self.bi = f('bi.i32', np.int32, 4)
        self.bw = f('bw.f32', np.float32, 4).astype(np.float64)
        self.uv = f('uv.f32', np.float32, 2)
        self.n = len(self.pos)
        self.bones = info['bones']
        self.bind = np.array([rm(b) for b in info['bindposes']])
        self.r2root = rm(info['rendererToRoot'])
        self.subs = info['submeshes']
        self.shape_names = info['blendShapes']
        sh = os.path.join(d, f"{self.tag}_shapes.f32")
        self.shapes = np.fromfile(sh, np.float32).reshape(len(self.shape_names), self.n, 3).astype(np.float64) if self.shape_names else np.zeros((0, self.n, 3))
        self.sub_of_tri = np.zeros(len(self.tri), np.int32)
        for i, s in enumerate(self.subs): self.sub_of_tri[s['start']:s['start'] + s['count']] = i


class Hero:
    def __init__(self, hid, dump=DUMP):
        self.id = hid
        self.dir = os.path.join(dump, hid)
        self.meta = json.load(open(os.path.join(self.dir, 'hero.json')))
        self.female = hid.endswith('Female'); self.golf = hid.startswith('Golf')
        self.bones = self.meta['bones']
        self.bidx = {b: i for i, b in enumerate(self.bones)}
        self.parts = [Part(self.dir, p) for p in self.meta['parts']]
        self.part = {p.tag: p for p in self.parts}
        self.body = self.part['body']
        self.body_src_tri = np.fromfile(os.path.join(self.dir, 'body_src_tri.i32'), np.int32).reshape(-1, 3)
        self.clips = self.meta['clips']
        self.rig = {k: rm(v) for k, v in self.meta['rig'].items()}
        # global bone index of every part's palette
        for p in self.parts: p.gidx = np.array([self.bidx[b] for b in p.bones], np.int64)
        self.nshape = [len(p.shape_names) for p in self.parts]
        self.frame_len = len(self.bones) * 16 + sum(self.nshape)

    def clip_info(self, name):
        return next(c for c in self.clips if c['file'] == name or c['name'] == name)

    def frames(self, clip):
        """-> mats (F, NB, 4, 4) root space, list of per-part shape weights (F, ns)."""
        c = self.clip_info(clip)
        a = np.fromfile(os.path.join(self.dir, 'clips', c['file'] + '.f32'), np.float32).reshape(c['frames'], self.frame_len).astype(np.float64)
        nb = len(self.bones)
        mats = a[:, :nb * 16].reshape(-1, nb, 4, 4)
        out, o = {}, nb * 16
        for p, k in zip(self.parts, self.nshape):
            out[p.tag] = a[:, o:o + k]; o += k
        return mats, out

    def rest_mats(self):
        """bone matrices of the bind pose (body bind poses; every bone the dump knows is in the body palette or derived from it)."""
        nb = len(self.bones); M = np.tile(np.eye(4), (nb, 1, 1))
        seen = np.zeros(nb, bool)
        for p in self.parts:
            for j, g in enumerate(p.gidx):
                if not seen[g]: M[g] = p.r2root @ np.linalg.inv(p.bind[j]); seen[g] = True
        return M


def pose(part, mats, shape_w=None, base=None):
    """part vertices posed by bone matrices (NB,4,4 root space) and blend shape weights (ns,) -> (n,3) root space.
    base overrides the rest positions (e.g. a candidate garment with correctives already added)."""
    v = part.pos if base is None else base
    if shape_w is not None and len(part.shapes):
        nz = np.nonzero(np.abs(shape_w) > 1e-6)[0]
        if len(nz): v = v + np.einsum('s,svk->vk', shape_w[nz] / 100.0, part.shapes[nz])
    skin = mats[part.gidx] @ part.bind                    # (nb,4,4)
    out = np.zeros((len(v), 3))
    for k in range(4):
        m = skin[part.bi[:, k]]
        out += part.bw[:, k:k + 1] * (np.einsum('nij,nj->ni', m[:, :3, :3], v) + m[:, :3, 3])
    return out


def lbs(pos, bi_g, bw, mats, bind_g):
    """generic: weights over GLOBAL bone indices bi_g with bind poses per global bone bind_g (NB,4,4)."""
    skin = mats @ bind_g
    out = np.zeros((len(pos), 3))
    for k in range(bi_g.shape[1]):
        m = skin[bi_g[:, k]]
        out += bw[:, k:k + 1] * (np.einsum('nij,nj->ni', m[:, :3, :3], pos) + m[:, :3, 3])
    return out


def vertex_normals(P, tri):
    fn = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
    vn = np.zeros_like(P)
    for k in range(3): np.add.at(vn, tri[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
