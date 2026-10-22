#!/usr/bin/env python3
"""Gate lines from PostcardLookStills output made with GOLF_STILLS_SWAY / GOLF_STILLS_SWAY_PAIR (RUNTIME.md v2 2026-10-05 area U).
usage: sway_gates.py <stills dir> [--other <second run dir>] [--label L]
  SWAY_FRAME_PAIR            per shot: plants-only change (plant-less frames identical, nothing outside the plant mask changed), change above noise, mirror displacement within the caps
  SWAY_ONLY_PLANTS_FRAMES    the plant-less frames of the two clocks are pixel-identical in every shot (ground, rocks, lava, surf, fall, sky, water do not move)
  SWAY_STILLS_DETERMINISTIC  A rendered twice at the same frozen clock is identical (in-run repeat), and, with --other, the same shots of a second RUN are pixel-identical
  SWAY_HOOK_ON_HOLE_START    GolfGame.Wind == the wind the hook gave GolfWindSway after every hole start
Prints GATE lines; exit 1 on a FAIL.  Needs only Pillow."""
import json, os, sys
from PIL import Image, ImageChops

def load(d):
    with open(os.path.join(d, "stills_stats.json")) as f:
        return json.load(f)

def dilate(mask, n=3):
    from PIL import ImageFilter
    m = mask.convert("L")
    for _ in range(n):
        m = m.filter(ImageFilter.MaxFilter(3))
    return m

def diff_bbox(a, b, water=()):
    """Bounding box of the pixels that differ between two frames (None = identical). `water` = mask PNGs (white = the sea, TennisWater) whose union, grown by 3 px, is left out: the sea reads the engine clock, ours is frozen."""
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return "size"
    d = ImageChops.difference(ia, ib).convert("L").point(lambda v: 255 if v > 0 else 0)
    for w in water:
        if os.path.isfile(w):
            d = ImageChops.multiply(d, ImageChops.invert(dilate(Image.open(w))))
    return d.getbbox()

def main():
    args = sys.argv[1:]
    d = args[0]
    other = args[args.index("--other") + 1] if "--other" in args else None
    st = load(d)
    shots = st["shots"]
    fails = 0
    def gate(name, ok, detail):
        nonlocal fails
        fails += 0 if ok else 1
        print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}")
    sw = [(s, s.get("sway")) for s in shots]
    missing = [s["name"] for s, x in sw if not x]
    test_cols = any(x and x.get("test_colours") for _, x in sw)
    if missing:
        gate("SWAY_FRAME_PAIR", False, f"no sway block (GOLF_STILLS_SWAY_PAIR missing) in {missing}")
        return 1
    per, bad = [], []
    holes = {}
    for s, x in sw:
        caps = x["caps_yd"]; disp = x["mirror_max_disp_yd"]
        over = [f"{k} {v:.4f} > {caps.get(k, .06):.2f}" for k, v in disp.items() if v > caps.get(k, .06) + 1e-6]
        ok = x["nonplant_px_diff"] == 0 and x["outside_plant_changed_px"] == 0 and x["repeat_max_diff"] == 0 and not over
        per.append(f"{s['name']}: plant px {x['plant_px']} ({x['plant_share']*100:.1f} %), changed {x['changed_px']} ({x['changed_share_of_plant_px']*100:.0f} % of them, mean |d| {x['mean_abs_change_plant_px']:.1f}), "
                   f"coloured plants {x['coloured_plant_objects']}/{x['plant_objects']}, max disp {', '.join(f'{k} {v:.3f}' for k, v in sorted(disp.items())) or 'none'}")
        if not ok:
            bad.append(f"{s['name']} (non-plant diff {x['nonplant_px_diff']}, outside {x['outside_plant_changed_px']}, repeat {x['repeat_max_diff']}{', over ' + ', '.join(over) if over else ''})")
        holes.setdefault(s["hole"], []).append(x)
    moving = {h: max((x["changed_px"] for x in xs), default=0) for h, xs in holes.items()}
    coloured = sum(x["coloured_plant_objects"] for _, x in sw)
    still_moves = all(v >= 150 for v in moving.values())
    tag = " [SYNTHETIC test colours: the installed FBX has no sway data; not a proof of the library colours]" if test_cols else ""
    if coloured == 0:
        gate("SWAY_FRAME_PAIR", False, f"NOT MEASURED: no plant of any shot carries sway colours (static plants by the B = 1 rule), nothing moved; frames {st.get('size')}")
    else:
        gate("SWAY_FRAME_PAIR", not bad and still_moves, f"{len(sw)} shot(s) rendered twice, dt {sw[0][1]['t1'] - sw[0][1]['t0']:.2f} s, {sw[0][1]['mph']:.0f} mph toward {sw[0][1]['deg']:.0f} deg: only plant pixels change "
             f"(changed px per hole {moving}, need >= 150 each), within the caps{tag}" + ("" if not bad else f"; BAD: {bad}") + " | " + " | ".join(per))
    non = [x["nonplant_px_diff"] for _, x in sw]
    gate("SWAY_ONLY_PLANTS_FRAMES", all(v == 0 for v in non) and sum(1 for _, x in sw if x["plant_px"] > 0) > 0, f"plant-less frames of the two clocks differ in {sum(non)} px over {len(sw)} shots (max channel diff {max(x['nonplant_max_diff'] for _, x in sw)}); ground, rocks, lava, surf, fall, sky, water read none of our clocks (TennisWater is rendered in the same player frame)")
    rep = max(x["repeat_max_diff"] for _, x in sw)
    detail = f"A rendered twice at the frozen clock: max channel diff {rep}"
    ok = rep == 0
    if other:
        names = [s["name"] for s in shots]
        diffs, raw = {}, {}
        for n in names:
            for suffix in ("", "__sway_t1"):
                a, b = os.path.join(d, n + suffix + ".png"), os.path.join(other, n + suffix + ".png")
                if os.path.isfile(a) and os.path.isfile(b):
                    diffs[n + suffix] = diff_bbox(a, b, (os.path.join(d, n + "__sway_water.png"), os.path.join(other, n + "__sway_water.png")))
                    raw[n + suffix] = diff_bbox(a, b)
        nd = {k: v for k, v in diffs.items() if v is not None}
        ok = ok and len(diffs) > 0 and not nd
        nraw = sum(1 for v in raw.values() if v is not None)
        wpx = sum((x.get("water_px", 0) for _, x in sw))
        detail += (f"; two separate Unity runs: {len(diffs)} frame(s) compared, {len(nd)} differ outside the sea" + (f": {dict(list(nd.items())[:4])}" if nd else " (pixel-identical)") +
                   f" ({nraw} frame(s) differ if the sea is counted: TennisWater reads the engine clock, which is not the same in two runs; {wpx} sea px over the shots, left out grown by 3 px)")
    gate("SWAY_STILLS_DETERMINISTIC", ok, detail)
    rtp = os.path.join(d, "sway_realtime.json")
    if os.path.isfile(rtp):
        with open(rtp) as f:
            rt = json.load(f)
        rs = rt["shots"]
        rbad = [r["name"] for r in rs if r["nonsea_px_diff"] != 0 or r["dt_real"] < rt["dt"] - 0.05]
        gate("SWAY_ONLY_PLANTS_REALTIME", not rbad and len(rs) > 0, f"{len(rs)} shot(s) rendered again {rt['dt']:.1f} s of real time later (measured {min(r['dt_real'] for r in rs):.2f}-{max(r['dt_real'] for r in rs):.2f} s, the player loop running, plants hidden): "
             f"{sum(r['nonsea_px_diff'] for r in rs)} px differ outside the sea (of {sum(r['nonsea_px'] for r in rs)}), max channel diff {max(r['nonsea_max_diff'] for r in rs)}: ground, rocks, lava, surf, fall, smoke and sky do not move by themselves; "
             f"the sea (TennisWater, the tennis shader's own engine-clock swell: {sum(r['sea_px'] for r in rs)} px) moved in {sum(r['sea_px_moved'] for r in rs)} px as before" + (f"; BAD: {rbad}" if rbad else ""))
    else:
        gate("SWAY_ONLY_PLANTS_REALTIME", False, "NOT MEASURED: no sway_realtime.json (run with GOLF_STILLS_REALTIME_PAIR=1.2)")
    hooks = [(s["name"], s.get("wind_hook")) for s in shots]
    hbad = [n for n, h in hooks if not h or not h.get("same")]
    gate("SWAY_HOOK_ON_HOLE_START", not hbad and len(hooks) > 0, f"{len(hooks)} shot(s): GolfGame.Wind equals the wind GolfGame.StartHole handed to GolfWindSway" + (f"; DIFFERENT / missing: {hbad}" if hbad else ""))
    return 1 if fails else 0

sys.exit(main())
