import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
W = Path(__file__).resolve().parent
PL = W.parent / 'male-silhouette'
res = {}
for d in sys.argv[1:]:
    r = {}
    for v in ['bald_front', 'bald_back', 'left', 'right', 'sheet_front', 'sheet_back']:
        m = np.array(Image.open(Path(d) / f'{v}.png').getchannel('A')) > 127
        p = np.array(Image.open(PL / f'{v}_target.png').convert('L')) > 127
        x = int((m ^ p).sum()); u = int((m | p).sum())
        r[v] = dict(xor=x, union=u, pct=round(100.0 * x / u, 3), plate_only=int((p & ~m).sum()), mesh_only=int((m & ~p).sum()))
    res[d] = r
    print(d, {k: v['pct'] for k, v in r.items()})
json.dump(res, open(W / 'data/sil_native.json', 'w'), indent=1)
