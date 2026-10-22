# pop_check.py <pop_dir> : moving-camera pop check for the far tree cells (MajesticHoleViews MAM_PROBE=pop).
# Each frame exists as played (_n) and with the far cells forced to the full mesh (_r). A LOD swap is a change in the
# played sequence that the reference sequence does not have:
#   excess_i = max over 16x16 blocks of ( |N_i - N_i-1| - |R_i - R_i-1| )   (luminance, 0-255, block means)
# plus, per frame, how different the far copy looks: farDiff_i = max over blocks of |N_i - R_i|.
# Writes <pop_dir>/../POP_RESULTS.md, a sheet of the worst event per sequence and an animated WebP of each flyover.
import sys, os, glob, re, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

d = sys.argv[1]; out = os.path.dirname(d.rstrip('/'))
B = 16; POP = 12.0; SW = 8.0   # block-mean luminance jump (0-255) that reads as a pop at phone size
def lum(p): return np.asarray(Image.open(p).convert('L'), dtype=np.float32)
def blocks(a): h, w = a.shape; a = a[:h // B * B, :w // B * B]; return a.reshape(h // B, B, w // B, B).mean(axis=(1, 3))
seqs = sorted({re.sub(r'_\d{3}_[nr]\.jpg$', '', os.path.basename(f)) for f in glob.glob(os.path.join(d, '*_n.jpg'))})
rows, sheet_items, report = [], [], {}
for s in seqs:
    idx = sorted(int(re.search(r'_(\d{3})_n\.jpg$', f).group(1)) for f in glob.glob(os.path.join(d, s + '_*_n.jpg')))
    pn = pr = None; worst = (0, -1, None); events = 0; farmax = 0; pdiff = None; swaps = 0; swapmax = 0
    for i in idx:
        n = lum(os.path.join(d, f'{s}_{i:03d}_n.jpg')); r = lum(os.path.join(d, f'{s}_{i:03d}_r.jpg'))
        nd = blocks(np.abs(n - r)); farmax = max(farmax, float(nd.max()))
        # swap signature: a block whose played-vs-full difference appears or vanishes from one frame to the next
        if pdiff is not None:
            sw = ((nd > SW) & (pdiff < SW / 3)) | ((pdiff > SW) & (nd < SW / 3))
            if sw.any(): swaps += 1; swapmax = max(swapmax, float(np.maximum(nd, pdiff)[sw].max()))
        pdiff = nd
        if pn is not None:
            ex = blocks(np.abs(n - pn)) - blocks(np.abs(r - pr)); e = float(ex.max())
            if e > POP: events += 1
            if e > worst[0]: worst = (e, i, np.unravel_index(int(ex.argmax()), ex.shape))
        pn, pr = n, r
    report[s] = dict(frames=len(idx), max_excess=round(worst[0], 1), worst_frame=worst[1], pop_events=events, max_far_vs_full=round(farmax, 1), swap_frames=swaps, swap_max=round(swapmax, 1))
    rows.append(f"| {s} | {len(idx)} | {swaps} | {swapmax:.1f} | {worst[0]:.1f} (frame {worst[1]}) | {farmax:.1f} |")
    if worst[1] > 0:
        i = worst[1]; by, bx = worst[2]
        for tag, f in [('prev', f'{s}_{i - 1:03d}_n.jpg'), ('played', f'{s}_{i:03d}_n.jpg'), ('full mesh', f'{s}_{i:03d}_r.jpg')]:
            im = Image.open(os.path.join(d, f)).convert('RGB'); dr = ImageDraw.Draw(im)
            dr.rectangle([bx * B - 24, by * B - 24, bx * B + B + 24, by * B + B + 24], outline=(255, 40, 40), width=3)
            sheet_items.append((f'{s} {tag} #{i}', im))
    if '_fly' in s:
        frames = [Image.open(os.path.join(d, f'{s}_{i:03d}_n.jpg')).convert('RGB').resize((640, 360)) for i in idx]
        frames[0].save(os.path.join(out, f'{s}_played.webp'), save_all=True, append_images=frames[1:], duration=33, loop=0, quality=70)
md = ['# Far tree cells: moving-camera pop check', '',
      f'Excess = largest 16x16-block luminance jump in the played sequence beyond the full-mesh reference (0-255); a pop reads at > {POP:.0f}.',
      'max far-vs-full = largest block difference between the far copy and the full mesh on the same frame.', '',
      'swap frames = frames where a 16x16 block\'s played-vs-full difference appears or vanishes (> %d vs < %d); swap max = that block\'s difference (the visible size of the swap).' % (SW, SW / 3), '',
      '| sequence | frames | swap frames | swap max | max excess (motion-confounded) | max far-vs-full |', '|---|---|---|---|---|---|'] + rows
open(os.path.join(out, 'POP_RESULTS.md'), 'w').write('\n'.join(md) + '\n'); json.dump(report, open(os.path.join(out, 'pop_results.json'), 'w'), indent=1)
if sheet_items:
    tw, th, lab = 480, 270, 22; cols = 3; rws = (len(sheet_items) + cols - 1) // cols
    sh = Image.new('RGB', (cols * tw, rws * (th + lab)), (24, 24, 28)); dd = ImageDraw.Draw(sh)
    try: fnt = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 15)
    except Exception: fnt = ImageFont.load_default()
    for k, (t, im) in enumerate(sheet_items):
        x, y = (k % cols) * tw, (k // cols) * (th + lab); sh.paste(im.resize((tw, th)), (x, y + lab)); dd.text((x + 5, y + 3), t, fill=(240, 240, 240), font=fnt)
    sh.save(os.path.join(out, 'pop_worst.jpg'), quality=85)
print('\n'.join(md))

# Precise swaps (r35+): Unity logged every far-cell LOD switch with its screen rectangle (<hole>_swaps.json). The visible
# size of a swap = the played-vs-full difference inside that rectangle on the frame the cell is on its far copy.
sw_rows = []; allmag = []
for f in sorted(glob.glob(os.path.join(d, '*_swaps.json'))):
    for e in json.load(open(f)):
        fr = e['frame'] if e['to'] == 1 else e['frame'] - 1
        pn_, pr_ = os.path.join(d, f"{e['seq']}_{fr:03d}_n.jpg"), os.path.join(d, f"{e['seq']}_{fr:03d}_r.jpg")
        if not (os.path.exists(pn_) and os.path.exists(pr_)): continue
        n, r = lum(pn_), lum(pr_); h, w = n.shape; x0, y0, x1, y1 = e['rect']
        a, b = int(x0 * w), int(x1 * w); c, dd_ = int(y0 * h), int(y1 * h)
        if b - a < 4 or dd_ - c < 4: continue
        diff = np.abs(n[c:dd_, a:b] - r[c:dd_, a:b])
        bl = blocks(diff) if diff.shape[0] >= B and diff.shape[1] >= B else np.array([[diff.mean()]])
        mag = float(np.percentile(bl, 95)); allmag.append(mag)
        sw_rows.append((e['seq'], e['frame'], e['to'], e['dist'], (b - a) * (dd_ - c) / (w * h), mag))
if sw_rows:
    per = {}
    for s_, fr, to, dist, area, mag in sw_rows: per.setdefault(s_, []).append(mag)
    lines = ['', '## Logged swaps (Unity LOD selection replicated per frame; rect = the cell on screen)', '',
             f'Visible size = 95th percentile of 16x16-block |played - full| inside the cell rect on its far frame; > {POP:.0f} reads as a pop.', '',
             '| sequence | swaps in view | median size | max size | swaps > %d |' % POP, '|---|---|---|---|---|']
    for s_, m in sorted(per.items()): lines.append(f'| {s_} | {len(m)} | {np.median(m):.1f} | {max(m):.1f} | {sum(x > POP for x in m)} |')
    lines.append(f'\nAll: {len(allmag)} swaps in view, median {np.median(allmag):.1f}, max {max(allmag):.1f}, {sum(x > POP for x in allmag)} above {POP:.0f}.')
    open(os.path.join(out, 'POP_RESULTS.md'), 'a').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
