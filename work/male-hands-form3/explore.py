"""py.sh explore.py base.json  'name={json overrides}' ...   -> ROI xor total / per ROI / full sil for each variation"""
import sys, json
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import evalp
base = json.load(open(sys.argv[1]))
def show(name, p):
    r = evalp.evaluate(p)
    print('%-28s roi %5d  [%s]  full bf %.3f bb %.3f' % (name, r['roi_total'], ' '.join('%3d' % v for v in r['roi'].values()), r['full']['bald_front'], r['full']['bald_back']))
show('base', base)
for a in sys.argv[2:]:
    name, js = a.split('=', 1); p = dict(base); p.update(json.loads(js)); show(name, p)
