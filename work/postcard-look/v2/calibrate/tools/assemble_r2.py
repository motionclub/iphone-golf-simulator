#!/usr/bin/env python3
"""Calibration round 2 (after review K): assemble calibration_stats_r2.json (gate lines + numbers) and the Game-view sheets from the FINAL runs.
usage: assemble_r2.py <smoke_label> <probe_label,probe_label,...> <stills_dir_name>
   e.g. assemble_r2.py r2final r2c,r2d,r2e stills_board_r2
Paths are fixed to this job. Pure Pillow."""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from img_stats import stats

R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
C = R + "/work/postcard-look/v2/calibrate"
REFS = R + "/ArtDir/environments/refs"
label, probes, stills_name = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
SMOKE = f"{R}/work/postcard-look/v2/runtime/smoke_{label}.txt"
SHOTS = f"{R}/work/postcard-look/v2/runtime/shots/{label}"
STILLS = f"{C}/{stills_name}"
OUT = C + "/r2"
os.makedirs(OUT, exist_ok=True)

def parse(path):
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
    im = im.convert("RGB").resize((w, h))
    d = ImageDraw.Draw(im); f = font(max(11, w // 22))
    d.rectangle([0, 0, w, f.size + 6], fill=(0, 0, 0)); d.text((4, 2), label, fill=(255, 255, 255), font=f)
    return im

def sheet(rows, path, w=300):
    cells = []
    for row in rows:
        r = []
        for src, box, lab in row:
            if isinstance(src, str) and not os.path.exists(src): continue
            im = Image.open(src) if isinstance(src, str) else src
            if box: im = im.crop(box)
            r.append(panel(im, w, int(w * im.size[1] / im.size[0]), lab))
        if r: cells.append(r)
    H = sum(max(c.size[1] for c in r) for r in cells); W = max(sum(c.size[0] for c in r) for r in cells)
    out = Image.new("RGB", (W, H), (20, 20, 20)); y = 0
    for r in cells:
        x = 0
        for c in r: out.paste(c, (x, y)); x += c.size[0]
        y += max(c.size[1] for c in r)
    out.save(path, quality=88)

gates, info = parse(SMOKE)
keep = [g for g in gates if re.match(r"(GRASS_|SURFACES_|SHELF_|OCEAN_|SEA_|LAVA_GAMEVIEW|BASALT_JOINT|BASALT_RENDERS|SMOKE_SOFT|URP_BOTH|NO_POST|LAVA_ORANGE|LAVA_LIGHTS)", g["id"])]
out = {"smoke": SMOKE.replace(R + "/", ""), "summary": [l.strip() for l in open(SMOKE) if l.startswith("SUMMARY")],
       "calibration_gates": keep, "info": [i for i in info if re.match(r"INFO: (GRASS|SEA|SMOKE|CRATER|BASALT)", i)]}

probe_runs = {}
for p in probes:
    rep = f"{C}/probe_{p}/probe_report.txt"
    if not os.path.exists(rep): continue
    pg, pi = parse(rep)
    interesting = [g for g in pg if re.match(r"(PROBE_SWAP|GOLFER_|PROBE_GROUND_TEXTURED|PROBE_SHELF)", g["id"])]
    tees = {}
    for n in ["hole08_tee_probe", "hole08_green_probe", "hole08_arch_probe", "hole09_tee_probe", "hole09_green_probe", "hole09_ridge_probe", "hole10_tee_probe", "hole10_green_probe", "hole10_lavaedge_probe"]:
        f = f"{C}/probe_{p}/{n}.jpg"
        if os.path.exists(f):
            c = stats(f, (300, 1067, 600, 1600)); w = stats(f, (0, 640, 900, 1600))
            tees[n] = {"central_lower_third": {k: c[k] for k in ("mean_rgb", "hue", "S", "V", "clip250_pct")}, "lower60_clip250_pct": w["clip250_pct"]}
    probe_runs[p] = {"gates": interesting, "summary": [l for l in open(rep) if l.startswith("SUMMARY")][0].strip(), "views": tees}
out["probe_runs"] = probe_runs
sj = f"{STILLS}/stills_stats.json"
if os.path.exists(sj): out["stills_board"] = json.load(open(sj))
json.dump(out, open(C + "/calibration_stats_r2.json", "w"), indent=1)
print("calibration_stats_r2.json written;", len(keep), "calibration gate lines;", len(probe_runs), "probe runs")

last = probes[-1]
PROBE = f"{C}/probe_{last}"
def ref(name, box): return (f"{REFS}/{name}.jpg", box, f"still {name}")
# golfers: the full frame and the matte, three holes (hole light), crater with its figure exposure
sheet([[(f"{PROBE}/hole08_golfer_full.jpg", (0, 300, 900, 1100), "8 golfer (Game view)"), (f"{PROBE}/hole09_golfer_full.jpg", (0, 300, 900, 1100), "9 golfer"), (f"{PROBE}/hole10_golfer_full.jpg", (0, 300, 900, 1100), "10 golfer (figure exposure)")],
       [(f"{PROBE}/hole08_golfer_matte.jpg", (150, 400, 500, 1000), "8 matte"), (f"{PROBE}/hole09_golfer_matte.jpg", (150, 400, 500, 1000), "9 matte"), (f"{PROBE}/hole10_golfer_matte.jpg", (150, 400, 500, 1000), "10 matte"), (f"{PROBE}/hole10_golfer_matte_legacy.jpg", (150, 400, 500, 1000), "10 legacy light")]],
      OUT + "/sheet_golfers_r2.jpg", w=420)
names = [["hole08_tee_probe", "hole08_green_probe", "hole08_arch_probe"], ["hole09_tee_probe", "hole09_green_probe", "hole09_ridge_probe"], ["hole10_tee_probe", "hole10_green_probe", "hole10_lavaedge_probe"]]
sheet([[(f"{PROBE}/{n}.jpg", None, n.replace("_probe", "")) for n in row] for row in names], OUT + "/sheet_probe_views_r2.jpg", w=300)
sheet([[(f"{PROBE}/hole08_aerial_probe.jpg", (0, 500, 900, 1450), "8 aerial (G geometry)"), (f"{PROBE}/hole09_aerial_probe.jpg", (0, 500, 900, 1450), "9 aerial"), (f"{PROBE}/hole10_aerial_probe.jpg", (0, 500, 900, 1450), "10 aerial")]],
      OUT + "/sheet_aerials_r2.jpg", w=420)
# crater board: lava, basalt, smoke
sheet([[ref("crater", (500, 330, 1250, 700)), (f"{PROBE}/hole10_lavaedge_probe.jpg", (0, 300, 900, 1300), "10 lava rim (G geometry)")],
       [(f"{SHOTS}/crater_lava_phone.jpg", (0, 600, 900, 1500), "board lava phone"), (f"{SHOTS}/crater_basalt.jpg", (0, 400, 900, 1300), "board basalt joints"), (f"{SHOTS}/crater_wall_lights_on.jpg", (0, 400, 900, 1300), "wall + lava lights"), (f"{SHOTS}/smoke_card.jpg", (0, 300, 900, 1300), "board smoke")]],
      OUT + "/sheet_crater_r2.jpg", w=360)
print("sheets written to", OUT)
