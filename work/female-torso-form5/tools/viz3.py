"""FORM3 visual helpers (Pillow + numpy, system python3).
plate_front_chest / plate_back_pelvis crops are framed EXACTLY like the render3 shots defined in shots_roi() so that
plate | model panels have the same scale and centre.
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps

ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
S = 0.0025954198473282443
FC, BC, SOLE = 440.0, 847.0, 679.0
BALD = Image.open(ROOT + 'ArtDir/hero/base_lock/female_body_bald.jpg').convert('L')
SHEET = Image.open(ROOT + 'ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('L')
FB = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
FR = '/System/Library/Fonts/Supplemental/Arial.ttf'


def font(sz, b=True):
    return ImageFont.truetype(FB if b else FR, sz)


# ROI definitions (plate pixel boxes of the bald plate) -> render3 shots
ROIS = {
    'chest': dict(view='front', box=(370, 130, 520, 310), yaw=0, scale=5),
    'chestW': dict(view='front', box=(350, 120, 540, 330), yaw=0, scale=4),
    'pelvis': dict(view='back', box=(750, 250, 950, 420), yaw=180, scale=5),
    'pelvisW': dict(view='back', box=(740, 230, 960, 440), yaw=180, scale=4),
    'torso_front': dict(view='front', box=(340, 120, 550, 400), yaw=0, scale=3),
    'torso_back': dict(view='back', box=(740, 120, 955, 420), yaw=180, scale=3),
}


def roi_shot(name, roi):
    r = ROIS[roi]
    x0, y0, x1, y1 = r['box']
    cx = FC if r['view'] == 'front' else BC
    sgn = 1 if r['view'] == 'front' else -1
    col = 0.5 * (x0 + x1)
    row = 0.5 * (y0 + y1)
    w, h = (x1 - x0) * r['scale'], (y1 - y0) * r['scale']
    return dict(name=name, yaw=r['yaw'], xc=sgn * (col - cx) * S, zc=(SOLE - row) * S, w=(x1 - x0) * S, res=[w, h])


def plate_crop(roi, enhance=1.0, autocontrast=False):
    r = ROIS[roi]
    c = BALD.crop(r['box'])
    c = c.resize((c.width * r['scale'], c.height * r['scale']), Image.LANCZOS)
    if autocontrast:
        c = ImageOps.autocontrast(c, cutoff=0.5)
    if enhance != 1.0:
        c = ImageEnhance.Contrast(c).enhance(enhance)
    return c.convert('RGB')


def label(img, t, xy=(8, 6), col=(255, 255, 255), sz=18, bg=(0, 0, 0)):
    dr = ImageDraw.Draw(img)
    w = dr.textlength(t, font=font(sz))
    dr.rectangle([xy[0] - 4, xy[1] - 3, xy[0] + w + 6, xy[1] + sz + 5], fill=bg)
    dr.text(xy, t, font=font(sz), fill=col)
    return img


def banner(img, text, sub=None, h=54):
    W = Image.new('RGB', (img.width, img.height + h), (24, 24, 28))
    W.paste(img, (0, h))
    dr = ImageDraw.Draw(W)
    dr.text((14, 8), text, font=font(24), fill=(255, 255, 255))
    if sub:
        dr.text((14, h - 20), sub, font=font(13, False), fill=(190, 190, 200))
    return W


def bgcomp(path):
    m = Image.open(path).convert('RGBA')
    bg = Image.new('RGBA', m.size, (225, 225, 228, 255))
    bg.alpha_composite(m)
    return bg.convert('RGB')


def strip(images, labels, scale=None):
    """horizontal strip of equally sized panels"""
    ims = [i if isinstance(i, Image.Image) else bgcomp(i) for i in images]
    h = ims[0].height
    ims = [i.resize((int(i.width * h / i.height), h), Image.LANCZOS) if i.height != h else i for i in ims]
    W = Image.new('RGB', (sum(i.width for i in ims), h))
    x = 0
    for i, l in zip(ims, labels):
        label(i, l)
        W.paste(i, (x, 0))
        x += i.width
    if scale:
        W = W.resize((int(W.width * scale), int(W.height * scale)), Image.LANCZOS)
    return W


if __name__ == '__main__':
    # python3 tools/viz3.py out.png roi label1=img1 label2=img2 ...
    out, roi = sys.argv[1], sys.argv[2]
    pairs = [a.split('=', 1) for a in sys.argv[3:]]
    ims = [plate_crop(roi, 1.0)] + [p[1] for p in pairs]
    strip(ims, ['PLATE'] + [p[0] for p in pairs]).save(out)
    print(out)


# ----------------------------------------------------------------------------------------------- band-pass structure maps
def _gblur_np(a, s):
    k = int(max(1, round(3 * s)))
    xs = np.arange(-k, k + 1)
    w = np.exp(-0.5 * (xs / s) ** 2)
    w /= w.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 1, a)


def bandpass(img, scale, s1=1.2, s2=9.0, gain=4.0):
    """DoG structure map (sigmas in ORIGINAL plate pixels; `scale` = upsampling of the given image)"""
    a = np.asarray(img.convert('L'), dtype=np.float64)
    # work at 1/2 res for speed
    f = 2
    small = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((a.shape[1] // f, a.shape[0] // f), Image.LANCZOS), dtype=np.float64)
    sc = scale / f
    d = _gblur_np(small, s1 * sc) - _gblur_np(small, s2 * sc)
    out = np.clip(128 + gain * d, 0, 255).astype(np.uint8)
    return Image.fromarray(out).resize((a.shape[1], a.shape[0]), Image.LANCZOS).convert('RGB')


def structure_strip(roi, files, labels, gain=4.0, s1=1.2, s2=9.0, scale_out=None):
    sc = ROIS[roi]['scale']
    pl = plate_crop(roi, 1.0)
    ims = [bandpass(pl, sc, s1, s2, gain)]
    for f in files:
        ims.append(bandpass(bgcomp(f) if isinstance(f, str) else f, sc, s1, s2, gain))
    return strip(ims, ['PLATE bandpass'] + labels, scale=scale_out)
