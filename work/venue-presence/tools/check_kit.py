"""COURT_UNCHANGED: every kept court-kit object sits exactly where it did before.

    check_kit.py <kit_before.txt> <capture log> [<capture log> ...]

`kit_before.txt` is the baseline dump of the kept kit (centre and size per object). The logs are Unity capture logs made with
HERO_VENUE_DUMP=1 HERO_VENUE_DUMP_KIT=1. For each baseline object the same name must appear in each log with the same centre and size
(to 0.01 m). Also reports the resort dressing (017/020/033): none may still be an enabled renderer.
"""
import re, sys

LINE = re.compile(r"\[VenueDump\] kit (TropicalV3_\d+) '([^']*)' tris=\d+ centre=\(([^)]*)\) size=\(([^)]*)\)")

def vec(s): return tuple(float(x) for x in s.split(','))

def parse_logs(path):
    out = {}
    for line in open(path, errors='replace'):
        m = LINE.search(line)
        if m: out[(m.group(1), m.group(2))] = (vec(m.group(3)), vec(m.group(4)))
    return out

def parse_before(path):
    out = {}
    pat = re.compile(r"^(TropicalV3_\d+) '([^']*)'\s+centre=\(([^)]*)\)\s+size=\(([^)]*)\)")
    for line in open(path):
        m = pat.match(line)
        if m: out[(m.group(1), m.group(2))] = (vec(m.group(3)), vec(m.group(4)))
    return out

if __name__ == '__main__':
    before = parse_before(sys.argv[1]); ok = True
    for log in sys.argv[2:]:
        after = parse_logs(log); print(f'-- {log}: {len(after)} kit renderers enabled')
        for key, (c0, s0) in before.items():
            hit = [v for k, v in after.items() if k[0] == key[0] and (k[1] == key[1] or k[1].startswith(key[1]) or key[1].startswith(k[1]))]
            if not hit: print(f'   MISSING {key}'); ok = False; continue
            c1, s1 = hit[0]
            dc = max(abs(a - b) for a, b in zip(c0, c1)); ds = max(abs(a - b) for a, b in zip(s0, s1))
            status = 'same' if dc <= .011 and ds <= .011 else 'MOVED'
            if status != 'same': ok = False
            print(f'   {status:5s} {key[0]} {key[1][:44]:44s} dCentre={dc:.3f} dSize={ds:.3f}')
        dressing = [k for k in after if k[0] in ('TropicalV3_017', 'TropicalV3_020', 'TropicalV3_033')]
        print(f'   resort dressing still enabled: {len(dressing)}' + ('' if not dressing else '  <-- FAIL'))
        if dressing: ok = False
    print('GATE COURT_UNCHANGED (kit part):', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)
