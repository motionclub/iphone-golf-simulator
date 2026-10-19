"""GARMENT PIPELINE: PASS/FAIL report + worst-12 contact sheet from suite.json (system python3 + PIL).
python3 gp/report.py <suite_dir>/<hero> [<before_dir>/<hero>]  -> REPORT.md, sheet_worst12.jpg (and before/after numbers if given)"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

TEAR_MAX = 0          # pixels after the noise filter, summed over the stress library
LAYER_MAX = 0


def font(sz):
    for f in ('/System/Library/Fonts/SFNSMono.ttf', '/System/Library/Fonts/Menlo.ttc', '/System/Library/Fonts/Helvetica.ttc'):
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()


def sheet(d, s, out, title):
    tiles = []
    for n, r in enumerate(s['worst']):
        p = os.path.join(d, f'worst_{n:02d}.png')
        if not os.path.exists(p): continue
        im = Image.open(p).convert('RGB')
        im = im.resize((432, 540))
        dr = ImageDraw.Draw(im)
        lab = f"{r['clip'].split('__')[-1]} f{r['frame']}  tear {r['tear']}  layer {r['layer']}"
        dr.rectangle([0, 0, 432, 26], fill=(20, 20, 30)); dr.text((6, 4), lab, fill=(255, 255, 255), font=font(15))
        tiles.append(im)
    if not tiles: return
    cols = 6; rows = (len(tiles) + cols - 1) // cols
    W, H = 432 * cols, 540 * rows + 48
    sh = Image.new('RGB', (W, H), (238, 238, 242))
    ImageDraw.Draw(sh).text((10, 10), title, fill=(10, 10, 20), font=font(26))
    for i, t in enumerate(tiles): sh.paste(t, ((i % cols) * 432, 48 + (i // cols) * 540))
    sh.save(out, quality=90)


def main():
    d = sys.argv[1]; b = sys.argv[2] if len(sys.argv) > 2 else None
    s = json.load(open(os.path.join(d, 'suite.json')))
    t = s['total']
    lines = [f"# Garment stress report: {s['hero']}", '', f"Stress poses: {s['poses']} (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.", '']
    ok_t, ok_l = t['tear'] <= TEAR_MAX, t['layer'] <= LAYER_MAX
    lines += [f"- GATE TEARS: {'PASS' if ok_t else 'FAIL'} - {t['tear']} skin pixels through cloth, in {t['poses_with_tear']} poses",
              f"- GATE LAYERS: {'PASS' if ok_l else 'FAIL'} - {t['layer']} garment pixels through an outer garment, in {t['poses_with_layer']} poses",
              f"- by victim: {t['by']}", f"- by victim<coverer: {dict(sorted(t.get('pair', {}).items(), key=lambda kv: -kv[1]))}"]
    if 'holes' in t: lines.append(f"- HOLES (hidden skin seen through): {t['holes']} px in {t.get('poses_with_holes', 0)} poses")
    rows_ = s.get('rows', []) if isinstance(s, dict) else []
    if rows_ and 'holes_bg' in rows_[0]:
        lines.append(f"  - holes split: background {sum(r['holes_bg'] for r in rows_)}, lining {sum(r['holes_inner'] for r in rows_)}, outer surface > 3 cm behind {sum(r['holes_deep'] for r in rows_)}")
    if b and os.path.exists(os.path.join(b, 'suite.json')):
        bt = json.load(open(os.path.join(b, 'suite.json')))['total']
        lines += ['', f"Before: tear {bt['tear']} px ({bt['poses_with_tear']} poses), layer {bt['layer']} px ({bt['poses_with_layer']} poses)"]
    lines += ['', '| # | clip | frame | why | tear | layer | by |', '|---|---|---|---|---|---|---|']
    for n, r in enumerate(s['worst']):
        lines.append(f"| {n} | {r['clip']} | {r['frame']} | {', '.join(r['why'][:3])} | {r['tear']} | {r['layer']} | {r['by']} |")
    open(os.path.join(d, 'REPORT.md'), 'w').write('\n'.join(lines) + '\n')
    sheet(d, s, os.path.join(d, 'sheet_worst12.jpg'), f"{s['hero']}  worst 12 stress poses  tear {t['tear']} px  layer {t['layer']} px  (red = through cloth)")
    print('\n'.join(lines[3:7]))


if __name__ == '__main__':
    main()
