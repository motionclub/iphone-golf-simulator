"""plate-lit zoom comparison of a region: python3.13 zoomsh.py out.png view z0 z1 xhalf tag1 tag2 ..."""
import sys; sys.path.insert(0, '.')
from relcorr import *
from PIL import Image
import numpy as np
out, view, z0, z1, xh = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]); tags = sys.argv[6:]
c = CAM['bald_' + view]; mpp = c['metres_per_pixel']
box = (int(c['centre_x'] - xh / mpp), int(c['sole_y'] - z1 / mpp), int(c['centre_x'] + xh / mpp), int(c['sole_y'] - z0 / mpp))
def boost(im, k=3.2):
    a = np.asarray(im.convert('L')).astype('float32'); return Image.fromarray(np.clip((a - 105) * k + 110, 0, 255).astype('uint8')).convert('RGB')
cols = [boost(PL).crop(box)] + [boost(Image.open(f'r/{t}sh/{view}.png')).crop(box) for t in tags]
Z = 3; cols = [c_.resize((c_.width * Z, c_.height * Z), Image.LANCZOS) for c_ in cols]
s = Image.new('RGB', (sum(c_.width for c_ in cols) + 6 * (len(cols) - 1), cols[0].height)); x = 0
for c_ in cols: s.paste(c_, (x, 0)); x += c_.width + 6
s.save(out); print(out, s.size)
