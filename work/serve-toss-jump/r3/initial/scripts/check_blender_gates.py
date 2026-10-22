"""check_blender_gates.py : gates 4, 5, 6 of GATE_DEFS_preregistered.md (system python + numpy).  Writes data/blender_gates.json, prints one line per gate."""
import json
import numpy as np
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump'
MA = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set'
ARM = ('Shoulder', 'UpperArm', 'LowerArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Little')
out = {}; ok_all = True
def ang(a, b): return np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(a * b, axis=-1)), 0, 1)))
for tag in ('male', 'female'):
    names = [b['name'] for b in json.load(open(f'{MA}/data/rig_{tag}.json'))['bones']]
    A = np.load(f'{W}/before/gen_serve_{tag}.npz', allow_pickle=True); B = np.load(f'{W}/data/gen_serve_{tag}.npz', allow_pickle=True)
    d = ang(A['quats'], B['quats'])                                        # (frames, bones)
    isarm = np.array([any(k in n for k in ARM) for n in names]); isroot = np.array([n == 'Root' for n in names])
    nonarm_max = float(d[:, ~isarm & ~isroot].max()); hips = float(np.abs(A['hips'] - B['hips']).max())
    f_in = float(d[:7].max()), float(d[46:].max())
    g4 = nonarm_max <= 0.05 and hips <= 1e-6 and f_in[0] <= 0.05 and f_in[1] <= 0.05
    # gate 5
    m = json.load(open(f'{W}/data/measure_final_{tag}.json'))
    tip = [float(np.linalg.norm(np.array(m[i]['rk_tip']) - np.array(m[i - 1]['rk_tip'])) * 1000) for i in range(1, 42)]
    q = B['quats']; st = ang(q[1:], q[:-1])                                  # step k = frame k -> k+1
    armb = [i for i, n in enumerate(names) if any(k in n for k in ('UpperArm', 'LowerArm', 'Hand')) and not any(k in n for k in ('Shoulder', 'Thumb', 'Index', 'Middle', 'Ring', 'Little'))]
    armstep = float(st[:41][:, armb].max())
    g5 = max(tip) <= 300 and armstep <= 60
    # gate 6
    pen = json.load(open(f'{W}/data/pen_final_{tag}.json'))
    inside = [(r['f'], r['inside'], round(r['depth_mm'], 1)) for r in pen if 7 <= r['f'] <= 71 and r['inside']]
    g6 = not inside
    out[tag] = dict(g4=g4, nonarm_max_deg=nonarm_max, hips_loc_max_m=hips, frames0_6_max_deg=f_in[0], frames46_75_max_deg=f_in[1],
                    g5=g5, tip_step_max_mm=max(tip), tip_step_at=int(np.argmax(tip)) + 1, arm_step_max_deg=armstep, g6=g6, racket_inside=inside)
    ok_all &= g4 and g5 and g6
    print(f'{tag}: G4 {"PASS" if g4 else "FAIL"} (non-arm bones max {nonarm_max:.4f} deg, hips {hips:.1e} m, frames 0-6 {f_in[0]:.4f}, frames 46-75 {f_in[1]:.4f})')
    print(f'{tag}: G5 {"PASS" if g5 else "FAIL"} (tip step max {max(tip):.0f} mm at frame {int(np.argmax(tip)) + 1}; arm bone step max {armstep:.1f} deg, frames 0-41)')
    print(f'{tag}: G6 {"PASS" if g6 else "FAIL"} (racket inside body, frames 7-71: {inside})')
json.dump(out, open(f'{W}/data/blender_gates.json', 'w'), indent=1)
print('BLENDER GATES', 'PASS' if ok_all else 'FAIL')
