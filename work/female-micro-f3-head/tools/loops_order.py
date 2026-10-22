"""ordered-chain audit of the patch loops: consecutive adjacency, closure, uniqueness.  python3 loops_order.py <tag> <out.json>"""
import json, sys, collections
import numpy as np
tag, out = sys.argv[1], sys.argv[2]
pd = np.load(f'data/{tag}_patch.npz'); P = pd['P']; off = pd['Foff']; flat = pd['F']; pj = json.load(open(f'data/{tag}_patch.json'))
F = [np.asarray(flat[off[i]:off[i + 1]]) for i in range(len(off) - 1)]
adj = collections.defaultdict(set)
for f in F:
    k = len(f)
    for i in range(k):
        a, b = int(f[i]), int(f[(i + 1) % k]); adj[a].add(b); adj[b].add(a)
CLOSED = {'eyeL', 'eyeR', 'nostril_L', 'nostril_R', 'ear_attach_L', 'ear_attach_R', 'helix_L', 'helix_R', 'concha_L', 'concha_R'}
res = {}
for nm, ch in pj['loops'].items():
    ch = [int(v) for v in ch]
    seq_ok = all(ch[i + 1] in adj[ch[i]] for i in range(len(ch) - 1))
    close_ok = ch[0] in adj[ch[-1]]
    uniq = len(set(ch)); dup = len(ch) - uniq
    kind = 'closed' if nm in CLOSED else 'open'
    ok = seq_ok and (close_ok if kind == 'closed' else True) and (dup <= 1)
    # arc-length along the chain and spacing
    el = np.linalg.norm(P[ch][1:] - P[ch][:-1], axis=1) * 1000
    res[nm] = dict(kind=kind, n=len(ch), unique=uniq, consecutive_adjacent=bool(seq_ok), closes=bool(close_ok), spacing_mm_mean=float(el.mean()), spacing_mm_max=float(el.max()), ok=bool(ok))
    print(f'{nm:16s} {kind:6s} n={len(ch):4d} unique={uniq:4d} edge-path={seq_ok} closes={close_ok} spacing mean {el.mean():.2f} max {el.max():.2f} mm  {"OK" if ok else "CHECK"}')
json.dump(res, open(out, 'w'), indent=1)
