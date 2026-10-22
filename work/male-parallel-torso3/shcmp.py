"""plate | plate-lit render of several candidates, torso crops, with contrast boost.  python3.13 shcmp.py out.png tag1 tag2 ..."""
import sys; sys.path.insert(0, '.')
from relcorr import *
from PIL import Image
import numpy as np
out = sys.argv[1]; tags = sys.argv[2:]
BOX = {'front': (225, 140, 485, 440), 'back': (790, 140, 1050, 440)}
def boost(im, k=2.2):
    a = np.asarray(im.convert('L')).astype('float32'); m = np.median(a[100:600, 200:1100]); return Image.fromarray(np.clip((a - 100) * k + 100, 0, 255).astype('uint8')).convert('RGB')
rows = []
for v in ('front', 'back'):
    box = BOX[v]; cols = [boost(PL).crop(box)] + [boost(Image.open(f'r/{t}sh/{v}.png')).crop(box) for t in tags]
    cols = [c.resize((int(c.width * 1.7), int(c.height * 1.7)), Image.LANCZOS) for c in cols]; rows.append(cols)
W_ = sum(c.width for c in rows[0]) + 6 * (len(rows[0]) - 1); s = Image.new('RGB', (W_, rows[0][0].height * 2 + 6))
for r, cols in enumerate(rows):
    x = 0
    for c in cols: s.paste(c, (x, r * (cols[0].height + 6))); x += c.width + 6
s.save(out); print(out, s.size)
