"""ua_cmp.py <run> [...]: underarm subset, today's polo (N1_BASE) vs each run, per pose + totals."""
import json, glob, sys
def rows(r): return {x['i']: x for x in (json.loads(l) for l in open(sorted(glob.glob(f'runs/{r}/suite/MatchHero_Male/rows_*.jsonl'))[-1]))}
sub = json.load(open('runs/ua_subset_male.json')); B = rows('N1_BASE'); R = {r: rows(r) for r in sys.argv[1:]}
key = ['Shock', 'Serve', 'Strike2', 'Turkey', 'Strike3', 'Split', 'Cheer', 'FollowThrough', 'Release']
print(f"{'group':14s} {'today':>7s}" + ''.join(f" {r:>8s}" for r in R))
for k in key:
    ids = [i for i in sub if k in B[i]['clip']]
    print(f"{k:14s} {sum(B[i]['tear'] for i in ids):7d}" + ''.join(f" {sum(R[r][i]['tear'] for i in ids if i in R[r]):8d}" for r in R))
print(f"{'TOTAL tear':14s} {sum(B[i]['tear'] for i in sub):7d}" + ''.join(f" {sum(R[r][i]['tear'] for i in sub if i in R[r]):8d}" for r in R))
print(f"{'TOTAL layer':14s} {sum(B[i]['layer'] for i in sub):7d}" + ''.join(f" {sum(R[r][i]['layer'] for i in sub if i in R[r]):8d}" for r in R))
