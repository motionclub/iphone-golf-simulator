import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
Vn, polys, si = asm3.assemble(json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}, verbose=False)
print('C_loop (a,n,w) =', [round(float(x), 6) for x in si[+1]['info']['C_loop']])
