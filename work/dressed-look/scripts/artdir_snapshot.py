"""Snapshot ArtDir (stat manifest of every file + SHA-256 of the hero base_lock files). python3 artdir_snapshot.py <out.json>
Read-only: nothing under ArtDir is opened for writing."""
import os, sys, json, hashlib, time
REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
ART = REPO + '/ArtDir'
out = sys.argv[1]
man = {}
for root, dirs, files in os.walk(ART):
    for f in files:
        p = os.path.join(root, f)
        try:
            st = os.stat(p)
        except OSError:
            continue
        man[os.path.relpath(p, ART)] = [st.st_size, st.st_mtime_ns]
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for ch in iter(lambda: fh.read(1 << 20), b''):
            h.update(ch)
    return h.hexdigest()
key = {}
for rel in sorted(man):
    if rel.startswith('hero/base_lock/') and man[rel][0] < 400 * 1024 * 1024:
        key[rel] = sha(os.path.join(ART, rel))
json.dump(dict(taken=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=len(man), total_bytes=sum(v[0] for v in man.values()), manifest=man, key_sha256=key), open(out, 'w'))
print('files', len(man), 'bytes', sum(v[0] for v in man.values()), 'hashed', len(key))
