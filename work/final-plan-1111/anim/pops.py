"""pops.py <round>: frames where the limits make the arm jump: the wrist or elbow after the limits changes by much more from one
frame to the next than the clip's own pose did (same hero, same side, consecutive frames)."""
import sys, csv, os, collections
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[1])
for sp in sorted(os.listdir(R)):
    f = os.path.join(R, sp, "arms.csv")
    if not os.path.exists(f): continue
    g = collections.defaultdict(list)
    for r in csv.DictReader(open(f)): g[(r['ctx'], r['sex'] + r.get('hero','')[-3:], r['side'])].append(r)
    for k, a in sorted(g.items()):
        n = 0; pops = []; switches = 0
        for p, q in zip(a, a[1:]):
            if int(q['frame']) - int(p['frame']) != 1: continue
            n += 1
            dB = abs(float(q['wristB']) - float(p['wristB'])); dA = abs(float(q.get('wristL', q['wristA'])) - float(p.get('wristL', p['wristA'])))   # the limits' own result (later passes, such as the ball in the toss hand, are not theirs)
            eB = abs(float(q['elbowB']) - float(p['elbowB'])); eA = abs(float(q['elbowA']) - float(p['elbowA']))
            if q['holds'] != p['holds']: switches += 1
            if dA > dB + 8 or eA > eB + 8: pops.append((int(q['frame']), p['holds'] + '>' + q['holds'], round(dB), round(dA), round(eB), round(eA)))
        print(f"{sp:9} {' '.join(k):22} pairs {n:5}  kind switches {switches:3}  pops {len(pops):3}  {pops[:6]}")
