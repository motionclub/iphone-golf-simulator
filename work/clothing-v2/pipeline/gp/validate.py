import sys, os, glob, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import rig
for hid in rig.HEROES:
    h = rig.Hero(hid)
    print(hid, [(p.tag, p.n, len(p.shape_names), p.kind) for p in h.parts])
    errs = {}
    for f in sorted(glob.glob(os.path.join(h.dir, 'check', '*.f32'))):
        b = os.path.basename(f)[:-4]
        for p in h.parts:
            if b.endswith('_' + p.tag):
                clip, fi = b[:-len(p.tag) - 1].rsplit('_', 1); break
        mats, sw = h.frames(clip)
        P = rig.pose(p, mats[int(fi)], sw[p.tag][int(fi)])
        ref = np.fromfile(f, np.float32).reshape(-1, 3)
        errs.setdefault(p.tag, []).append(np.abs(P - ref).max() * 1000)
    print('  max err mm', {k: round(max(v), 4) for k, v in errs.items()})
    print('  clips', len(h.clips), 'frames', sum(c['frames'] for c in h.clips), [c['file'] for c in h.clips][:50])
