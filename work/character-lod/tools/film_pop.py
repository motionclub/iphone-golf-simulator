"""Pop check on a LOD film: at every frame where the hero's level changes, the frame-to-frame image change vs its neighbours
(the camera moves every frame, so a pop shows as a spike). film_levels.tsv + film/fNNNN.jpg from CharacterLodProbe."""
import sys, os, numpy as np
from PIL import Image
d = sys.argv[1]
lv = [l.split('\t') for l in open(os.path.join(d, 'film_levels.tsv')).read().strip().split('\n')[1:]]
level = [int(x[3]) for x in lv]; sh = [float(x[2]) for x in lv]
def img(i): return np.asarray(Image.open(os.path.join(d, 'film', f'f{i:04d}.jpg')).convert('L'), dtype=np.float32)
cache = {}
def box(i, a):
    # the probe's camera aims at the hero's middle: a box of the hero's screen height (x 0.6 wide) around the image centre
    H, W = a.shape; h = int(min(H, sh[i] * H) / 2) + 4; w = int(h * .6) + 4
    return a[max(0, H // 2 - h):H // 2 + h, max(0, W // 2 - w):W // 2 + w]
def diff(i):
    if i not in cache: cache[i] = float(np.abs(box(i, img(i)) - box(i, img(i - 1))).mean())
    return cache[i]
worst = 0; lines = []
for f in range(1, len(level)):
    if level[f] == level[f - 1]: continue
    # the new level is visible from frame f (LateUpdate picked it before that frame rendered)
    nb = [diff(k) for k in range(max(1, f - 6), min(len(level), f + 7)) if k != f and level[k] == level[k - 1]]
    r = diff(f) / max(1e-6, float(np.median(nb)))
    worst = max(worst, r)
    lines.append(f'frame {f}: LOD{level[f-1]}->LOD{level[f]}  change {diff(f):.3f} vs neighbours median {np.median(nb):.3f}  ratio {r:.2f}')
print('\n'.join(lines)); print(f'worst swap/neighbour ratio {worst:.2f}  GATE (<= 1.5): {"PASS" if worst <= 1.5 else "FAIL"}')
