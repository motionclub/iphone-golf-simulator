"""structural edge comparison: plate (red) vs mesh Unity-like render (cyan) -- gradient magnitude after local contrast normalisation.  python3.13 edgecmp.py <ul_dir> <view> <out.png>"""
import sys; sys.path.insert(0, '.')
from m1i_lib import *
d, view, out = sys.argv[1:4]
BOX = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
CROP = {'front': (150, 40, 700, 580), 'left': (100, 40, 700, 580), 'q3L': (100, 20, 740, 540), 'q3R': (100, 20, 740, 540)}
def blur(a, s):
    k = int(max(1, round(3 * s))); xs = np.arange(-k, k + 1); w = np.exp(-0.5 * (xs / s) ** 2); w /= w.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 1, a)
def edges(img):
    g = np.asarray(img.convert('L')).astype(float)
    g = blur(g, 2.2)
    gy, gx = np.gradient(g); mag = np.hypot(gx, gy)
    loc = blur(mag, 14) + 1.5
    return np.clip(mag / loc / 2.2, 0, 1)
p = PLATE.crop(BOX[view]); p = p.resize((p.width * 2, p.height * 2), Image.LANCZOS)
m = Image.open(f'{d}/plate_{view}.png').convert('RGB').resize(p.size, Image.LANCZOS)
c = CROP[view]
ep = edges(p)[c[1]:c[3], c[0]:c[2]]; em = edges(m)[c[1]:c[3], c[0]:c[2]]
rgb = np.zeros(ep.shape + (3,)); rgb[..., 0] = ep; rgb[..., 1] = em; rgb[..., 2] = em     # red = plate edge, cyan = mesh edge, white = both
Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(out); print(out, rgb.shape)
