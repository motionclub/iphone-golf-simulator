#!/usr/bin/env python3
"""Calibration round 2: search the LK_LAVA ramp (RampDeep, RampCrust) / HeatBias / HeatGain for the setting that passes ALL of T's lava model gates (LAVA_FLOW_BRIGHT,
LAVA_NOT_CELLS, ...) and has the most near-black crust (V<.4). Uses T's own lava_gates() with lava_spec() monkeypatched. Blender's python3.13."""
import sys, io, contextlib, numpy as np
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import golf_look_textures as T
C, E, N = (T.read_png(f"{R}/Unity/Assets/Resources/Course/Look/{n}.png") for n in ("Lava_C", "Lava_E", "Lava_N"))
imgs = {"Lava_C.png": C, "Lava_E.png": E, "Lava_N.png": N}
base = T.lava_spec()
def trial(deep, crust, bias, gain):
    sp = dict(base); r = list(base['ramp']); r[0] = deep; r[1] = crust; sp['ramp'] = r; sp['HeatBias'] = bias; sp['HeatGain'] = gain
    T.lava_spec = lambda: sp
    res = []
    with contextlib.redirect_stdout(io.StringIO()):
        T.lava_gates(imgs, lambda name, ok, detail: res.append((name.split(' ')[0], ok, detail)))
    m = T.lava_shader_metrics(C, E, N, sp)
    v04 = float((m['rgb'].reshape(-1, 3).max(1) / 255 < .40).mean())
    return res, m, v04
rows = []
for deep in [(60, 13, 5), (24, 6, 3)]:
    for crust in [(198, 46, 14), (204, 48, 15), (210, 52, 16), (216, 55, 17)]:
        for bias in [-.15, -.16, -.17, -.18]:
            for gain in [1.4, 1.5, 1.6]:
                res, m, v04 = trial(deep, crust, bias, gain)
                ok = all(r[1] for r in res)
                rows.append((ok, v04, deep, crust, bias, gain, m, [r[0] for r in res if not r[1]]))
rows.sort(key=lambda r: (not r[0], -r[1]))
for ok, v04, deep, crust, bias, gain, m, bad in rows[:25]:
    print(f"{'ALL-PASS' if ok else 'fail:'+','.join(bad):28s} V<.4 {v04*100:4.1f}% dark {m['dark']*100:4.1f}% hot {m['hot']*100:4.1f}% flow {m['share_flow']*100:5.1f}% in-band {m['in_band']*100:5.1f}% medheat {m['med_heat']:.2f} p50 {tuple(int(x) for x in m['p50'])}  deep{deep} crust{crust} bias {bias} gain {gain}")
print("n all-pass:", sum(1 for r in rows if r[0]), "of", len(rows))
