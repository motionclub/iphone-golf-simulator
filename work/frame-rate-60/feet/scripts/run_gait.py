"""Generate a locomotion clip with numpy only:  python3.13 run_gait.py <walk|runf|runr|runl> <male|female>  -> data/gen_<clip>_<hero>.npz"""
import sys, json, time, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet/scripts')
import loco, gait
clip, tag = sys.argv[1], sys.argv[2]
t0 = time.time()
hero = loco.Hero(tag)
gen = dict(walk=gait.walk, runf=gait.runf, runr=gait.runr, runl=gait.runl)[clip]
Ps, tgt, meta = gen(hero)
hs = loco.calibrate(hero, Ps, tgt, verbose=True)
quats, hips, infos, bases = loco.solve_frames(hero, Ps)
N = len(Ps)
# close the loop: frame N == frame 0
quats = np.concatenate([quats, quats[:1]]); hips = np.concatenate([hips, hips[:1]])
# diagnostics
kf = np.array([[i['lf_knee_flex_deg'], i['rf_knee_flex_deg']] for i in infos])
drop = np.array([i.get('pelvis_auto_drop', 0.0) for i in infos])
short = np.array([[i['lf_short'], i['rf_short'], i.get('R_arm_short', 0), i.get('L_arm_short', 0)] for i in infos])
wr = np.array([[i.get('R_wrist_swing_deg', 0), i.get('R_wrist_clamp_deg', 0), i.get('L_wrist_swing_deg', 0)] for i in infos])
step = np.array([np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(quats[k + 1] * quats[k], axis=1)), 0, 1))).max() for k in range(N)])
print(clip, tag, 'frames', N, 'cycle', meta['cycle_s'], 'time %.1fs' % (time.time() - t0))
print(' knee flex L min/max', kf[:, 0].min().round(1), kf[:, 0].max().round(1), ' R', kf[:, 1].min().round(1), kf[:, 1].max().round(1))
print(' pelvis auto drop max mm', (drop.max() * 1000).round(1), ' leg short max mm', (short[:, :2].max() * 1000).round(2), ' arm short max mm', (short[:, 2:].max() * 1000).round(2))
print(' R wrist swing max', wr[:, 0].max().round(1), 'clamp max', wr[:, 1].max().round(1), ' L wrist swing max', wr[:, 2].max().round(1))
print(' max bone step deg per frame', step.max().round(1), 'at', int(step.argmax()))
print(' foot heights mm  L peak', (hs[:, 0].max() * 1000).round(1), ' R peak', (hs[:, 1].max() * 1000).round(1), ' planted frames L/R', int((hs[:, 0] < 0.010).sum()), int((hs[:, 1] < 0.010).sum()))
np.savez_compressed(f'{loco.DATA}/gen_{clip}_{tag}.npz', quats=quats, hips=hips, heights=hs, knee=kf, meta=json.dumps(meta))
