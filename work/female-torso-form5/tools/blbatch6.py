"""blbatch6.py: render the BACK pelvis panel (soft matcap, the same pipeline as proof/06z) for many coordinate files in ONE Blender session, and trace the fold line in the panel.
api: render_panels({tag: coords.npy}) -> {tag: PIL 'L' panel (420 px wide)};  plate_panel();  fold_rows(panel) -> {dx: row}"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import board3
from run4 import SOFT, HERE
import bandtrace_panel6 as bp

BL = '/Applications/Blender.app/Contents/MacOS/Blender'
START = HERE + '/START_form4_candidate.blend'
BOXB = (0.05, 0.20, 0.95, 0.90)         # tri5.BOX['pelvis']['back']
_SHOT = None

def _shot():
    global _SHOT
    if _SHOT is None:
        _SHOT = board3.shots_for('pelvis', 420)[0][0]
    return _SHOT

def _panel(img):
    w, h = img.size
    c = img.crop((int(BOXB[0] * w), int(BOXB[1] * h), int(BOXB[2] * w), int(BOXB[3] * h)))
    ch = int(420 * c.height / c.width)
    return c.resize((420, ch), Image.LANCZOS).convert('L')

def plate_panel():
    return _panel(board3.shots_for('pelvis', 420)[1][0].convert('RGB'))

def render_panels(variants, prefix='q6', look=SOFT, clear_cn=False):
    shot = _shot()
    def _v(t, p):
        cw = None
        if isinstance(p, (tuple, list)): p, cw = p
        d = {"tag": t, "coords": p if p.startswith('/') else HERE + '/' + p}
        if cw: d["cn_weight"] = cw if cw.startswith('/') else HERE + '/' + cw
        return d
    spec = {"variants": [_v(t, p) for t, p in variants.items()],
            "out": f"{HERE}/scratch/r/{prefix}", "shots": [shot], "look": look, "cavity": 0.0, "clear_cn": bool(clear_cn)}
    r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    if 'RENDER_OK' not in r.stdout:
        print(r.stdout[-1500:], r.stderr[-1500:]); raise SystemExit('render failed')
    out = {}
    for t in variants:
        m = Image.open(f"{HERE}/scratch/r/{prefix}_{t}_{shot['name']}.png").convert('RGBA')
        bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m)
        out[t] = _panel(bg.convert('RGB'))
    return out

def fold_rows(panel):
    tr = bp.trace_panel(panel)
    return {dx: v[0] for dx, v in tr.items()}

ABS = (45, 60, 75, 90, 105)
def lr_avg(rows):
    return np.array([0.5 * (rows[-a] + rows[a]) for a in ABS])

if __name__ == '__main__':
    # self-test: render the r5 candidate + F4 and print traces
    pp = plate_panel(); pr = lr_avg(fold_rows(pp)); print('plate avg rows', np.round(pr, 1))
    ps = render_panels({'F4': 'data/co_FORM4_final.npy', 'F5r5': 'data/co_FORM5_final.npy', 'F5r4': 'data/co_FORM5_r4_backup.npy'})
    for t, p in ps.items():
        r = lr_avg(fold_rows(p)); print(t, np.round(r, 1), 'err rms %.1f rise %.1f' % (np.sqrt(((r - pr) ** 2).mean()), r[0] - r[-1]))
