"""Per-gate mutation table from a self-test log: for every gate id, how many mutants that must FAIL it do (MUT_FAILS_ON_BAD) and how many positives / controls
that must PASS it do (MUT_PASSES_ON_GOOD). Usage: summarize_mut.py <selftest log> [--json out.json]"""
import re, sys, json, ast, collections
log = open(sys.argv[1], errors="ignore").read().splitlines()
bad = collections.defaultdict(lambda: [0, 0])      # gate -> [ok, total]
good = collections.defaultdict(lambda: [0, 0])
pos_fail = collections.defaultdict(list)
for ln in log:
    m = re.match(r"SELFTEST: hole (\d+) mutation (\S+): must FAIL (\[.*?\]), failed (.*?)( / FBX .*?)?( \(also failed.*\))? (PASS|FAIL)$", ln)
    if m:
        exp = ast.literal_eval(m.group(3)); ok = m.group(7) == "PASS"
        for g in exp:
            bad[g][1] += 1; bad[g][0] += ok
        continue
    m = re.match(r"SELFTEST: hole (\d+) control (\S+): must still PASS (\[.*?\]), failed now .* (PASS|FAIL)$", ln)
    if m:
        exp = ast.literal_eval(m.group(3)); ok = m.group(4) == "PASS"
        for g in exp:
            good[g][1] += 1; good[g][0] += ok
        continue
    m = re.match(r"SELFTEST: hole (\d+) synthetic positive \(blend \+ FBX\): (\d+) gates, expected ALL PASS, failed (\[.*?\]) (PASS|FAIL)$", ln)
    if m:
        failed = {x.split("@")[0] for x in ast.literal_eval(m.group(3))}
        pos_fail[m.group(1)] = sorted(failed)
        continue
    m = re.match(r"SELFTEST: (?:hole (\d+) )?mutation (\S+): must FAIL \['(\w+)'\].*(PASS|FAIL)$", ln)
rows = {}
for g in sorted(set(bad) | set(good)):
    rows[g] = dict(bad_ok=bad[g][0], bad_n=bad[g][1], good_ok=good[g][0], good_n=good[g][1])
# positives: every gate a positive passes counts as a good case; read the SELFTEST_GATE lines for the totals the tool itself counted
sg = {}
for ln in log:
    m = re.match(r"SELFTEST_GATE (\w+) MUT_FAILS_ON_BAD (\d+)/(\d+) (PASS|FAIL); MUT_PASSES_ON_GOOD (\d+)/(\d+) (PASS|FAIL)", ln)
    if m:
        sg[m.group(1)] = dict(bad_ok=int(m.group(2)), bad_n=int(m.group(3)), good_ok=int(m.group(5)), good_n=int(m.group(6)),
                              ok=(m.group(4) == "PASS" and m.group(7) == "PASS"))
out = dict(per_gate_from_lines=rows, selftest_gate=sg, positives_failed=pos_fail)
if "--json" in sys.argv:
    json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
print(f"{'gate':32s} {'MUT_FAILS_ON_BAD':>18s} {'MUT_PASSES_ON_GOOD':>20s}")
for g in sorted(set(rows) | set(sg)):
    r = sg.get(g) or rows[g]
    print(f"{g:32s} {r['bad_ok']:>8d}/{r['bad_n']:<8d} {r['good_ok']:>10d}/{r['good_n']:<8d}")
print("positives failed gates:", dict(pos_fail))
