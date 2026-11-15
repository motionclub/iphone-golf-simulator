"""stats.py <round> [sport...]: the probe's arms.csv per sport, hero, side and held / empty hand: the wrist's bend before and after
the limits (mean, 95th percentile, worst), the share of frames past 45 and past 60 degrees, the elbow's range, the swivel used."""
import sys, csv, os, collections
import numpy as np
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[1])
sports = sys.argv[2:] or sorted(d for d in os.listdir(R) if os.path.exists(os.path.join(R, d, "arms.csv")))
def rows(sport):
    with open(os.path.join(R, sport, "arms.csv")) as f: return list(csv.DictReader(f))
if __name__ == "__main__":
    print(f"{'sport':10}{'who':16}{'frames':>7} | wrist before: mean  p95  max  >45  >60 | after: mean  p95  max  >45  >60 | elbow b/a max | swivel p95")
    for sp in sports:
        g = collections.defaultdict(list)
        for r in rows(sp): g[(r['ctx'].split('/')[-1], r['sex'], r['side'], {'0':'free','1':'grip','2':'support'}.get(r['holds'],r['holds']))].append(r)
        for k in sorted(g):
            a = g[k]; b = np.array([float(r['wristB']) for r in a]); c = np.array([float(r['wristA']) for r in a])
            eb = np.array([float(r['elbowB']) for r in a]); ea = np.array([float(r['elbowA']) for r in a]); sw = np.abs(np.array([float(r['swivel']) for r in a]))
            f = lambda x: f"{x.mean():5.0f}{np.percentile(x,95):5.0f}{x.max():5.0f}{(x>45).mean()*100:4.0f}%{(x>60).mean()*100:4.0f}%"
            print(f"{sp:10}{' '.join(k):16}{len(a):7} |              {f(b)} |       {f(c)} | {eb.max():5.0f}/{ea.max():3.0f}    | {np.percentile(sw,95):5.0f}")
