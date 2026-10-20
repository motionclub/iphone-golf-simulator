"""side-silhouette depth deficit (plate - mesh) averaged over left/right; python3.13 depthdef.py <tag> [<tag2>...]"""
import sys, json, numpy as np
sys.path.insert(0, '.')
import prof
for tag in sys.argv[1:]:
    P = prof.profile(f'r/sil_{tag}')
    out = []
    for z in sorted(P['left']['plate'], key=float):
        zf = float(z)
        if zf < 0.80 or zf > 1.36: continue
        dl = []
        for v in ('left', 'right'):
            a, b = P[v]['plate'][z], P[v]['mesh'][z]
            if a and b: dl.append((a[1] - a[0]) - (b[1] - b[0]))
        out.append((zf, np.mean(dl)))
    print(tag, 'depth deficit mm by z:', ' '.join(f'{z:.2f}:{d:+.0f}' for z, d in out))
    zs = np.array([o[0] for o in out]); ds = np.array([o[1] for o in out]); m = (zs >= 0.92) & (zs <= 1.30)
    print(tag, 'mean deficit z .92-1.30: %.1f mm   rms %.1f' % (ds[m].mean(), np.sqrt((ds[m] ** 2).mean())))
