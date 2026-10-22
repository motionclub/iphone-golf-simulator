import sys
sys.path.insert(0, '.')
from relcorr import *
tags = sys.argv[2:]; out = sys.argv[1]
c = CAM['bald_back']; mpp = c['metres_per_pixel']
# back view: image right = -x ; crop |x|<0.19, z 0.72..1.08
xa, xb = int(c['centre_x'] - 0.19 / mpp), int(c['centre_x'] + 0.19 / mpp); ya, yb = int(c['sole_y'] - 1.08 / mpp), int(c['sole_y'] - 0.72 / mpp)
box = (xa, ya, xb, yb); Z = 6
def enh(img, k=6, s=9):
    c_ = img.crop(box); a = np.asarray(c_).astype('float32'); d = a - blur(a, s)
    return Image.fromarray(np.clip(d * k + 128, 0, 255).astype('uint8')).resize((c_.width * Z, c_.height * Z), Image.LANCZOS)
cols = [PL.crop(box).resize(((xb - xa) * Z, (yb - ya) * Z), Image.LANCZOS), enh(PL)]
for t in tags:
    m = Image.open(R / f'work/male-parallel-torso/r/{t}/back.png').convert('L')
    cols += [m.crop(box).resize(((xb - xa) * Z, (yb - ya) * Z), Image.LANCZOS), enh(m)]
s = Image.new('L', (sum(c.width for c in cols) + 6 * (len(cols) - 1), cols[0].height)); x = 0
for c_ in cols: s.paste(c_, (x, 0)); x += c_.width + 6
s = s.resize((s.width * 2 // 3, s.height * 2 // 3)); s.save(out); print(out, s.size)
