"""clearance.py: how near the polo comes to the skin around the arms and shoulders (cm, along the skin's normal; negative = the
cloth is under the skin), before and after the muscle field. Rest pose."""
import numpy as np, armio, armfield as af, posed
def gap(parts):
    b, t = parts['Body'], parts['Kit_Top']; sb = np.abs(b['pos'][:, 0]) > 0.13; st = np.abs(t['pos'][:, 0]) > 0.17
    P, N, Q = b['pos'][sb], b['nrm'][sb], t['pos'][st]; out = np.empty(len(Q))
    for i in range(0, len(Q), 400):
        d = ((Q[i:i + 400, None, :] - P[None]) ** 2).sum(2); j = d.argmin(1)
        out[i:i + 400] = ((Q[i:i + 400] - P[j]) * N[j]).sum(1)
    return out * 100
if __name__ == "__main__":
    parts = posed.load("male_torso"); new = posed.muscles(parts, af.P)
    # (the field moves positions, not normals: the base normals are near enough for a signed distance)
    for name, g in (("before", gap(parts)), ("after", gap(new))):
        print(f"{name:7} polo sleeve to skin: least {g.min():5.2f}  1% {np.percentile(g, 1):5.2f}  5% {np.percentile(g, 5):5.2f}  median {np.median(g):5.2f} cm   under the skin: {(g < 0).sum()} of {len(g)} vertices, under 0.3 cm: {(g < .3).sum()}")
