# Proposal: one game-wide Feel system (VFX + sound + phone haptics + UI) for Party Sports

For Adnan, 2026-10-17. **This is a proposal only. Nothing gets built until you say "proceed".**
Inputs: [CURRENT_STATE.md](CURRENT_STATE.md) (what we have), [RESEARCH.md](RESEARCH.md) (what top games do), and [REFERENCE_BOARD.html](REFERENCE_BOARD.html) (clips plus our mock-ups).

---

## 0. The pitch in six lines

1. **One pipe.** Gameplay emits one `FeelEvent` per moment (contact, bounce, cup, point…). A single `FeelDirector` plays the visual, the TV sound, the phone haptic or knock, the UI pop and the crowd from **one preset, on one timestamp**. This replaces today's five hand-copied fan-outs.
2. **One tier ladder for both sports:** Miss · Weak · Solid · Great · Perfect · Special. Each step up **adds a channel**, so you can see and hear the grade without reading text. The Special tier stays rare.
3. **One surface table:** every court, lie and hazard has its own bounce/landing look, sound, mark and haptic.
4. **Real, layered hit sounds** replace the runtime synthesisers. Each hit is a transient, a body, a soft-plastic "toy" layer and a tier sweetener, with round-robin takes. Shot quality changes the *timbre*, not just the volume.
5. **The phone is the "now" channel and the TV is the "world" channel.** The phone plays only *your own* contact (haptic plus an optional local knock), immediately. The TV carries everything else, in sync with its own picture.
6. **Built for 60 fps at ≥1080p.** Shuriken only, solid toon mesh particles (nearly free on iPhone GPUs), pooled, zero allocations per event, and measured per effect.

**Respected as you set them:** no camera shake and no hit-stop (`EXPERIENCE_AUDIT.md:166-167`), no full-body celebration while the ball is live, contact sound on the true contact frame, palette rules, and the fixed gameplay camera. Decision #1 in §11 asks whether you want to keep those as they are.

---

## 1. Architecture

```
 Gameplay (TennisGame / GolfGame / Hub / UI)
        │  Feel.Emit(in FeelEvent)        ← one line per moment, no per-channel calls
        ▼
 ┌──────────────── FeelDirector (one per scene, DefaultExecutionOrder 1100) ────────────────┐
 │ ring buffer (no alloc) → resolve FeelCue[id] → pick tier row → resolve SurfaceTable      │
 │ → cooldown / max-per-frame / rarity gates → dispatch to channels on ONE timestamp        │
 └───────┬───────────┬────────────┬───────────────┬─────────────┬─────────────┬────────────┘
         ▼           ▼            ▼               ▼             ▼             ▼
   VfxChannel   TvSfxChannel  PhoneChannel     UiChannel   CrowdVoChannel  CameraChannel
   (pooled      (AudioMixer,  (Core Haptics +  (one pop/   (crowd intensity (OFF by default:
   Shuriken     SfxBank, ARC  System-Sound      tween       + announcer    no shake, no
   emitters,    round-robin,  knock; clock =    vocabulary) queue + music  hit-stop; kept as
   decals)      voice caps)   Now or TvDelayed)             stingers)      an empty slot)
```

### 1.1 The event (gameplay writes only this)
```csharp
public enum FeelId : ushort { TennisContact, TennisServeContact, TennisBounce, TennisNet, TennisWhiff,
    TennisFault, TennisPoint, TennisGame, TennisMatch, RallyMilestone, Footstep, Brake, Dive, ...,
    GolfAddress, GolfTension, GolfTop, GolfStrike, GolfLand, GolfKnock, GolfHazard, GolfLipOut, GolfCup,
    GolfHoleOut, UiNavigate, UiConfirm, UiBack, Unlock, Reward, ... }
public enum FeelTier : byte { Miss, Weak, Solid, Great, Perfect, Special }
public struct FeelEvent {
    public FeelId id; public FeelTier tier; public float strength;   // 0..1 within the tier (power/speed)
    public SurfaceId surface; public Vector3 pos, dir;                // where + which way
    public byte actor; public FeelFlags flags;                        // LocalPlayer/Remote/Cpu, Replay, Online, Predicted
    public double simTime; public uint seq;                           // one timestamp + id for online/replay de-dupe
    public ushort variant;                                            // club, stroke kind, score-vs-par…
}
```
- **Gameplay never calls `fx.`, `sounds.`, `Haptics.` or `juice.` directly again.** The existing static events (`ContactMade`, `Landed`, `Netted`, `ShotStruck`, `ScoreChanged`…) stay for the phone bridge, recorder and tutorial.
- **Online, Versus and replay** emit the same event with a `seq` and flags. Each channel decides, for example "no haptic on replay" or "the remote hitter gets the haptic". This fixes today's drift: online bounce with no VFX, opponent contact with no haptic, golf replay with no landing or cup.

### 1.2 One timestamp, two clocks
| Channel | When it fires | Why |
|---|---|---|
| VFX, TV sound, UI, crowd | **Together, on the displayed contact frame** (the existing `TennisContactPresentation` LateUpdate flush, order 1100, generalised to every event) | AirPlay delays the TV picture and TV sound together (about 100–200 ms), so firing them in the same rendered frame keeps them in sync on the TV. Today audio fires on the 120 Hz sim step and VFX on the render frame. |
| Phone haptic and knock for **your own arm** (strike, swing, whiff) | **Now**, at the gameplay contact (unchanged from `PLAN_HitFeel_Haptics.md`) | Apple: sound and haptic are "same tempo". The hand must feel the hit when the arm does (Switch Sports "one step behind"). |
| Phone haptic for **things you see on the TV** (bounce, landing, cup, point) | `+ TvLatency` | So the phone buzz lands with the TV picture. Golf gets this too (today it has no TV clock). |

**Proposed gameplay-side split (for the owner of `TennisLagLearner`):** today `Lag` mixes TV delay with the player's timing habit. Split it into `TvLatency` (measured once per TV and stored, as now via the AirPlay port prior) and `PlayerBias`. Only `TvLatency` is used for feel. A short **calibration screen** (tap when the TV flashes, as rhythm games do) measures it. If you prefer not to touch gameplay, Feel can keep using `Lag`.

### 1.3 Presets (designers edit these, not code)
- **`FeelCue` (ScriptableObject, one per `FeelId`)** has one row per tier. Each row holds:
  - VFX recipe and scale
  - SFX bank, gain and pitch bias
  - phone pattern and clock (Now / TvDelayed)
  - UI pop
  - crowd reaction and announcer line
  - camera (disabled)
  - cooldown, max-per-frame, and rarity gate (e.g. at most one Special per 20 s)
  - `strength` curves (size, gain, intensity)
- **`SurfaceTable`** maps each `SurfaceId` to:
  - landing/bounce VFX recipe
  - two palette colours
  - bounce/land/roll sound bank
  - mark/decal and its lifetime
  - phone tick sharpness
- **`TierStyle`** is one row per tier: palette colour, shape family, timing curve, and which channels are allowed. The ladder in §3 is this asset.
- **Theme banks:** one `SfxBank` set per audio theme, so the 10-15 three-theme idea (Clubhouse Pop / Stadium Snap / Toybox Rally) becomes a bank swap later.

### 1.4 Guarantees the director enforces
- **No allocations per event.** Ring buffer, prebuilt emitters (as `TennisFx` and `ShotEffects` already do), pooled decals, preloaded clips. No runtime `AudioClip.Create`. An EditMode GC test checks this.
- **Every important event gets ≥3 channels** (art bible §12). An EditMode coverage test walks every `FeelId` × tier and fails if fewer than 3 channels are set.
- **Contact sound is never stolen.** Reserved priority-0 voices and per-category voice caps.
- **Rarity and cooldowns** keep the top tier special (Mario Tennis Fever lesson).
- **Quality scaling:** one global `FeelQuality` (Full / Reduced) wraps `EnvironmentFx.Reduced` and the reduce-motion setting, and now covers golf, weather and lava too.

---

## 2. Event catalogue (v1 scope)

C = contact-class event (tier ladder), M = moment (importance ladder), A = ambient/continuous. "Phone" = haptic (+ knock where marked).

| Event | Class | TV VFX | TV sound | Phone | UI / crowd |
|---|---|---|---|---|---|
| Tennis contact (rally, serve, smash, volley, opponent) | C | tier ladder at the strings; ball trail coloured by tier for the whole flight | layered racket hit by tier × power × stroke | own contact: Now. Opponent contact: a light TvDelayed tick (new) | one-word grade at the ball (EXPERIENCE_AUDIT #4); crowd micro-reaction at Great+ |
| Tennis swing whiff | C(Miss) | white swish ring, dust | swish + comic "whoop" | existing Whiff | "WHIFF!" |
| Bounce | A | per-court puff + mark (clay scuff persists for the point) | per-court bounce sound | ball landing in on your side: TvDelayed (exists); **your own ball landing in: TvDelayed (new)** | — |
| Net cord / net | M1 | net wobble + tick sparks | net "zzip"/tick | TvDelayed tick (new) | "NET!" + crowd "ooh" |
| Out / fault / double fault | M1 | line-judge chalk puff at the mark | call + crowd groan | TvDelayed double-tap (new) | "OUT" |
| Rally milestone 4/8/12 | M1 | counter pop at the HUD | crowd swells (intensity parameter) | — | rally counter (EXPERIENCE_AUDIT #9) |
| Point / game / set / match | M2–M4 | confetti (existing `Celebrate`, now wired) sized by importance | crowd + stinger on the music beat + announcer | existing PointWon/GameWon/MatchWon (TvDelayed) | titles; match-point **heartbeat** haptic before the serve (Aces) |
| Supercharge / Ultimate | C(Special) | player-colour shape signature, stream | special layer + rise | surge (exists) | title; rarity-gated |
| Footstep / brake / slide / dive land | A | per-court puff (dive gets a bigger skid mark) | shoe squeak/scuff/land per surface | — | — |
| Golf address / tension / top / whoosh | A | — | existing tension, whoosh | existing Tension/Top | — |
| Golf strike | C | tier ladder at the ball + lie-specific debris (divot chunk, sand blast, rough swish, ice chips, tee shard) | club family × lie × grade layered strike | Now (exists: Strike/Putt) | grade word (StrikeHud) |
| Golf flight | A | tracer coloured by grade (fix comment vs data mismatch), reward trails | flight whoosh by speed (new) | — | — |
| Golf land / bounce / roll | A | **per-lie** puff + mark (table exists for colour, extend to recipe) | **per-lie** land and roll sounds (today one thud) | TvDelayed tick (new for golf) | — |
| Obstacle knock / movers | M1 | existing Knock/Burst | existing, moved into SurfaceTable (wood/stone/leaves/balloon…) | TvDelayed tick (stop reusing the tennis Bounce cue) | callout |
| Hazard (water / lava / OOB) | M1 | splash / lava / **new OOB poof** | splash / hiss / whistle + comic beat ≤1.5 s (EXPERIENCE_AUDIT #10) | TvDelayed Failure | "+1" |
| Lip-out | M2 | **new** rim-spin sparks | rattle + crowd "NOOO" | TvDelayed (new) | — |
| Cup | M2–M4 by rarity (tap-in < long putt < chip-in < hole-in-one) | cup ring + flag wobble + confetti scaled by rarity | rattle + drop "plunk" + crowd + stinger | Roar (TvDelayed, new clock) | score after the drop |
| UI navigate / confirm / back / unlock / reward | A/M | UI pop vocabulary | UI bank (TV) | UIKit tick through the plugin (respects the strength setting) | — |

---

## 3. Strength tiers (the ladder)

**Mapping:** tennis `Timing` Missed→Miss, Ok/Good→Solid, Great/Excellent→Great, Perfect→Perfect, supercharged/smash/ultimate→Special. Golf Thin→Weak, Good→Solid, Great→Great, Perfect→Perfect, plus signature shot → Special. Off-centre/mishit → Weak in both sports. `strength` (power or speed) scales size, gain and intensity *within* a tier.

| Tier | Shape (meaning is carried by shape, because player colours are customisable) | Colour | TV sound | Phone | Lasts | Adds |
|---|---|---|---|---|---|---|
| **Miss** | white swish ring | white | swish + comic whoop | Whiff | 0.25 s | — |
| **Weak** | small grey-blue puff, 2–3 crumbs, slight wobble | muted blue `#A3C2DB`-ish | dull "pok" / frame "clack" + buzz (mishit layer) | crack + **sting** (exists) | 0.2 s | mishit sound |
| **Solid** | round puff + thin ring | cream | clean pop + body | crack + body | 0.25 s | ring |
| **Great** | ring + 4–6 plastic chips flying out + white flash frame | cream-white | crisp "thwack" + bright click sweetener | + EXCELLENT ring (exists) | 0.3 s | chips, flash, sweetener, crowd micro-"oh" |
| **Perfect** | **rounded 5-point gold star** + double ring + 8–12 sparkle beads; gold ball trail for the shot | gold `#FFD152` (glow ≤1.5 HDR in daylight) | sweet-spot crack + **tuned chime in the music key** (calypso in F) | + PERFECT ring + sparkle (exists) | 0.35 s | star, trail, chime, crowd "ahh" |
| **Special** | player-colour signature shape (comet / bolt / bubble per ability) + stream; title | player colour + gold rim | special layer + whoosh rise; music duck 0.5 s | + surge/shock (exists) | ≤0.6 s | signature + duck + title. **Rarity-gated.** |

**Weight without camera shake or hit-stop** (your rule stays; ideas from Sakurai, Celeste and Vlambeer that don't touch the camera or time):
- **Ball squash** is already scaled by power. Extend it to tier: Perfect gets a bigger, cleaner squash.
- **A one-frame impact shape** (white or gold star) drawn only on the contact frame, like an anime impact frame. This is FX only: the simulation never pauses.
- **The trail carries the grade while the ball flies**, which is where the eye already is.
- **Sound weight:** a lower body and stronger transient as power rises, and the crowd and music duck −3 dB for 300 ms on Great and above (Rocket League "make the others quieter").
- **The opponent reacts** (Wii Sports Club stomp). This is for the animation chat; the hook is the event.
- The hero torso kick is currently disabled for match heroes. It belongs to the animation chats, not this system.

---

## 4. Per-surface table (v1)

Tennis venues today are `Resort`, `Skyscraper` and `Volcano` (`Tennis/TennisVenue.cs:5`). Golf lies are from `Course/Hole.cs:23`, and material surfaces from `GolfCourseLook.cs:17`.

| SurfaceId | Bounce / land VFX | Mark | Sound (bounce / land / roll) | Phone tick |
|---|---|---|---|---|
| Court · Resort (blue hard) | small cream puff, ripple | faint skid quad, 2 s | crisp "tock" | sharp .6 |
| Court · Skyscraper (rooftop) | cool grey puff + tiny sparkle | skid quad | tighter, slight slap echo (rooftop space) | sharp .65 |
| Court · Volcano | dark ash puff + 3 ember beads | warm scorch skid | dull "tunk" + faint sizzle | .5 |
| (future) Clay | terracotta dust plume | **scuff that stays for the point** (TopSpin) | soft "pfft" | .35 |
| Golf · Tee / Fairway | grass clippings + green puff | **divot chunk** (mesh particle) | turf thud, grass brush on roll | .4 |
| Golf · Rough | taller blade spray, ball sits down | — | muffled thud + swish | .3 |
| Golf · Fringe / Green | tiny puff, roll | ball mark dent (pooled decal) | soft "pat", smooth roll | .45 |
| Golf · Bunker | sand blast (mesh grains) | crater ring | sand "kshh" | .2 |
| Golf · Water / Shallow / Surf | splash crown + rings (exists) + **one skip before sinking** (comic) | rings | plunk + splash + duck quack (comic beat) | Failure |
| Golf · Ice | ice chips + skid spray (exists) | scratch line | skid/scrape (exists) | sharp .9 |
| Golf · Snow | powder puff | dimple | soft crunch | .25 |
| Golf · Lava | lava burst (exists) | — | hiss (exists) + "sizzle-pop" | Failure |
| Golf · Ash | ash puff + ember | — | dull crunch | .3 |
| Golf · OOB | **new** poof + whistle | — | whistle + groan | Failure |
| Obstacles: wood / stone / leaves / balloon / cart / gull | existing Knock/Burst recipes | — | existing, as SurfaceTable rows | .5–.7 |

---

## 5. VFX art direction (soft-plastic party)

**Shape language.** Round, chunky, toy-like, the same plastic as the heroes.
- Default particle: a **solid toon-lit mesh** (bead, chip, rounded star, disc, ring, blobby puff), lit with the same 2–3 step ramp plus rim as `TennisCharacter`/`TennisCloth`, so FX look like they belong in the world.
- Puffs are **low-poly blob spheres that scale up and shrink away**, not grey alpha smoke. This also fixes the old "grey smoke dust" note.
- Alpha-blended sprites only for small glows and the impact flash.

**Colour.**
- Every colour comes from the art-bible palette asset.
- Tier colours: blue-grey, cream, gold.
- Player colour appears only on Special and the trail rim.
- **Hazard orange `#FF5A1F` and ball yellow `#FFF36B` stay reserved.**
- Daylight glow ≤1.5 HDR; dusk and volcano up to 3 (art bible §9).

**Timing.** Three shared curves: **Pop** (EaseOutBack, overshoot 1.15), **Puff** (fast out, slow shrink) and **Drift** (confetti). The pattern is anticipation, then impact at frame 0 (biggest and brightest), then a short dissipation. Hits last ≤0.35 s; moments ≤1.2 s, except match-end confetti.

**Readability** (Riot rules):
- one primary shape per effect;
- size scales with importance;
- mid-range values;
- never out-contrast the hero or the ball (art bible §10).

**Persistence.** Marks stay a little while: clay scuffs for the point, golf divots and ball marks for the hole, all pooled.

**Toolbox:**
- one master **toon-FX shader** (hand-written HLSL, GPU-instanced mesh particles, Custom Data for tint and erosion, stepped dissolve with a coloured rim);
- one **FX atlas** (masks plus 8–16-frame stepped flipbooks, no blending);
- a **mesh kit** (shockwave ring, chip, star, bead, blob, divot chunk, sand grain, swing arc).

Mock-ups of the ladder are on the reference board.

---

## 6. Sound design direction and sourcing

**Identity: "toy sports".** Real sports transients give credibility, and a soft-plastic layer gives the party feel. The closest sourced cues are Fall Guys (balloon and toy samples) and Splatoon (Foley from beads and pellets).

**Hit recipe** (from Loughborough: the racket "crack plus ring"; golf feel tracks loudness and sharpness):

| Layer | Tennis racket | Golf club (Driver/Hybrid · Iron · Wedge · Putter) | Varies with |
|---|---|---|---|
| Transient | string "pok" / crack, 2–4 kHz | titanium "tink" · compressed "click" · crisp "tsk" · milled "tock" | tier (sweet spot = sharper), power |
| Body | felt-ball thump + frame | shaft/clubhead weight | power → lower and heavier |
| Toy layer (our signature) | hollow plastic "bonk" (tupperware / bottle tap) | plastic "pip" | theme |
| Tier sweetener | Great click; **Perfect chime tuned to the music key**; Special rise | same | tier |
| Mishit | frame "clack" + string buzz | thin "clank" + sting / fat "thud" + turf | Weak tier |
| Lie layer | — | tee shard, turf divot, rough swish, sand blast, ice scrape | surface |
| Tail | short venue reverb send | same | venue (Switch Sports tuned reverb per venue) |

**Variation.**
- 4–6 round-robin takes per layer (Audio Random Container, avoid-repeat 2).
- Pitch ±3% and volume ±1.5 dB. This range is industry habit, not sourced; tune by ear.
- **Fix the pitch-cancel bug.** Variation becomes per-voice, not per-source.

**Mix.**
- **AudioMixer buses:** `Hits` (protected, never ducked), `Ball&Surface`, `Feet&Cloth`, `Crowd`, `Announcer`, `Music`, `Ambience`, `UI`.
- **Snapshots:** Rally, PointEnd, Menu, Replay.
- **Ducking:**
  - Great or better ducks Crowd and Music −3 dB for 300 ms;
  - point-won ducks Music for the stinger;
  - the announcer ducks Music −6 dB.
- **Voice caps:** Hits 4 reserved, Ball 3 with an 80 ms cooldown, Feet 4, Crowd 2 beds + 2 one-shots, Announcer 1, UI 2.
- **Loudness targets per bus** in LUFS (`Hits` loudest), checked by the offline pipeline. Mix for **TV speakers** (Rocket League remixed for its real listening device). A "Dynamic range: TV / Night" option is a later nice-to-have.

**Phone side.** Your own contact only (Wii and Galaxy rule):
- haptic (existing, extended);
- an optional System-Sound knock with **one take per tier** (so it isn't the Wii's one sample). It is never a copy of the TV mix.

System Sounds obey the silent switch and have no volume control, so haptics stay the guaranteed phone channel. Knock default ON/OFF is decision #3, after a device test.

**Crowd and announcer.**
- The crowd has an **intensity parameter** driven by rally length, score tension and comebacks (fixes the AO Tennis 2 failure; Wii "wow" on comebacks).
- One-shots: ooh, ahh, applause, groan, laugh.
- The announcer queue already exists (`TennisAnnouncer`, 43 line keys) but has **no recordings**. PGA 2K shows a second-person, in-house voice works.

**Music.** Diegetic venue music ducked under hits (Switch Sports), stingers on the beat via `PlayScheduled`. Golf and hub music are new (decision #6).

**Sourcing plan and costs:**

| Source | Use | Cost | Licence notes |
|---|---|---|---|
| Sonniss GDC bundles (2015–2026) | base transients, crowd, ambience, UI | free | royalty-free, no attribution, **no AI training** |
| Freesound, CC0 / CC-BY only | gaps | free | keep a credits manifest; no NC |
| **Home Foley day** (Zoom F3 32-bit float + small condenser + piezo contact mic) | racket on ball, bounces on 4 floors, net brush, clubs on a mat, putter, cup drops, **plastic toys** for the toy layer | **about $550–700** one-off + 1–2 days | ours outright |
| Targeted packs (e.g. BOOM Casual UI) | UI polish | about $130 per pack | perpetual royalty-free; read the EULA |
| AI SFX (ElevenLabs paid / Stable Audio) | ideation and ambience fills only | subscription; Stable Audio free under $1M revenue (verify) | provenance log per file; never feed Sonniss files into them |
| Announcer VO | 43+ lines × 3 takes | in-house voice = free; hired VO is a budget call | second-person "talks to you" style |
| Existing synth (`TennisSynth`, `GolfSounds`) | **baked offline** into WAVs for chimes and stings tuned to the music key | free | no more runtime `AudioClip.Create` |

**Offline pipeline** (a Python script under `work/`):
- trim and onset-align, so every transient starts at sample 0 (frame-accurate);
- normalise to the bus LUFS target;
- mono 48 kHz;
- name `sfx_<sport>_<event>_<layer>_<nn>.wav`;
- import presets via `AssetPostprocessor`: ADPCM + Decompress On Load for hits, Vorbis Compressed-In-Memory for loops, Vorbis Streaming for music.

---

## 7. Unity tech choices (with reasons)

| Choice | Pick | Why (source in RESEARCH Part C) |
|---|---|---|
| Particles | **Shuriken** (built-in Particle System) | VFX Graph is still *preview* on URP and mobile in 17.3, and Unity said "not officially supported on mobile" on 2025-12-01. Our effects are small bursts where Shuriken is cheap. The repo already pools Shuriken well. |
| Particle look | **Opaque toon mesh particles, GPU-instanced**; alpha-blend only small | Apple's GPU removes hidden opaque pixels for free and translucency costs overdraw. Matches the plastic look. Shader Graph particle instancing only lands in 6.6, so we hand-write one HLSL shader now. |
| Soft particles | **No** | Don't make VFX depend on the depth texture. Ground contact comes from meshes and lifted decals. |
| Decals | pooled flat quads (exists for bounce marks); URP Screen-Space decals only if measured cheaper | TBDR-friendly; already in use. |
| Audio engine | **Unity built-in**: AudioMixer + snapshots + **Audio Random Container** + our `SfxBank` | One audio engine next to voice chat and Core Haptics. Our needs are a few hundred one-shots plus ducking. FMOD Indie and Wwise Indie are likely free but add a second engine on iOS. Revisit if a dedicated sound designer joins. |
| Haptics | **Keep `GolfHitFeel.h` / `GolfHaptics.mm`** | Already the best part of the stack. Add cues instead of adopting Nice Vibrations or Apple's Unity plug-in. |
| Phone-local sound | **System Sound Services** (existing knock path) | The only documented path that plays on the phone speaker while AirPlay is active. |
| Feel sequencing | **Our own `FeelDirector`** | Feel ($50) is a good model but its haptics would duplicate ours, and data-only cue ids are easy to replay online. Optional: buy Feel as a prototyping reference only. |
| Camera | **Nothing now.** If you ever reopen it: a ~100-line rotation-only trauma shaker with a TV comfort cap, no Cinemachine | Respects your no-shake and no-hit-stop decision. |
| Tweens / UI pop | one tiny in-house tween set (Pop / Puff / Drift curves) | No library is installed and three curves cover it. |

**Risks to test early:**
- **AirPlay connect or disconnect mid-match may reset Unity audio.** That is Classic audio-foundation behaviour; the fix is Unity 6.7 EAF.
- **With party voice on, AirPlay works only as mirroring.** That is fine, because we mirror.
- First-use PSO hitches: **prewarm all FX and golf shaders** at the loading cover, as `TennisWarmup` does for tennis today.

---

## 8. Performance budget (60 fps at ≥1920×1080)

`work/frame-rate-60b/BUDGET.md` (owned by chat 1) **does not exist yet**. These are *proposed* Feel shares, to reconcile with it before Phase 4:

| Item | Proposed cap (worst realistic moment, on the minimum device, 1080p) |
|---|---|
| Feel CPU (director + Shuriken simulation + audio dispatch) | ≤ 0.6 ms per frame at peak; ≤ 0.2 ms typical |
| Feel GPU (all FX + decals + UI pops) | ≤ 1.0 ms at peak |
| Live particles | typical ≤ 300; peak ≤ 600 (match-end confetti) |
| Alpha-blended screen coverage | ≤ 15% of the frame at peak (opaque mesh particles don't count against overdraw) |
| FX draw calls / SetPass | ≤ 12 / ≤ 4 (one atlas, one master shader, instancing) |
| GC allocation per event | **0 bytes** |
| Audio memory | ≤ 30 MB (ADPCM hits, compressed loops, ≤2 music streams) |
| Real voices | stay at 32, with reserved contact voices |

How it's checked:
- the golden-capture harness from `EnvironmentFxProofTests`, extended to every event × tier × surface;
- a device run at 1920×1080 over AirPlay with Xcode GPU counters;
- a **stress scene** (4-player Versus smash rally + confetti + rain) that must hold 60 fps.

All Unity runs are muted (GOLF_MUTE=1 + Editor mute).

---

## 9. Authoring tools (so adding an effect or sound takes minutes)

1. **Feel Lab** (editor window plus a fixed-camera scene):
   - fire any `FeelId` × tier × surface × venue from buttons;
   - tweak the `FeelCue` live in play mode, with a "copy back" button;
   - **record a contact sheet + a WAV of the TV mix + the phone pattern (AHAP-style JSON)** for review.
   - It replaces ad-hoc proof scripts.
2. **Audition grid:** play the whole tier ladder for one event back to back (A/B), and for all three themes.
3. **Coverage test** (EditMode, CI): every `FeelId` × tier has ≥3 channels, every `SurfaceId` has a row, every clip exists, and no runtime `AudioClip.Create` or `Instantiate` inside channels.
4. **Palette lint:** every FX colour must resolve to the palette asset; hazard orange is allowed only on hazard rows.
5. **Offline audio script:** trim, onset-align, LUFS, naming and import presets (§6).
6. **Naming:** `fx_<sport>_<event>_<variant>`, `sfx_<sport>_<event>_<layer>_<nn>`, `hap_<event>`, `cue_<FeelId>`.
7. **A style sheet page** (`VFX_STYLE.md`) with the ladder, shapes, curves and do/don't frames, so every chat builds the same look.

---

## 10. Phased plan with binary gates

Rough times assume one focused chat per phase. Every phase writes `GATE_RESULTS.md` + proof into `work/feel-system/<phase>/`, stages only its own files and never commits.

| Phase | What | Binary gates (all must PASS) | Time |
|---|---|---|---|
| **P0 Decisions** | Your answers to §11; sync the budget with chat 1 | decisions recorded; budget numbers agreed | 0.5 day |
| **P1 Spine (no look or sound change)** | `FeelEvent`/`FeelDirector`/`FeelCue`/`SurfaceTable`; channel adapters that *wrap today's* `TennisFx`, `ShotEffects`, `TennisSounds`, `GolfSounds`, `Haptics` and `TennisJuice`; migrate every call site (tennis rally, serve, opponent, Versus, online; golf strike, land, hazard, cup, replay, network) | **PARITY:** a recorded trace of channel calls before and after is identical except the listed drift fixes. **DRIFT:** online bounce shows VFX, opponent contact has a tick, golf replay shows landing and cup. **SYNC:** VFX, TV sound and UI fire in the same rendered frame (trace). **GC:** 0 B per event. **NO DIRECT CALLS:** a grep finds no `fx.`/`sounds.`/`Haptics.` in gameplay outside the adapters. EditMode + PlayMode green | 3–4 days |
| **P2 Audio foundation** | AudioMixer, buses and snapshots, ducking, `SfxBank` + Audio Random Container, voice caps, offline bake of existing synth sounds into WAVs, import presets, pitch-bug fix | **NO RUNTIME SYNTH:** 0 `AudioClip.Create` at runtime. **NEVER CULLED:** contact plays in a 48-voice stress scene. **DUCK:** crowd and music dip measured −3 dB ±1 on Great+. **LUFS** per bus within ±1 LU of target. Sounds unchanged by ear (A/B WAVs) | 3 days |
| **P3 Hit sounds v1** | Sourcing + Foley day; layered tennis racket and golf club × lie × grade; per-surface bounce, land and roll; mishit layers; Perfect chime in key | **COVERAGE:** every tier × club family × lie row has ≥4 takes. **NO REPEAT:** the same take never plays twice in a row. **ONSET:** every transient within 2 ms of sample 0. **BLIND TIER TEST:** friends name Solid/Great/Perfect by ear ≥80% (EXPERIENCE_AUDIT #4). **LICENCE:** every file in the provenance manifest | 5–7 days (+ Foley day) |
| **P4 VFX art system** | Toon-FX shader, atlas, mesh kit; tier ladder for both sports; SurfaceTable VFX; persistent marks; wire confetti and celebrations; UI pop vocabulary; Reduced mode for golf, weather and lava | **LADDER:** a contact sheet per tier shows distinct shapes (shape-only check with colour removed). **PALETTE:** lint PASS. **PERF:** stress scene ≥60 fps at 1920×1080 on device and within the §8 caps. **COVERAGE:** every SurfaceId has a recipe. **READ:** hero and ball pass the blur test with FX on | 6–8 days |
| **P5 Phone channel** | Per-tier knock takes; new haptics (opponent contact, own ball in, fault, golf TV clock, lip-out); `TvLatency` split + calibration screen; Swift UI haptics routed through the plugin; match-point heartbeat | **MAC GATES:** extended `work/hit-feel/run.sh` PASS. **DEVICE:** haptic-to-TV offset ≤ 1 frame on a 240 fps phone video. **SILENT SWITCH:** haptics carry the hit. **AIRPLAY:** knock plays on the phone while TV audio continues | 3–4 days + device time |
| **P6 Crowd, announcer, music** | Crowd intensity system; announcer recordings in the existing queue; golf and hub music; stingers on the beat; venue reverb sends | **TENSION:** crowd intensity rises with rally length (trace). **ANNOUNCER:** no line plays after the next point starts (existing rule). **MUSIC:** never masks hits (hits bus ≥ +6 LU over music during rallies) | 5 days |
| **P7 Moments and polish** | Rarity tuning; failure comic beats ≤1.5 s and skippable; cup payoff by rarity; big-moment presentation within your camera rules | **BEATS:** failure beats ≤1.5 s. **RARITY:** Special ≤1 per 20 s in a CPU match trace. **3 CHANNELS:** coverage test PASS | 4 days |
| **P8 Device sweep** | Full matches over AirPlay at ≥1080p; route connect/disconnect; thermal 10 min | 60 fps sustained (p95 frame ≤ 16.7 ms); no audio reset on reconnect (or a recovery path); your sign-off by eye and ear | 2 days |

**Total:** about 5–7 weeks single-threaded, or **about 2.5–3 weeks with parallel chats.**

### How to split into parallel chats
1. **P1 Spine runs alone first.** It touches `TennisGame*.cs` and `GolfGame*.cs` call sites, which today's chats also edit (tennis-anim-integrity owns `HeroTennisDriver`, chat 1 the frame budget). **Start it after the 10-17 chats are merged by integration chat 6**, or have it ship an install patch for chat 6.
2. Then four chats in parallel, each owning its own files:
   - **A · Audio** (P2 → P3): the mixer, `SfxBank`, audio assets, `TennisSounds`/`GolfSounds` adapters.
   - **B · VFX** (P4): FX shader, atlas, meshes, `TennisFx`/`ShotEffects` recipes, `SurfaceTable` VFX columns.
   - **C · Phone** (P5): `GolfHitFeel.h`, `GolfHaptics.mm`, `Haptics.cs`, Swift haptic routing, calibration UI.
   - **D · Crowd/VO/Music** (P6, starts once A's mixer lands): `TennisAudioDirector`, `TennisAmbience`, announcer assets, music.
3. **P7 and P8** run in one integration chat at the end.
- **Shared files** (`FeelCue` assets, `SurfaceTable`) are owned by the spine chat. Other chats add rows through a request file, the same way as `work/delegation-2026-10-17/REQUESTS.md`.

---

## 11. Decisions I need from you (before "proceed")

1. **Camera shake and hit-stop:** keep both **OFF** as you decided before? (Recommended: yes. The art bible's "14/30/45 ms holds" line contradicts the code and your earlier call, so I'd correct the art bible.)
2. **Sound themes:** build **one** theme first (recommended: a "Toybox × Clubhouse" blend), or all three from the 10-15 plan?
3. **Phone knock:** after the device test, should the per-tier phone knock default to **ON**? (It obeys the silent switch, so haptics stay the guaranteed channel.)
4. **Sourcing budget:** OK to spend about **$550–700** on a Foley kit plus up to about **$300** on packs? Are AI SFX tools OK for ideation and ambience only?
5. **Announcer voice:** in-house recordings (you or friends, second-person style), hired VO, or keep it silent for now?
6. **Music** for golf and hub: in scope for this pass?
7. **Special tier rarity:** is at most one Special effect per ~20 s right, or rarer?
8. **Big-moment camera:** cinematic cuts or instant replay for match point, hole-in-one and chip-in, *outside* live play? (Today all are off.)
9. **Lag split:** OK to propose splitting `Lag` into `TvLatency` + `PlayerBias` to the gameplay owner, plus a calibration screen?

When you say **proceed** (with or without answers; I'll use the recommended defaults), I start with P0 → P1.
