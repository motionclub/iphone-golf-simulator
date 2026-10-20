"""Ball-to-background contrast in the lob band of a gameplay or postcard capture.

The ball felt measured in the shipped gameplay shots (hue 67 deg, S .65, V .69-.92) is taken as sRGB (.72, .80, .27).
For each pixel of the central band behind the far baseline we compute the WCAG-style contrast ratio between the ball
and that pixel (linear luminance). Usage:
    ball_contrast.py <dir> [prefix]       prints median ratio and the share of pixels under 1.5:1 / 2:1 / 3:1
"""
import sys, numpy as np
from PIL import Image

BALL = np.array([.72, .80, .27], dtype=np.float32)

def lin(c): return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
def lum(a): return lin(a) @ np.array([.2126, .7152, .0722], dtype=np.float32)

BALL_Y = float(lum(BALL[None, None, :])[0, 0])

def report(path, rows, cols=(400, 1520)):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)[rows[0]:rows[1], cols[0]:cols[1]] / 255
    y = lum(a)
    cr = (np.maximum(y, BALL_Y) + .05) / (np.minimum(y, BALL_Y) + .05)
    return dict(median=float(np.median(cr)), under15=float((cr < 1.5).mean() * 100), under2=float((cr < 2).mean() * 100), under3=float((cr < 3).mean() * 100))

SHOTS = {'1_gameplay': (150, 445), '2_postcard': (30, 470)}

if __name__ == '__main__':
    d = sys.argv[1].rstrip('/') + '/'
    for name in ['skyscraper', 'volcano', 'resort']:
        for shot, rows in SHOTS.items():
            try: r = report(f'{d}{name}_{shot}.png', rows)
            except FileNotFoundError: continue
            print(f"{name:10s} {shot:11s} ball:background median {r['median']:.2f}:1 | under 1.5:1 {r['under15']:5.1f}% | under 2:1 {r['under2']:5.1f}% | under 3:1 {r['under3']:5.1f}%")
