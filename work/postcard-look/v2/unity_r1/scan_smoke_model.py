import sys, os, importlib.util, numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sp_ = importlib.util.spec_from_file_location("glt", REPO + "/blender/scripts/golf_look_textures.py")
g = importlib.util.module_from_spec(sp_); sys.modules["glt"] = g; sp_.loader.exec_module(g)
import bpy
img = bpy.data.images.load(REPO + "/Unity/Assets/Resources/Course/Look/Smoke_C.png"); w, h = img.size
arr = np.array(img.pixels[:]).reshape(h, w, 4)
S = np.round(arr * 255).astype(np.uint8)   # image_stats order: row 0 bottom; the model uses the same orientation as the generator? (only colour/alpha stats matter)
base = g.smoke_spec()
for tint, lit, sl in [((1,1,1),.5,.55), ((1,1,1),.5,.45), ((1,1,1),.5,.40), ((1,1,1),.6,.45), ((1,1,1),.6,.40), ((1,.97,.95),.5,.45), ((1,.97,.95),.6,.45), ((1,.95,.92),.8,.4), ((1,.97,.95),.5,.5), ((1,1,1),.4,.5), ((1,1,1),.4,.45)]:
    sp = dict(base, tint=tint + (1.0,), lit=lit, selflight=sl)
    st = g.smoke_game(S, sp)
    own = tuple(int(x) for x in st['own'])
    ok = all(abs(own[i] - g.SMOKE_STILL[i]) <= 14 for i in range(3)) and st['own_hsv'][1] <= .26 and st['med'] >= 10 and 32 <= st['p99'] <= 86 and st['grad'] <= 5
    print(f"MODEL tint {tint} lit {lit} self {sl}: own {own} S {st['own_hsv'][1]:.2f} med {st['med']:.1f} p99 {st['p99']:.1f} grad {st['grad']:.2f} top {tuple(int(x) for x in st['top'])} {'PASS' if ok else 'FAIL'}")
