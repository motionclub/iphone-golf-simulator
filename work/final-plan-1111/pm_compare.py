#!/usr/bin/env python3
"""pm_compare.py <base-label> <new-label>: per-test PlayMode results of the baseline copy against the changed copy (logs/<label>-<batch>.xml)."""
import sys, glob, os, xml.etree.ElementTree as E
base, new = sys.argv[1], sys.argv[2]
def load(label):
    out = {}
    for f in sorted(glob.glob(f"logs/{label}-*.xml")):
        batch = os.path.basename(f)[len(label) + 1:-4]
        for t in E.parse(f).getroot().iter("test-case"):
            m = t.find(".//message")
            out[t.get("fullname").replace("GolfArcade.PlayTests.", "").replace("GolfArcade.Tests.", "")] = (
                t.get("result"), batch, " ".join(((m.text or "") if m is not None else "").split())[:230])
    return out
b, n = load(base), load(new)
count = lambda d: {r: sum(1 for v in d.values() if v[0] == r) for r in ("Passed", "Failed", "Skipped")}
print("baseline", len(b), count(b)); print("changed ", len(n), count(n))
for title, pick in (("PASS -> FAIL", lambda x, y: x == "Passed" and y == "Failed"), ("FAIL -> PASS", lambda x, y: x == "Failed" and y == "Passed")):
    print("\n==", title)
    for k in sorted(b):
        if k in n and pick(b[k][0], n[k][0]): print(f"  [{n[k][1]}] {k}\n      base: {b[k][2]}\n      new:  {n[k][2]}")
print("\n== FAIL in both, different message")
for k in sorted(b):
    if k in n and b[k][0] == n[k][0] == "Failed" and b[k][2] != n[k][2]: print(f"  [{n[k][1]}] {k}\n      base: {b[k][2]}\n      new:  {n[k][2]}")
print("\n== only in one run")
for k in sorted(set(b) ^ set(n)): print("  ", "base only" if k in b else "new only", k, (b.get(k) or n.get(k))[0])
