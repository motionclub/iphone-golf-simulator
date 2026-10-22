#!/usr/bin/env python3
"""label_sheets.py : build the labelled proof from proof/shots.json + proof/raw.
Writes into proof/: LOCKER_male.png, LOCKER_female.png, CAMPAIGN_vs_Nadia.png, CAMPAIGN_vs_Viktor.png, RALLY_*.png and the clip-labelled rally frames in proof/rally/."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here); proof = os.path.join(root, 'proof')
shots = json.load(open(os.path.join(proof, 'shots.json')))['shots']
def font(size):
    for p in ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()
def load(s): return Image.open(os.path.join(proof, s['file'])).convert('RGB')
def burn(im, lines, size=None):
    """Clip name (and detail) in the top-left corner on a dark plate."""
    size = size or max(14, im.width // 38); f = font(size); d = ImageDraw.Draw(im)
    w = max(d.textlength(l, font=f) for l in lines) + 16; h = len(lines) * (size + 6) + 10
    d.rectangle([0, 0, w, h], fill=(12, 14, 22)); y = 6
    for i, l in enumerate(lines):
        d.text((8, y), l, fill=(255, 224, 96) if i == 0 else (225, 225, 230), font=f); y += size + 6
    return im
def caption(s):
    c = [s['clip'] or ('(no clip)' if s['role'] == 'BOTH' else '-')]
    if s['clip']: c.append(f"t={s['clipTime']:.3f}s  contact {s['contact']:.3f}s")
    c.append(f"{s['role']} {s['sex']}  {s['state']}".strip())
    return c
def sheet(items, out, cols, cell, title):
    cap = 40; rows = (len(items) + cols - 1) // cols
    S = Image.new('RGB', (cols * cell, rows * cell + cap), (16, 18, 26)); d = ImageDraw.Draw(S)
    d.text((10, 10), title, fill=(240, 240, 240), font=font(18))
    for i, (im, _) in enumerate(items):
        t = im.copy(); t.thumbnail((cell, cell)); S.paste(t, ((i % cols) * cell + (cell - t.width) // 2, cap + (i // cols) * cell))
    S.save(out); print(out, S.size)
def pick(pred): return [s for s in shots if pred(s)]

# ---- LOCKER: the locker's choices applied as the phone applies them, male and female (Play mode, game camera moved onto the hero)
for sex in ('male', 'female'):
    items = [(burn(load(s), [f"LOCKER {sex} (Play mode)", os.path.basename(s['file'])[:-4].replace('locker_' + sex + '_', ''), f"hero: {s['sex']}  mesh Body_{'F' if sex == 'female' else 'M'}"]), s) for s in pick(lambda s: s['scenario'] == 'locker' and ('locker_' + sex) in s['file'])]
    if items: sheet(items, os.path.join(proof, f'LOCKER_{sex}.png'), 3, 640, f"HERO_MAINSTAY proof - locker, {sex}: Play mode, the game's own camera moved onto the hero, locker look applied as NativeSportsSession applies it")

# ---- CAMPAIGN: vs Nadia (female rival, male player) and vs Viktor (male rival, female player)
for key, rival, player in (('Nadia', 'female', 'male'), ('Viktor', 'male', 'female')):
    sc = f'vs_{key}'; items = []
    for s in pick(lambda s: s['scenario'] == sc and any(t in s['file'] for t in ('_wide.png',)) and '_rally_' not in s['file'] and 'replay' not in s['file']):
        items.append((burn(load(s), [f"CAMPAIGN vs {key.upper()} - wide game camera", f"rival {rival}  player {player}"]), s))
    for tag, who in (('_rival_front34', f'RIVAL {key} ({rival})'), ('_player_back34', f'PLAYER ({player})')):
        for s in pick(lambda s: s['scenario'] == sc and tag in s['file']): items.append((burn(load(s), [who, f"{s['sex']} body"]), s))
    if items: sheet(items, os.path.join(proof, f'CAMPAIGN_vs_{key}.png'), 3, 640, f"HERO_MAINSTAY proof - campaign match vs {key} ({rival}), player is {player}: both meshes on court, Play mode, game camera")

# ---- RALLY: contact frames with the clip name burned into the corner
os.makedirs(os.path.join(proof, 'rally'), exist_ok=True)
for sc in ('vs_Nadia', 'vs_Viktor'):
    rally = pick(lambda s: s['scenario'] == sc and '_rally_' in s['file'])
    labelled = []
    for s in rally:
        im = burn(load(s), caption(s)); name = os.path.basename(s['file']); im.save(os.path.join(proof, 'rally', name)); labelled.append((im, s))
    def order(s):
        c = s['clip'] or ''
        for i, k in enumerate(('Serve', 'Forehand', 'Backhand', 'Return', 'Volley', 'Overhead')):
            if k in c: return (0 if s['role'] == 'PLAYER' else 1, i, c, s['file'])
        return (2, 9, c, s['file'])
    labelled.sort(key=lambda t: order(t[1]))
    close = [t for t in labelled if t[1]['file'].endswith('_close.png')]; wide = [t for t in labelled if t[1]['file'].endswith('_wide.png')]
    if close: sheet(close, os.path.join(proof, f'RALLY_{sc}_closeups.png'), 4, 540, f"HERO_MAINSTAY proof - one rally ({sc}): every stroke at the gameplay contact frame, clip name in the corner")
    if wide: sheet(wide, os.path.join(proof, f'RALLY_{sc}_game_camera.png'), 3, 640, f"HERO_MAINSTAY proof - rally ({sc}), the game camera at the contact frame, clip name in the corner")
# the single rally sheet the brief asks for: serve, forehand, backhand (player) from the Nadia match
want = []
for k in ('Male_Serve', 'Male_Forehand', 'Male_Backhand'):
    for s in pick(lambda s: s['scenario'] == 'vs_Nadia' and '_rally_' in s['file'] and s['clip'] == k and s['role'] == 'PLAYER'):
        want.append((burn(load(s), caption(s)), s)); break
if len(want) == 3:
    two = []
    for k in ('Male_Serve', 'Male_Forehand', 'Male_Backhand'):
        for suffix in ('_wide.png', '_close.png'):
            for s in pick(lambda s: s['scenario'] == 'vs_Nadia' and '_rally_' in s['file'] and s['clip'] == k and s['role'] == 'PLAYER' and s['file'].endswith(suffix)):
                two.append((burn(load(s), caption(s)), s)); break
    sheet(two, os.path.join(proof, 'RALLY_serve_forehand_backhand.png'), 2, 720, "HERO_MAINSTAY proof - one rally vs Nadia: serve, forehand, backhand at the gameplay contact frame (game camera / hero close-up), clip name in the corner")
else: print("rally sheet: missing", [k for k in ('Male_Serve', 'Male_Forehand', 'Male_Backhand')][len(want):])

# ---- SWIFT LOCKER: the phone's locker mirror (CharacterModelPreview, SceneKit) rendered by GolfArcadeTests/MatchHeroLockerTests
sw = os.path.join(proof, 'swift_locker')
if os.path.isdir(sw):
    for sex in ('male', 'female'):
        items = []
        for name, label in ((f'locker_{sex}_body', 'locker, full body'), (f'locker_{sex}_head', 'locker, head close-up'), (f'practice_{sex}_backswing', 'practice swing: backswing (match Forehand)'),
                            (f'practice_{sex}_contact', 'practice swing: contact frame'), (f'club_{sex}_settings', 'club menu: settings'), (f'hosted_view_{sex}', 'the real SwiftUI view, read back from its SCNView')):
            p = os.path.join(sw, name + '.png')
            if os.path.exists(p): items.append((burn(Image.open(p).convert('RGB'), [f"SWIFT LOCKER {sex}", label], 20), None))
        if items: sheet(items, os.path.join(proof, f'LOCKER_SWIFT_{sex}.png'), 3, 520, f"HERO_MAINSTAY proof - Swift locker mirror (CharacterModelPreview), {sex}: the match hero mesh, bald, skin + racket picks, no old Hero V4")
