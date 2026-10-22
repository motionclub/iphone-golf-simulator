"""zoom3.py <part chest|pelvis> <out.png> <look,look,..> tag=coords ... : big (900px) renders, views front + 3/4 for each look, one row per tag"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from rr import *
LOOKS = {'soft': 'matcap:soft', 'clay': 'matcap:clay_studio.exr', 'stripe': 'matcap:check_reflection_vertical.exr', 'stripeh': 'matcap:check_reflection_horizontal.exr', 'rim': 'matcap:check_rim_light.exr'}
def zoom(part, out, looks, items, px=700, w=0.30, yaws=(0, -25)):
    zc = 1.21 if part == 'chest' else 0.90
    rows = []
    for t, c in items:
        ims, labs = [], []
        for lk in looks:
            shots = [dict(name=f'v{y}', yaw=(y if part == 'chest' else (180 if y == 0 else (-155 if y < 0 else 155))), xc=0.0, zc=zc, w=w, res=[px, px]) for y in yaws]
            spec = {"variants": [{"tag": t, "coords": c if c.startswith('/') else HERE + '/' + c}], "out": f"{HERE}/scratch/r/zm_{part}_{lk}", "shots": shots, "look": LOOKS[lk]}
            r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
            assert 'RENDER_OK' in r.stdout, r.stdout[-800:]
            for s in shots:
                ims.append(bgcomp(f"{HERE}/scratch/r/zm_{part}_{lk}_{t}_{s['name']}.png")); labs.append(f'{t} {lk} {s["name"]}')
        rows.append(strip(ims, labs, scale=0.55))
    W = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)))
    y = 0
    for r in rows:
        W.paste(r, (0, y)); y += r.height
    W.save(out); print(out, W.size)
if __name__ == '__main__':
    part, out = sys.argv[1], sys.argv[2]
    looks = sys.argv[3].split(',')
    items = [a.split('=', 1) for a in sys.argv[4:]]
    zoom(part, out, looks, items)
