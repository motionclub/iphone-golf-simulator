"""Blender-side proof sheets (gate 9): python3 proofs_blender.py   (system python + Pillow; calls Blender for the renders)
 proof/Sheet_<Hero>_Dressed.png      ReadyIdle front / 3-4 / side / back + contact frames of Forehand, Serve, Backhand, Overhead (kit as skinned, White colourway)
 proof/BEFORE_AFTER_<Hero>.png        the same poses bare (top row) and dressed (bottom row)
 proof/BEFORE_AFTER_all.png           both heroes, one sheet
 proof/worst_<Hero>_<Piece>.png       the worst skin-poke pose of every piece (body shown red, close-up on the worst body vertex)"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/hero-dressed'
BLENDER = '/Applications/Blender.app/Contents/MacOS/Blender'
PROOF = W + '/proof'
CELL = PROOF + '/_cells'
os.makedirs(CELL, exist_ok=True)
CW, CH = 540, 675
try:
    FONT = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 15)
    FONT_B = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 18)
except Exception:
    FONT = FONT_B = ImageFont.load_default()
CONTACT = {'Forehand': 20, 'Serve': 27, 'Backhand': 19, 'Overhead': 22}
HEROES = [('male', 'Male'), ('female', 'Female')]


def shot(name, **kw):
    d = dict(out=f'{CELL}/{name}.png', res=[CW, CH], follow='Hips', offset=[0, 0, 0.18], dist=3.5, el=6, az=35, lens=50)
    d.update(kw)
    return d


def render(tag, label, shots):
    spec = f'{CELL}/spec_{tag}.json'
    json.dump({'shots': shots}, open(spec, 'w'))
    subprocess.run([BLENDER, '-b', '--factory-startup', f'{W}/export/HeroBase_{label}_Dressed.blend', '--python', f'{W}/scripts/rview.py', '--', tag, spec], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def caption(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 26], fill=(30, 34, 40))
    d.text((8, 4), text, fill=(235, 235, 235), font=FONT)
    return im


def cell(name, text):
    return caption(Image.open(f'{CELL}/{name}.png').convert('RGB'), text)


for tag, label in HEROES:
    shots = []
    for nm, az in (('front', 0), ('q34', 40), ('side', 90), ('back', 180)):
        shots.append(shot(f'{tag}_ready_{nm}', clip='ReadyIdle', frame=0, az=az))
        shots.append(shot(f'{tag}_bare_ready_{nm}', clip='ReadyIdle', frame=0, az=az, kit=False))
    for clip, f in CONTACT.items():
        up = 0.38 if clip in ('Serve', 'Overhead') else 0.18
        shots.append(shot(f'{tag}_{clip}', clip=clip, frame=f, offset=[0, 0, up], dist=4.1 if up > 0.3 else 3.6))
        shots.append(shot(f'{tag}_bare_{clip}', clip=clip, frame=f, offset=[0, 0, up], dist=4.1 if up > 0.3 else 3.6, kit=False))
    render(tag, label, shots)
    # Sheet_<Hero>_Dressed
    sheet = Image.new('RGB', (4 * CW, 2 * (CH + 26) + 36), (22, 24, 28))
    ImageDraw.Draw(sheet).text((10, 8), f'{label} hero, White kit skinned to the match rig (work/hero-dressed) - top: ReadyIdle frame 0 front / 3/4 / side / back; bottom: contact frames of Forehand, Serve, Backhand, Overhead', fill=(235, 235, 235), font=FONT_B)
    names = [(f'{tag}_ready_{n}', f'ReadyIdle f0 - {n}') for n in ('front', 'q34', 'side', 'back')] + [(f'{tag}_{c}', f'{c} contact (frame {f})') for c, f in CONTACT.items()]
    for i, (n, t) in enumerate(names):
        sheet.paste(cell(n, t), ((i % 4) * CW, 36 + (i // 4) * (CH + 26)))
    sheet.save(f'{PROOF}/Sheet_{label}_Dressed.png')
    # BEFORE_AFTER
    ba = Image.new('RGB', (4 * CW, 2 * (CH + 26) + 36), (22, 24, 28))
    ImageDraw.Draw(ba).text((10, 8), f'{label}: BEFORE (bare mannequin, top) vs AFTER (dressed, bottom) - same poses, same camera', fill=(235, 235, 235), font=FONT_B)
    sel = [('ready_front', 'ReadyIdle front'), ('ready_q34', 'ReadyIdle 3/4'), ('Forehand', 'Forehand contact'), ('Serve', 'Serve contact')]
    for i, (n, t) in enumerate(sel):
        ba.paste(cell(f'{tag}_bare_{n}', 'BEFORE  ' + t), (i * CW, 36))
        ba.paste(cell(f'{tag}_{n}', 'AFTER   ' + t), (i * CW, 36 + CH + 26))
    ba.save(f'{PROOF}/BEFORE_AFTER_{label}.png')
    print('sheets', label)

both = Image.new('RGB', (4 * CW, 2 * (2 * (CH + 26) + 36)), (22, 24, 28))
for k, (tag, label) in enumerate(HEROES):
    both.paste(Image.open(f'{PROOF}/BEFORE_AFTER_{label}.png'), (0, k * (2 * (CH + 26) + 36)))
both.save(f'{PROOF}/BEFORE_AFTER_all.png')

# worst-pose renders (gate 3)
for tag, label in HEROES:
    g = json.load(open(f'{W}/data/gate3_{tag}.json'))
    shots, meta = [], []
    for p, s in g['summary'].items():
        pose = next(r for r in g['poses'] if r['clip'] == s['worst_poke_clip'] and r['frame'] == s['worst_poke_frame'])
        v = pose['pieces'][p].get('worst_body_vertex')
        if v is None:
            continue
        shots.append(dict(out=f'{CELL}/{tag}_worst_{p}.png', res=[CW, CW], clip=s['worst_poke_clip'], frame=s['worst_poke_frame'], body_vertex=v, dist=1.1, el=8, az=35, lens=50, body_rgb=[0.85, 0.2, 0.15]))
        meta.append((p, s))
    if shots:
        render(tag, label, shots)
        sheet = Image.new('RGB', (3 * CW, 2 * (CW + 26) + 36), (22, 24, 28))
        ImageDraw.Draw(sheet).text((10, 8), f'{label}: worst skin-poke pose of every kit piece (body shown red; camera 1.1 m from the worst body vertex)', fill=(235, 235, 235), font=FONT_B)
        for i, (p, s) in enumerate(meta):
            c = caption(Image.open(f'{CELL}/{tag}_worst_{p}.png').convert('RGB'), f'{p}: poke {s["poke_max_mm"]:.1f} mm at {s["worst_poke_pose"]}')
            sheet.paste(c, ((i % 3) * CW, 36 + (i // 3) * (CW + 26)))
            c.save(f'{PROOF}/worst_{label}_{p}.png')
        sheet.save(f'{PROOF}/WORST_POKE_{label}.png')
print('done')
