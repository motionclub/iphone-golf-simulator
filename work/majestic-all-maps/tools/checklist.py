# Structural checklist per reference view (coordinator 10-18: score structurally, not by pixel metric).
# Reads design/HOLE_BRIEFS.md tables; writes g2/CHECKLIST.json (expected items per hole/view) and, given a verdicts
# file g2/verdicts_<round>.json ({"h07_tee": {"landmark": 1, ...}}), a summary table g2/SCORE_<round>.md.
import json, os, re, sys, glob
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = {}
course = None
for line in open(os.path.join(D, 'design/HOLE_BRIEFS.md')):
    if line.startswith('## Course'): course = line.split('—')[1].split(':')[0].strip() if '—' in line else line[3:].strip()
    m = re.match(r'\| (\d+) \| ([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|', line)
    if m:
        n, name, fwd, back, lr, sets, off = [x.strip() for x in m.groups()]
        rows[int(n)] = dict(course=course, name=name, fwd=fwd, back=back, lr=lr, sets=sets, off=off)
SKY = {'Cliffside': 'fresh morning, blue sky, sun right/behind', 'Wild Isles': 'golden afternoon, low sun left, warm sky', 'Magma Open': 'violet pre-dawn, orange horizon, lava glow'}
ITEMS = ['subject', 'skyline', 'sky_hour', 'palette', 'near_dressing', 'mid_dressing', 'water_edge', 'no_empty']
check = {}
for ref in sorted(glob.glob(os.path.join(D, 'refs/holes/h*_*.jpg'))):
    key = os.path.basename(ref)[:-4]; hole = int(key[1:3]); view = key[4:]
    r = rows.get(hole); 
    if not r: continue
    lr = r['lr']
    both = lr.startswith('L/R')
    left = lr if both or 'R:' not in lr else lr.split('R:')[0]
    right = lr if both or 'R:' not in lr else 'R:' + lr.split('R:', 1)[1]
    subject = {'greenBack': r['back'], 'offL': left, 'offR': right}.get(view, r['fwd'])
    check[key] = dict(course=r['course'], hole=hole, view=view, subject=subject, skyline='far layer: landforms/sea/karst or caldera, layered into haze',
                      sky_hour=next((v for k, v in SKY.items() if r['course'].startswith(k)), ''), set_pieces=r['sets'], offline=r['off'], items=ITEMS)
json.dump(check, open(os.path.join(D, 'g2/CHECKLIST.json'), 'w'), indent=1)
print(len(check), 'views in checklist')
if len(sys.argv) > 1:
    v = json.load(open(sys.argv[1])); out = ['| view | ' + ' | '.join(ITEMS) + ' | score | biggest gap |', '|' + '---|' * (len(ITEMS) + 3)]
    tot = 0
    for key in sorted(v):
        s = v[key]; sc = sum(s.get(i, 0) for i in ITEMS); tot += sc
        out.append(f"| {key} | " + ' | '.join('✓' if s.get(i) else '✗' for i in ITEMS) + f" | {sc}/{len(ITEMS)} | {s.get('gap', '')} |")
    out.append(f"\n**Total {tot} / {len(ITEMS) * len(v)}**")
    open(sys.argv[1].replace('verdicts_', 'SCORE_').replace('.json', '.md'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out[-1:]))
