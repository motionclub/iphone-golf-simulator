import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitcheck import overlap_pairs
from collections import Counter
A, B = sys.argv[sys.argv.index('--')+1:][:2]       # e.g. sockR_male shoeR_male
da, db = np.load(f'{WORK}/data/{A}.npz'), np.load(f'{WORK}/data/{B}.npz')
pairs = overlap_pairs(da['V'], da['F'], db['V'], db['F'])
ga = sorted(set(p[0] for p in pairs)); gb = sorted(set(p[1] for p in pairs))
print(f"{A} vs {B}: {len(pairs)} pairs, {len(ga)} tris in A, {len(gb)} tris in B")
for nm, d, ids in ((A, da, ga), (B, db, gb)):
    if 'T' in d.files and ids:
        names = list(d['tagnames']); print(f"  {nm} by tag:", dict(Counter(names[d['T'][i]] for i in ids)))
        C = d['V'][d['F'][ids]].mean(1)
        print(f"  {nm} centroid bbox", C.min(0).round(3).tolist(), C.max(0).round(3).tolist())
