# Female face + shader (chat 7) — working notes
- 2026-10-17: cross-session target (Adnan via coordinator): game must hold 60 fps at >=1920x1080 with both heroes on screen.
  For this chat: measure HeroFaceSkin/TennisCharacter female shader cost before/after at 1080p; no crunch on face textures;
  all proof/overlay renders >=1080p. Frame budget: work/frame-rate-60b/BUDGET.md (fps60-everywhere owns settings).
- Head mesh: existing lip edge loops in the game frame: upper vermilion border y~-69 (centre) -> corners (+-25, -78), seam -80/-82,
  lower border -91. Upper lip = one sliver band (no interior rows) -> ridge sits on the border loop.
- 2026-10-17 09:33: /private/tmp wiped by restarts twice; clone moved to ~/female-face-UnityClone (APFS clone). Delete when done.
