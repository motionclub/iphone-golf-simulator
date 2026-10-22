"""python3 tools/set_verdict5.py bust=PASS underbutt=PASS mirror=PASS "notes text" -> export/visual_verdict.json"""
import sys, json
from pathlib import Path
WD = Path(__file__).resolve().parent.parent
v = {'bust': 'PENDING', 'underbutt': 'PENDING', 'mirror': 'PENDING', 'notes': ''}
for a in sys.argv[1:]:
    if '=' in a and a.split('=')[0] in ('bust', 'underbutt', 'mirror'):
        k, val = a.split('=', 1); v[k] = val
    else:
        v['notes'] += a
json.dump(v, open(WD / 'export/visual_verdict.json', 'w'), indent=1)
print(v)
