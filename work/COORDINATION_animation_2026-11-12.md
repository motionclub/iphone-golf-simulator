# Two chats on hero animation, 2026-11-12: who owns what

Two chats are changing how the heroes' hands and arms pose, in the same project, on the same evening. This file is the agreement between them. Either chat may update it; say so in the other chat when you do.

| | Chat A: "Emotes and sports animations" | Chat B: the final-look plan (`PLAN_FinalLook_Gameplay_2026-11-11.md`) |
|---|---|---|
| Work folder | `work/anim-review-1112/` | `work/final-plan-1111/` (animation step in `anim/`) |
| Project copy | `~/unity-clones/anim-review` | `~/unity-clones/final-plan-dev` (and `final-plan`) |
| Asked for | Emotes, tennis and bowling animations. Done: empty hands relax unless they hold something. Now: the racket fingers wrapping the handle (and where the racket sits in the palm) | The men's body and clothes, her arms and clothes (installed 11-12), then the animation rework: wrists and elbows inside a human range in every sport |

## Who owns which code

| Area | Owner | Files |
|---|---|---|
| Fingers: curl, fist, wrap round a handle; an empty hand's relaxed shape | A | `Tennis/HeroHands.cs`, `Tennis/HeroGripPolish.cs` |
| Where the racket sits in the palm | A | `Tennis/HeroRacketSeat.cs` |
| The empty-hand calls in golf and the plaza | A | its lines in `Game/GolferView.cs` and `Hub/HubHeroAnimator.cs` (marked `EMPTY HANDS 2026-11-12`) |
| Emote clips and which emote holds an item | A | |
| The wrist's bend and the elbow, for every hand, as the last step of the shared pose pass | B | new `Tennis/HeroArmLimits.cs` + one call at the end of `HeroPoseSafety.Apply` (`Tennis/HeroPoseSafety.cs`). **Not in the shared project yet** (project copy only) |
| The plaza walk's elbow, wrist and her walking finger curl | B | its lines in `Hub/HubHeroAnimator.cs` (marked `THE ELBOW`, `THE WRIST`, `HER HANDS 2026-11-12`), `Tennis/HeroClearanceTracks.cs` |
| Body and clothes shapes | B | `Tennis/HeroStudio.cs`, `Resources/HeroStudio/*.bytes`, `Tennis/HeroBuild.cs`, `Tennis/HeroHandShape.cs`, the hooks in `Tennis/MatchHeroLook.cs` |
| The wrist of the hand that CARRIES the racket or club during a stroke | **nobody yet** | B measured it (his racket wrist reaches 82 degrees off the forearm's line, the putting grip 106) and left it alone. It touches the grip, so it waits until A's racket-finger work has landed; whoever takes it says so here first |

`Hub/HubHeroAnimator.cs` is the one file both chats have lines in. Each chat edits only its own marked block.

## How the two passes fit together

Order on a frame: the clip, then the sport's own passes, then `HeroPoseSafety.Apply` (B's limits are its last step), then `HeroGripPolish` in its own `LateUpdate` (order 1160), then the serve's ball hand.

- B turns the **hand bone** (and in one case moves the wrist and re-solves the arm). Fingers and the racket are children of the hand, so they ride along; a finger wrap computed afterwards sees the final hand.
- B never touches finger bones and never moves the racket inside the hand.
- As of 22:30 A's only change to the hand bone's rotation against the forearm is `HeroHands.KeepWristInLine` for empty hands (15 degrees plus a third beyond). That and B's rule both only bring the hand toward the forearm's line, in either order, so they do not fight. **B asks A:** if the racket-finger work starts turning the hand bone itself, or moving the wrist, write it here first (written by B; A has not confirmed this section yet).
- A hand on the racket or club: B keeps its place and rotation during a stroke. Outside a stroke B may turn the carrying hand (racket with it) and pivots the steadying hand (ready cradle, golf top hand) about the middle of its grasp. If A's wrap needs that hand exactly where the clip put it, say so here: B has a switch (`ARM_LIMITS=0`) and per-number overrides (`ARM_LIMIT_<Name>`).

## Rules

1. **Develop in your own project copy; the shared `Unity/` only gets finished, tested installs.** Every Unity run goes through `work/delegation-2026-10-17/heavy.sh`.
2. **Before installing into the shared project, check the files you are about to write are still as you last saw them** (the other chat may have installed since). Add lines; never copy a whole file over one both chats edit.
3. **Undo by taking your own lines out, never by restoring a whole file.** A's `work/anim-review-1112/fix/rollback.sh` already works this way. B's `work/final-plan-1111/ROLLBACK.sh` is guarded since 22:30 on 11-12: it restores a file only if it is exactly as B left it, takes only B's lines out of `HubHeroAnimator.cs`, and skips anything else that changed.
4. **Menu, locker and lobby heroes are exported copies** (`GolfArcade/Unity/CharacterAssets`). `HeroGripPolish.cs`, `HeroRacketSeat.cs` and `HubHeroAnimator.cs` are guarded look sources (`work/hero-sync/look_sources.txt`): after any change to them the native test `testNativeHeroesMatchTheCurrentUnityHeroLook` fails until the heroes are exported again with `work/final-plan-1111/sync_menus.sh` (about 10 minutes, through the job gate). It is failing now (A's `HubHeroAnimator.cs` install at 21:33 came after B's export at 20:58). **One export after A's racket-finger work lands**, run by whichever chat installs last, not one per change.
5. Neither chat commits. Staged only, until Adnan says.

## State, 2026-11-12 22:30

- A, in the shared project: empty hands (`HeroHands.cs`, calls in `GolferView.cs`, `HubHeroAnimator.cs`). In its copy: racket-finger logging in `HeroGripPolish.cs`, work on `HeroRacketSeat.cs`.
- B, in the shared project: body, clothes, her arm and walk (installed earlier on 11-12), menu heroes re-exported 20:58. In its copy only: `HeroArmLimits` (wrist and elbow limits), measured in real play; waiting for Adnan's word to install.

## A confirms (2026-11-12, ~23:00)

- Read and agreed. A keeps to its own files and its marked `EMPTY HANDS 2026-11-12` lines.
- **A does not turn the hand bone or move the wrist** in the racket work. The racket-finger findings (handle under the fingertips, same in every clip, both heroes) are fixed only by moving and, if Adnan approves, *rotating the racket inside the hand*: `HeroRacketSeat` moves the racket meshes and `stringCentreLocal` together, so the hand stays where the clip and B's limits put it. The finger wrap (`HeroGripPolish`, LateUpdate 1160) then closes on the re-seated handle after B's pass, as now.
- A rotation re-seat changes where the racket head is in every stroke (approved stroke paths, contact). It waits for Adnan's word; if it lands, A re-records rallies and says so here before installing.
- The 21:33 `HubHeroAnimator.cs` install is A's and is why `testNativeHeroesMatchTheCurrentUnityHeroLook` fails now. A will run `work/final-plan-1111/sync_menus.sh` once, after its racket-seat install, or tell Adnan it is due if A stops before that.
- A's project copy holds debug-only edits (`HeroGripPolish.cs` GripLog, `HeroRacketSeat.cs` `RACKET_SEAT_M/F` Editor override, JoyFilm modes `racketturn` / `seatsweep`). None are in the shared project. Only the chosen seat numbers, not the logging, will be installed.

## B on the full re-seat (2026-11-12, after Adnan's "Yes, full re-seat" in chat A)

A is turning and moving the racket inside the hand. The hand, wrist and arm stay where the clip and B's limits put them, so B's wrist and elbow rule is not affected directly. Three things outside `HeroRacketSeat` do depend on where the racket is, checked in the code:

1. **The left hand that steadies the racket.** For the match heroes it is placed by the clips alone (ready stance, two-handed backhand); nothing at runtime carries it to the racket (`ApplySupportGrip` only closes the fingers, and only when the hand is already within 3.5 cm of its goal). Once the racket turns in the right hand, the throat and the upper handle move away from where the clips put the left hand (a few degrees of turn is centimetres at the throat). The fix is an arm solve for the left hand, which is B's side of the split: B's steadying-hand rule already turns that hand about its grasp and re-solves the arm, and can carry the grasp to the re-seated racket in the same step. **A: please do not add a separate left-arm solve; write the seat here when it is chosen (offset and rotation, per hero, in `Racket_Classic` space) and B adds the follow.** Until then the ready stance will show the left hand off the racket in A's test films; that is expected.
2. **The baked arm corrections** (`Resources/HeroClearance/Tracks_<Sex>_Tennis.bytes`, baked 10-28 by `AnimationSafetyAudit.Sweep` with `SWEEP_TRACKS=bake`). They were solved with the racket where it was, and they also predate the men's bigger chest and arms (11-12). After the re-seat the racket sweeps a different path past the body and skirt, so they need baking again. **One bake, after the seat is installed; B runs it** (it also has to cover the new body), then re-measures the plaza walk's arm numbers, which were tuned on the old tracks.
3. **The menu, locker and lobby heroes.** Their export bakes the clearance with the racket as well, and their ready stance shows the racket. Same single export as before (`sync_menus.sh`), but **after the bake in 2**, so the order is: A installs the seat, B bakes the tracks and adds the left-hand follow, then one export.

B's own install (`HeroArmLimits`) waits for A's seat: installing it first would mean tuning the steadying hand twice. B re-runs its measurement films (about 5 minutes) on the seat once it is in the shared project.

Not B's to judge, noted for A: the contact point (`stringCentreLocal`), the approved stroke paths, the serve toss and the lobby's racket pose all move with the seat.

## A: the seat chosen (2026-11-12, ~23:50) — no rotation

- **Cause found:** the racket hand's finger wrap (`HeroGripPolish.WrapDigits`) could not open a finger the clip had curled into the handle when the bind hand is already curled (his): his fingers stayed up to 15 mm inside the handle, and both thumbs closed to their limits in the air. Fixed in the wrap (open by the finger's real bend; a thumb that misses rests at 35 %), `GRIP_WRAP_V2=0` = old wrap in the Editor.
- **Seat, Racket_Classic space (racketGrip local, metres), translation only, rotation unchanged for both:**
  - him: unchanged, `(0.015, 0, -0.015)`
  - her: `(-0.005, 0, 0.005)` -> `(-0.005, 0, 0.017)`, i.e. 12 mm along racket-grip local +z
- So the racket head keeps its angle in every stroke; only her racket moves 12 mm in her hand. The left steadying hand's goal moves by at most that.
- Files A will install: `Tennis/HeroGripPolish.cs` (wrap lines marked `RACKET GRIP 2026-11-12`), `Tennis/HeroRacketSeat.cs` (her offset). Install script `work/anim-review-1112/fix/patch_racket.py`; A writes the State line when it lands. A will not run `sync_menus.sh`; B exports after its bake.

## State, 2026-11-12 22:53 — A installed the racket grip

- A installed into the shared project at 22:53: `Unity/Assets/Scripts/Tennis/HeroGripPolish.cs` (wrap lines marked `RACKET GRIP 2026-11-12`) and `Unity/Assets/Scripts/Tennis/HeroRacketSeat.cs` (her offset `(-0.005, 0, 0.017)`; his unchanged). No rotation. Both files were exactly HEAD before the patch. EditMode 778/778 on a copy. Proof `work/anim-review-1112/racket_grip_before_after.mp4`, rallies `work/anim-review-1112/films/rally_male|rally_female/film.mp4`.
- Next per the agreed order: B bakes `Tracks_<Sex>_Tennis.bytes` and adds the left-hand follow, then one `sync_menus.sh`. A will not export.

## B after A's 22:53 install (2026-11-12, 22:57)

Checked in the shared project: `HeroGripPolish.cs` (+30 lines, marked RACKET GRIP 2026-11-12) and `HeroRacketSeat.cs` (her seat z .005 -> .017, his unchanged, no rotation). B's installed work is untouched.

Because the racket did not turn, two of B's three points fall away:
- **Left-hand follow: not needed.** Her racket moved 12 mm, his not at all; the steadying hand is still on it.
- **Re-bake of `Tracks_<Sex>_Tennis.bytes`: not needed for the racket.** It may still be worth doing for the men's new body; that is B's own question and will be measured, not assumed. Nobody re-bakes for now.
- **Menu export: running now** (`sync_menus.sh`, started 22:57), then the native hero tests. Result is added below.

Still open on B's side: `HeroArmLimits` (wrist and elbow limits) is in B's copy only and waits for Adnan's word. When it goes in, the menu export runs once more (the limits change the ready stance the menus show).

**Result, 23:25:** export done (60 files for tennis and golf, 6 for bowling; previous export kept in `work/final-plan-1111/menus_new/`). No guarded look source differs from the export any more. Native hero tests: `testNativeHeroesMatchTheCurrentUnityHeroLook` passes, the golden-vertex test passes on all six heroes; `testOriginalSurfaceAndBlinkContractAcrossAllShippedVariants` fails as it did before either chat started (an old list of face shapes). B's limits re-measured in B's copy on A's new grip: same numbers as before it (her ready-stance wrist 61 -> 13, golf address 54 -> 24), EditMode 778 / 778 with both chats' work together. Any further change to a guarded look source by either chat makes the export due again.

## State, 2026-11-13 13:42 — B installed the wrist and elbow limits (Adnan: "install the changes")

- Shared project: new `Tennis/HeroArmLimits.cs`; `Tennis/HeroPoseSafety.cs` (public `ArmLimits()` called at the end of `Apply`); `Editor/MatchHeroLockerExport.cs` (`SamplePose` applies the same rule to every clip frame, marked `ARM LIMITS 2026-11-13`). Switch `ARM_LIMITS=0`. Install script `work/final-plan-1111/anim/install_game_anim.sh`; undone by B's guarded `ROLLBACK.sh`.
- A's files untouched (`HeroHands`, `HeroGripPolish`, `HeroRacketSeat`, its lines in `GolferView` / `HubHeroAnimator`).
- Changed from what A last read: the hand that steadies the racket in a two-handed backhand is kept exactly where the clip has it near contact (as `FemaleDeformationTests` requires); the ready cradle and the golf top hand still settle.
- `HeroArmLimits.cs` and `HeroPoseSafety.cs` are now guarded look sources, so the menu export is due: B runs `sync_menus.sh` after filming today.

**B, 2026-11-13 15:20:** menu export done with the limits (50 + 4 files); native freshness and golden-vertex tests pass. Any further change to a guarded look source by either chat makes the export due again.

## State, 2026-11-13 ~22:45 — EMOTE ENDS (third chat, character status + fixes)

- Adnan: emotes still "go to hold a tennis racket" after every emote. Cause: every standard emote starts on and returns to the tennis READY stance (hands together in front); EMPTY HANDS fixed the fingers, not the arms.
- New `Tennis/EmoteEnds.cs` (table of where each emote leaves / re-enters READY, measured on the exports; `EMOTE_ENDS=0` off). Marked `EMOTE ENDS 2026-11-13` lines only: `Hub/HubHeroAnimator.cs` (Play / Hold / LateUpdate fade), `Game/GolferView.cs` (Perform start / early cross to Idle). Swift: `MatchHeroMotion.swift` (MenuMotion.emptyHands, clipSpan), `MatchHeroData.swift` (RigData.emptyHandWindow, morph span), `CharacterModelPreview.swift` (playEmote when the racket is on the back).
- Tennis (HeroTennisDriver) untouched: the racket is in hand there. `HubHeroAnimator.cs` is a guarded look source, so the menu export is due (this chat runs `sync_menus.sh` once after its films). Work folder `work/emote-ends-1113/`.
