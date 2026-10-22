"""unpatch_cs.py <project Unity root> : removes exactly the lines patch_cs.py added (TennisGame taunt hold + the HeroTennisDriver call).  Other edits in those files are left alone."""
import sys, os, re
root = sys.argv[1]
g = os.path.join(root, 'Assets/Scripts/Tennis/TennisGame.cs')
d = os.path.join(root, 'Assets/Scripts/Tennis/HeroTennisDriver.cs')
s = open(g).read()
i0 = s.find('        /// EMOTES: a taunt longer than the between-points beat keeps the next serve waiting')
if i0 >= 0:
    i1 = s.index('void ApplyTauntHold()', i0)
    i1 = s.index('\n', i1) + 1
    s = s[:i0] + s[i1:]
s = re.sub(r'\n            ApplyTauntHold\(\);[^\n]*', '', s)
s = s.replace('void BeginPoint() { tauntHold = 0;', 'void BeginPoint() {')
open(g, 'w').write(s)
s = open(d).read()
s = re.sub(r'\n            if \(game && Array\.IndexOf\(Taunts, c\) >= 0\) game\.HoldNextPoint[^\n]*', '', s)
open(d, 'w').write(s)
print('reverted')
