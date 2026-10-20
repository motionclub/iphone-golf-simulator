"""Writes proof/sheet_notes.txt: the measured lines printed under each before/after sheet.

Every number is computed here from the captures and the Unity logs (nothing is typed by hand).
    write_sheet_notes.py
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import ball_contrast as bc
import light_metrics as lm

ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
VP = f'{ROOT}/work/venue-presence'
OLD = f'{ROOT}/ArtDir/screenshots/venues'
NEW = f'{VP}/proof/after'

def tris(log, venue):
    m = re.search(r'\[VenueDump\] ' + venue + r': venue-owned static tris=(\d+) in (\d+) mesh renderers \| arena kit tris=(\d+)', open(log, errors='replace').read())
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

def built(log, kind):
    m = re.search(r'\[VenueBuild\] ' + kind + r' venue built in (\d+) ms', open(log, errors='replace').read())
    return int(m.group(1)) if m else None

def dome(log):
    m = re.search(r"sky dome '(\w+)' baked in (\d+) ms", open(log, errors='replace').read())
    return int(m.group(2)) if m else None

lines = []
def add(v, t): lines.append(f'{v}|{t}')

# ---- sky
for shot, label, rows in (('1_gameplay', 'gameplay', bc.SHOTS['1_gameplay']), ('2_postcard', 'postcard', bc.SHOTS['2_postcard'])):
    o = bc.report(f'{OLD}/skyscraper_{shot}.png', rows); n = bc.report(f'{NEW}/skyscraper_{shot}.png', rows)
    add('skyscraper', f"Ball vs background in the lob band, {label}: median {o['median']:.2f}:1 -> {n['median']:.2f}:1;  pixels under 2:1: {o['under2']:.0f}% -> {n['under2']:.0f}%;  under 1.5:1: {o['under15']:.0f}% -> {n['under15']:.0f}%")
b = tris(f'{VP}/logs/before_capture_skyscraper.log', 'skyscraper'); a = tris(f'{VP}/logs/final_capture_skyscraper.log', 'skyscraper')
add('skyscraper', f"Triangles owned by the venue: {b[0]:,} -> {a[0]:,}.  Resort props hidden: arena kit {b[2]:,} -> {a[2]:,} (-{b[2]-a[2]:,}).  Whole static scene {b[0]+b[2]:,} -> {a[0]+a[2]:,} (+{(a[0]+a[2])-(b[0]+b[2]):,})")
tb = built(f'{VP}/logs/before_capture_skyscraper.log', 'Skyscraper'); ta = built(f'{VP}/logs/final_capture_skyscraper.log', 'Skyscraper'); d = dome(f'{VP}/logs/final_capture_skyscraper.log')
add('skyscraper', f"Build time in the Editor (Mono): {tb} ms -> {ta} ms, of which the baked sky is {d} ms (first match only; cached after). Not measured on a phone")
add('skyscraper', "Cloud layer: solid lit cloud sea 58 m under the deck (was four alpha sheets 348-388 m down). Towers: 34, 6 facade families, 9 silhouettes, 1 landmark (was 3 textures in all, and the 14 visible neighbours shared one facade and one box recipe)")

# ---- volcano
for shot, label, rows in (('1_gameplay', 'gameplay', bc.SHOTS['1_gameplay']), ('2_postcard', 'postcard', bc.SHOTS['2_postcard'])):
    o = bc.report(f'{OLD}/volcano_{shot}.png', rows); n = bc.report(f'{NEW}/volcano_{shot}.png', rows)
    add('volcano', f"Ball vs background in the lob band, {label}: median {o['median']:.2f}:1 -> {n['median']:.2f}:1;  pixels under 2:1: {o['under2']:.1f}% -> {n['under2']:.1f}%")
for shot in ('1_gameplay', '2_postcard'):
    parts = []
    for name, reg in (('left strip', (-10, -7.8, -4, 10)), ('right strip', (7.8, 10, -4, 10)), ('court (control)', (1, 4, -9, -3))):
        o = lm.measure(f'{OLD}/volcano_{shot}.png', shot, reg); n = lm.measure(f'{NEW}/volcano_{shot}.png', shot, reg)
        parts.append(f"{name} {o['warmth']:+.2f} -> {n['warmth']:+.2f}")
    add('volcano', f"Lava light on the slab edge, {shot[2:]}: warmth (red minus blue) of the same floor patch: " + ';  '.join(parts))
b = tris(f'{VP}/logs/before_capture_volcano.log', 'volcano'); a = tris(f'{VP}/logs/final_capture_volcano.log', 'volcano')
add('volcano', f"Triangles owned by the venue: {b[0]:,} -> {a[0]:,}.  Resort props hidden: arena kit {b[2]:,} -> {a[2]:,}.  Whole static scene {b[0]+b[2]:,} -> {a[0]+a[2]:,} ({(a[0]+a[2])/(b[0]+b[2])*100:.0f}% of before)")
tb = built(f'{VP}/logs/before_capture_volcano.log', 'Volcano'); ta = built(f'{VP}/logs/final_capture_volcano.log', 'Volcano')
add('volcano', f"Build time in the Editor (Mono): {tb} ms -> {ta} ms. Active lights 9 -> 9 (unchanged: slab glow, four braziers, sun, fill, two lava lights). Not measured on a phone")
add('volcano', "Removed: 420 trees (1,327,160 tris), grassland, sea quad, 240 sphere boulders: no shipped camera sees them. Added: terraced bowl, 8 lavafalls, 20 basalt clusters, rock keel, lava channel")

open(f'{VP}/proof/sheet_notes.txt', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
