#!/usr/bin/env python3
"""clip_usage.py proof/trace.csv : NEW_CLIPS / MISSING_LISTED. Which FBX clip each hero played in the rally trace (frames per role + clip) and whether any clip that is not one of the
32 match-set clips (an old Hero_* clip) was ever playing."""
import csv, collections, json, os, sys
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
rows = list(csv.DictReader(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, 'proof/trace.csv'))))
tab = json.load(open(os.path.join(root, 'data/clip_table.json')))
known = {f"{h['sex']}_{c['name']}" for h in tab['heroes'] for c in h['clips']}
cnt = collections.Counter((r['role'], r['clip']) for r in rows)
swing = collections.Counter((r['clip']) for r in rows if r['swinging'] == 'True')
out = ["frames per (role, clip) over both rallies (vs Nadia: male player / female rival; vs Viktor: female player / male rival):"]
for (role, clip), n in sorted(cnt.items()): out.append(f"  {role:6s} {clip:24s} {n:6d} frames{'' if clip in known else '   <-- NOT A MATCH-SET CLIP'}")
out.append("")
out.append("swing frames (actor.Swinging) per clip: " + ", ".join(f"{c}={n}" for c, n in sorted(swing.items())))
bad = sorted({c for (_, c) in cnt if c not in known})
need = ['Serve', 'Forehand', 'Backhand', 'VolleyForehand', 'VolleyBackhand', 'Overhead']
seen = {k: any(c.endswith('_' + k) and n > 0 for (_, c), n in cnt.items()) for k in need}
out.append("")
out.append("every clip that played is one of the 32 match-set clips: " + ("YES" if not bad else "NO " + str(bad)))
out.append("serve / forehand / backhand / volley (both) / overhead all played in the rallies: " + ("YES" if all(seen.values()) else "NO " + str(seen)))
for sex in ('Male', 'Female'):
    out.append(f"  {sex}: " + ", ".join(f"{k}={'played' if any(c == sex + '_' + k and n > 0 for (_, c), n in cnt.items()) else 'not seen'}" for k in need))
print("\n".join(out)); open(os.path.join(root, 'proof/clip_usage.txt'), 'w').write("\n".join(out) + "\n")
