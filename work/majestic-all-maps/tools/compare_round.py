# compare_round.py <round_dir> [holes...] : for every hole captured in the round, every view that has a target:
# today (audit/views_clear) | this round | target (refs/holes), plus REF_MATCH (today vs target, round vs target) and
# NO_EMPTY_VIEW of the round's frame. Writes <round_dir>/compare_hNN.jpg and <round_dir>/scores.json; prints a summary.
import sys, os, glob, json
sys.path.insert(0, os.path.dirname(__file__))
import ref_match as rm
from PIL import Image, ImageDraw, ImageFont

root = os.path.join(os.path.dirname(__file__), '..'); rd = sys.argv[1]
holes = sys.argv[2:] or sorted({os.path.basename(f)[1:3] for f in glob.glob(os.path.join(rd, 'h*_tee.jpg'))})
try: F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 22)
except Exception: F = ImageFont.load_default()
allscores = {}
for h in holes:
    refs = sorted(glob.glob(os.path.join(root, 'refs/holes', f'h{h}_*.jpg')))
    rows = []
    for ref in refs:
        v = os.path.basename(ref)[4:-4]
        now = os.path.join(rd, f'h{h}_{v}.jpg'); today = os.path.join(root, 'audit/views_clear', f'h{h}_{v}.jpg')
        if not os.path.exists(now): continue
        s = {'today': rm.match(today, ref) if os.path.exists(today) else None, 'now': rm.match(now, ref), 'empty_now': rm.empty(now)}
        allscores[f'h{h}_{v}'] = s; rows.append((v, today, now, ref, s))
    if not rows: continue
    tw, th = 640, 360; W = tw * 3; H = len(rows) * (th + 30)
    sheet = Image.new('RGB', (W, H), (22, 24, 28)); d = ImageDraw.Draw(sheet)
    for i, (v, today, now, ref, s) in enumerate(rows):
        y = i * (th + 30)
        for j, (label, p) in enumerate((('today', today), ('build', now), ('target', ref))):
            if os.path.exists(p):
                im = Image.open(p).convert('RGB').resize((tw, th)); sheet.paste(im, (j * tw, y + 30))
            sc = '' if j == 2 else (lambda m: f"  value {m['value_dist']} chroma {m['chroma_dist']} sky {m['sky_dist']} detail {m['detail_ratio']} {'PASS' if m['pass'] else 'FAIL'}")(s['today'] if j == 0 else s['now']) if (s['today'] if j == 0 else s['now']) else ''
            d.text((j * tw + 8, y + 4), f'h{h} {v} {label}{sc}', fill=(235, 235, 235), font=F)
        e = s['empty_now']; d.text((tw + 8, y + th + 4), f"no-empty {e['widest_flat_fraction']} {'PASS' if e['pass'] else 'FAIL'}", fill=(255, 210, 120), font=F)
    sheet.save(os.path.join(rd, f'compare_h{h}.jpg'), quality=82)
json.dump(allscores, open(os.path.join(rd, 'scores.json'), 'w'), indent=1)
n = len(allscores); p_now = sum(1 for s in allscores.values() if s['now']['pass']); p_today = sum(1 for s in allscores.values() if s['today'] and s['today']['pass'])
e_now = sum(1 for s in allscores.values() if s['empty_now']['pass'])
print(f'{n} target views: REF_MATCH(objective) today {p_today}/{n} -> build {p_now}/{n}; NO_EMPTY_VIEW build {e_now}/{n}')
for k, s in allscores.items():
    m = s['now']; print(f"  {k:16s} value {m['value_dist']:.3f} chroma {m['chroma_dist']:5.1f} sky {m['sky_dist']:5.1f} detail {m['detail_ratio']:.2f} {'PASS' if m['pass'] else 'fail'}  empty {s['empty_now']['widest_flat_fraction']}")
