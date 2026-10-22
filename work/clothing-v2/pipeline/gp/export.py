"""GARMENT PIPELINE: candidate npz -> the files GarmentPipelineInstall.cs reads (body mesh space, the hero's bone names).
python3 gp/export.py <hero> <run_dir> [<Tag> ...]     -> out/<hero>/<Tag>.gp.json + <Tag>.gp.bin + <Tag>_correctives.json
gp.bin: int32 bone index (n,4) into `bones`, float32 weight (n,4), float32 shape position deltas (S,n,3), float32 rest positions (n,3)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rig

OUT = os.environ.get('GP_OUT_DIR') or os.environ.get('GP_OUT') or os.path.join(rig.PIPE, 'out')        # GP_OUT_DIR / GP_OUT: a private install source dir per chat


def export(h, cand_path, out_dir):
    z = np.load(cand_path, allow_pickle=False)
    tag = str(z['tag'])
    body = h.body
    Minv = np.linalg.inv(body.r2root)
    P = z['P'] @ Minv[:3, :3].T + Minv[:3, 3]
    shapes = np.einsum('svk,jk->svj', z['shapes'], Minv[:3, :3]) if len(z['shapes']) else np.zeros((0, len(P), 3))
    bi, bw = z['bi'], z['bw']
    gl = body.gidx[bi]                                     # global bone ids
    used = np.unique(gl[bw > 0])
    remap = -np.ones(len(h.bones), np.int64); remap[used] = np.arange(len(used))
    bl = np.where(bw > 0, remap[gl], 0).astype(np.int32)
    pal = {g: j for j, g in enumerate(body.gidx)}
    binds = [body.bind[pal[g]] for g in used]
    names = [h.bones[g] for g in used]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, tag + '.gp.bin'), 'wb') as f:
        f.write(bl.astype(np.int32).tobytes()); f.write(bw.astype(np.float32).tobytes())
        f.write(shapes.astype(np.float32).tobytes()); f.write(P.astype(np.float32).tobytes())
    shape_names = [str(s) for s in z['shape_names']]
    json.dump({'tag': tag, 'vertexCount': int(len(P)), 'bones': names,
               'bindposes': [float(v) for b in binds for v in b.T.reshape(-1)],     # column-major like Unity's Matrix4x4[k]
               'shapes': shape_names}, open(os.path.join(out_dir, tag + '.gp.json'), 'w'))
    if len(shape_names):
        A = z['corr_anchor_f']; C = z['corr_coef']
        json.dump({'featureMode': 'gp-rbf', 'shapes': shape_names, 'anchorCount': int(len(A)), 'featureCount': int(A.shape[1]),
                   'sigma': float(z['corr_sigma']), 'anchors': [float(x) for x in A.reshape(-1)], 'coef': [float(x) for x in C.reshape(-1)]},
                  open(os.path.join(out_dir, tag + '_correctives.json'), 'w'))
    elif os.path.exists(os.path.join(out_dir, tag + '_correctives.json')):
        os.remove(os.path.join(out_dir, tag + '_correctives.json'))
    print('EXPORT %s %s: %d verts, %d bones, %d shapes' % (h.id, tag, len(P), len(names), len(shape_names)))


if __name__ == '__main__':
    hid, run = sys.argv[1], sys.argv[2]
    h = rig.Hero(hid)
    d = os.path.join(run, hid)
    tags = sys.argv[3:] or [f[:-4] for f in sorted(os.listdir(d)) if f.endswith('.npz') and f != 'body.npz' and not f.startswith('_')]
    for t in tags: export(h, os.path.join(d, t + '.npz'), os.path.join(OUT, hid))
