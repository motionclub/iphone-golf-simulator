"""bpview5.py: band-pass view plate | model(s) | diff for the chest front view at the plate-matched gain.  python3 tools/bpview5.py out.png [--gain 1.5] [--sig 6] tag=coords.npy ..."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import costb5 as cb

def main(out, items, gain=1.5, sig=6.0, k=7.0, sc=3):
    bpp = cb.bp(cb.PLATE, sig)
    ims = []
    def to_img(a, lab):
        im = Image.fromarray(np.clip(128 + k * a, 0, 255).astype(np.uint8)).resize((a.shape[1] * sc, a.shape[0] * sc), Image.LANCZOS).convert('RGB')
        ImageDraw.Draw(im).text((6, 6), lab, fill=(255, 0, 0)); return im
    ims.append(to_img(bpp, f'PLATE bp(sigma={sig})'))
    for tag, p in items:
        co = np.load(p).astype(np.float64)
        img, mask = cb.render_front(co, gain)
        bpm = cb.bp(img, sig); bpm[~mask] = 0
        ims.append(to_img(bpm, f'{tag} bp'))
        d = bpm - bpp; d[~mask] = 0
        rgb = np.zeros(d.shape + (3,), np.uint8)
        rgb[..., 0] = np.clip(128 + 1.8 * k * np.maximum(-d, 0), 0, 255); rgb[..., 2] = np.clip(128 + 1.8 * k * np.maximum(d, 0), 0, 255); rgb[..., 1] = np.clip(128 - 0.9 * k * np.abs(d), 0, 255)
        im = Image.fromarray(rgb).resize((d.shape[1] * sc, d.shape[0] * sc), Image.LANCZOS); ImageDraw.Draw(im).text((6, 6), f'{tag} - plate (red: model darker, blue: brighter)', fill=(255, 255, 255)); ims.append(im)
    W = Image.new('RGB', (sum(i.width for i in ims), ims[0].height)); x = 0
    for im in ims: W.paste(im, (x, 0)); x += im.width
    W.save(out); print(out, W.size)

if __name__ == '__main__':
    a = sys.argv[1:]; out = a[0]; a = a[1:]; gain = 1.5; sig = 6.0
    while a and a[0].startswith('--'):
        if a[0] == '--gain': gain = float(a[1])
        if a[0] == '--sig': sig = float(a[1])
        a = a[2:]
    main(out, [x.split('=', 1) for x in a], gain, sig)
