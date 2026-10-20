# Tennis gameplay audit — 2026-10-13

Measured through the real TennisGame code (PlayMode, ManualSimulation, NativeControlled = true so TimingAims = true).
Nothing in the project was changed. Re-run after any aim/serve change:

1. `cp -c -R Unity <scratch>/UnityAudit` (APFS clone), copy `AuditSweepTests.cs.txt` to `Assets/Tests/PlayMode/AuditSweepTests.cs`.
2. `GOLF_MUTE=1 AUDIT_OUT=<dir> Unity -batchmode -projectPath <scratch>/UnityAudit -runTests -testPlatform PlayMode -testFilter AuditSweepTests.RallySweep -testResults r.xml -logFile l.log -screen-width 640 -screen-height 360`
   (also `.ServeSweep`, `.ServeFilm`). Do NOT pass `-nographics`: the render loop crashes the editor.

Files: rally_sweep.csv (ball x, power, swing time -> lateness, grade, landing), serve_sweep.csv (swing offset from the apex -> pace, launch delay, landing), serve_film.csv (per-step racket/ball), serve_sheet.png (12 frames).
