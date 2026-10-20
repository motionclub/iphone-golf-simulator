"""grid3.py: render many coordinate files in ONE Blender launch and compose  plate | v1 | v2 ... (soft, optional bandpass row)
python3 tools/grid3.py <roi> <out.png> [--bp] [--look matcap:soft] [--enh 1.0] tag=coords.npy ..."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from rr import *
import viz3

def render_variants(roi, items, look='matcap:soft', cav=0.0, tag='gv', extra_shots=None):
    shots = [roi_shot(roi, roi)] + (extra_shots or [])
    spec = {"variants": [{"tag": t, "coords": c if c.startswith('/') else HERE + '/' + c} for t, c in items],
            "out": f"{HERE}/scratch/r/{tag}", "shots": shots, "look": look, "cavity": cav}
    r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    if 'RENDER_OK' not in r.stdout:
        print(r.stdout[-2000:], r.stderr[-2000:]); raise SystemExit('render failed')
    return {t: [f"{HERE}/scratch/r/{tag}_{t}_{s['name']}.png" for s in shots] for t, _ in items}

def compose(roi, out, items, bp=False, look='matcap:soft', enh=1.0, scale=0.6, cav=0.0):
    files = render_variants(roi, items, look, cav)
    pl = plate_crop(roi, enh)
    ims = [pl] + [Image.open(files[t][0]).convert('RGB') if False else bgcomp(files[t][0]) for t, _ in items]
    labs = ['PLATE'] + [t for t, _ in items]
    a = strip(ims, labs, scale=scale)
    if bp:
        b = viz3.structure_strip(roi, [files[t][0] for t, _ in items], [t for t, _ in items], scale_out=scale)
        W = Image.new('RGB', (max(a.width, b.width), a.height + b.height)); W.paste(a, (0, 0)); W.paste(b, (0, a.height)); a = W
    a.save(out); print(out)

if __name__ == '__main__':
    roi, out = sys.argv[1], sys.argv[2]
    bp = '--bp' in sys.argv
    look = sys.argv[sys.argv.index('--look') + 1] if '--look' in sys.argv else 'matcap:soft'
    enh = float(sys.argv[sys.argv.index('--enh') + 1]) if '--enh' in sys.argv else 1.0
    items = [a.split('=', 1) for a in sys.argv[3:] if '=' in a and not a.startswith('--')]
    compose(roi, out, items, bp, look, enh)
