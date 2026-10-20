"""try_left.py <d_release> <d_ext> : set the left-arm radii (p1 and the 0.90 / 1.17 keys), rebuild the male Serve, print left elbow flex + the worst arm steps up to frame 46"""
import re, subprocess, sys
p = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-dip-jump/scripts/serve_new.py'
s = open(p).read()
dr, de = sys.argv[1], sys.argv[2]
s = re.sub(r"p1 = np.array\(ls\(2, 56, [\d.]+\)\)", f"p1 = np.array(ls(2, 56, {dr}))", s)
s = re.sub(r"K\(g\(0\.90\), 'S3.R3', l_hand=ls\(0, 86, [\d.]+\)", f"K(g(0.90), 'S3.R3', l_hand=ls(0, 86, {de})", s)
s = re.sub(r"K\(g\(1\.17\), 'S3.R3', l_hand=ls\(0, 88, [\d.]+\)", f"K(g(1.17), 'S3.R3', l_hand=ls(0, 88, {de})", s)
open(p, 'w').write(s)
