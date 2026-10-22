"""Gate metrics vs the plates for a vertex array: python3.13 metrics.py <tag>"""
import sys; sys.path.insert(0, '.')
import contours as C
from m1i_lib import *
tag = sys.argv[1]
V, F, loops = load(tag); E = edges_of(F)
print('=== 3/4 contours (mesh - plate, mm) ===')
res = C.report_q3(V, E, rows=[502, 514, 526, 538, 550, 556, 562, 568, 574, 580], verbose=True)
print('=== profile / front silhouette (mesh - plate, mm) ===')
C.report_profile(V, E, rows=list(range(96, 262, 8)))
