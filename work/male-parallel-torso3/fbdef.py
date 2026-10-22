"""front/back separate error (mesh - plate, mm; + = mesh protrudes more) from left+right side silhouettes. python3.13 fbdef.py <tag>..."""
import sys, numpy as np
sys.path.insert(0, '.')
import prof
for tag in sys.argv[1:]:
    P = prof.profile(f'r/sil_{tag}'); rows = []
    for z in sorted(P['left']['plate'], key=float):
        zf = float(z)
        if zf < 0.80 or zf > 1.36: continue
        out = []
        # left view: lo = y_min (front), hi = y_max (back)
        a, b = P['left']['plate'][z], P['left']['mesh'][z]
        if a and b: lf = -(b[0] - a[0]); lb = b[1] - a[1]
        else: lf = lb = np.nan
        a, b = P['right']['plate'][z], P['right']['mesh'][z]       # right view mirrored: hi = front, lo = back
        if a and b: rf = b[1] - a[1]; rb = -(b[0] - a[0])
        else: rf = rb = np.nan
        rows.append((zf, lf, rf, lb, rb))
    print(tag, ' z   | front L   R   avg | back L   R   avg   (mesh - plate, +=mesh protrudes)')
    for zf, lf, rf, lb, rb in rows:
        print(f'  {zf:.2f} | {lf:+5.0f} {rf:+5.0f} {np.nanmean([lf, rf]):+5.0f} | {lb:+5.0f} {rb:+5.0f} {np.nanmean([lb, rb]):+5.0f}')
