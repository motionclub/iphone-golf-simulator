# Measurement definitions and corrections

Gate limits are unchanged from prompt 31. F3 counts the FBX body rotation keys and their serialized interpolation flags. Blender 5.2.2 hard-codes all imported keys to LINEAR, even if the file contains cubic Hermite curves. The audit records that derived Blender count separately and evaluates the file's actual tangents at 60 Hz. The independent native-reader validation against all 12 original stock-Blender traces is in proof/native_reader_validation.json (worst bone position error under 0.002 mm). The original files are linear; candidates contain actual cubic flags and slopes. No source-action PASS is substituted for a file measurement.

F11 wrist twist means the axial twist component about the local hand +Y axis, measured with swing/twist decomposition. Full joint rotation is also reported, but includes wrist bending and is not the same quantity. The initial draft audit counted full joint rotation; both BEFORE and AFTER are remeasured using the correct definition.

F1 uses signed angular velocity projected onto the dominant motion axis within each preregistered beat window. A sign crossing or arrival at a zero plateau counts once. Completely stationary bones have no crossing and are separately measured by F3. Results list every crossing and the worst frame. F2 uses per-link local angular-speed peaks, not world rotations inherited from the parent.

F8 remains an exact comparison to 1.000 with no tolerance. A clarification is pending because the original protected READY samples contain non-unit floating-point scales. The original READY samples remain protected while awaiting that clarification.

F10 reuses the original 96 threshold expressions. G5 compares re-imported candidates to independently captured world matrices from the authored layer before serialization, exactly as the original gate compared to its authored solver. G7 reuses collide3.py on evaluated dressed meshes posed from the actual re-import trace, rather than the old generator. G8 retains the baseline clearance correction field and evaluates it with the same new polish displacement applied to cleared and uncleared targets.


Iteration 05 measurement corrections apply identically to BEFORE and AFTER. F2 indexes angular-velocity samples by their ending frame; its last allowed frame is pose + settle, not pose + settle + 1. F4 finds the last nonzero incoming angular increment, including a settled pause. F6 measures pelvic angular counter-motion as well as pelvic translation, as permitted by the brief. F3 tests whether at least three consecutive identical component keys occur outside the union of intended hold and READY intervals. All numeric thresholds are unchanged.

Adnan authorized READY-edge retiming on 2026-10-05, preserving endpoint poses and contacts. The protected-edge F12 failures remain recorded in locked_ready_F12_steps.json; the exception does not change the 30 mm gate.


Revision 06: only endpoint poses are fixed after Adnan’s READY-edge retiming exception. Pose/settle keys receive priority over overlapping anticipation windows. Source angular moves below 0.1 degrees receive a deliberate 2-degree torso tilt; overshoot is authored at 12%. F5 refuses to count fractional overshoot of float noise (move magnitude at most 0.001 degrees is not measurable). Contact IK and planted-foot constraints are authored at 60 Hz before writing FBX. Forearm roll redistribution for Pushups is logged and remains subject to the 15-degree wrist gate and eye review.

Revision 07 removes the old quarter-second boundary keys after the authorized READY retiming exception. Endpoint poses remain copied from the originals; contacts use the 60 Hz solve. Body-drive phase tracks use separate triangular velocity profiles and 12% torso overshoot. These authored settings are not gate evidence: the re-imported audit determines PASS or FAIL.

Additional references read: [Cooper’s authored Game Anim excerpt](https://www.gamedeveloper.com/production/the-12-principles-of-animation-in-video-games) supports overlap, readable follow-through and staged exaggeration of existing poses. [Unity Damped Transform documentation](https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/constraints/DampedTransform.html) describes separate positional and rotational damping; this pass uses offline curves and adds no gameplay constraint. The brief’s video timestamps are still brief-provided guidance, not a claim that those videos have been watched.

Revision 09 corrects F2 action-window attribution: per-link ranges in plan JSON contain each authored action and its settle. The earlier shared window could include another action’s peak (e.g. Spike slam inside wind-up). The audit keeps previous_shared_window_peaks alongside corrected measurements. BEFORE uses the original action’s pose boundary; all 1–4 frame and no-ties requirements remain unchanged.

Gibson’s supplied YouTube reference was inspected at the Tracer jump demonstration and its caption transcript read for the listed timing, overlap, overshoot and hero/emote sections. The Fortnite/Unreal reference was inspected around 10:46 and its captions verify the spine bone-translation discussion. No dance choreography was researched or copied.

Female film startup: one normal launch failed to connect UPM; a cached-package (-noUpm) retry failed to resolve UGUI/URP compiler references. The next normal-package launch recovered and is capturing. Canonical gameplay and package files were not modified.

Revision 10 restores the original world foot and toe targets in the 60 Hz authoring solve; the earlier solver incorrectly used post-polish FK feet. Scuba reach floor is 0.994 of the full arm length, and its swimming hand's yaw is carried relative to the actual pelvis. Original thresholds are unchanged. Revision 11 is a single-clip continuity experiment, not the revision 10 candidate: action starts use the actual preceding recovery value rather than an obsolete pose target. Neither change is a gate PASS until measured.

Rosen's supplied GDC talk was inspected around the bounce/cubic-interpolation demonstration; its transcript was read for cubic spatial/velocity continuity (6:43–7:27), spring damping (7:32–8:54), and layered spring transitions (17:46–18:38). The offline curve layer follows these timing rules, without adding a runtime system. Vimeo 204601876 currently displays “Unable to play media.” Its authored process description was read; the timelapse has not been watched.

All 48 revision 07 comparison films are encoded; male and female decode verification logs contain the exact frame count, dimensions, and duration per movie. F14 remains FAIL with 0/12 eye approvals. Female capture recovered on a normal UPM launch.

Revision 10 Unity F12: 10/12 PASS, Pushups FAIL at frame60=9 (male38.73687mm, female38.694973mm, limit30). All six taunts finish before the serve starts. Tests use the actual AwardPoint game-win and TennisPresentation.Drive match-start flows; candidate FBX/meta hashes are recorded per result. The clone test runner gained FLUID_WAIT_XCODE=0 so its isolated project can run independently of another chat’s Xcode build. No unrelated process was interrupted.

Revision 12 staggered anticipation experiment: male Spike F1 count8→7 remains FAIL and F5 passes5/5→4/5, so that phase change is not adopted. Revision 13 returns to revision10 phase tracks and corrects the nose-contact transform and its release; contact targets derive from the original head-relative hand pose instead of an already-clamped authoring pose. Revision14 tests a broad-based opening velocity profile for Pushups and an early source-time endpoint1.5 instead of2.1; it retains contact destination frame9. Neither experiment is an installation approval.

Lobby export inspected: MatchHeroLockerExport.RigClips includes all six emote/intro slots, and GolfArcade.EditorTools.MatchHeroLockerExport.Run is a standalone Editor command. Export is deferred while candidate gates fail; failed candidates are not written into lobby Rig lzfse. Any eventual accepted export must be performed and hash-tested in the clone before publishing the permitted rig payloads.
