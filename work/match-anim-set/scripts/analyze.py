"""Quick numeric review of a bake (plain python + numpy, no Blender):  analyze.py <male|female> [clip ...]
Reports per clip: seam/pop statistics, ready-blend gaps at start/end, contact speed, finish hold, shortfalls at contact."""
import json, sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
tag = sys.argv[1]
want = sys.argv[2:]
A = np.load(f'{DATA}/anim_{tag}.npz')
B = json.load(open(f'{DATA}/bake_{tag}.json'))
rig = json.load(open(f'{DATA}/rig_{tag}.json'))
names = [b['name'] if isinstance(b, dict) else b for b in rig['bones']] if 'bones' in rig else None
FPS = 30.0

def qang(a, b):
    d = np.abs(np.sum(a * b, axis=-1)).clip(0, 1)
    return np.degrees(2 * np.arccos(d))

R0 = {k: A['ReadyIdle/' + k][0] for k in ('quats', 'hips', 'ankle_L', 'ankle_R', 'sweet', 'rk_origin', 'pelvis')}
for name, c in B['clips'].items():
    if want and name not in want:
        continue
    q = A[name + '/quats']; sw = A[name + '/sweet']; nF = len(q)
    dq = qang(q[1:], q[:-1])               # (nF-1, nbones)
    step = dq.max(axis=1)
    v = np.linalg.norm(np.diff(sw, axis=0), axis=1) * FPS
    ci = None if c['contact_s'] is None else int(round(c['contact_s'] * FPS))
    s0 = qang(q[0], R0['quats']).max(); s1 = qang(q[-1], R0['quats']).max()
    h0 = np.linalg.norm(A[name + '/pelvis'][0] - R0['pelvis']); h1 = np.linalg.norm(A[name + '/pelvis'][-1] - R0['pelvis'])
    f0 = max(np.linalg.norm(A[name + '/ankle_L'][0] - R0['ankle_L']), np.linalg.norm(A[name + '/ankle_R'][0] - R0['ankle_R']))
    f1 = max(np.linalg.norm(A[name + '/ankle_L'][-1] - R0['ankle_L']), np.linalg.norm(A[name + '/ankle_R'][-1] - R0['ankle_R']))
    k0 = np.linalg.norm(sw[0] - R0['sweet']); k1 = np.linalg.norm(sw[-1] - R0['sweet'])
    line = f'{name:15s} n={nF:3d} start[{s0:5.1f}deg hip {h0*100:4.1f}cm foot {f0*100:4.1f}cm head {k0*100:4.1f}cm] end[{s1:5.1f}deg hip {h1*100:4.1f}cm foot {f1*100:4.1f}cm head {k1*100:4.1f}cm]  maxstep {step.max():5.1f}deg@{(step.argmax()+1)/FPS:.2f}'
    if ci is not None:
        i0 = max(ci - 4, 0); i1 = min(ci + 4, len(v))
        vpk = v.max(); vc = v[max(ci - 3, 0):min(ci + 3, len(v))].max()
        # hold: frames after peak where v <= 12% of peak, consecutive
        ipk = int(v.argmax())
        after = v[ipk + 1:]
        run = 0; best = 0
        for x in after:
            if x <= 0.12 * vpk:
                run += 1; best = max(best, run)
            else:
                run = 0
        line += f'\n                  contact f{ci} ({c["contact_s"]:.3f}s) vpk {vpk:4.1f}m/s @ {ipk/FPS:.2f}s  v@contact(+-3f) {vc:4.1f}  hold_run {best}f  Rshort@c {A[name+"/R_short"][ci]*100:.1f}cm Lshort@c {A[name+"/L_short"][ci]*100:.1f}cm shift@c {A[name+"/racket_shift"][ci]*100:.1f}cm'
    rs = A[name + '/R_short'] * 100; ls = A[name + '/L_short'] * 100; rsh = A[name + '/racket_shift'] * 100
    bad = np.where((rs > 1.2) | (ls > 1.2) | (rsh > 2.0))[0]
    if len(bad):
        line += '\n                  shortfall frames: ' + ' '.join(f'{i/FPS:.2f}s(R{rs[i]:.1f}/L{ls[i]:.1f}/sh{rsh[i]:.1f})' for i in bad[:14])
    print(line)
