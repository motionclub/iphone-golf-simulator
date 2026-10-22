import json, subprocess, sys
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
S = R + "/work/postcard-look/v2/hole10"
TEE_CAM, APP_CAM, RIM_CAM = [-0.87, -4.02], [93.82, 145.52], [64.01, 98.76]
base = [dict(cam=TEE_CAM, p=[20, 300, 0], wh=[120, 100], n=3, seed=1), dict(cam=APP_CAM, p=[305, 118, 0], wh=[80, 70], n=3, seed=2),
        dict(cam=RIM_CAM, p=[300, 330, 30], wh=[130, 110], n=3, seed=3), dict(cam=TEE_CAM, p=[150, 435, 95], wh=[110, 120], n=3, seed=4)]
trials = {"t5a": base + [dict(cam=TEE_CAM, p=[88, 385, 25], wh=[90, 130], n=3, seed=5)],
          "t5b": base + [dict(cam=TEE_CAM, p=[100, 400, 35], wh=[80, 140], n=3, seed=5, spread=0.06)],
          "t5c": base + [dict(cam=TEE_CAM, p=[75, 360, 20], wh=[100, 140], n=3, seed=5, spread=0.08)]}
for k, spec in trials.items():
    json.dump(spec, open(f"{S}/repair_r2/smoke/{k}.json", "w"))
    subprocess.run(["python3", f"{S}/repair_r1/mk_cards.py", f"{S}/repair_r2/smoke/{k}.json", f"{S}/repair_r2/smoke/cards_{k}.json"], capture_output=True)
    r = subprocess.run(["/Applications/Blender.app/Contents/MacOS/Blender", "-b", f"{S}/stage/hole_10.blend", "--python", f"{S}/repair_r1/smoke_probe.py", "--", "--cards", f"{S}/repair_r2/smoke/cards_{k}.json", "--out", f"{S}/repair_r2/smoke/o_{k}"], capture_output=True, text=True)
    print(k, [l for l in r.stdout.splitlines() if l.startswith("SMOKE")])
