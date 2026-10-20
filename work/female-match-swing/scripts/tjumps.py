import csv, sys, math
def ang(a, b): d = abs(sum(x*y for x, y in zip(a, b))); return 2*math.degrees(math.acos(min(1, d)))
for p in sys.argv[1:]:
    r = list(csv.reader(open(p))); h = r[0]; rows = r[1:]
    names = []
    for c in h[2:]:
        n = c.rsplit("_", 1)[0]
        if n not in names: names.append(n)
    print("==", p.split("/")[-2], p.split("/")[-1], len(rows), "frames")
    for n in names:
        i = h.index(n + "_qx"); steps = []
        for k in range(1, len(rows)):
            a = [float(x) for x in rows[k-1][i:i+4]]; b = [float(x) for x in rows[k][i:i+4]]
            steps.append((int(rows[k][0]), ang(a, b)))
        big = [(f, round(s)) for f, s in steps if s > 8]
        print(f"{n:14s} max {max(s for f,s in steps):5.1f}  >8deg frames: {len(big):3d}  {big[:8]}")
