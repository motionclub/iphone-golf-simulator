# For this chat's Unity clone only: take the wave-2 siblings' in-progress hooks (B mannerisms, E course/FX) back out of
# GolfGame.cs, so the shared checkout's finished wave-1 work + chat C compile while B/E/G files stay at HEAD in the clone.
import sys
p = sys.argv[1]; s = open(p).read()
s = s.replace(", club == GolfClub.Putter, lastReport.Grade);", ", club == GolfClub.Putter);")
s = s.replace(" or ObstacleKind.Twister or ObstacleKind.Launchpad or ObstacleKind.Target)", " or ObstacleKind.Twister)")
s = "\n".join(l for l in s.split("\n") if "HookMannerisms();" not in l)
open(p, "w").write(s)
