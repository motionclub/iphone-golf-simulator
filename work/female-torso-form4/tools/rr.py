"""rr.py: render ROI shots for one or more coordinate files and compose plate | a | b | ...
usage: python3 tools/rr.py <roi> <out.png> <look> [label=coords.npy ...]
roi in viz3.ROIS ; look = matcap:soft | matcap:clay_studio.exr | eevee | cycles ; extra env CAV=0.4 for workbench cavity"""
import sys, json, subprocess, os
sys.path.insert(0, os.path.dirname(__file__))
from viz3 import *
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = HERE + '/START_form3_candidate.blend'


def render(rois, coords, tag, look='matcap:soft', cav=0.0, extra=None, shots_extra=None):
    shots = [roi_shot(f'{r}', r) for r in rois]
    if shots_extra:
        shots += shots_extra
    spec = {"coords": coords, "out": f"{HERE}/scratch/r/{tag}", "shots": shots, "look": look, "cavity": cav}
    if extra:
        spec.update(extra)
    p = f"{HERE}/scratch/r/spec_{tag}.json"
    json.dump(spec, open(p, 'w'))
    r = subprocess.run([BL, '-b', START, '--python', HERE + '/tools/render3.py', '--', json.dumps(spec)], capture_output=True, text=True)
    if 'RENDER_OK' not in r.stdout:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit('render failed')
    return [f"{HERE}/scratch/r/{tag}_{s['name']}.png" for s in shots]


if __name__ == '__main__':
    roi, out, look = sys.argv[1], sys.argv[2], sys.argv[3]
    items = [a.split('=', 1) for a in sys.argv[4:]]
    cav = float(os.environ.get('CAV', '0'))
    ims, labs = [plate_crop(roi, 1.0)], ['PLATE']
    for lab, co in items:
        p = render([roi], co if co.startswith('/') else HERE + '/' + co, 'rr_' + lab.replace(' ', '_'), look, cav)[0]
        ims.append(p)
        labs.append(lab)
    strip(ims, labs).save(out)
    print(out)
