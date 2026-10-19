"""GARMENT PIPELINE: the stress pose library. From every clip a hero plays (tennis / golf, plaza + emote moves), the worst frames per
garment region (axilla, shoulder blade, side seam, waist, seat, kneel / lunge, arms crossed, overhead, ...) plus farthest-point coverage
of the whole pose space. Saved as stress/<Hero>/poses.npz: bone matrices + blend shape weights per pose, with clip / frame / reason.
python3 gp/stress.py [hero ...]"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, features as FT

TOPK = int(os.environ.get('GP_STRESS_TOPK', 6))
COVER = int(os.environ.get('GP_STRESS_COVER', 50))
NMS_S = .25
REGIONS = ['axilla_L', 'axilla_R', 'side_seam_L', 'side_seam_R', 'shoulder_blade', 'across_L', 'across_R', 'armback_L', 'armback_R',
           'overhead', 'waist', 'trunk_flex', 'trunk_twist', 'trunk_side', 'seat', 'hipflex_L', 'hipflex_R', 'hipabd_L', 'hipabd_R',
           'knee_L', 'knee_R', 'kneel', 'lunge', 'elbow_L', 'elbow_R']


def build(hid):
    h = rig.Hero(hid)
    rest = h.rest_mats()
    rows, mats_all, sw_all, vec, sc = [], [], {p.tag: [] for p in h.parts}, [], {}
    for c in h.clips:
        mats, sw = h.frames(c['file'])
        for f in range(len(mats)): rows.append((c['file'], f, f / max(1, len(mats) - 1) * c['length']))
        mats_all.append(mats)
        for k in sw_all: sw_all[k].append(sw[k])
        vec.append(FT.vector(h, mats, rest))
        for k, v in FT.region_scores(h, mats, rest).items(): sc.setdefault(k, []).append(v)
    mats_all = np.concatenate(mats_all); vec = np.concatenate(vec)
    sc = {k: np.concatenate(v) for k, v in sc.items()}
    chosen, why = [], {}

    def take(i, reason):
        c, f, t = rows[i]
        for j in chosen:
            if rows[j][0] == c and abs(rows[j][2] - t) < NMS_S:
                why[j].append(reason); return False
        chosen.append(i); why[i] = [reason]; return True
    for r in REGIONS:
        order = np.argsort(-sc[r]); n = 0
        for i in order:
            if n >= TOPK: break
            n += take(int(i), r)
    # farthest point coverage of the pose space (from the rest-like first pick)
    d = np.full(len(vec), np.inf)
    for j in chosen: d = np.minimum(d, np.linalg.norm(vec - vec[j], axis=1))
    for _ in range(COVER):
        i = int(np.argmax(d)); take(i, 'coverage'); d = np.minimum(d, np.linalg.norm(vec - vec[i], axis=1))
    chosen = sorted(chosen)
    out = os.path.join(rig.PIPE, 'stress', hid); os.makedirs(out, exist_ok=True)
    np.savez_compressed(os.path.join(out, 'poses.npz'), mats=mats_all[chosen].astype(np.float32), vec=vec[chosen],
                        **{'sw_' + k: np.concatenate(v)[chosen].astype(np.float32) for k, v in sw_all.items()})
    meta = [{'i': n, 'clip': rows[i][0], 'frame': rows[i][1], 'time': round(rows[i][2], 3), 'why': why[i],
             'scores': {r: round(float(sc[r][i]), 1) for r in REGIONS}} for n, i in enumerate(chosen)]
    json.dump({'hero': hid, 'frames_total': len(rows), 'poses': meta}, open(os.path.join(out, 'poses.json'), 'w'), indent=1)
    np.savez_compressed(os.path.join(out, 'all_features.npz'), vec=vec, **{'s_' + k: v for k, v in sc.items()},
                        clip=np.array([r[0] for r in rows]), frame=np.array([r[1] for r in rows]))
    print(hid, 'frames', len(rows), 'stress poses', len(chosen),
          'max: axilla %.0f overhead %.0f seat %.0f knee %.0f waist %.0f' % (sc['axilla_L'].max(), sc['overhead'].max(), sc['seat'].max(), sc['kneel'].max(), sc['waist'].max()))


class Library:
    def __init__(self, hid):
        d = os.path.join(rig.PIPE, 'stress', hid)
        z = np.load(os.path.join(d, 'poses.npz'))
        self.mats = z['mats'].astype(np.float64); self.vec = z['vec']
        self.sw = {k[3:]: z[k].astype(np.float64) for k in z.files if k.startswith('sw_')}
        self.meta = json.load(open(os.path.join(d, 'poses.json')))['poses']

    def __len__(self): return len(self.mats)

    def shape_w(self, i, tags=('body',)):
        return {t: self.sw[t][i] for t in tags if t in self.sw}


if __name__ == '__main__':
    for hid in (sys.argv[1:] or rig.HEROES): build(hid)
