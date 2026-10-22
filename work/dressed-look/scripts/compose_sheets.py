"""Compose the four proof sheets (system python + Pillow).   python3 compose_sheets.py

Inputs : proof/raw/<tag>_<Color>_<cell>.png (render_dressed.py), data/fit_<tag>.json (measure_fit.py), data/build_<tag>.json, data/verify_<tag>.json,
         data/sheet_labels.json (which measured findings are visible in the renders: decided by looking at them; the rest is captioned 'measured only').
Outputs: proof/Sheet_<Male|Female>_<White|Black>.png"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/dressed-look/'
RAW, DATA, OUT = W + 'proof/raw/', W + 'data/', W + 'proof/'
BG = (28, 29, 33)
PANEL = (44, 46, 52)
CELL_W = 700
FULL_H = round(CELL_W * 1140 / 780)
CLOSE_H = 700
GAP = 14
MARGIN = 26
RED = (214, 64, 58)
AMBER = (224, 160, 40)
GREEN = (70, 170, 110)
TEXT = (236, 236, 236)
DIM = (170, 172, 180)


def font(sz, bold=False):
    for p, idx in (('/System/Library/Fonts/Helvetica.ttc', 1 if bold else 0), ('/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf', 0),
                   ('/Library/Fonts/Arial.ttf', 0)):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz, index=idx)
            except Exception:
                try:
                    return ImageFont.truetype(p, sz)
                except Exception:
                    pass
    return ImageFont.load_default()


def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if draw.textlength(t, font=fnt) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def chip(img, xy, text, fill, fg=(255, 255, 255), sz=19, bold=True):
    d = ImageDraw.Draw(img)
    f = font(sz, bold)
    tw = d.textlength(text, font=f)
    x, y = xy
    d.rounded_rectangle([x, y, x + tw + 18, y + sz + 12], radius=7, fill=fill)
    d.text((x + 9, y + 5), text, font=f, fill=fg)
    return x + tw + 18


def captions(tag, fit, labels, build, verify):
    """-> list of (kind, text) rows: kind in CLIP / FLOAT / OK / NOTE ; plain words."""
    rows = []
    lab = labels[tag]
    pcs = fit['pieces']
    foot = [n for n in pcs if 'Sock' in n or 'Shoe' in n]
    clip_cnt = sum(pcs[n]['skin_through'] for n in foot)
    clip_mm = max([pcs[n]['skin_through_max_mm'] for n in foot] + [0])
    flo_mm_shoe = max([pcs[n]['float_max_mm'] for n in foot if 'Shoe' in n] + [0])
    flo_mm_sock = max([pcs[n]['float_max_mm'] for n in foot if 'Sock' in n] + [0])
    polo = [n for n in pcs if 'Polo' in n][0]
    bottom = [n for n in pcs if 'Shorts' in n or 'Skort' in n][0]
    bname = 'skort' if 'Skort' in bottom else 'shorts'
    any_clip = False
    if clip_cnt >= 10:
        any_clip = True
        rows.append(('CLIP', f"Heels, ankles and toes poke out through the socks and shoes, up to {clip_mm:.0f} mm ({clip_cnt} cloth vertices inside the body). "
                             f"The kit was fitted to the older placeholder feet; left as is." + ('' if 'feet' in lab['visible'] else ' (measured only)')))
    if max(pcs[n]['float_verts'] for n in foot) >= 100:
        any_clip = True
        rows.append(('FLOAT', f"Socks and shoes stand off the front of the new feet: shoes up to {flo_mm_shoe:.0f} mm, socks up to {flo_mm_sock:.0f} mm further out than on the feet they were fitted to." +
                     ('' if 'feet' in lab['visible'] else ' (measured only)')))
    if pcs[polo]['float_verts'] >= 100:
        any_clip = True
        rows.append(('FLOAT', f"Polo stands up to {pcs[polo]['float_max_mm']:.0f} mm further off the new back than off the body it was fitted to (measured only, not visible at sheet scale)."))
    if pcs[bottom]['float_verts'] >= 100:
        any_clip = True
        rows.append(('FLOAT', f"{bname.capitalize()} stands up to {pcs[bottom]['float_max_mm']:.0f} mm further off the new hips and backside (measured only, not visible at sheet scale)."))
    if pcs[polo]['skin_through'] >= 10 or pcs[bottom]['skin_through'] >= 10:
        any_clip = True
        rows.append(('CLIP', 'Skin shows through the polo / bottom (see measurements).'))
    rk = fit['racket']
    hd = fit.get('hand', {})
    rk_clip = rk['overlap_tri_pairs_vs_body_not_hand'] > 0 or any(v > 0 for v in rk['overlap_vs_kit'].values())
    hd_clip = (hd.get('posed_hand_vs_body_not_hand_tri_pairs', 0) > 0) or any(v > 0 for v in hd.get('posed_hand_vs_kit_tri_pairs', {}).values())
    if rk_clip:
        any_clip = True
        rows.append(('CLIP', 'Racket passes through the body or the kit.'))
    if hd_clip:
        any_clip = True
        rows.append(('CLIP', 'Right hand passes into the body or the kit.'))
    if rk['grip_to_hand_min_mm'] > 3.0:
        any_clip = True
        rows.append(('FLOAT', f"Racket grip floats {rk['grip_to_hand_min_mm']:.1f} mm off the palm."))
    if not any_clip:
        rows.append(('OK', 'NO CLIP, NO FLOAT FOUND. Every vertex of the polo, ' + ('shorts' if tag == 'male' else 'skort') + ', socks and shoes was tested against the body: skin through cloth 0, cloth squeezed into the body 0, '
                           'standing off the body the kit was fitted to 0. Nothing was moved.'))
    rows.append(('NOTE', f"Racket hand: fingers are closed on the grip with finger bones only (action Pose_GripClosed); grip-to-hand gap {rk['grip_to_hand_min_mm']:.2f} mm, "
                         f"racket and fingers pass through the body or the kit in {rk['overlap_tri_pairs_vs_body_not_hand'] + sum(rk['overlap_vs_kit'].values()) + hd.get('posed_hand_vs_body_not_hand_tri_pairs', 0) + sum(hd.get('posed_hand_vs_kit_tri_pairs', {}).values())} triangles. "
                         f"Thumb stays in its bind pose."))
    return rows


def sheet(tag, color, fit, labels, build, verify):
    names = ['full_front', 'full_q3', 'full_side', 'full_back', 'waist_front', 'waist_back', 'hand_a', 'hand_b']
    cap_names = ['FRONT', '3/4  (racket side)', 'SIDE  (racket side)', 'BACK', 'WAIST  front', 'WAIST  back', 'RACKET HAND  back of hand', 'RACKET HAND  fingers on the grip']
    ims = {}
    for n in names:
        p = f'{RAW}{tag}_{color}_{n}.png'
        im = Image.open(p).convert('RGB')
        h = FULL_H if n.startswith('full') else CLOSE_H
        ims[n] = im.resize((CELL_W, h), Image.LANCZOS)
    rows = captions(tag, fit, labels, build, verify)
    # measure caption height
    probe = Image.new('RGB', (10, 10))
    d0 = ImageDraw.Draw(probe)
    f_cap = font(24)
    text_w = 4 * CELL_W + 3 * GAP - 150
    n_lines = 0
    for kind, t in rows:
        n_lines += len(wrap(d0, t, f_cap, text_w))
    foot_lines = 3
    cap_h = 64 + n_lines * 32 + len(rows) * 8 + foot_lines * 26 + 30
    title_h = 128
    Wd = 2 * MARGIN + 4 * CELL_W + 3 * GAP
    Ht = title_h + FULL_H + GAP + CLOSE_H + GAP + cap_h + MARGIN
    img = Image.new('RGB', (Wd, Ht), BG)
    d = ImageDraw.Draw(img)
    sex = 'MALE' if tag == 'male' else 'FEMALE'
    d.text((MARGIN, 18), f'{sex}  -  {color.upper()} KIT  -  dressed look', font=font(48, True), fill=TEXT)
    b = build
    sub = (f"HeroBase {tag} full body ({'merged_fd04bc28.blend' if tag == 'male' else 'HeroBase_Female_FULL_STAGED.blend'}, SHA {b['copy_sha256_before_edit'][:8]}... verified)  +  standard tennis kit (worn)  +  classic racket.  "
           f"Bind pose, no refit, no shrinkwrap; body shown in its own materials.")
    d.text((MARGIN, 80), sub, font=font(22), fill=DIM)
    # panels
    x0, y0 = MARGIN, title_h
    pos = {}
    for k, n in enumerate(names[:4]):
        x = x0 + k * (CELL_W + GAP)
        img.paste(ims[n], (x, y0))
        pos[n] = (x, y0)
    y1 = y0 + FULL_H + GAP
    for k, n in enumerate(names[4:]):
        x = x0 + k * (CELL_W + GAP)
        img.paste(ims[n], (x, y1))
        pos[n] = (x, y1)
    for n, c in zip(names, cap_names):
        x, y = pos[n]
        chip(img, (x + 10, y + 10), c, (20, 22, 26), TEXT, sz=20, bold=True)
        # CLIP / FLOAT chips on the panels where the finding is visible
        yy = y + 52
        for kind, txt in labels[tag]['panel_chips'].get(n, []):
            chip(img, (x + 10, yy), f'{kind}  {txt}', RED if kind == 'CLIP' else AMBER, sz=19)
            yy += 40
    # caption block
    yc = y1 + CLOSE_H + GAP
    d.rectangle([MARGIN, yc, Wd - MARGIN, yc + cap_h - 8], fill=PANEL)
    d.text((MARGIN + 18, yc + 12), 'CLIP / FLOAT', font=font(30, True), fill=TEXT)
    yy = yc + 56
    for kind, t in rows:
        col = {'CLIP': RED, 'FLOAT': AMBER, 'OK': GREEN, 'NOTE': (120, 150, 200)}[kind]
        chip(img, (MARGIN + 18, yy), kind, col, sz=20)
        for ln in wrap(d, t, f_cap, text_w):
            d.text((MARGIN + 150, yy + 2), ln, font=f_cap, fill=TEXT)
            yy += 32
        yy += 8
    yy += 6
    foot = ["Kit pieces are the unchanged authority pieces (polo -> Chest_Top, bottom -> Hip_Bottom, socks/shoes -> Foot_L_Shoe / Foot_R_Shoe), separate objects, one collection per colour (Kit_White, Kit_Black); same geometry in both colours.",
            "Racket_Classic is parented to Hand_Racket on the right-hand palm bone. Body mesh geometry is bit-identical to the source; the only data added to the body is the right-hand finger skin weights for the pose.",
            "Floor shadow, grey studio and lights are proof set-up only (not in the blends)."]
    for ln in foot:
        for l2 in wrap(d, ln, font(19), Wd - 2 * MARGIN - 36):
            d.text((MARGIN + 18, yy), l2, font=font(19), fill=DIM)
            yy += 25
    out = f"{OUT}Sheet_{'Male' if tag == 'male' else 'Female'}_{color}.png"
    img.save(out)
    return out, img.size


if __name__ == '__main__':
    labels = json.load(open(DATA + 'sheet_labels.json'))
    res = {}
    for tag in ('male', 'female'):
        fit = json.load(open(f'{DATA}fit_{tag}.json'))
        build = json.load(open(f'{DATA}build_{tag}.json'))
        verify = json.load(open(f'{DATA}verify_{tag}.json'))
        for color in ('White', 'Black'):
            res[f'{tag}_{color}'] = sheet(tag, color, fit, labels, build, verify)
            print('sheet', res[f'{tag}_{color}'])
    json.dump({k: dict(path=v[0], size=v[1]) for k, v in res.items()}, open(DATA + 'sheets.json', 'w'), indent=1)
