# Paste prompt for GPT-6 Astra (Codex): experience-first audit and plan only

Party Sports (Unity 6000.3.24f1, URP, iPhone, phone-as-controller tennis and golf party game).

**Principle: every effect, animation or pause must make the game more responsive, easier to read, or more rewarding. No effects for their own sake.** No camera shake or hit-stop by default; that's intentional. The Scuba racket drop is also intentional.

## Rules
- Write only `ArtDir/style/EXPERIENCE_PLAN.md`. You may add "## Suggested changes (Astra)" at the end of `EXPERIENCE_AUDIT.md` or `VFX_ANIMATION_STANDARD.md`, and leave the rest as it is.
- No project changes. No `git add`, commit, push, stash or checkout.
- Captures only in a scratch APFS clone (`~/UnityScratch_depths`, rsync Assets/Packages/ProjectSettings), in **foreground** batchmode. Light tests.
- Don't touch animations or the hero body, rig or face.

## Read
`ArtDir/style/EXPERIENCE_AUDIT.md` (the ranked top 10 with measurements), `VFX_ANIMATION_STANDARD.md`, `ART_BIBLE.md`, the sheets in `vfx-anim-audit/`, and the traces in `~/UnityScratch_depths/work/vfxaudit/`.

Then check the code behind each item: `TennisGame.cs`, `HeroTennisDriver.cs`, `TennisFx.cs`, `TennisAudioDirector.cs`, `GolfGame*.cs` (Flight/Result/HoleOut), `ShotEffects.cs`, `GolfWindSway.cs`, `WeatherView.cs`, `Haptics.cs`, and the input and swing detection code.

## Write `EXPERIENCE_PLAN.md`
(a) Confirm or correct each of the 10 items with file:line evidence and your own measurement, especially the input → visible-response latency, which should be measured on device if you can. Add anything that matters more.
(b) For each item: the smallest change that fixes the feel, the files it touches, a phone feel test, and a number to measure (for example point end → serve-ready ≤ 1.5 s, golf strike → next aim ≤ 8 s, visible golf contact ≤ 100 ms after impact).
(c) Order the work by player impact per effort, in phases, with before/after trace numbers and frame strips as proof.
(d) Short decision-type questions for Adnan.

Plain English, concise. End with a 5-line summary and the first change you'd make.
