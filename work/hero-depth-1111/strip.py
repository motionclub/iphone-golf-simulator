#!/usr/bin/env python3
"""strip.py <film dir> <out.jpg> <start> <count> [every] [views]: rows = views, columns = consecutive samples."""
import sys, glob, os, subprocess
d, out, start, count = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
every = int(sys.argv[5]) if len(sys.argv) > 5 else 1
views = sys.argv[6].split(',') if len(sys.argv) > 6 else ['back', 'front', 'side', 'feet']
ids = sorted({os.path.basename(f).split('_', 1)[1] for f in glob.glob(d + '/back_*.jpg')})
pick = ids[start:start + count * every:every]
args = []
for v in views:
    for i in pick: args.append(f'{d}/{v}_{i}::{v} {i[:4]} {i[5:-4][:6]}')
subprocess.run(['python3', os.path.dirname(os.path.abspath(__file__)) + '/sheet.py', out, str(len(pick)), '300'] + args)
