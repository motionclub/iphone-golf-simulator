#!/usr/bin/env python3
"""Analyse the takes written by Play -> Calibration (the `aimcal take` lines in SportsDiagnostics.log).

Usage:
    aimcal_analyze.py SportsDiagnostics.log [more.log ...]   report on the takes found
    aimcal_analyze.py --json out.json SportsDiagnostics.log   also write the numbers as JSON
    aimcal_analyze.py --selftest                              run on synthetic takes (no phone needed)

A take line looks like (one line, wrapped here):
    1731700000.1 aimcal take phase=capture wing=0 lane=-1 angle=-31.80 facing=1 landingX=-3.000 legal=1 accepted=1
        trace=-1100:-5.2:0.40,-1090:-5.0:0.42,...,0:-31.8:9.60
Since 11-15 `angle` is the swing's direction (the way the phone travelled, degrees right of the TV direction) and `face` the
racket-face angle at the same moment (logged only). Older logs have no `face`, and their `angle` is the racket face. `trace` is
ms-before-confirmation:face:gyro-rate(rad/s)[:side:forward room acceleration m/s²] for the last 1.2 s. wing 0 = forehand, 1 = backhand;
lane -1 / 0 / 1 = the target the player was asked to hit (left / straight / right).

What it answers
  * Where do left / straight / right sit for each wing, and how far do they spread?
  * Which reading separates the lanes best: the confirm angle, the angle at the gyro-rate peak, or the angle swept in the
    last 200 ms? (smaller overlap = better)
  * What lane boundaries would a fixed mapping need, relative to the player's own straight, so nearly every take is right?
  * In the checking phase, how often did the ball really land in the asked lane?
"""
import json
import math
import re
import statistics
import sys
from collections import defaultdict

TAKE = re.compile(r"aimcal take (?P<kv>.*?)(?: trace=(?P<trace>\S*))?\s*$")
LANE_NAMES = {-1: "left", 0: "straight", 1: "right"}
WING_NAMES = {0: "forehand", 1: "backhand"}
# How the game reads the angle today (SteeringFilter.swift TennisAimWing.standard + TennisRules.SideFromSwing)
CURRENT_SPAN, CURRENT_DEAD, CURRENT_LANE_AIM, CURRENT_AIM_CAP = 32.0, 2.5, 0.3, 0.8


def current_lane_threshold_deg():
    """Degrees from straight at which the game starts calling a swing left/right now (aim 0.3 of the 0.8 cap)."""
    return CURRENT_DEAD + (CURRENT_LANE_AIM / CURRENT_AIM_CAP) * (CURRENT_SPAN - CURRENT_DEAD)


def parse(lines):
    takes = []
    for line in lines:
        if "aimcal take" not in line:
            continue
        m = TAKE.search(line.strip())
        if not m:
            continue
        kv = dict(p.split("=", 1) for p in m.group("kv").split() if "=" in p)
        try:
            take = {
                "phase": kv["phase"], "wing": int(kv["wing"]), "lane": int(kv["lane"]),
                "angle": float(kv["angle"]), "facing": float(kv["facing"]),
                "face": float(kv["face"]) if "face" in kv else None,
                "landingX": float(kv["landingX"]), "legal": kv.get("legal") == "1",
                "accepted": kv.get("accepted") == "1",
            }
        except (KeyError, ValueError):
            continue
        trace = []
        for item in (m.group("trace") or "").split(","):
            parts = item.split(":")
            if len(parts) in (3, 5):
                try:
                    vals = [int(parts[0])] + [float(p) for p in parts[1:]]
                    trace.append(tuple(vals) if len(vals) == 5 else tuple(vals) + (None, None))
                except ValueError:
                    pass
        take["trace"] = trace
        takes.append(take)
    return takes


def wrap(d):
    """Wrap a degree difference into -180..180 (headings wrap; the faces rarely do)."""
    return (d + 180.0) % 360.0 - 180.0


def features(take):
    """The candidate readings of one take, in degrees."""
    out = {"confirm": take["angle"]}
    if take.get("face") is not None and not math.isnan(take["face"]):
        out["face"] = take["face"]
    tr = take["trace"]
    accel = [s for s in tr if s[3] is not None and -250 <= s[0] <= 0]
    if len(accel) >= 3:
        # the swing's direction re-derived offline from the logged room acceleration over the last 250 ms
        vs = sum(s[3] for s in accel) * .01; vf = sum(s[4] for s in accel) * .01
        if math.hypot(vs, vf) >= .25:
            out["path250"] = math.degrees(math.atan2(vs, vf))
    if tr:
        peak = max(tr, key=lambda s: s[2])
        out["peak"] = peak[1]
        late = [s for s in tr if s[0] >= -200]
        if len(late) >= 2:
            out["sweep200"] = late[-1][1] - late[0][1]
        window = [s for s in tr if -120 <= s[0] <= 0]
        if window:
            out["mean120"] = statistics.fmean(s[1] for s in window)
    return out


def summary(values):
    if not values:
        return None
    return {"n": len(values), "mean": statistics.fmean(values),
            "sd": statistics.pstdev(values) if len(values) > 1 else 0.0, "min": min(values), "max": max(values)}


def overlap_score(groups):
    """Fraction of takes closer to another lane's mean than to their own (nearest-mean classifier on one feature)."""
    means = {lane: statistics.fmean(v) for lane, v in groups.items() if v}
    if len(means) < 2:
        return None
    wrong = total = 0
    for lane, vals in groups.items():
        for v in vals:
            total += 1
            if min(means, key=lambda l: abs(v - means[l])) != lane:
                wrong += 1
    return wrong / total if total else None


def boundaries(groups):
    """Left|straight and straight|right cut points halfway between the lane means, plus their distance from straight."""
    if any(not groups.get(l) for l in (-1, 0, 1)):
        return None
    m = {l: statistics.fmean(groups[l]) for l in (-1, 0, 1)}
    return {"left_straight": (m[-1] + m[0]) / 2, "straight_right": (m[0] + m[1]) / 2,
            "left_offset": (m[-1] + m[0]) / 2 - m[0], "right_offset": (m[0] + m[1]) / 2 - m[0]}


def analyse(takes):
    report = {"takes": len(takes), "wings": {}, "check": {}}
    for wing in (0, 1):
        mine = [t for t in takes if t["wing"] == wing and t["accepted"] and t["phase"] == "capture"]
        if not mine:
            continue
        by_feature = defaultdict(lambda: defaultdict(list))
        for t in mine:
            for name, v in features(t).items():
                by_feature[name][t["lane"]].append(v)
        wing_report = {"n": len(mine), "lanes": {}, "features": {}}
        for lane in (-1, 0, 1):
            wing_report["lanes"][LANE_NAMES[lane]] = summary(by_feature["confirm"].get(lane, []))
        for name, groups in by_feature.items():
            wing_report["features"][name] = {"misread": overlap_score(groups), "boundaries": boundaries(groups)}
        usable = {n: f["misread"] for n, f in wing_report["features"].items() if f["misread"] is not None and n != "sweep200"}
        if usable:
            wing_report["best_feature"] = min(usable, key=usable.get)
        report["wings"][WING_NAMES[wing]] = wing_report
    check = [t for t in takes if t["phase"] == "check"]
    for wing in (0, 1):
        mine = [t for t in check if t["wing"] == wing]
        if mine:
            ok = sum(1 for t in mine if t["legal"] and lane_of(t["landingX"]) == t["lane"])
            report["check"][WING_NAMES[wing]] = {"n": len(mine), "right_lane": ok, "rate": ok / len(mine)}
    return report


def lane_of(x):
    """The lane a landing counts as (TennisAimLesson.lane: beyond 1.2 m of the centre line)."""
    return -1 if x < -1.2 else 1 if x > 1.2 else 0


def pct(x):
    return "  n/a" if x is None else f"{x * 100:4.0f}%"


def render(report):
    out = [f"{report['takes']} takes read", ""]
    thresh = current_lane_threshold_deg()
    out.append(f"Today's game calls a swing left/right once the face is {thresh:.1f} deg either side of the player's straight "
               f"(aim {CURRENT_LANE_AIM} of {CURRENT_AIM_CAP}, span {CURRENT_SPAN:.0f} deg).")
    for wing, w in report["wings"].items():
        out += ["", f"== {wing} ({w['n']} learning takes) =="]
        out.append("  lane      n    mean     sd     min     max   (confirm angle, degrees)")
        for lane, s in w["lanes"].items():
            if s:
                out.append(f"  {lane:<8} {s['n']:2d} {s['mean']:7.1f} {s['sd']:6.1f} {s['min']:7.1f} {s['max']:7.1f}")
        out.append("  reading            misread   left|straight cut   straight|right cut   (offsets from straight, deg)")
        for name, f in sorted(w["features"].items()):
            b = f["boundaries"]
            cuts = f"{b['left_offset']:+8.1f}            {b['right_offset']:+8.1f}" if b else "      n/a                 n/a"
            out.append(f"  {name:<18} {pct(f['misread'])}    {cuts}")
        if "best_feature" in w:
            out.append(f"  best separating reading: {w['best_feature']}")
        conf = w["features"].get("confirm", {}).get("boundaries")
        if conf:
            ok_now = abs(conf["left_offset"]) >= thresh * .75 and abs(conf["right_offset"]) >= thresh * .75
            out.append("  verdict: today's thresholds " + ("sit near the cut points for this player." if ok_now else
                       f"are far from this player's cut points ({conf['left_offset']:+.1f} / {conf['right_offset']:+.1f} deg): a fixed mapping "
                       f"needs boundaries about {abs(conf['left_offset']):.0f} deg either side of straight, not {thresh:.0f}."))
    if report["check"]:
        out += ["", "== checking phase: did the ball land in the asked lane? =="]
        for wing, c in report["check"].items():
            out.append(f"  {wing}: {c['right_lane']}/{c['n']} ({pct(c['rate']).strip()})")
    return "\n".join(out)


def synthetic(seed=7):
    import random
    rng = random.Random(seed)
    lines = []
    for wing in (0, 1):
        for lane in (0, -1, 1) * 4:
            angle = lane * 30 + wing * 6 + rng.gauss(0, 4)
            trace = ",".join(f"{ms}:{angle - 0.01 * (ms) + rng.gauss(0, .3):.1f}:{max(0.2, 9 - abs(ms) / 60):.2f}" for ms in range(-1100, 1, 100))
            lines.append(f"1.0 aimcal take phase=capture wing={wing} lane={lane} angle={angle:.2f} facing={1 if wing == 0 else -1} "
                         f"landingX={lane * 3:.3f} legal=1 accepted=1 trace={trace}")
        for lane in (1, 0, -1, 0, -1, 1):
            angle = lane * 30 + wing * 6 + rng.gauss(0, 4)
            lines.append(f"2.0 aimcal take phase=check wing={wing} lane={lane} angle={angle:.2f} facing={1 if wing == 0 else -1} "
                         f"landingX={lane * 3 + rng.gauss(0, .3):.3f} legal=1 accepted=1 trace=")
    return lines


def main(argv):
    if "--selftest" in argv:
        report = analyse(parse(synthetic()))
        assert report["takes"] == 36, report["takes"]
        fore = report["wings"]["forehand"]
        assert abs(fore["lanes"]["left"]["mean"] + 30) < 6 and abs(fore["lanes"]["right"]["mean"] - 30) < 6
        assert fore["features"]["confirm"]["misread"] < 0.1
        assert report["check"]["forehand"]["n"] == 6 and report["check"]["forehand"]["rate"] >= 0.8
        print(render(report))
        print("\nselftest OK")
        return 0
    json_out = None
    if "--json" in argv:
        i = argv.index("--json")
        json_out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    paths = [a for a in argv[1:] if not a.startswith("-")]
    if not paths:
        print(__doc__)
        return 2
    lines = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as f:
            lines += f.readlines()
    takes = parse(lines)
    if not takes:
        print("No `aimcal take` lines found. Run Play > Calibration, then Settings > Send diagnostics.")
        return 1
    report = analyse(takes)
    print(render(report))
    if json_out:
        with open(json_out, "w") as f:
            json.dump(report, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
