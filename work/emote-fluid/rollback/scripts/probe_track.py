"""probe_track.py <male|female> <clip> : compute the clearance track and print the correction of every frame that has one (python of Blender)."""
import sys, os, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
a_ = sys.argv[sys.argv.index('--') + 1:]
tag, clip = a_[0], a_[1]
H = EH.EmoHero(tag)
C = EC.build(clip, H)
t0 = time.time()
xs = C.clearance_track()
print('track %s %s: %d frames, %.1fs' % (clip, tag, len(xs), time.time() - t0))
n = 0
for f in range(len(xs)):
    L, R = xs[f, 0], xs[f, 1]
    if np.any(L) or np.any(R):
        n += 1
        print('f%3d t=%.2f  L mv %.3f sw %5.1f x=%s | R mv %.3f sw %5.1f x=%s' % (f, f / 30.0, np.linalg.norm(L[:3]), np.degrees(L[3]), np.round(L[:3], 3), np.linalg.norm(R[:3]), np.degrees(R[3]), np.round(R[:3], 3)))
print('frames with a correction:', n, 'of', len(xs), ' max |dw| L %.3f R %.3f' % (max(np.linalg.norm(xs[:, 0, :3], axis=1)), max(np.linalg.norm(xs[:, 1, :3], axis=1))))

if os.environ.get('SHOW_REPORTS'):
    lo, hi = [int(v) for v in os.environ['SHOW_REPORTS'].split('-')]
    for f, reps in C.track_reports:
        if lo <= f <= hi:
            for r in reps:
                print('  rep f%d %s v0 %s n0 %s ncands %s x %s' % (f, r['side'], r.get('viol0'), r.get('n0'), r.get('n_cands'), r.get('x')))
