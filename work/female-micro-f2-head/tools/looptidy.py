"""tidy ordered loop lists: remove self-touching spurs from closed rings; split an eye ring into contiguous upper / lower lid chains"""
import numpy as np


def simple_cycle(ch):
    """closed ring given as an ordered list that may touch itself (spurs): repeatedly remove the SHORTER arc between two occurrences of the same vertex"""
    ch = [int(v) for v in ch]
    while True:
        pos = {}; dup = None
        for i, v in enumerate(ch):
            if v in pos: dup = (pos[v], i); break
            pos[v] = i
        if dup is None: return ch
        i, j = dup; n = len(ch)
        if (j - i) <= n - (j - i): ch = ch[:i + 1] + ch[j + 1:]            # drop the excursion i+1..j (v stays once)
        else: ch = ch[i:j]                                                 # drop the wrap-around arc, keep i..j-1


def split_lids(eye_loop, P, z_split):
    """eye_loop: ordered closed ring of vertex ids -> (upper, lower) contiguous chains (upper: z >= z_split)"""
    lp = [int(v) for v in eye_loop]; n = len(lp)
    up = np.array([P[v, 2] >= z_split for v in lp])
    starts = [i for i in range(n) if up[i] and not up[i - 1]]
    if len(starts) != 1:
        raise RuntimeError(f'eye ring crosses the split height {len(starts)} times')
    s = starts[0]; lp = lp[s:] + lp[:s]; up = np.roll(up, -s)
    k = int(np.argmin(up)) if not up.all() else n
    return lp[:k], lp[k:]
