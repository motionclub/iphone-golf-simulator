"""Summarise MajesticCost JSONs into <out>/baseline.md + baseline.csv.

usage: python3 -I tools/summarize.py <json_dir> <out_dir> [<reference_json_dir>]

Timings: 'pix' = (T2x - T1x)/3, per-pixel GPU of one 1080p frame (CPU-free); 'sync1x' = one synchronous
render at 1080p, CPU submit + GPU (upper bound); 'syncq' = the same at 1/4 resolution.

Counts: in the loaded sweep (2026-10-17 02:28-02:50, load 24-64) one profiler frame sometimes held two
camera renders, so some counter reads are exactly double. The harness now keeps the smallest non-zero
read (quiet runs: sky-only = 18 draws, empty = 6, i.e. single). For sweep JSONs:
  1. geometry is identical in full / noPost / noMSAA, so start from the smallest of the three;
  2. if a reference dir (quiet run, single-render counts) has the same place (slot minus weather),
     divide by round(count / reference) (1 or 2);
  3. otherwise, golf slots whose sky-only read was doubled (>= 30 draws) and whose three geometry-identical
     variants agree are halved: on holes 8, 12 and 18 this gives exactly the quiet run's counts;
  4. an ablation (noShadows / noHeroes) above the slot's single count is a doubled read and is halved.
"""
import json, os, sys, statistics as st, glob, csv

src, out = sys.argv[1], sys.argv[2]
refdir = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(out, exist_ok=True)

def place(slot): return slot.rsplit("_", 1)[0]
ref = {}
if refdir:
    for p in glob.glob(os.path.join(refdir, "*.json")):
        r = json.load(open(p)); v = {x["name"]: x for x in r["variants"]}
        ref.setdefault(place(r["slot"]), min(v[k]["triangles"] for k in ("full", "noPost", "noMSAA")))

rows = []
for p in sorted(glob.glob(os.path.join(src, "*.json"))):
    r = json.load(open(p))
    v = {x["name"]: x for x in r["variants"]}
    f = v["full"]
    geo = min((v[k] for k in ("full", "noPost", "noMSAA")), key=lambda x: x["triangles"])
    T, D, S, C = geo["triangles"], geo["drawCalls"], geo["setPass"], geo["shadowCasters"]
    k = 1; why = ""
    if place(r["slot"]) in ref:
        k = max(1, round(T / ref[place(r["slot"])]))
        if k > 1: why = f"/{k} vs quiet-run reference"
    elif r["slot"].startswith("golf") and v["skyOnly"]["drawCalls"] >= 30 and f["triangles"] <= T * 1.02:
        k = 2; why = "/2 golf doubled read"
    T, D, S, C = T / k, D / k, S / k, C / k
    def single(x, ref_):  # ablation counts, scaled by the slot factor, then stray doubles halved
        x = x / k
        return x / 2 if x > ref_ * 1.02 else x
    row = dict(slot=r["slot"], fixed=why, tris=T, draws=D, setpass=S, casters=C,
               renderers=r["renderers"], skinned=r["skinned"], particles=r["particleSystems"], transparent_mats=r["transparentMaterials"],
               materials=r["uniqueMaterials"], shaders=r["uniqueShaders"], lights=r["lights"],
               pix=f["pixelGpuMs1080"], sync1x=f["sync1xP25Ms"], sync2x=f["sync2xP25Ms"], syncq=f["syncQuarterP25Ms"])
    for name in ["noShadows", "noPost", "noMSAA", "noHeroes", "skyOnly", "empty"]:
        if name in v:
            row[f"{name}_tris"] = single(v[name]["triangles"], T) if name in ("noShadows", "noHeroes") else T
            row[f"{name}_draws"] = single(v[name]["drawCalls"], D) if name in ("noShadows", "noHeroes") else v[name]["drawCalls"]
            row[f"{name}_pix"] = v[name]["pixelGpuMs1080"]; row[f"{name}_sync1x"] = v[name]["sync1xP25Ms"]
    rows.append(row)

with open(os.path.join(out, "baseline.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

def med(xs):
    xs = [x for x in xs if x == x]
    return st.median(xs) if xs else float("nan")
lines = ["| slot | tris/frame (M) | draws | SetPass | shadow casters | skinned | particle sys | pixel GPU ms (M5) | sync 1080p ms (M5) | count fix |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
for r in rows:
    lines.append(f"| {r['slot']} | {r['tris']/1e6:.2f} | {r['draws']:.0f} | {r['setpass']:.0f} | {r['casters']:.0f} | {r['skinned']} | {r['particles']} | {r['pix']:.2f} | {r['sync1x']:.2f} | {r['fixed']} |")

groups = {"golf clear": lambda s: s.startswith("golf") and s.endswith("clear"),
          "golf weather": lambda s: s.startswith("golf") and not s.endswith("clear"),
          "tennis clear": lambda s: s.startswith("tennis") and s.endswith("clear"),
          "tennis weather": lambda s: s.startswith("tennis") and not s.endswith("clear"),
          "hub": lambda s: s.startswith("hub")}
summ = ["| group | n | tris median (M) | tris max (M) | draws median | pixel GPU median ms | sync 1080p median ms | shadows Δtris (M) | characters Δtris (M) | shadows Δsync ms | characters Δsync ms | MSAA Δpix ms | post Δsync ms | sky-only sync ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for name, pred in groups.items():
    g = [r for r in rows if pred(r["slot"])]
    if not g: continue
    summ.append("| {} | {} | {:.2f} | {:.2f} | {:.0f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} |".format(
        name, len(g), med([r["tris"] for r in g]) / 1e6, max(r["tris"] for r in g) / 1e6, med([r["draws"] for r in g]),
        med([r["pix"] for r in g]), med([r["sync1x"] for r in g]),
        med([(r["tris"] - r["noShadows_tris"]) / 1e6 for r in g]), med([(r["tris"] - r["noHeroes_tris"]) / 1e6 for r in g]),
        med([r["sync1x"] - r["noShadows_sync1x"] for r in g]), med([r["sync1x"] - r["noHeroes_sync1x"] for r in g]),
        med([r["pix"] - r["noMSAA_pix"] for r in g]), med([r["sync1x"] - r["noPost_sync1x"] for r in g]),
        med([r["skyOnly_sync1x"] for r in g])))
wx = ["| weather slot | Δtris vs clear (M) | Δdraws | Δpixel GPU ms | Δsync ms | particle systems |", "|---|---:|---:|---:|---:|---:|"]
by = {r["slot"]: r for r in rows}
for r in rows:
    base = place(r["slot"]) + "_clear"
    if r["slot"] != base and base in by:
        b = by[base]
        wx.append(f"| {r['slot']} | {(r['tris']-b['tris'])/1e6:+.2f} | {r['draws']-b['draws']:+.0f} | {r['pix']-b['pix']:+.2f} | {r['sync1x']-b['sync1x']:+.2f} | {r['particles']} |")
open(os.path.join(out, "baseline.md"), "w").write(
    "# Baseline per slot (Mac M5, editor, 1920x1080, 4x MSAA)\n\nCounts are single-render (see the docstring of tools/summarize.py for the doubled-read fix).\n\n"
    + "\n".join(lines) + "\n\n## Groups (medians across slots)\n\n" + "\n".join(summ) + "\n\n## Weather vs clear, same place\n\n" + "\n".join(wx) + "\n")
print("\n".join(summ)); print(); print("\n".join(wx))
