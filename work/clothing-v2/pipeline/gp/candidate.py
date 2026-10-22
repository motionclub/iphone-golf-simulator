"""GARMENT PIPELINE: a fitted garment (or a new body cover) as one npz, root space.
  <Piece>.npz: tag, kind, P (n,3) rest root space, tri, bi (n,4) GLOBAL bone ids (hero.bones), bw (n,4), sub (per triangle submesh),
               shapes (S,n,3) root-space corrective deltas, shape_names, corr_anchor_f (A,K) features, corr_anchor_w (A,S) targets,
               corr_sigma, corr_coef (A,S) RBF coefficients (see correctives.py)
  body.npz:    drawn (per source-body triangle) = the new cover
Correctives are driven by features.vector (same code in KitV2PoseCorrectives.cs)."""
import os
import numpy as np
import scene, features as FT


class RBF:
    def __init__(self, anchors, coef, sigma, lin=None):
        self.A, self.C, self.s, self.lin = anchors, coef, sigma, lin

    def __call__(self, f):
        d2 = ((self.A - f[None]) ** 2).sum(1)
        phi = np.exp(-d2 / (2 * self.s * self.s))
        w = phi @ self.C
        return np.clip(w, 0, 1)


def load_one(path, hero):
    """one candidate npz (any file name)."""
    import tempfile, shutil
    tmpd = tempfile.mkdtemp(); shutil.copy(path, os.path.join(tmpd, 'one.npz'))
    out = load_dir(tmpd, hero); shutil.rmtree(tmpd)
    return out


def load_dir(d, hero):
    out = {}
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.npz') or fn.startswith('_'): continue
        z = np.load(os.path.join(d, fn), allow_pickle=False)
        tag = str(z['tag'])
        if tag == 'body':
            base = scene.items_from_dump(hero, include=[])[0]
            base.drawn = z['drawn'].astype(bool)
            out['body'] = base; continue
        it = scene.Item(tag, str(z['kind']), z['P'], z['tri'], z['bi'], z['bw'],
                        z['shapes'] if 'shapes' in z.files and len(z['shapes']) else None,
                        list(z['shape_names']) if 'shape_names' in z.files else [], sub=z['sub'] if 'sub' in z.files else None)
        if 'corr_anchor_f' in z.files and len(z['corr_anchor_f']):
            it.corr = RBF(z['corr_anchor_f'], z['corr_coef'], float(z['corr_sigma']))
        out[tag] = it
    return out


def shape_weights(items, recorded, mats, hero, rig_):
    """blend shape weights per item tag for this pose: corrective model if the item has one, else the recorded runtime weights."""
    out = dict(recorded)
    f = None
    for it in items:
        if it.corr is not None:
            if f is None: f = FT.vector(hero, mats[None], rig_.rest)[0]
            out[it.tag] = 100.0 * it.corr(f)
        elif it.gidx is None:
            out[it.tag] = None
    return out


def save(path, item, **extra):
    np.savez(path, tag=item.tag, kind=item.kind, P=item.P, tri=item.tri, bi=item.bi, bw=item.bw, sub=item.sub,
             shapes=item.shapes, shape_names=np.array(item.shape_names, dtype='U32'), **extra)
