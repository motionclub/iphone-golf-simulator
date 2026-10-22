"""try_wf.py <wf> : set the face weight on the racket keys between 0.37 and 1.00 s (the key blocks that SERVE_TOSS_ARM added), solve unspliced, print the per-frame difference to the job-start clip"""
import re, subprocess, sys
p = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump/scripts/serve_new.py'
s = open(p).read()
wf = sys.argv[1]
a = s.index("K(g(0.30), 'S3.R1'"); b = s.index("K(T_T, 'S3.R3', rk_pos=rs(125, 42, 0.45)")
blk = re.sub(r"rk_w=\[[\d.]+, 1\.0\]", f"rk_w=[{wf}, 1.0]", s[a:b])
open(p, 'w').write(s[:a] + blk + s[b:])
