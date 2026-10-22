"""Summarise the replay of the skeptic's mutants (v2/gates/review3/mut2_h*.log, mut3_h*.log): per hole how many ran, which attacks (names containing
RK_ / FM_ / LB_ / PL_ / foam / skirt / baked / welded / terrain_wall / UP_) FAIL which gates, and every mutant that FAILS NO gate (controls expected)."""
import re, os, glob, collections
G = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "review3"))
rows = collections.OrderedDict()
for h in (8, 9, 10):
    for sc in ("mut2", "mut3"):
        p = os.path.join(G, f"{sc}_h{h}.log")
        if not os.path.isfile(p):
            continue
        for ln in open(p, errors="replace"):
            m = re.match(r"MUT (\d+) (\S+) -> (FAILED|HARNESS-ERROR)(.*)", ln)
            if not m:
                continue
            nm = m.group(2)
            fails = sorted({x for x in re.findall(r"'([A-Z_0-9]+)@", m.group(4).split("NEW")[0])})
            rows[(h, sc, nm)] = (m.group(3), fails, m.group(4)[:90])
for h in (8, 9, 10):
    r = {k: v for k, v in rows.items() if k[0] == h}
    if not r:
        continue
    err = [k[2] for k, v in r.items() if v[0] != "FAILED"]
    none = [k[2] for k, v in r.items() if v[0] == "FAILED" and not v[1]]
    print(f"hole {h}: {len(r)} mutants run (blend + FBX), {len(err)} harness errors {err[:6]}, {len(none)} fail NO gate (controls / design passes): {none}")
key = ("RK_", "FM_", "LB_", "PL_", "foam", "skirt", "baked", "welded", "terrain_wall", "UP_", "rk_bundle", "rk_ico", "pl_", "st_scale", "st_shear", "stack_")
print("attacks of the review rounds and the gates that catch them (hole 8 / 9):")
seen = set()
for (h, sc, nm), (st, fails, _t) in rows.items():
    if h in (8, 9) and any(nm.startswith(k) or k in nm for k in key) and (nm, h) not in seen:
        seen.add((nm, h))
        print(f"  h{h} {nm:52s} -> {','.join(fails) if fails else '(none)'}")
