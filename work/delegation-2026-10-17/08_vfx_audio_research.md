# Chat 8 — Research: game-wide VFX system + sound system (RESEARCH ONLY until Adnan says proceed)

Adnan (10-17): "need to work on a game wide vfx system, as well as sound system for hits in each sport and other sound effects. spin up a research chat that will research from top games how they did theirs and what we will do to create our own and then i will tell it when to proceed".

**Do not change the game.** Write only into `work/vfx-audio-research/`. When the research is done, stop and wait for Adnan to say proceed.

## Read first
`AGENTS.md`, `CLAUDE.md`, `work/delegation-2026-10-17/README.md`. Memory notes: `hit-feel-haptics`, `tennis-visual-target-video`, `feedback-mute-windowed-unity`, `party-chat-voice-recording`, `tennis-gameplay-direction`. What exists now: `work/gameplay-audio/`, `GolfHitFeel.h`, `TennisContactPresentation`, impact/footstep-dust FX, golf plume/weather shaders, `Resources/Effects`. Inventory the current VFX and audio: every effect, sound, mixer, trigger point, and the TV-vs-phone audio split.

## Research (cite sources: GDC talks, dev blogs, breakdowns, interviews, frame-by-frame footage by id + timestamp)
- **Games:** Wii Sports / Wii Sports Resort, Nintendo Switch Sports, Mario Tennis Aces, Mario Golf: Super Rush, Everybody's Golf, Golf Story, Top Spin 2K25, PGA Tour 2K, Tennis Clash / Golf Clash (mobile), Fall Guys, Rocket League, Fortnite, Overwatch (impact feel), Hades or Celeste (juice), plus any others that are stronger references.
- **VFX:** how they structure a game-wide system: an effect library/pooling, event-driven triggers, hit-strength tiers (weak/good/perfect), trails, impact flashes, hit-stop/freeze frames, camera shake/punch, screen-space effects, ball trails, turf/sand/water/dust per surface, celebration/score FX, UI FX, a consistent art style (shape language, colour, timing curves), and the mobile budget (overdraw, particle counts, GPU instancing, VFX Graph vs Shuriken on iOS/Metal).
- **Audio:** hit sounds per sport (racket string/frame, sweet spot vs mishit, golf club by type and lie, putt, ball bounce per surface, net, cup), layering (transient + body + tail), randomization (pitch/volume/round-robin), hit-strength mapping, crowd/ambience reacting to play, music stingers/ducking, footsteps/cloth, UI sounds, spatialization for TV vs phone speaker, haptics sync, mixer/bus/snapshot structure, middleware (Unity audio vs FMOD vs Wwise) and licensing/cost for iOS.
- **Feel:** how VFX, audio, haptics, hit-stop and camera stay synchronized at a single contact event (frame-accurate timing). How their teams kept it consistent across many effects (tools, presets, naming).

## Deliverables (in work/vfx-audio-research/)
1. `RESEARCH.md`: per game, what they do and why it works, with sources, plus cross-game patterns.
2. `CURRENT_STATE.md`: our inventory and its gaps.
3. `PROPOSAL.md`: what we build ourselves:
   - Architecture: an event bus from gameplay contact/score/UI events into VFX, audio, haptics and camera, with strength tiers and per-surface tables.
   - Authoring tools/presets so new effects and sounds are fast to add.
   - Art direction for VFX matching our soft-plastic party look.
   - Sound design direction and a sourcing plan (record/synthesize/license, with costs).
   - Unity tech choices with reasons (VFX Graph vs particles on iOS, Unity audio vs FMOD/Wwise).
   - Performance budget: it must hold **60 fps at ≥1920×1080** (see `work/frame-rate-60b/BUDGET.md` when it exists).
   - Phased implementation plan with binary gates and rough time per phase, plus how to split it into parallel chats.
4. A reference board: an HTML page with embedded timestamps/links (no downloaded copyrighted media) and our own mock-ups if useful.

Show Adnan the proposal and **stop**. Implement nothing until he says proceed.

## Rules
Research only: no edits outside `work/vfx-audio-research/`, no staging of game files, no commits. Cite videos by id + timestamp; don't download or redistribute copyrighted footage or audio. If you watch video in the Browser pane, play only the clips you listed and pause at the end (Adnan watches the pane live). Mute any Unity run (`GOLF_MUTE=1`).
