#!/usr/bin/env python3
"""send.py <cmd.json | -> [timeout]: hand one command to the film server and wait for it."""
import sys, os, time, json, shutil
W = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(W, "stage")
src = sys.argv[1]; timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 900
data = sys.stdin.read() if src == "-" else open(src).read()
json.loads(data)
done = os.path.join(S, "done.txt")
if os.path.exists(done): os.remove(done)
tmp = os.path.join(S, "cmd.tmp"); open(tmp, "w").write(data); os.replace(tmp, os.path.join(S, "cmd.json"))
t0 = time.time()
while not os.path.exists(done):
    if time.time() - t0 > timeout: print("TIMEOUT"); sys.exit(2)
    time.sleep(.25)
time.sleep(.1)
r = open(done).read(); print(r[:3000]); 
lg = os.path.join(S, "log.txt")
if os.path.exists(lg): print(open(lg).read()[:6000])
print("%.1fs" % (time.time() - t0)); sys.exit(0 if r.startswith("ok") else 1)
