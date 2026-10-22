#!/usr/bin/env python3
"""Assemble the calibration evidence: calibration_stats.json (gate lines + the numbers) and the Game-view sheets, from the final runs.
usage: assemble.py   (run from anywhere; paths are fixed to this job)"""
import json, os, re, sys, colorsys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from img_stats import stats

R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
C = R + "/work/postcard-look/v2/calibrate"
SMOKE = R + "/work/postcard-look/v2/runtime/smoke_k5.txt"
SHOTS = R + "/work/postcard-look/v2/runtime/shots/k5"
REFS = R + "/ArtDir/environments/refs"
STILLS = C + "/stills_board_final"
PROBE = C + "/probe_p4"

def parse_gates(path):
    gates, info = [], []
    for ln in open(path, encoding="utf-8"):
        ln = ln.rstrip("\n")
        m = re.match(r"GATE: (.*?) (PASS|FAIL) - (.*)", ln)
        if m: gates.append({"id": m.group(1), "pass": m.group(2) == "PASS", "detail": m.group(3)})
        elif ln.startswith("INFO:"): info.append(ln)
    return gates, info

def font(sz):
    for f in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()

def panel(im, w, h, label):
    im = im.convert("RGB"); im = im.resize((w, h))
    d = ImageDraw.Draw(im); f = font(max(11, w // 22))
    d.rectangle([0, 0, w, f.size + 6], fill=(0, 0, 0)); d.text((4, 2), label, fill=(255, 255, 255), font=f)
    return im

def sheet(rows, path, w=300):
    """rows: list of rows, each a list of (image path or PIL image, crop box or None, label)"""
    ph = int(w * 16 / 9 * 0.0 + w * 0.8)
    cells = []
    for row in rows:
        r = []
        for src, box, label in row:
            im = Image.open(src) if isinstance(src, str) else src
            if box: im = im.crop(box)
            r.append(panel(im, w, int(w * im.size[1] / im.size[0]), label))
        cells.append(r)
    H = sum(max(c.size[1] for c in r) for r in cells); W = max(sum(c.size[0] for c in r) for r in cells)
    out = Image.new("RGB", (W, H), (20, 20, 20)); y = 0
    for r in cells:
        x = 0
        for c in r: out.paste(c, (x, y)); x += c.size[0]
        y += max(c.size[1] for c in r)
    out.save(path, quality=88)

gates, info = parse_gates(SMOKE)
keep = [g for g in gates if re.match(r"(GRASS_|SURFACES_|SHELF_|OCEAN_|SEA_|LAVA_GAMEVIEW|BASALT_JOINT|BASALT_RENDERS|SMOKE_SOFT|URP_BOTH|NO_POST|LAVA_ORANGE|LAVA_LIGHTS)", g["id"])]
out = {"smoke": SMOKE.replace(R + "/", ""), "summary": [l for l in open(SMOKE) if l.startswith("SUMMARY")][0].strip(), "calibration_gates": keep, "info": [i for i in info if re.match(r"INFO: (GRASS|SEA|SMOKE|CRATER|BASALT)", i)]}

# real-geometry probe numbers (G's smoke FBX through HoleView.BuildFromModel), central lower third + whole lower 60 %
probe = {}
for n in ["hole08_tee_probe", "hole08_green_probe", "hole08_arch_probe", "hole09_tee_probe", "hole09_green_probe", "hole09_ridge_probe", "hole10_tee_probe", "hole10_green_probe", "hole10_lavaedge_probe"]:
    c = stats(f"{PROBE}/{n}.jpg", (300, 1067, 600, 1600)); w = stats(f"{PROBE}/{n}.jpg", (0, 640, 900, 1600))
    probe[n] = {"central_lower_third": {k: c[k] for k in ("mean_rgb", "hue", "S", "V", "clip250_pct")}, "lower60_clip250_pct": w["clip250_pct"], "lower60_clip255_pct": w["clip255_pct"]}
out["probe_real_geometry_grass"] = probe
sj = C + "/stills_board_final/stills_stats.json"
if os.path.exists(sj): out["stills_board_final"] = json.load(open(sj))
# stills board: fairway strip (between the horizon band and the ball)
strip = {}
for n, box in [("hole08_tee", (300, 480, 600, 930)), ("hole09_tee", (300, 420, 600, 930)), ("hole10_tee", (300, 480, 600, 930))]:
    p = f"{STILLS}/{n}.png"
    if os.path.exists(p): strip[n] = stats(p, box)
out["stills_board_fairway_strip"] = strip
json.dump(out, open(C + "/calibration_stats.json", "w"), indent=1)
print("calibration_stats.json written;", len(keep), "calibration gate lines")

# ---------------- sheets
def ref(name, box): return (f"{REFS}/{name}.jpg", box, f"still {name}")
sheet([[ref("needle", (560, 250, 1100, 560)), ref("split", (580, 90, 880, 330)), ref("crater", (260, 120, 700, 500))],
       [(f"{STILLS}/hole08_tee.png", (0, 440, 900, 960), "Game view 8 tee (board)"), (f"{STILLS}/hole09_tee.png", (0, 440, 900, 960), "Game view 9 tee (board)"), (f"{STILLS}/hole10_tee.png", (0, 440, 900, 960), "Game view 10 tee (board)")],
       [(f"{PROBE}/hole08_tee_probe.jpg", (0, 500, 900, 1300), "probe 8 tee (real geometry)"), (f"{PROBE}/hole09_tee_probe.jpg", (0, 500, 900, 1300), "probe 9 tee"), (f"{PROBE}/hole10_tee_probe.jpg", (0, 500, 900, 1300), "probe 10 tee")]],
      C + "/sheet_grass_gameview.jpg", w=420)
sheet([[ref("needle", (700, 330, 1180, 720)), ref("split", (480, 200, 1000, 480))],
       [(f"{PROBE}/hole08_aerial_probe.jpg", (0, 500, 900, 1450), "Game view 8 aerial (G geometry)"), (f"{PROBE}/hole09_aerial_probe.jpg", (0, 500, 900, 1450), "Game view 9 aerial (G geometry)")],
       [(f"{SHOTS}/sea_hole08_aerial_thin.jpg", (0, 300, 900, 760), "board 8 thin shelf (1.5 yd) aerial"), (f"{SHOTS}/sea_hole09_aerial_thin.jpg", (0, 300, 900, 760), "board 9 thin shelf (1.5 yd) aerial")]],
      C + "/sheet_water_gameview.jpg", w=420)
sheet([[ref("crater", (500, 330, 1250, 700)), (f"{PROBE}/hole10_lavaedge_probe.jpg", (0, 300, 900, 1300), "Game view 10 lava rim (G geometry)")],
       [(f"{SHOTS}/crater_lava_phone.jpg", (0, 600, 900, 1500), "board lava phone"), (f"{SHOTS}/crater_basalt.jpg", (0, 400, 900, 1300), "board basalt joints"), (f"{SHOTS}/crater_wall_lights_on.jpg", (0, 400, 900, 1300), "board wall + lava lights"), (f"{SHOTS}/smoke_card.jpg", (0, 300, 900, 1300), "board smoke card")]],
      C + "/sheet_crater_gameview.jpg", w=360)
print("sheets written")

names = [["hole08_tee_probe", "hole08_green_probe", "hole08_arch_probe"], ["hole09_tee_probe", "hole09_green_probe", "hole09_ridge_probe"], ["hole10_tee_probe", "hole10_green_probe", "hole10_lavaedge_probe"]]
sheet([[(f"{PROBE}/{n}.jpg", None, n.replace("_probe", "")) for n in row] for row in names], C + "/sheet_probe_views.jpg", w=300)
print("probe sheet written")
