"""Tiny PIL line plots for the integrity proofs (no matplotlib on this machine)."""
from PIL import Image, ImageDraw, ImageFont

COLORS = [(31, 119, 180), (214, 39, 40), (44, 160, 44), (255, 127, 14), (148, 103, 189), (140, 86, 75)]


def font(sz=14):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc'):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def lines(series, w=640, h=300, title='', xlabel='', ylabel='', vlines=(), hlines=(), ylim=None, xlim=None):
    """series: list of (label, xs, ys). vlines/hlines: list of (value, label)."""
    im = Image.new('RGB', (w, h), 'white'); d = ImageDraw.Draw(im); f = font(13); ft = font(15)
    L, R, T, B = 52, 12, 30, 34
    xs = [x for _, X, _ in series for x in X]; ys = [y for _, _, Y in series for y in Y]
    x0, x1 = xlim or (min(xs), max(xs)); y0, y1 = ylim or (min(ys + [v for v, _ in hlines]), max(ys + [v for v, _ in hlines]))
    if y1 - y0 < 1e-9: y1 = y0 + 1
    if x1 - x0 < 1e-9: x1 = x0 + 1
    X = lambda x: L + (x - x0) / (x1 - x0) * (w - L - R)
    Y = lambda y: h - B - (y - y0) / (y1 - y0) * (h - T - B)
    d.rectangle([L, T, w - R, h - B], outline=(180, 180, 180))
    for k in range(5):
        yv = y0 + (y1 - y0) * k / 4; d.line([L, Y(yv), w - R, Y(yv)], fill=(235, 235, 235)); d.text((4, Y(yv) - 7), f'{yv:.3g}', fill='black', font=f)
        xv = x0 + (x1 - x0) * k / 4; d.text((X(xv) - 12, h - B + 4), f'{xv:.3g}', fill='black', font=f)
    for v, lab in vlines:
        d.line([X(v), T, X(v), h - B], fill=(120, 120, 120), width=1); d.text((X(v) + 3, T + 2), lab, fill=(90, 90, 90), font=f)
    for v, lab in hlines:
        d.line([L, Y(v), w - R, Y(v)], fill=(200, 120, 120), width=1); d.text((w - R - 8 * len(lab) - 4, Y(v) - 15), lab, fill=(170, 70, 70), font=f)
    for k, (lab, XS, YS) in enumerate(series):
        c = COLORS[k % len(COLORS)]
        pts = [(X(x), Y(min(max(y, y0), y1))) for x, y in zip(XS, YS)]
        if len(pts) > 1: d.line(pts, fill=c, width=2)
        for p in pts: d.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=c)
        d.text((L + 8 + 170 * k, h - 16), lab, fill=c, font=f)
    d.text((L, 6), title, fill='black', font=ft)
    if ylabel: d.text((L + 4, T + 2), ylabel, fill=(90, 90, 90), font=f)
    return im


def grid(images, cols):
    w = max(i.width for i in images); h = max(i.height for i in images); rows = (len(images) + cols - 1) // cols
    out = Image.new('RGB', (w * cols, h * rows), 'white')
    for k, im in enumerate(images): out.paste(im, ((k % cols) * w, (k // cols) * h))
    return out


def label(im, text, sz=22):
    d = ImageDraw.Draw(im); f = font(sz); d.rectangle([0, 0, im.width, sz + 10], fill=(0, 0, 0)); d.text((6, 4), text, fill='white', font=f); return im
