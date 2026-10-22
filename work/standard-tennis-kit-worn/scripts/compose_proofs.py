"""Compose the proof sheets from proof/raw cells (system python + Pillow).  python3 compose_proofs.py"""
import json, os, sys, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-worn/'
RAW = W + 'proof/raw/'
OUT = W + 'proof/'
BG = (30, 31, 34)


def font(sz):
    for p in ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Supplemental/Arial.ttf', '/Library/Fonts/Arial.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def label(img, text, xy, sz=22, fill=(235, 235, 235), bg=None):
    d = ImageDraw.Draw(img)
    f = font(sz)
    if bg:
        tw = d.textlength(text, font=f)
        d.rectangle([xy[0] - 4, xy[1] - 2, xy[0] + tw + 4, xy[1] + sz + 4], fill=bg)
    d.text(xy, text, font=f, fill=fill)


def grid(title, rows, col_labels, cell, row_labels=None, footer=None, bgs=None):
    """rows: list of lists of image paths (or None); returns a sheet with a title bar, column labels, row labels."""
    w, h = cell
    ncol = max(len(r) for r in rows)
    top = 74
    lab = 24 if row_labels else 0
    foot = 40 if footer else 0
    sheet = Image.new('RGB', (ncol * w + lab, top + len(rows) * (h + 6) + foot), BG)
    label(sheet, title, (14, 10), 26)
    for c, t in enumerate(col_labels or []):
        label(sheet, t, (lab + c * w + w // 2 - 6 * len(t) // 1, 44), 18, (200, 200, 200))
    for r, row in enumerate(rows):
        y = top + r * (h + 6)
        if row_labels:
            d = Image.new('RGB', (h, lab), BG)
            label(d, row_labels[r], (6, 2), 18, (240, 200, 120))
            sheet.paste(d.rotate(90, expand=True), (0, y))
        for c, p in enumerate(row):
            if p is None or not os.path.exists(p):
                continue
            im = Image.open(p).convert('RGB')
            if im.size != (w, h):
                im = im.resize((w, h))
            sheet.paste(im, (lab + c * w, y))
    if footer:
        label(sheet, footer, (14, sheet.height - 32), 18, (190, 190, 190))
    return sheet


def onbody(gender, tag, title):
    views = ('front', 'back', 'left', 'right', 'q3')
    rows = [[f'{RAW}onbody_{gender}_{tag}_{cw}_{v}.png' for v in views] for cw in ('White', 'Black')]
    if not os.path.exists(rows[0][0]):
        return None
    return grid(title, rows, ['FRONT', 'BACK', 'LEFT', 'RIGHT', '3/4'], (560, 800), ['WHITE KIT', 'BLACK KIT'])


def waist(gender):
    chk = json.load(open(f'{RAW}checks_{gender}.json'))
    ph = chk['polo_hem']
    rows, rl = [], []
    for cw in ('White', 'Black'):
        rows.append([f'{RAW}waist_{gender}_{cw}_{v}.png' for v in ('front', 'q3', 'side', 'back')])
        rl.append(f'{cw.upper()} wide')
        rows.append([f'{RAW}waist_{gender}_{cw}_{v}.png' for v in ('c_front', 'c_q3', 'c_side', 'c_back')])
        rl.append(f'{cw.upper()} close')
    band = chk['band_color']
    foot = (f"polo hem overlaps the band top by {ph['overlap_mm']['min']:.1f}-{ph['overlap_mm']['max']:.1f} mm (mean {ph['overlap_mm']['mean']:.1f}); band {ph['band_height_mm']:.0f} mm tall, "
            f"{ph['visible_band_below_hem_mm']['min']:.1f}-{ph['visible_band_below_hem_mm']['max']:.1f} mm of it visible below the hem; white kit band = {band['White']['band_material']}, "
            f"black kit band = {band['Black']['band_material']}; skin exposed at the waist: {chk['skin_flash']['exposed']} of {chk['skin_flash']['ray_tests']} camera rays")
    return grid(f'{gender.upper()} - waist: untucked polo hem over the contrasting waistband (separate objects)', rows, ['FRONT', '3/4', 'SIDE', 'BACK'], (560, 560), rl, footer=foot)


def hem():
    chk = json.load(open(f'{RAW}checks_female.json'))
    sk = chk['skirt']
    rows, rl = [], []
    for cw in ('White', 'Black'):
        rows.append([f'{RAW}hem_female_{cw}_{v}.png' for v in ('front', 'back', 'left', 'right')])
        rl.append(f'{cw.upper()}')
        rows.append([f'{RAW}hem_female_{cw}_{v}.png' for v in ('q3f', 'q3b', 'low_front', 'low_back')])
        rl.append(f'{cw.upper()} 3/4 + low')
    foot = (f"skirt hem z {sk['skirt_hem_z']:.3f} (mid-thigh {sk['mid_thigh_z']:.3f}: {sk['hem_fraction_down_thigh']*100:.0f}% of the way from crotch to knee) vs inner-short hem z {sk['liner_hem_z']:.3f} "
            f"-> skirt longer by {sk['skirt_longer_than_liner_mm']:.0f} mm; liner faces visible at gate views: {chk['liner_visibility']['visible_faces_gate_views']}")
    return grid('FEMALE - skirt hem: front / back / sides / 3/4 / low views (inner shorts must not show)', rows, ['FRONT / 3/4F', 'BACK / 3/4B', 'LEFT / LOW FRONT', 'RIGHT / LOW BACK'], (560, 640), rl, footer=foot)


def liner_mask():
    chk = json.load(open(f'{RAW}checks_female.json'))
    lv = chk['liner_visibility']
    azs = list(range(0, 360, 30))
    els = (-12, 0, 8, 22)
    tw, th = 240, 280
    out = {}
    counts = {}
    for cw in ('White', 'Black'):
        rows, rl = [], []
        tot = collections_counter = 0
        per = {}
        for el in els:
            row = []
            for az in azs:
                p = f'{RAW}mask_female_{cw}_a{az:03d}_e{el:+03d}.png'
                row.append(p)
                if os.path.exists(p):
                    a = np.array(Image.open(p).convert('RGB')).astype(int)
                    m = int(((a[:, :, 0] > 200) & (a[:, :, 1] < 60) & (a[:, :, 2] > 200)).sum())
                    per[(el, az)] = m
            rows.append(row)
            rl.append(f'el {el:+d}')
        counts[cw] = per
        rows.append([f'{RAW}mask_female_{cw}_ctl_front.png', f'{RAW}mask_female_{cw}_ctl_q3.png', f'{RAW}mask_female_{cw}_ctl_back.png'])
        rl.append('control')
        out[cw] = (rows, rl)
    sheets = []
    for cw in ('White', 'Black'):
        rows, rl = out[cw]
        per = counts[cw]
        gate = sum(v for (el, az), v in per.items() if el >= 0)
        under = sum(v for (el, az), v in per.items() if el < 0)
        foot = (f"{cw.upper()} kit, liner painted magenta: magenta pixels at elevations 0/+8/+22 deg (12 azimuths): {gate}; below the horizon (-12 deg, looks up under the hem): {under}.  "
                f"Bottom row = positive control (skirt + flap hidden): the mask works.")
        sheets.append(grid(f'FEMALE {cw.upper()} - liner visibility mask (inner shorts = magenta)', rows, [f'{a} deg' for a in azs], (tw, th), rl, footer=foot))
    w = max(s.width for s in sheets)
    sheet = Image.new('RGB', (w, sum(s.height for s in sheets)), BG)
    y = 0
    for s in sheets:
        sheet.paste(s, (0, y))
        y += s.height
    return sheet, {cw: dict(gate_px=sum(v for (el, az), v in counts[cw].items() if el >= 0), under_px=sum(v for (el, az), v in counts[cw].items() if el < 0)) for cw in counts}


def exploded(gender):
    rows = [[f'{RAW}exploded_{gender}_{cw}_{v}.png' for v in ('front', 'q3', 'back')] for cw in ('White', 'Black')]
    if not os.path.exists(rows[0][0]):
        return None
    return grid(f'{gender.upper()} - exploded: polo, bottom, socks and shoes are separate objects (body hidden)', rows, ['FRONT', '3/4', 'BACK'], (620, 880), ['WHITE KIT', 'BLACK KIT'])


def ids(gender):
    row1 = [f'{RAW}ids_{gender}_{v}.png' for v in ('front', 'q3', 'side', 'back')]
    row2 = [f'{RAW}ids_nobody_{gender}_{v}.png' for v in ('front', 'q3')]
    foot = 'object id colours: polo blue | bottom green | waistband orange (inside the bottom object, slot 2)' + (' | inner shorts (liner) magenta | ' if gender == 'female' else ' | ') + 'socks gold | shoes violet'
    return grid(f'{gender.upper()} - object ids (flat colours, every piece is its own object)', [row1, row2], ['FRONT', '3/4', 'SIDE', 'BACK'], (560, 800), ['on body', 'garments only'], footer=foot)


def clearance(gender):
    views = ['front', 'back', 'right', 'q3']
    cells = [f'{RAW}clear_{gender}_{v}.png' for v in views]
    if not os.path.exists(cells[0]):
        return None
    st = json.load(open(f'{RAW}clear_{gender}.json'))
    sheet = grid(f'{gender.upper()} - clearance heat map (kit on the authority body; colour = distance of each garment vertex to the skin)', [cells], ['FRONT', 'BACK', 'RIGHT', '3/4'], (560, 800))
    d = ImageDraw.Draw(sheet)
    y = sheet.height + 6
    sheet2 = Image.new('RGB', (sheet.width, sheet.height + 80), BG)
    sheet2.paste(sheet, (0, 0))
    d = ImageDraw.Draw(sheet2)
    for k, (txt, col) in enumerate((('< 3 mm', (242, 26, 26)), ('3 - 6 mm', (250, 140, 26)), ('6 - 9 mm', (250, 224, 51)), ('>= 9 mm', (64, 199, 89)))):
        x = 20 + k * 230
        d.rectangle([x, y, x + 34, y + 26], fill=col)
        label(sheet2, txt, (x + 44, y), 22)
    msg = '   '.join(f"{k.replace('_White', '').replace('Kit_', '')}: min {v['min_mm']:+.1f} mm (outer + inner faces)" for k, v in st.items())
    label(sheet2, msg, (14, y + 38), 17, (190, 190, 190))
    return sheet2


def sections(gender):
    f = f'{RAW}sections_{gender}.json'
    if not os.path.exists(f):
        return None
    data = json.load(open(f))
    levels = data['levels']
    cols = {'body': (210, 160, 125), 'polo': (80, 140, 255), 'bottom': (70, 200, 120), 'band': (255, 140, 30)}
    cw, ch = 520, 380
    sheet = Image.new('RGB', (cw * 4, ch * 2 + 80), (24, 25, 28))
    label(sheet, f'{gender.upper()} - horizontal sections: body (tan), polo (blue), bottom fabric (green), waistband (orange) - the polo hem sits OUTSIDE the band', (14, 8), 21)
    for i, z in enumerate(levels):
        x0, y0 = (i % 4) * cw, 44 + (i // 4) * (ch + 18)
        d = ImageDraw.Draw(sheet)
        d.rectangle([x0 + 4, y0, x0 + cw - 4, y0 + ch], outline=(70, 72, 78))
        pts = [p for lname in ('body', 'polo', 'bottom') for loop in data['layers'][lname][i] for p in loop['p']]
        if not pts:
            continue
        # frame on the torso/pelvis: ignore far-out loops (arms) by using the largest body loop's bbox + margin
        body_loops = data['layers']['body'][i]
        big = max(body_loops, key=lambda L: len(L['p'])) if body_loops else None
        pb = big['p'] if big else pts
        xs = [p[0] for p in pb]; ys = [p[1] for p in pb]
        pad = 0.06
        minx, maxx, miny, maxy = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
        s = min((cw - 40) / max(maxx - minx, 1e-3), (ch - 50) / max(maxy - miny, 1e-3))

        def tf(p):
            return (x0 + 20 + (p[0] - minx) * s, y0 + 20 + (maxy - p[1]) * s)
        for name in ('body', 'bottom', 'band', 'polo'):
            for loop in data['layers'][name][i]:
                q = [tf(p) for p in loop['p']]
                if len(q) > 2:
                    d.line(q + ([q[0]] if loop['closed'] else []), fill=cols[name], width=3 if name == 'body' else 2)
        label(sheet, f'z = {z:.3f} m', (x0 + 12, y0 + ch - 28), 18, (210, 210, 210))
    return sheet


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []

    def save(img, name):
        if img is not None:
            img.save(OUT + name)
            made.append(name)
    save(onbody('male', 'authority', 'MALE - HeroBase_Male_Silhouette.blend (sha fd04bc28...) - worn kit, on body'), 'ONBODY_Male.png')
    save(onbody('female', 'authority', 'FEMALE - HeroBase_Female.blend (sha 200dc3b9...) - worn kit, on body'), 'ONBODY_Female.png')
    save(onbody('female', 'arms_candidate', 'FEMALE - arms candidate fit-ref (573ab443...) - polo + skort + candidate-fit socks/sneakers'), 'ONBODY_Female_ArmsCandidate.png')
    for g in ('male', 'female'):
        if os.path.exists(f'{RAW}checks_{g}.json'):
            save(waist(g), f'WAIST_{g.capitalize()}.png')
        save(exploded(g), f'EXPLODED_{g.capitalize()}.png')
        save(ids(g), f'OBJECT_ID_{g.capitalize()}.png')
        save(clearance(g), f'CLEARANCE_{g.capitalize()}.png')
        save(sections(g), f'SECTIONS_{g.capitalize()}.png')
    if os.path.exists(f'{RAW}checks_female.json'):
        save(hem(), 'HEM_Female.png')
        sheet, mc = liner_mask()
        save(sheet, 'LINER_MASK_Female.png')
        json.dump(mc, open(RAW + 'liner_mask_pixels.json', 'w'), indent=1)
        print('magenta px', mc)
    print(made)


main()
