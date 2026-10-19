"""FRAME_RATE_60B: the hole-12 signature shot (Resources/Course/hole_12_shot.json, 30 fps samples) played at 60 fps,
as SignatureShot sampled it before (straight lines between samples) and now (Catmull-Rom through them).
Prints the no_step parity ratio of the chase camera, the look point, the wide camera and the ball, and the max distance
between the two at the file's own frames (must be 0: the curve passes through every sample)."""
import json, sys, numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
d = json.load(open(sys.argv[1])); n, fps = d["frames"], d["fps"]
def track(flat, stride, off): a = np.array(flat).reshape(-1, stride)[:n, off:off + 3]; return a
def lin(P, f): i = np.clip(np.floor(f).astype(int), 0, n - 1); j = np.minimum(i + 1, n - 1); u = (f - i)[:, None]; return P[i] * (1 - u) + P[j] * u
def cr(P, f):
    i = np.floor(f).astype(int); u = (f - i)[:, None]; g = lambda k: P[np.clip(k, 0, n - 1)]
    p0, p1, p2, p3 = g(i - 1), g(i), g(i + 1), g(i + 2)
    return .5 * (2 * p1 + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u**2 + (3 * p1 - p0 - 3 * p2 + p3) * u**3)
f = np.arange(0, (n - 1) * 60 / fps + 1) * fps / 60.0          # every 1/60 s, in file frames
import importlib.util; spec = importlib.util.spec_from_file_location("ns", __file__.rsplit('/', 1)[0] + "/no_step.py")
src = open(spec.origin).read().replace("\nmain()\n", "\n"); ns = {}; exec(src, ns)
out = {}
for name, P in [("chase_camera", track(d["cam"], 10, 0)), ("chase_look", track(d["cam"], 10, 3)), ("wide_camera", track(d["overview"], 10, 0)), ("ball", track(d["ball"], 3, 0))]:
    a, b = ns["analyse"](lin(P, f)), ns["analyse"](cr(P, f))
    shared = float(np.abs(cr(P, f[::2]) - P[:len(f[::2])]).max())
    out[name] = dict(before_parity=a["parity_ratio"], after_parity=b["parity_ratio"], shared_frames_max_m=round(shared, 6))
    print(f"{name:13s} parity before {a['parity_ratio']:>8} after {b['parity_ratio']:>6}   shared-frame difference {shared:.2e} m")
json.dump(out, open(sys.argv[2], "w"), indent=1)
