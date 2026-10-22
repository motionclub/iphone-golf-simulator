# Golf + tennis gameplay audio — 2026-10-15

User request: responsive, fun contact/movement/crowd/announcer audio for both sports, with three audible themes to choose from. Music is deferred.

## Themes

| Theme | Contacts / movement | Crowd / announcer direction |
| --- | --- | --- |
| Clubhouse Pop | Warm hollow contact, felt/wood texture, light rubber soles, clean readable accents | Friendly small gallery; relaxed, smiling host, short encouraging calls |
| Stadium Snap | Dry athletic crack, firmer body, sharp shoe grip and slides | Larger stands, dynamic applause; confident concise sports broadcaster |
| Toybox Rally | Rounded rubber/plastic pops, elastic motion, comic misses without abrasive beeps | Playful friends cheering; energetic game-show host, brief cheeky reactions |

All three share event timing and fair feedback. A theme changes sound, not gameplay, animation or controls. Distinction must include timbre/envelope/space/crowd/voice, not just pitch.

## Execution

1. Author deterministic offline SFX packs and matched, music-free comparison reels. These are original procedural sound designs, not Scenario outputs.
2. Add theme banks, reserved contact voices, bounded movement/crowd overlap, nonrepeating takes, channel levels and a bounded contextual announcer queue.
3. Connect the existing golf/tennis events, plus tennis brake/slide/landing audio. Preserve animation sources and gameplay behavior.
4. Provide an audition surface and reproducible tests/evidence.
5. Scenario: installed 0.11.0; no credentials at task start. User asked asynchronously to enter them in Blender. Cloud-generated crowd/voice production and live quality review remain pending until available. Never label local system speech or synthetic crowds as provider-generated or final recorded performances.

## Acceptance

- All three packs cover core golf + tennis contacts, running, stops/slides, landings, crowd reactions and UI feedback. No music in previews.
- Contact sound submits synchronously on the existing contact event; no generation, file access, new source allocation or delayed scheduling per hit.
- Contact voices cannot be stolen by footsteps or crowds. Movement and crowd overlap are bounded.
- Announcer has priority, expiry, take rotation, interruption protection and new-play cancellation. Scores cannot be read after the next play begins.
- Source files and metrics identify onset, peak, duration and clipping. Technical PASS does not imply human listening or iPhone playback acceptance.
- Unity compile and focused meaningful tests pass. Evidence in `proof/`, including `GATE_RESULTS.md`.
- Keep maps, body/head/hair/garments/cameras/gameplay rules unchanged. No commits; stage only the task's files when complete.
