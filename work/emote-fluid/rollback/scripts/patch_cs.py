"""patch_cs.py <project Unity root> : the minimal C# change for the longer emotes (taunt hold).  Idempotent; upgrades the first (simple) form.

  TennisGame
    float tauntHold;  HoldNextPoint(seconds)  - a taunt asks the game to keep the next serve waiting for `seconds` of GAME time; the request is remembered until the point-over timer exists
    ApplyTauntHold()  - while a point is over and the serve timer runs (0 < resetTimer < 1e5: not a match result, not a live point) the timer is raised to the request (it only ever grows) and the request is consumed
    AwardPoint        - calls ApplyTauntHold() right after resetTimer is set (the reactions - and with them the taunt - start BEFORE that line)
    BeginPoint        - clears a stale request
  HeroTennisDriver.PlayEmote - for a TAUNT (Emote_Scuba / Emote_Thrust / Emote_Spike): game.HoldNextPoint((clip length + 0.4 s) * TennisGame.GameSpeed); the game's timers run at GameSpeed (1.2) x real time, which is
    why the old 2.0 s emotes fitted the 2.4 s beat.  Intros are played before the match and need no hold."""
import sys, os
root = sys.argv[1]
g = os.path.join(root, 'Assets/Scripts/Tennis/TennisGame.cs')
d = os.path.join(root, 'Assets/Scripts/Tennis/HeroTennisDriver.cs')
s = open(g).read()
if 'ApplyTauntHold' not in s:
    if 'HoldNextPoint' in s:                                        # first form -> remove it
        i0 = s.index('        /// EMOTES: a taunt longer than the between-points beat')
        i1 = s.index('\n', s.index('public void HoldNextPoint', i0)) + 1
        s = s[:i0] + s[i1:]
    old = "        public void Refeed() { resetTimer=0; BeginPoint(); }"
    new = old + """
        /// EMOTES: a taunt longer than the between-points beat keeps the next serve waiting until it has played out. The request (game seconds) is kept until the point-over timer exists, then the timer is
        /// raised to it once (it only ever grows; a match result or a live point is never touched).
        float tauntHold;
        public void HoldNextPoint(float seconds) { tauntHold = Mathf.Max(tauntHold, seconds); ApplyTauntHold(); }
        void ApplyTauntHold() { if (tauntHold > 0 && Flow == Phase.PointOver && resetTimer > 0 && resetTimer < 1e5f) { resetTimer = Mathf.Max(resetTimer, tauntHold); tauntHold = 0; } }"""
    assert s.count(old) == 1
    s = s.replace(old, new)
    old = "            resetTimer = Match.Complete ? (AutoPlay ? 5f : ResultsHold) : setWon ? 4.4f : 2.4f;   // 2B: reaction cam + auto emotes, then the next serve\n"
    assert s.count(old) == 1
    s = s.replace(old, old + "            ApplyTauntHold();                                                                       // EMOTES: a taunt started by the reactions above holds the serve until it is over\n")
    old = "        void BeginPoint() {"
    assert s.count(old) == 1
    s = s.replace(old, "        void BeginPoint() { tauntHold = 0;")
    open(g, 'w').write(s)
    print('TennisGame.cs patched')
else:
    print('TennisGame.cs already has ApplyTauntHold')
s = open(d).read()
if 'HoldNextPoint((length' not in s:
    if 'game.HoldNextPoint(length' in s:
        s = s.replace("game.HoldNextPoint(length[(int)c] + .4f);      // the next serve waits for the taunt", "game.HoldNextPoint((length[(int)c] + .4f) * TennisGame.GameSpeed);      // the next serve waits for the taunt (the game's timers run at GameSpeed x real time)")
    else:
        old = "            EmotesPlayed++; LastEmotePlayed = c.ToString(); LastEmote = c.ToString();\n            return true;"
        new = "            EmotesPlayed++; LastEmotePlayed = c.ToString(); LastEmote = c.ToString();\n            if (game && Array.IndexOf(Taunts, c) >= 0) game.HoldNextPoint((length[(int)c] + .4f) * TennisGame.GameSpeed);      // the next serve waits for the taunt (the game's timers run at GameSpeed x real time)\n            return true;"
        assert s.count(old) == 1
        s = s.replace(old, new)
    open(d, 'w').write(s)
    print('HeroTennisDriver.cs patched')
else:
    print('HeroTennisDriver.cs already patched')
