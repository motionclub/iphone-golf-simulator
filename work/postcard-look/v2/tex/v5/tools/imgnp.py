"""Load a PNG/JPG as float32 sRGB 0..1 (H,W,3) for numpy-only python (Blender's python3.13 has numpy, no Pillow).
JPG (and any non-8-bit PNG) goes through system python3 + Pillow, dumped as raw RGB."""
import os, subprocess, tempfile, numpy as np

def load(path):
    tmp = tempfile.mktemp(suffix='.rgb')
    code = ("import sys\nfrom PIL import Image\nim=Image.open(sys.argv[1]).convert('RGB')\n"
            "open(sys.argv[2],'wb').write(im.size[0].to_bytes(4,'little')+im.size[1].to_bytes(4,'little')+im.tobytes())\n")
    subprocess.check_call(['/usr/bin/env', 'python3', '-c', code, path, tmp])
    b = open(tmp, 'rb').read(); os.remove(tmp)
    w = int.from_bytes(b[:4], 'little'); h = int.from_bytes(b[4:8], 'little')
    return (np.frombuffer(b[8:], np.uint8).reshape(h, w, 3).astype(np.float32) / 255.0)

def lum(a):
    return a[..., 0] * .2126 + a[..., 1] * .7152 + a[..., 2] * .0722

def wsd(l, w):
    H, W = l.shape; h2, w2 = H // w, W // w
    if h2 == 0 or w2 == 0: return np.array([np.nan])
    return l[:h2 * w, :w2 * w].reshape(h2, w, w2, w).std(axis=(1, 3)).ravel()

def hsv_of_mean(rgb):
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*[float(x) for x in rgb])
    return h * 360, s, v
