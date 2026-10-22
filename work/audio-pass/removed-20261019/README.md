# Chat D audio pass, removed 2026-10-19 at Adnan's request

Everything chat D added is here. To restore it:
- copy `Unity/` back over the repo (or `git apply audio_edits.patch` for the 7 edited scripts)
- re-add D's two hooks in GolfGame.cs:
  - `sounds.PlayStrike(club, LastShot.Power, lastReport.Grade);` at the strike, instead of `sounds.PlayStrike(club, LastShot.Power);`
  - `sounds.OnRest(shot, toPin, club == GolfClub.Putter, InLava(shot));` in React(), after toPin is computed
