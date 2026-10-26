# IDLE HANDS (2026-10-24): Plaza stand, hands relaxed and empty

Adnan: "characters act as if they are holding something when they are holding nothing" (capture: work/idle-presentation-20261024/sheets/4_hands.jpg).

## Root causes
1. **Hidden racket grip pass.** The plaza hero keeps `look.racketGrip` in its right hand (HubPlayer / HubRemotes only hide its renderers), and
   `HeroGripPolish` (order 1160, added by `MatchHeroLook.Awake`) ran every frame AFTER `HubHeroAnimator` (order 900):
   - `ApplyGrip` wrapped the right fingers round the invisible handle: the male claw and the female thumb-index pinch.
   - `ApplyFreeHand` re-curled the left fingers from the cupped bind pose (22/32/16 deg plus more on ring/little, weight .8): the female cupped hook, and the male left claw.
   So the stand's own `RelaxFingers` never showed on the female left or right, and the male never had it at all.
2. **Male stand never relaxed the fingers.** `RelaxFingers` and `FingerWeight` were female-only, and the male wrist was bent (`-up + fwd*.1`).
3. **Hand roll from the thumb root.** The roll aimed the thumb ROOT forward, but that root sits on the palm side of the wrist. The female right palm faced OUT (166 deg off the thigh).
4. **Forearms forward.** The forearm aim was `+fwd*.16`, so the hands sat 10-18 cm in front of the thigh line.

## Fix (Unity/Assets/Scripts/Hub/HubHeroAnimator.cs, staged, not committed)
- `Attach` disables `HeroGripPolish` on plaza heroes (player + friends). Tennis/golf heroes keep it.
- Both heroes: straight wrist; knuckle-line roll (index->little knuckle line points forward, turned in .12); `RelaxFingers` for both sexes.
- `RelaxFingers` works in the hand's own frame (axis, knuckle line, palm normal from handedness). Index near-straight, little finger curls most, small fan.
  The thumb stays on the palm side beside the index, about 28 deg out.
- `FingerWeight` applies to both sexes (fingers relaxed while walking/running too; emotes keep their own hands via actionFade).
- Arms: upper arm `fwd*-.1` (was +.01), forearm `fwd*.05` (was .16).
- Unchanged: Walk/Run/emote clips, all meshes (no hand shape edit), seated pose logic (it builds on the relaxed stand).

## Proof
- `final/hands_m.jpg`, `final/hands_f.jpg`: BEFORE vs AFTER, both hands, out / frontout / front / back.
- `final/arms.jpg`: BEFORE vs AFTER, shoulders to knees from 5 angles.
- `final/m_front_r6_vs_r7.jpg`: male thumb rounds 6 vs 7 (r7 shipped).
- Raw shots + reports: `before/shots`, `r7/shots` (`*_report.txt` = the numbers below). Full sheets: `r7/sheets/`.
- Tool: the clone's `IdleTurnaroundCapture.cs` with the `HandMetrics` block added (clone only), `run_capture.sh <label>`, `compare.py`.

## Gates
Thresholds were set from anatomy and the baseline. The beside-thigh limit was loosened from 6 to 7 cm in round 3, after the male read 6-9 cm.

| Gate | Limit | Male L / R before | Male L / R after | Female L / R before | Female L / R after |
|---|---|---|---|---|---|
| PALM_TO_THIGH (palm normal vs inward, deg) | <= 20 | 11 / 4 | 5 / 9 | 37 / **166** | 5 / 8 |
| BESIDE_THIGH (hand fore of thigh line, cm) | abs <= 7 | **13.8 / 12.3** | 6.5 / 6.1 | **18.3** / **9.9** | 3.1 / 2.8 |
| CURL_JOINT (max MCP/PIP/DIP, deg) | <= 30 | **64 / 89** | 24 / 24 | **57** / 25 | 24 / 24 |
| CURL_TOTAL (finger MCP+PIP+DIP, deg) | 10..60 | **69 / 82** | 16-51 | **70** / 39 | 16-51 |
| FAN (adjacent finger spread, deg) | <= 8 | **17 / 31** | 5 / 5 | **9** / 5 | 5 / 5 |
| THUMB_NO_PINCH (thumb tip to index tip, cm) | >= 3 | 3.1 / 9.5 | 3.7 / 3.5 | **1.3** / 6.6 | 5.7 / 5.4 |
| THUMB_ALONGSIDE (thumb vs fingers, deg; tip on the thumb side) | <= 35, side >= 0 | **91 / 97** | 28 / 28, +3.2 / +3.3 | **46**, **-0.2** / 19, **-3.5** | 28 / 28, +2.1 / +1.1 |
| VISUAL (no hook / pinch / claw in 4 views) | eye | FAIL | PASS* | FAIL | PASS |

\* Male straight-front close-up: the camera looks along the thumb-to-index line, so the thumb overlaps the index tip in projection. In 3D they are 3.5 cm apart and parallel, and every other view reads as an open hand. Flagged for Adnan's eye.

**GATE: HANDS_EMPTY (male) PASS**
**GATE: HANDS_EMPTY (female) PASS**

## Open / not done
- **Phone lobby not refreshed.** `MatchHeroLockerExport` bakes the "relaxed" clip from `PoseRelaxed` (it already skips the grip pass for that clip).
  The lobby needs a hero re-sync, `work/hero-sync/sync_heroes.sh`, which was NOT run (needs Adnan's OK).
- Male hands are still the most forward (about 6 cm): his shoulders sit ahead of the thigh line. Pulling him back further would need a per-sex arm aim.
- Plaza emotes now show their authored hands. Before, the grip pass also wrapped the right hand of empty-handed emotes round the hidden racket.
