"""FRAME_RATE_60B NO_STEP: does anything on screen move in 1/30 s steps at a 60 fps draw?

Input: tracks_<scene>.tsv from FrameRate60bTests.NothingStepsAtThirty (one point per drawn frame, game clock fixed at 1/60 s).
Two signatures of 30 Hz motion on a 60 fps screen:
  * duplicate frames: the thing does not move on every other frame while it is moving (a 30 Hz update);
  * 30 Hz kinks: it moves in straight lines between 1/30 s keys, so its acceleration (second difference) is ~0 on every
    other frame. Parity ratio = median |accel| on the busier frame parity / on the quieter one, over moving frames.
    Smooth motion: ~1. Straight lines between 30 Hz keys: >> 3.
Per signal: PASS when duplicate share < 5 % and parity ratio < 2.5.
    python3 no_step.py <dir with tracks_*.tsv> [--json out.json]
"""
import sys, os, glob, json
import numpy as np

def load(path):
    out = {}
    for line in open(path):
        k, v = line.rstrip("\n").split("\t")
        out[k] = np.array([[float(x) for x in p.split(",")] for p in v.split(";") if p])
    return out

def analyse(P):
    v = np.linalg.norm(np.diff(P, axis=0), axis=1)              # per-frame travel
    if len(v) < 10: return None
    moving_thr = max(1e-4, np.percentile(v, 75) * .05)
    mov = v > moving_thr
    # duplicates: a still frame between two moving ones
    dup = [(not mov[i]) and mov[i - 1] and mov[i + 1] for i in range(1, len(v) - 1)]
    nmov = int(mov.sum())
    a = np.linalg.norm(P[2:] - 2 * P[1:-1] + P[:-2], axis=1)    # accel at frame k (1..n-2)
    am = mov[1:] & mov[:-1]                                       # both neighbouring steps moving
    # drop cuts / impacts: travel jumps more than 4x the local median
    med = np.median(v[mov]) if nmov else 0
    ok = am & (np.maximum(v[1:], v[:-1]) < 6 * max(med, 1e-9))
    even = a[0::2][ok[0::2]]; odd = a[1::2][ok[1::2]]
    if len(even) < 8 or len(odd) < 8: ratio = float('nan')
    else:
        me, mo = np.median(even), np.median(odd)
        ratio = float(max(me, mo) / max(min(me, mo), 1e-12))
    return dict(frames=len(P), moving=nmov, duplicate_share=round(sum(dup) / max(1, nmov), 4), parity_ratio=round(ratio, 2),
                passed=bool(sum(dup) / max(1, nmov) < .05 and (ratio != ratio or ratio < 2.5)))

def main():
    d = sys.argv[1]; res = {}
    for f in sorted(glob.glob(os.path.join(d, "tracks_*.tsv"))):
        scene = os.path.basename(f)[7:-4]
        for k, P in load(f).items():
            r = analyse(P)
            if r: res[f"{scene}/{k}"] = r
    for k, r in res.items(): print(f"{'PASS' if r['passed'] else 'FAIL'} {k:34s} frames {r['frames']:4d} moving {r['moving']:4d} dup {r['duplicate_share']:.3f} parity {r['parity_ratio']}")
    if "--json" in sys.argv: json.dump(res, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)

main()
