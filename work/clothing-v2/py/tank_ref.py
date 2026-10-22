"""Female tennis top towards reference sheet 09 (neutral pack 2026-10-15): the 10-16 'soulful' tank (female-soulful/build_garments.py,
tank2.py + drape settle) with design overrides from TANK_DESIGN (JSON). Blender -b --factory-startup --python tank_ref.py -- <out.blend>"""
import sys, os, json, importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('build_garments', HERE.parent.parent / 'female-soulful' / 'build_garments.py')
bg = importlib.util.module_from_spec(spec); spec.loader.exec_module(bg)
a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]; job = a[1] if len(a) > 1 else 'tennis_top'
nxt = {'tennis_top': 'def golf_top():', 'golf_top': 'def skirt(golf):'}[job]
over = json.loads(os.environ.get('TANK_DESIGN', '{}'))
src = (HERE.parent.parent / 'female-soulful' / 'build_garments.py').read_text()
# reuse tennis_top() exactly, only redirect the output and add the overrides on top of its design
fn = src[src.index('def %s():' % job):src.index(nxt)]
fn = fn.replace("        return d\n", "        d.update(OVER)\n        return d\n").replace("str(ROOT/'source/tennis_top.blend')", "OUT").replace("str(ROOT/'source/golf_top.blend')", "OUT")
ns = dict(bg.__dict__); ns.update(OVER=over, OUT=out)
exec(fn, ns); ns[job]()
print('TANKREF', out, over)
