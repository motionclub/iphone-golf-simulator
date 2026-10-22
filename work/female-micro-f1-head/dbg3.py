import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl
d = np.load(fl.W / sys.argv[1]); P = d['V']; Fo = d['F']; off = d['Foff']
F = [Fo[off[i]:off[i+1]] for i in range(len(off)-1)]
big = []
for fi, f in enumerate(F):
    for i in range(len(f)):
        a, b = f[i], f[(i+1) % len(f)]; L = np.linalg.norm(P[a]-P[b])
        if L > 0.03: big.append((L, fi, a, b))
big.sort(reverse=True); print(len(big), 'long edges'); 
for L, fi, a, b in big[:12]: print(round(L*1000,1), fi, a, b, np.round(P[a],3), np.round(P[b],3))
