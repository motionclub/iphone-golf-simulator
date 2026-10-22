"""mergeparams3.py bust.json glute.json out.json : take every bust/chest-side key from bust.json and every glute-side key from glute.json"""
import sys, json
GLUTE_PREFIX = ('gl_', 'gm_', 'cl_', 'll_', 'gc_', 'bk_')
GLUTE_KEYS = {'gm', 'leg_f', 'leg_r', 'lf_on', 'lf_x0', 'lf_x1'}
b = json.load(open(sys.argv[1])); g = json.load(open(sys.argv[2]))
out = dict(b)
for k, v in g.items():
    if k.startswith(GLUTE_PREFIX) or k in GLUTE_KEYS:
        out[k] = v
json.dump(out, open(sys.argv[3], 'w'), indent=1)
print('merged ->', sys.argv[3], '; glute keys taken:', sorted(k for k in g if k.startswith(GLUTE_PREFIX) or k in GLUTE_KEYS)[:6], '...')
