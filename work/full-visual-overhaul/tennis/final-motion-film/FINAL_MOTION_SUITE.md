# Final full-speed motion library

Root runs each graphics job after accepted main-character source and final approved reaction bake. All methods are play-mode fixtures that exit themselves: omit `-quit` and `-nographics`. No gameplay or approved source clips change. Physical phone checks are deferred at the user’s request.

The machine-readable recipe is `final-motion-suite.json`. All movies must have distinct actual `unityFrame` rows at60Hz evaluation and a saved image every two frames before30fps encoding. The older unguarded movies are provisional. ServeAndFeetProof and MatchHeroProof retain the nested coroutine stack, now with actual-frame guards; they supply contracts/selected stills, not full-speed movies. All real-frame guards are installed; final reruns still require accepted main-character source and a trace cadence gate. All four formerly relative film fields now record absolute Time.frameCount; logical frame remains zero-based.

- tennis_emotes_male: `GolfArcade.EditorTools.EmoteFilm.Run`
  - Environment: `EF_OUT=../proof/full-visual-overhaul/final-motion/emotes-male`, `EF_FEMALE=0`, `EF_CLIPS=Intro_Wave,Intro_BringIt,Intro_Pushups,Emote_Scuba,Emote_Thrust,Emote_Spike`
  - Evidence: `*/trace.csv`, `triggers.json`, `summary.txt`, `capture-contract.txt`
  - Gate: All six actual entry points observed; all finish and hold >40 real frames after return. Each clip has one CSV row per actual game frame; every second frame is saved. Validate contextual plain-point=0/won-game=1/point-after-game=0 and explicit Spike/intro hooks separately.
- tennis_emotes_female: `GolfArcade.EditorTools.EmoteFilm.Run`
  - Environment: `EF_OUT=../proof/full-visual-overhaul/final-motion/emotes-female`, `EF_FEMALE=1`, `EF_CLIPS=Intro_Wave,Intro_BringIt,Intro_Pushups,Emote_Scuba,Emote_Thrust,Emote_Spike`
  - Evidence: `*/trace.csv`, `triggers.json`, `summary.txt`, `capture-contract.txt`
  - Gate: Same as male; visually inspect prop release/return in Spike and Pushups, full-body self-intersection, sleeves/hand/face, and camera coverage.
- tennis_reactions_both: `GolfArcade.EditorTools.TennisPerformanceFilm.Run`
  - Environment: `TPF_OUT=../proof/full-visual-overhaul/final-motion/reactions`
  - Evidence: `*/trace.csv`, `summary.txt`, `capture-contract.txt`
  - Gate: Six PlayJuice reactions x both bodies; observed active then inactive plus45 real return frames. Wait for main hand corrective acceptance/rebake before calling this final.
- tennis_locomotion_both: `GolfArcade.EditorTools.TennisLocomotionFilm.Run`
  - Environment: `TLF_OUT=../proof/full-visual-overhaul/final-motion/locomotion`
  - Evidence: `male/trace.csv`, `female/trace.csv`, `audit.txt`
  - Gate: 11 seconds/body, tracked SetLateralInput movement at60Hz; start/reverse/stop/sprint/reverse/settle/moving reaction. Hard moved/reversed/reaction and final stopped checks. Review shoe contact and full-speed continuity, not scalar no-slip claims.
- tennis_dives_all4: `GolfArcade.EditorTools.TennisDiveFilm.Run`
  - Environment: `TDF_OUT=../proof/full-visual-overhaul/final-motion/dives`
  - Evidence: `*/trace.csv`, `audit.txt`
  - Gate: Both directions x both bodies, actual CanDive and accepted RequestDive required; three seconds each,180 real frames. Hard accepted/active/recovered/not-active final. No forcibly set dive pose or contact clock.
- tennis_rally_fx_both: `GolfArcade.EditorTools.TennisActionFilm.Run`
  - Environment: `TAF_OUT=../proof/full-visual-overhaul/final-motion/rally-fx`
  - Evidence: `male_rally/trace.csv`, `female_rally/trace.csv`, `audit.txt`
  - Gate: 20 seconds live self-play per body plus eight separately labelled production FX fixture cases. Do not count dive coverage if audit dive=False; focused DiveFilm supplies that. List observed real stroke names; absence of a rare stroke variant is not proof it was exercised.
- tennis_serve_feet_contract: `GolfArcade.EditorTools.ServeAndFeetProof.Run`
  - Environment: `SF_PROOF_OUT=../proof/full-visual-overhaul/final-motion/serve-feet`, `SF_PRODUCTION_KIT=1`
  - Evidence: `trace.csv`, `shots.json`, `audit.txt`
  - Gate: Guarded actual game walk-in/toss/trophy/contact/landing plus repeated serve contacts and selfplay. Existing nested IEnumerator stack is preserved. unityFrame column is the old absolute fc field renamed. Full run, not SF_QUICK=1, certifies repeated serve sample counts. Images are selected diagnostic poses rather than a consecutive30fps film.
- tennis_contact_selfplay_contract: `GolfArcade.EditorTools.MatchHeroProof.Run`
  - Environment: `MH_PROOF_OUT=../proof/full-visual-overhaul/final-motion/selfplay-contract`, `MH_PRODUCTION_KIT=1`
  - Evidence: `trace.csv`, `shots.json`, `audit.txt`
  - Gate: Guarded actual default presentation plus both-sex matches, live contacts/dives/replay. Compare source durations/contact anchors, physicsRestoreError, actual player/rival string-ball gaps. Rows are grouped by scenario/role for cadence. Images are selected diagnostic poses; use ActionFilm for full-speed game sequences.
- golf_both_five_strokes_intro_performance: `GolfArcade.EditorTools.GolfMotionFilm.Run`
  - Environment: `GMF_OUT=../proof/full-visual-overhaul/final-motion/golf`
  - Evidence: `*/trace.csv`, `audit.txt`
  - Gate: Both bodies: production course intro, real synthetic Driver/Iron/PitchingWedge/Wedge/Putter shots, then Idle/Wave/Cheer/FistPump through actual GolferView.Perform. Existing real-frame guard retained. Require real flight and observed target; performance returns to Idle. Golf intro+shots+performance all carry explicit absolute unityFrame.

The studio source library contains all33 slots; live selfplay’s trace names must be reported as observed coverage. Pure slot population, static sampled poses, or native source graph parity alone do not certify real full-speed contacts/entry/return. Keep those scopes distinct.
