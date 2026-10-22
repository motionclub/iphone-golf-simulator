import csv, sys, math
def load(p):
    r = list(csv.reader(open(p))); h = r[0]; rows = r[1:]
    names = []
    for c in h[3:]:
        n = c.rsplit("_", 1)[0]
        if n not in names: names.append(n)
    return h, rows, names
def q(row, h, n):
    i = h.index(n + "_qx"); return [float(x) for x in row[i:i+4]], [float(x) for x in row[i+4:i+7]]
def ang(a, b):
    d = abs(sum(x*y for x, y in zip(a, b))); return 2*math.degrees(math.acos(min(1, d)))
for p in sys.argv[1:]:
    h, rows, names = load(p + "/bones.csv")
    print("==", p.split("/")[-1])
    # frames 385..400 per-frame angular step for each bone (degrees)
    for n in names:
        steps = []
        for i in range(1, len(rows)):
            f = int(rows[i][1])
            if 380 <= f <= 405:
                steps.append((f, ang(q(rows[i-1], h, n)[0], q(rows[i], h, n)[0])))
        print(f"{n:14s}", " ".join(f"{a:5.0f}" for f, a in steps))
    print("frames", [f for f, a in steps])
