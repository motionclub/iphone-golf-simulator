"""open_lava_gate.py STAGE_SHARES.json ROUND1_SHARES.json ROUND2_SHARES.json : H_OPEN_LAVA from the mask renders (tools/render_views.py --mask, 4 aerial cameras of landmarks_with_aerial.json).

Round-1 reviewer: 'a strip and a small pillar in a huge orange lake' (orange 63-72 % of the aerial); round-2 reviewer: 44.7 / 50.4 / 42.3 % in his own cameras, crater.jpg is far lower.
Measured as the share of the NON-SKY pixels that are lava (WATER_LAVA mask colour) on the same four cameras for the round-1 build, the round-2 build and this build.
GATE: H_OPEN_LAVA PASS iff every camera is at least 5 points below round 2, no camera is above 45 %, the mean is <= 40 % and at least 10 points below round 2 (round 2 gate: 55 %), and rock (+ cone) is >= 40 % of the
non-sky pixels in every camera. The reference still stays far lower (about 15-25 %): this build does not reach it (the crater floor is 340 yd across for a 357 yd hole, the keep-outs
round the play surfaces stay 24 / 38 / 25 yd), the numbers are printed.
"""
import json
import sys
now = json.load(open(sys.argv[1]))
old1 = json.load(open(sys.argv[2]))
old2 = json.load(open(sys.argv[3]))
rows, ok = [], True
means = []
for k in sorted(now):
    n, o1, o2 = now[k]["lava_of_nonsky"], old1[k]["lava_of_nonsky"], old2[k]["lava_of_nonsky"]
    rock = now[k]["rock_of_nonsky"]
    means.append(n)
    good = (o2 - n) >= 0.05 and n <= 0.45 and rock >= 0.40
    ok &= good
    rows.append(f"{k.replace('hole10_', '').replace('.png', '')}: lava {n:.1%} of non-sky (round 1 {o1:.1%}, round 2 {o2:.1%}, -{(o2 - n) * 100:.1f} pts vs round 2), rock {rock:.1%}{'' if good else ' FAIL'}")
mean = sum(means) / len(means)
m1 = sum(v["lava_of_nonsky"] for v in old1.values()) / len(old1)
m2 = sum(v["lava_of_nonsky"] for v in old2.values()) / len(old2)
ok &= mean <= 0.40 and (m2 - mean) >= 0.10
print(f"GATE: H_OPEN_LAVA {'PASS' if ok else 'FAIL'} - " + "; ".join(rows) + f"; mean {mean:.1%} (<= 40 %; round 1 {m1:.1%}, round 2 {m2:.1%}); mask renders of the 4 aerial cameras (preview geometry, not the Game view); the reference still is ~15-25 % lava")
sys.exit(0 if ok else 1)
