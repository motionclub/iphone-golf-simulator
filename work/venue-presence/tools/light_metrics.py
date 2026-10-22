"""VOLCANO_LIGHT metric: how much lava light reaches the slab edge.

The apron's outer strip (x in +-[7.8, 10], the 2.2 m the glow covers) is projected into each capture with the capture
tool's own camera parameters, so the old and new frames are compared over the same patch of floor. Warmth = mean (R - B)
of the pixels (0..1 scale); luminance is Rec.709. The court interior (x in +-[1, 4], z in [-9, -3]) is the control.

    light_metrics.py <old_dir> <new_dir>
"""
import sys
import numpy as np
from PIL import Image, ImageDraw

CAMS = {   # name: (position, look-at, vertical fov)
    '1_gameplay': ((0, 3.5, -15.6), (0, 1.15, -3.2), 56),
    '2_postcard': ((0, 9, -30), (0, 1, 6), 46),
}

def project(P, cam, look, fov, W=1920, H=1080):
    P, C, L = np.array(P, float), np.array(cam, float), np.array(look, float)
    f = L - C; f /= np.linalg.norm(f)
    right = np.cross([0, 1, 0], f); right /= np.linalg.norm(right)
    up = np.cross(f, right)
    v = P - C; zc = v @ f
    t = np.tan(np.radians(fov) / 2)
    return ((v @ right / (zc * t * W / H) + 1) / 2 * W, (1 - (v @ up) / (zc * t)) / 2 * H)

def mask(shot, x0, x1, z0, z1, y=.07):
    cam, look, fov = CAMS[shot]
    pts = [project((x, y, z), cam, look, fov) for x, z in [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]]
    m = Image.new('L', (1920, 1080), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.asarray(m) > 0

def measure(path, shot, region):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255
    m = mask(shot, *region)
    if m.sum() < 50: return None
    px = a[m]
    return dict(px=int(m.sum()), warmth=float((px[:, 0] - px[:, 2]).mean()), lum=float((px @ np.array([.2126, .7152, .0722])).mean()), red=float(px[:, 0].mean()))

if __name__ == '__main__':
    old, new = sys.argv[1].rstrip('/'), sys.argv[2].rstrip('/')
    regions = {'left strip (x -10..-7.8)': (-10, -7.8, -4, 10), 'right strip (x 7.8..10)': (7.8, 10, -4, 10), 'control: court interior': (1, 4, -9, -3)}
    for shot in CAMS:
        print(f'== {shot}')
        for name, reg in regions.items():
            o = measure(f'{old}/volcano_{shot}.png', shot, reg); n = measure(f'{new}/volcano_{shot}.png', shot, reg)
            if not o or not n: print(f'   {name:28s} (outside the frame)'); continue
            print(f"   {name:28s} warmth R-B: {o['warmth']:+.3f} -> {n['warmth']:+.3f}   red: {o['red']:.3f} -> {n['red']:.3f}   luminance: {o['lum']:.3f} -> {n['lum']:.3f}   ({n['px']} px)")
