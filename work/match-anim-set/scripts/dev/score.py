"""dev/score.py <hero> [scripts_dir]  : one-line-per-clip quality table (contact error, shifts, pops, orientation error). numpy only."""
import sys, os, importlib, numpy as np
here = os.path.dirname(os.path.abspath(__file__))
sdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, '..')
sys.path.insert(0, os.path.join(sdir, 'dev') if os.path.exists(os.path.join(sdir, 'dev', 'trk.py')) else here)
sys.path.insert(0, sdir)
import trk
tag = sys.argv[1]
only = sys.argv[3:] if len(sys.argv) > 3 else None
rig, solver = trk.load(tag)
FPS = 30.0
import clipkit
if os.environ.get('SPH'): clipkit.Clip.SPH_RMIN['rk_pos'] = float(os.environ['SPH'])
if os.environ.get('SPHL'): clipkit.Clip.SPH_RMIN['l_hand'] = float(os.environ['SPHL'])
if os.environ.get('MINW'): solver.min_wrist_r = float(os.environ['MINW']) * solver.A_arm
if os.environ.get('LAM'): clipkit.Clip.TRK_LAM = float(os.environ['LAM'])
if os.environ.get('ANCH'): clipkit.Clip.TRK_ANCHOR = bool(int(os.environ['ANCH']))
print('variant', {k: os.environ.get(k) for k in ('SPH', 'SPHL', 'MINW', 'LAM', 'ANCH')})
rows = []
for n in trk.CL.BUILDERS.keys():
    if only and n not in only: continue
    r = trk.run(tag, n, rig, solver, quiet=True)
    inf = r['infos']; dq = r['dq']; arm = dq[:, r['arm_b']]
    ci = r['ci']
    shift = max(i.get('racket_shift', 0) for i in inf) * 100
    short = max(max(i.get('R_arm_short', 0), i.get('L_arm_short', 0)) for i in inf) * 100
    ce = (r['shE'][ci] + r['fcE'][ci]) / 2 if ci is not None else float('nan')
    clamp = max(i.get('R_wrist_clamp_deg', 0) for i in inf)
    rows.append((n, ce, r['shE'][ci] if ci is not None else float('nan'), r['fcE'][ci] if ci is not None else float('nan'), r['shE'].mean(), r['fcE'].mean(), shift, short, int((arm > 90).sum()), int((arm > 60).sum()), clamp, r['track_s']))
print('%-15s %6s %5s %5s | %5s %5s | %6s %6s | %4s %4s | %5s %4s' % ('clip', 'cErr', 'cSh', 'cFc', 'mSh', 'mFc', 'shift', 'short', '>90', '>60', 'clamp', 's'))
for r in rows:
    print('%-15s %6.0f %5.0f %5.0f | %5.0f %5.0f | %6.1f %6.1f | %4d %4d | %5.0f %4.1f' % r)
a = np.array([[x for x in r[1:]] for r in rows], float)
print('%-15s %6.0f %5.0f %5.0f | %5.0f %5.0f | %6.1f %6.1f | %4d %4d | %5.0f' % (('MEAN/SUM',) + tuple(np.nanmean(a[:, :6], axis=0)) + (a[:, 6].max(), a[:, 7].max(), a[:, 8].sum(), a[:, 9].sum(), a[:, 10].max())))
