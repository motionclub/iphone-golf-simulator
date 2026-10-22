#!/usr/bin/env python3
"""Calibration round 2: T's GolfLava shader model (golf_look_textures.lava_shader_metrics) on the installed Lava_C/E/N for candidate ramp / bias / gain, next to the
quantities the Game-view gates read (V<.4 share, in-band share). usage: Blender's python3.13 lava_ramp_model.py"""
import sys, os, numpy as np, colorsys
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import golf_look_textures as T
C, E, N = (T.read_png(f"{R}/Unity/Assets/Resources/Course/Look/{n}.png") for n in ("Lava_C", "Lava_E", "Lava_N"))
sp0 = T.lava_spec()
def run(tag, deep, crust, bias, gain, hot=None):
    sp = dict(sp0); ramp = list(sp0['ramp']); ramp[0] = deep; ramp[1] = crust
    if hot: ramp[3] = hot
    sp['ramp'] = ramp
    m = T.lava_shader_metrics(C, E, N, sp, bias, gain)
    f = m['rgb'].reshape(-1, 3)
    mx = f.max(1) / 255
    v04 = float((mx < .40).mean())
    print(f"{tag:46s} hd {m['hd']:.3f} dark(V<.7) {m['dark']*100:5.1f}% V<.4 {v04*100:4.1f}% hot {m['hot']*100:4.1f}% flow {m['share_flow']*100:5.1f}% medheat {m['med_heat']:.2f} p50 ({int(m['p50'][0])},{int(m['p50'][1])},{int(m['p50'][2])}) hue {m['hue']:.1f} in-band {m['in_band']*100:5.1f}%")
print("spec", sp0['src'], sp0['HeatBias'], sp0['ramp'])
run("A  now (deep150, crust186, bias-.15)", (150, 33, 10), (186, 43, 13), -.15, 1.4)
run("C  deep60 crust186 bias-.15", (60, 13, 5), (186, 43, 13), -.15, 1.4)
run("D  deep60 crust186 bias-.20", (60, 13, 5), (186, 43, 13), -.20, 1.4)
for deep in [(60, 13, 5), (30, 7, 3), (12, 4, 2)]:
    for crust in [(198, 46, 14), (204, 48, 15), (210, 52, 16)]:
        for bias, gain in [(-.15, 1.4), (-.15, 1.7), (-.12, 1.7), (-.12, 2.0)]:
            run(f"deep{deep} crust{crust} b{bias} g{gain}", deep, crust, bias, gain)
