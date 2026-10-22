# Female alive quick pass

Review `ArtDir/style/alive/AUDIT.md` and `ArtDir/style/alive/after/GATE_RESULTS.md`. Start with the 27-second muted `female-alive-review.mp4`; full before/after takes and two sheets are alongside it.

Runtime: `FemaleHeroAlive` attaches only to female `MatchHeroLook` instances, including golf's dynamically assembled look. `GolferView.AliveAtRest` is a read-only state query. No source character/garment mesh, rig, clip, material, palette, prefab or camera was edited. Four additions: small upper-body idle, golf attention, wave/outcome mood, bounded garment secondary motion. Replay poses are left alone. In the editor only, `FEMALE_ALIVE=0` disables attachment for baseline proof.

`FemaleAliveCapture` captures actual tennis idle and wave/joy/slump through `PlayEmote`; only the between-point timer is held. Its close view uses a separate disabled diagnostic camera and does not move the gameplay camera. Golf reuses `CurrentGolfSwingRecorder`; rallies use `CurrentTennisPointFilm`. The initial baseline was recorded before implementation, then the final comparison was repeated with the layer disabled/enabled under fixed weather. Full source traces are staged in `after/evidence/`.

Reproduce with `work/female-alive/run.sh /absolute/fresh/output`. It runs an isolated APFS Unity clone (override `ALIVE_UNITY_PROJECT`), requires Unity 6000.3.24f1 with graphics/license access, and never launches batch mode against the shared Unity project. The original capture runs used `after/before-matched` and `after/after-final`, plus `after/before/golf`; `package.py` encodes those original directories into silent H.264 and labeled sheets. Raw frame folders/logs are untracked local working evidence, not required to view the staged deliverables.

Validation: 7/7 focused tests. All 1,272 tennis simulation rows match for gameplay, ball/root positions and score; golf impact, flight and landing match. Added-layer editor CPU mean 0.008310 ms / maximum 0.030626 ms over 990 samples; phone 60 fps has NOT been measured. Existing underarm fit defects are visible on both sides of proof. No claim of a garment collision overhaul or a device performance pass.
