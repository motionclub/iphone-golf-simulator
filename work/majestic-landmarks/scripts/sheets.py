"""1920x1080 sheet per asset: target crop | matching-angle render | facts, then a 4-view turntable + LOD1/LOD2.
System python3 + PIL:  python3 sheets.py [Name ...]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG = {'A': ('#8ec5f5', '#e8f4ff'), 'B': ('#f7c27a', '#fde9c8'), 'C': ('#4a3a8a', '#f08a4a')}


def font(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc'):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def grad(w, h, top, bot):
    t = tuple(int(top[i:i + 2], 16) for i in (1, 3, 5)); b = tuple(int(bot[i:i + 2], 16) for i in (1, 3, 5))
    im = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        k = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(t[i] + (b[i] - t[i]) * k) for i in range(3)))
    return im


def fit(im, w, h):
    k = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)


def panel(png, w, h, course, crop_alpha=True):
    g = grad(w, h, *BG[course])
    if not Path(png).exists():
        return g
    im = Image.open(png).convert('RGBA')
    if crop_alpha and im.getbbox():
        bb = im.split()[3].getbbox()
        if bb:
            pad = int(max(bb[2] - bb[0], bb[3] - bb[1]) * 0.08)
            im = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))
    im = fit(im, w - 10, h - 10)
    g.paste(im, ((w - im.width) // 2, (h - im.height) // 2), im)
    return g


def sheet(name, gates=None):
    m = json.loads((ROOT / 'proof/metrics' / f'{name}.json').read_text())
    c = m['course']
    S = Image.new('RGB', (1920, 1080), '#1d1f24')
    d = ImageDraw.Draw(S)
    F, f, fs = font(30), font(20), font(16)
    # top row: target | match render | facts (each 640x560 incl. caption)
    tgt = ROOT / 'targets' / f"{m.get('target') or name}.jpg"
    if tgt.exists():
        t = fit(Image.open(tgt).convert('RGB'), 630, 520)
        S.paste(t, (5 + (630 - t.width) // 2, 40 + (520 - t.height) // 2))
        tsrc = json.loads((ROOT / 'scripts/targets.json').read_text()).get(m.get('target') or name, ['?'])[0]
        d.text((10, 8), f'TARGET  refs/holes/{tsrc}.jpg (crop)', fill='white', font=f)
    else:
        d.text((10, 8), 'TARGET: none in refs (brief-only asset)', fill='#ffb', font=f)
    S.paste(panel(ROOT / 'renders' / name / 'match.png', 630, 520, c), (645, 40))
    d.text((650, 8), f"BUILT  LOD0, matching angle (az {m['match'][0]}, el {m['match'][1]})", fill='white', font=f)
    x0 = 1290
    d.text((x0, 8), name, fill='white', font=F)
    lod = {k: sum(v['tris'] for n, v in m['reimport'].items() if n.endswith(f'_LOD{k}')) for k in (0, 1, 2)}
    lo, hi = m['bbox_fbx']
    dims = [round(hi[i] - lo[i], 2) for i in range(3)]
    mats = sorted({mm for v in m['reimport'].values() for mm in v['mats']})
    lines = [f"course {c}  holes {', '.join(map(str, m['holes']))}  ({m['kind']})",
             f"tris  LOD0 {lod[0]:,}  LOD1 {lod[1]:,} ({lod[1] / max(1, lod[0]):.0%})  LOD2 {lod[2]}",
             f"budget LOD0 <= {m['budget']:,}",
             f"size  {dims[0]} x {dims[1]} x {dims[2]} m (x, y, z)",
             f"materials: {', '.join(mats)}"]
    if m.get('animated'):
        lines.append('separate parts: ' + '; '.join(f'{a} ({b})' for a, b in m['animated']))
    yy = 52
    import textwrap
    for ln in lines:
        for w in textwrap.wrap(ln, 58):
            d.text((x0, yy), w, fill='#dde', font=fs); yy += 22
    yy += 6
    d.text((x0, yy), 'features (SHAPE_MATCH checklist):', fill='white', font=fs); yy += 22
    for ft in m.get('features', []):
        for w in textwrap.wrap('- ' + ft, 58):
            d.text((x0, yy), w, fill='#cfc', font=fs); yy += 20
    if gates:
        yy += 8
        for g, (ok, why) in gates.items():
            d.text((x0, yy), f"{'PASS' if ok else 'FAIL'}  {g}", fill='#7f7' if ok else '#f77', font=fs); yy += 20
    # bottom row: 4 turntable + LOD1 + LOD2 (6 x 320)
    labels = ['30', '120', '210', '300']
    for k, az in enumerate(labels):
        S.paste(panel(ROOT / 'renders' / name / f'turn_{int(az):03d}.png', 315, 440, c), (5 + k * 320, 600))
        d.text((10 + k * 320, 572), f'LOD0 az {az}', fill='white', font=f)
    S.paste(panel(ROOT / 'renders' / name / 'lod1.png', 315, 440, c), (5 + 4 * 320, 600))
    d.text((10 + 4 * 320, 572), f'LOD1 {lod[1]:,} tris', fill='white', font=f)
    if m.get('no_impostor'):
        d.text((10 + 5 * 320, 572), 'LOD2: none (flat kit piece)', fill='white', font=f)
        for k2, w in enumerate(textwrap.wrap(m.get('no_impostor_why', ''), 30)):
            d.text((10 + 5 * 320, 620 + 22 * k2), w, fill='#ccd', font=fs)
    else:
        S.paste(panel(ROOT / 'renders' / name / 'lod2.png', 315, 440, c), (5 + 5 * 320, 600))
        d.text((10 + 5 * 320, 572), 'LOD2 impostor cards', fill='white', font=f)
    out = ROOT / 'sheets' / f'{name}.jpg'
    S.save(out, quality=88)
    return out


if __name__ == '__main__':
    names = sys.argv[1:] or [p.stem for p in sorted((ROOT / 'proof/metrics').glob('*.json'))]
    for n in names:
        print(sheet(n))
