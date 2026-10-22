#!/usr/bin/env python3
"""Run the area-I Game-view measurement (v2/proof/measure.py, with the round-3 BASALT_JOINTS additions) on a PRIVATE copy of the inputs, so area I's metrics.json / METRICS.md / masks are not overwritten.
usage: python3 measure_r3.py <stills dir (9 PNG + stills_stats.json)> <proofcopy dir (masks/9/, optional mesh_checks.json)>"""
import sys, os, shutil
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/proof")
import measure as M
stills, proofcopy = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
mc = os.path.join(M.P, "mesh_checks.json")
if os.path.exists(mc) and not os.path.exists(os.path.join(proofcopy, "mesh_checks.json")):
    shutil.copy(mc, proofcopy)
M.ART = stills; M.P = proofcopy
os.makedirs(proofcopy, exist_ok=True)
M.main()
