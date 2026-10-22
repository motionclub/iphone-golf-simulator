"""probe_clear.py <male|female> <clip> <spec> : per-frame body-clearance report (violation before / after, how far the arm was moved) + time per frame."""
import sys, os, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
a_ = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
tag, clip = a_[0], a_[1]
spec = a_[2] if len(a_) > 2 else 'every:3'
H = EH.EmoHero(tag)
t0 = time.time()
C = EC.build(clip, H)
print('build %.1fs' % (time.time() - t0))
nF = int(round(C.length * 30)) + 1
frames = list(range(0, nF, int(spec[6:]))) if spec.startswith('every:') else [int(round(float(x) * 30)) for x in spec.split(',')]
t0 = time.time()
for f in frames:
    d = C.solve(f / 30.0)
    r = d['clear']
    txt = ' | '.join('%s v %.3f->%.3f mv %.3f sw %5.1f it %d st %d x=%s' % (x['side'], x['viol0'], x['viol1'], x['moved'], x['swing'], x['iters'], x.get('starts', 0), x.get('x')) for x in r if x['iters'] > 0 or x['viol0'] > 0)
    print('f%3d t=%.2f short R %.3f L %.3f  %s' % (f, f / 30.0, d['info']['R_arm_short'], d['info']['L_arm_short'], txt))
print('per frame %.2fs' % ((time.time() - t0) / len(frames)))
