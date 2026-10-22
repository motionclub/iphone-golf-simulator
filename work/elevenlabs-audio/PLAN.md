# ElevenLabs audio plan — 2026-10-22

Nothing has been generated yet. No credits spent. Key is in `.env.local` (gitignored, ends cf57).

## Balance

Starter plan: 40,000 credits/month, 14,850 used, **25,150 left**, resets 2026-11-22.

## 1. Announcer — Jax Meridian (`iB0m5bo5Htdz0t9yE0xq`, found in your voice list)

- Replace the Kokoro announcer lines (they were removed 10-19; tennis announcer was silent before that).
- Line source: `TennisAnnouncer.cs` keys (score calls, ace/winner/rally/fault, welcome, match end) + golf calls in `work/audio-pass/tools/make_voices.py` (welcome, par/birdie/bogey, hole-out, etc.). ~90-110 lines, ~2,500 characters.
- Model `eleven_multilingual_v2`, 1 credit per character. Two takes of the reaction lines so the game can rotate them.
- Output: WAV/OGG into `Unity/Assets/Resources/Audio/Announcer/{Golf,Tennis}/`, same key names the code already loads.
- **Estimate: ~4,000 credits.**

## 2. Lobby music — no credits

`~/Downloads/Victory_Menu_2026-10-22T165145.mp3` (3:00, 4.3 MB, stereo 44.1 kHz).
- Convert to OGG Vorbis, find a clean loop point (the mp3 has encoder padding, so do not loop the raw file), crossfade the seam if needed.
- Hook to the menu/lobby/plaza via a looping `AudioSource`, routed to a music bus.
- Plays on loop in the plaza hub, stops (fades out) when a game starts.

## 3. Map intro music — credits depend on music rate (not published)

One ~20 s sting/intro per place, each in its own vibe:

| Course / venue | Direction |
|---|---|
| Tennis: Resort | sunny tropical, steel drums, marimba, bright |
| Tennis: Skyscraper | rooftop city, punchy synth-pop, tight drums |
| Tennis: Volcano | tribal drums, low brass, ominous but fun |
| Golf: Cliffside | breezy seaside, light strings, gentle guitar |
| Golf: Wild Isles | jungle/island, hand percussion, flutes, playful |
| Golf: Magma | molten, heavy low synth, rising tension |

ElevenLabs does not publish a per-second music price; the app shows the cost on hover. Plan: after you approve, I generate **one 10 s test**, read the balance change, and then give you the exact total for the 7 intros before generating the rest. Also need to confirm the Music commercial terms cover the Starter plan (elevenlabs.io/music-terms) before shipping.

## 4. Sound effects — ~67 unique sounds

Priced at the documented 40 credits per second when duration is set (older docs said 20; I will measure with the first one).

| Group | Sounds | Gens | Seconds | Credits |
|---|---|---|---|---|
| Ball contact (3 variants each) | driver (big crack + long ring), iron, wedge, putter (soft low tock, deliberately unlike the driver), perfect sting, cup drop, tennis soft/sweet/perfect/smash/rival hit, serve hit, bounce (hard + clay), net cord, net hit | ~54 | ~54 | ~2,200 |
| Movement and foley | club swoosh light/heavy, racket swoosh, whiff, serve toss, shoe slide/brake, landing, run loops on grass / hard court / stone / sand / ice / lava rock, ball roll on green | ~28 | ~65 | ~2,600 |
| Hazards and world | splash, lava hiss, ice skid, thud, leaves, knock wood/stone, bunker sand, flag pole | ~12 | ~20 | ~800 |
| Crowd (new) | murmur loops small/large, cheer small/big, polite golf clap, big applause, gasp, groan, "ooh" near-miss, "aww", roar for winner/hole-out, tennis rally build-up, chant | ~20 | ~80 | ~3,200 |
| UI, stings and crowd | tick, ready, confirm, cancel, menu nav, fanfare, whistle, point win/lose, countdown | ~10 | ~25 | ~1,000 |
| Map ambience loops (7 places, 10 s) | birds/surf, city wind, lava rumble, etc. | 7 | 70 | ~2,800 |
| **SFX total** | | ~125 | | **~11,800** |

## Budget

| Item | Credits |
|---|---|
| Announcer | ~4,000 |
| SFX | ~11,800 |
| 15 % retry buffer | ~2,400 |
| **Subtotal before music** | **~18,200 of 25,150** |
| Left for music | ~6,900 |

If music costs more than that, options: shorten intros to 15 s, skip the ambience loops (-2,800), or wait for the Nov 22 reset. Cutting variants from 3 to 2 saves ~700.

## Build order (after approval)

1. Python script in `work/elevenlabs-audio/` (venv with `elevenlabs` SDK, key read from env only), a manifest of every prompt/duration, and a log of credits per call. No generation without checking the balance first.
2. Test one SFX + one 10 s music clip to measure real rates. Report back before the bulk run.
3. Generate announcer, then SFX, then music. Keep every raw file under `work/elevenlabs-audio/raw/` (not in Unity) with its prompt in a manifest.
4. Loudness-normalise, trim, loop-fix; import into `Unity/Assets/Resources/Audio/...`.
5. Wire into the existing `GolfSounds`, `TennisSounds`, `TennisAnnouncer`, and `TennisMusic` code. Previous audio pass (`work/audio-pass/removed-20261019/`, with restore steps) is a reference for the buses and ducking.

## Decisions (2026-10-22)

- Golf cart dropped. Driver and putter get clearly different sounds (checked by listening and by comparing spectra).
- Crowd sounds added (see SFX table).
- Lobby music = plaza hub only, until a game starts.
- Intros are per course/venue, each with its own identity: Magma sounds nothing like Cliffside or Wild Isles (tropical).

## Revision 2 (2026-10-22): announcer, crowd, grunts

### Announcer (Jax Meridian), ~7,500 credits (1 per character, ~190 lines)
- Welcome per map: 6 maps x 2 variants (~1,300)
- Praise for specific good actions: golf (long drive, fairway, close to pin, long putt, chip-in, bunker save, par save, birdie, eagle, ace, ring/bounty) and tennis (ace, winner, smash, on the line, long rally, comeback, break/set/match) x 3 variants (~2,750)
- Roasts for bad actions: golf (water, lava, OB, whiff, shank, 3-putt, missed tap-in, tree) and tennis (double fault, net, out, whiff, lost long rally) x 3 variants (~2,300)
- Score and rules calls, match start/end (~1,100)

Anti-overuse governor (code, no credits): 8 s global cooldown; routine shots stay silent (speak ~1 in 3); big moments always speak; roasts capped (max 1 per ~2 holes / ~4 games, never twice in a row on one player); no repeat of a line within 10 calls; silent during tennis rallies, speaks only at point end; lines expire if the next play starts; crowd ducks under him.

### Crowd, ~4,800 credits (~30 clips)
Golf (Wii Golf style, driven by ball-to-cup distance and state):
- hush at address; polite clap after shots; murmur loop
- rising "swell" layers that scale with how close the ball is to the hole while it rolls; inhale at the last 30 cm; then eruption (in), groan (lip-out), "ooh" near-miss, "aww" (short), roar for chip-in / ace
Tennis:
- hush before serve; murmur; rally build-up that grows with rally length; "ooh" on close or line calls; short vs long applause scaled to point importance (set/match point loudest); sighs on faults; standing ovation at match end

### Tennis grunts, ~1,000 credits
Male and female, 4 shot types (ground stroke, hard forehand, serve, smash) x 3 variants, plus stretch/reach effort and frustrated exhale.

### Revised budget (credits, 25,150 left)
| Item | Credits |
|---|---|
| Announcer | ~7,500 |
| Crowd | ~4,800 |
| Grunts | ~1,000 |
| Sound effects (rest) | ~8,600 |
| 15 % retry buffer | ~3,300 |
| **Total before music** | **~25,200** |

That uses everything and leaves nothing for music. Proposed phasing:
- Phase 1 now: announcer, crowd, grunts, music tests + 6 intros (~15,300 + music).
- Phase 2 after the Nov 22 reset (or a plan upgrade): the rest of the SFX and ambience loops.

### Music rate (from Adnan): 900 credits per 2 minutes = 7.5 credits/second
- 6 intros x 20 s = 120 s = 900 credits; two takes each to pick the best = ~1,800.
- Music is cheap, so intros can be 30 s (1,350 for one take, ~2,700 for two) if you want fuller ones.
- New total: ~25,200 + ~1,800 = ~27,000 vs 25,150 left. Phase 1 (announcer, crowd, grunts, intros, buffer) is ~17,100, leaving ~8,000 for most of the SFX now; the remainder (mainly ambience loops) after the Nov 22 reset.
