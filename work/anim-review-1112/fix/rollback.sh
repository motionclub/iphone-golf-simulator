#!/usr/bin/env python3
# rollback.sh <Unity project dir>: remove EMPTY HANDS (HeroHands.cs and its two call sites).
import os, re, sys
S = os.path.join(sys.argv[1], 'Assets/Scripts')
for f in ('Tennis/HeroHands.cs', 'Tennis/HeroHands.cs.meta'):
    p = os.path.join(S, f)
    if os.path.exists(p): os.remove(p)
for rel in ('Game/GolferView.cs', 'Hub/HubHeroAnimator.cs'):
    p = os.path.join(S, rel); s = open(p).read()
    s = re.sub(r'[ \t]*// EMPTY HANDS 2026-11-12:.*\n(?:[ \t]*// .*\n)?[ \t]*if \(.*HeroHands\.Empty.*\n', '', s)
    s = re.sub(r'[ \t]*/// A club mesh is showing \(in the hands\): only then do the hands grip\.\n[ \t]*bool ClubShown\(\).*\n', '', s)
    open(p, 'w').write(s); print(rel, 'HeroHands' in s and 'STILL REFERENCES HeroHands' or 'clean')
