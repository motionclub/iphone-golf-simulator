import re, subprocess, sys, json
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-dip-jump'
rk, sh = sys.argv[1], sys.argv[2]
p=W+'/scripts/serve_new.py'; s=open(p).read()
s=re.sub(r"K\(g\(0\.27\), 'S3.R1', rk_pos=\[[^\]]*\], shaft=D\([^)]*\)", f"K(g(0.27), 'S3.R1', rk_pos=[{rk}], shaft=D({sh})", s)
open(p,'w').write(s)
