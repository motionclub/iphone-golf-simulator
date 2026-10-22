"""pure-numpy run of the clip tracker (no Blender):  python3.13(Blender) dev/trk.py <male|female> <Clip> [Clip...]
prints the per-bone / per-frame step table, the orientation error against the authored intent and the arm pop count."""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import numpy as np
import kin, pose as PS, clipkit, clips as CL
DATA = os.path.join(HERE, '..', '..', 'data')
FPS = 30.0

def load(tag):
    rig = kin.Rig(f'{DATA}/rig_{tag}.json')
    racket = json.load(open(f'{DATA}/racket_{tag}.json'))
    hands = json.load(open(f'{DATA}/hands_{tag}.json'))
    return rig, PS.Solver(rig, racket, hands)

def qang(a, b):
    d = np.abs(np.sum(a * b, axis=-1)).clip(0, 1)
    return np.degrees(2 * np.arccos(d))

def run(tag, name, rig=None, solver=None, quiet=False):
    if rig is None:
        rig, solver = load(tag)
    d = CL.build(name, solver)
    clip = clipkit.Clip(d, solver.ready)
    d = clip.d
    t0 = time.time()
    clip.track(solver)
    t1 = time.time()
    frames = clip.frame_times()
    solver.reset()
    N = len(frames)
    quats = np.zeros((N, rig.n, 4)); elb = np.zeros((N, 3)); wr = np.zeros((N, 3)); sweet = np.zeros((N, 3)); att = np.zeros(N)
    shE = np.zeros(N); fcE = np.zeros(N); infos = []
    prev = None
    for i, t in enumerate(frames):
        P = clip.params(t)
        basis, hl, info = solver.solve(P)
        Q, Pos = rig.fk(basis, hl)
        for b in range(rig.n):
            q = kin.mat_to_quat(basis[b])
            if prev is not None and np.dot(q, prev[b]) < 0:
                q = -q
            quats[i, b] = q
        prev = quats[i]
        elb[i] = Pos[rig.idx['RightLowerArm']]; wr[i] = Pos[rig.idx['RightHand']]; sweet[i] = info['sweet']; att[i] = P.get('l_attach', solver.ready['l_attach'])
        try:
            ish, ifc = clip.intent(t)
        except Exception:
            ish, ifc = np.asarray(solver.ready['rk_shaft'], float) / np.linalg.norm(solver.ready['rk_shaft']), np.asarray(solver.ready['rk_face'], float)
        shE[i] = np.degrees(np.arccos(np.clip(np.dot(info['shaft_a'], ish), -1, 1)))
        fcE[i] = np.degrees(np.arccos(np.clip(np.dot(info['face_a'], ifc), -1, 1)))
        infos.append(info)
    t2 = time.time()
    dq = qang(quats[1:], quats[:-1])
    ci = None if d['contact'] is None else int(round(d['contact'] * FPS))
    arm_b = [rig.idx[n] for n in ('RightUpperArm', 'RightLowerArm', 'RightHand', 'LeftUpperArm', 'LeftLowerArm', 'LeftHand')]
    res = dict(name=name, N=N, track_s=t1 - t0, solve_s=t2 - t1, quats=quats, elbow=elb, wrist=wr, sweet=sweet, shE=shE, fcE=fcE, ci=ci, att=att, infos=infos, dq=dq, arm_b=arm_b, clip=clip, d=d)
    if not quiet:
        top = np.argsort(-dq.max(axis=0))[:4]
        names = rig.names
        print(f'{name:15s} N={N:3d} track {t1-t0:4.1f}s  max step: ' + ', '.join(f'{names[b]} {dq[:, b].max():.0f}@{dq[:, b].argmax()/FPS+1/FPS:.2f}' for b in top))
        armstep = dq[:, arm_b]
        cnt90 = int((armstep > 90).sum()); cnt60 = int((armstep > 60).sum())
        del_e = np.linalg.norm(np.diff(elb, axis=0), axis=1) * 100
        print(f'    arm steps >90deg: {cnt90}, >60deg: {cnt60};  elbow move/frame max {del_e.max():.0f}cm @ {del_e.argmax()/FPS+1/FPS:.2f}s;  sweet-spot err shaft/face mean {shE.mean():.0f}/{fcE.mean():.0f} max {shE.max():.0f}/{fcE.max():.0f}')
        if ci is not None:
            sl = slice(max(ci - 1, 0), min(ci + 2, N))
            print(f'    at contact f{ci}: shaft err {shE[sl].round(0)} face err {fcE[sl].round(0)}  shorts R/L {infos[ci]["R_arm_short"]*100:.1f}/{infos[ci]["L_arm_short"]*100:.1f}cm  swing/twist {infos[ci]["R_wrist_swing_deg"]:.0f}/{infos[ci]["R_wrist_twist_deg"]:.0f}')
    return res

if __name__ == '__main__':
    tag = sys.argv[1]
    rig, solver = load(tag)
    for n in sys.argv[2:]:
        run(tag, n, rig, solver)
