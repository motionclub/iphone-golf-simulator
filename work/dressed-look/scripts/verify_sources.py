"""python3 verify_sources.py <out.json> : SHA-256 of the five source blends against the SHAs in the brief (stdlib only)."""
import sys, json, hashlib, os, time
REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
SRC = dict(
    male_body=REPO + '/work/male-pelvis-form3/export/merged_fd04bc28.blend',
    female_body=REPO + '/work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend',
    kit_male=REPO + '/work/standard-tennis-kit-worn/export/StandardKit_Male.blend',
    kit_female=REPO + '/work/standard-tennis-kit-worn/export/StandardKit_Female.blend',
    racket=REPO + '/work/classic-tennis-racket/export/Racket_Classic.blend')
SHA = dict(
    male_body='d6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781',
    female_body='a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1',
    kit_male='ad07a7b9ba984b0f220f975b9fe1b0c1b7068d9897c7e6f96e44f70d23aa77a9',
    kit_female='f19a9c03789b7af343c56b005ed587137e8764779d31c3109942156ee71eaf4e',
    racket='53e83714856a14c1533653b3fce3e164dfb17e9c58c995cbdb325d86eec7e8ba')
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()
res = {}
ok = True
for k, p in SRC.items():
    if not os.path.exists(p):
        res[k] = dict(path=p, missing=True, ok=False); ok = False; continue
    g = sha(p); st = os.stat(p)
    res[k] = dict(path=p, sha256=g, expected=SHA[k], ok=(g == SHA[k]), size=st.st_size, mtime_ns=st.st_mtime_ns)
    ok = ok and g == SHA[k]
json.dump(dict(taken=time.strftime('%Y-%m-%d %H:%M:%S'), all_ok=ok, files=res), open(sys.argv[1], 'w'), indent=1)
print('ALL_OK' if ok else 'MISMATCH', {k: v['ok'] for k, v in res.items()})
