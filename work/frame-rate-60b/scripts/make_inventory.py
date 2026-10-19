"""FRAME_RATE_60B: INVENTORY.csv = the Unity clip survey (FrameRate60bInventory, after the 60 Hz install, in the clone)
+ the baked tracks and timed motion that are not AnimationClips. Every row has a key rate and either '60' or a written reason."""
import csv, sys
raw = list(csv.DictReader(open(sys.argv[1])))
FLUID = ("Emote_Spike", "Emote_Scuba", "Emote_Thrust", "Intro_Wave", "Intro_BringIt", "Intro_Pushups")
STD = ("Emote_JumpJoy", "Emote_FistPump", "Emote_Stomp", "Emote_Slump", "Emote_Shock", "Emote_Victory", "Emote_Defeat")
rows = []
for r in raw:
    p, c = r["path"].replace("Assets/", "Unity/Assets/"), r["clip"]
    rate = {"60": "60", "static": "static", "mixed": "mixed 30/60", "30": "30"}[r["grid"]]
    played, owner, source, shared, reason = "yes" if r["shipped"] == "1" else "no (not in the build)", "", "", "", ""
    if "/MatchHeroes/" in p:
        if any(c.endswith(x) for x in FLUID): owner, source, shared = "chat 1 (header) / emote-fluid rev37", "work/emote-fluid (rev37); 60 fps header by work/frame-rate-60b/scripts/fbx_timemode60.py", "tennis, golf (copied into golfer_*), lobby"
        elif any(c.endswith(x) for x in STD): owner, source, shared = "emote-standard (shared emotes)", "work/frame-rate-60/emotes (10-16 60 Hz fork of work/emote-standard)", "tennis, lobby"
        else: owner, source, shared = "chat 4 (tennis clips)", "work/match-anim-set, work/frame-rate-60 forks", "tennis, lobby"
        if c.endswith("ReadyIdle"): reason = "chat 4's file (REQUESTS.md; their B18 OPEN). 60 Hz candidate ready: work/frame-rate-60b/readyidle60 (same keys + monotone in-betweens)"
    elif "/HeroMoves/" in p: owner, source, shared = "emote-standard (shared)", "work/frame-rate-60/emotes + feet (10-16 60 Hz)", "golf, plaza"
    elif "/Resources/Hero/golfer" in p: owner, source, shared = "chat 1", "work/frame-rate-60b/scripts/golf60.py (fork of work/swing-fix splice_swings.py)", "golf, lobby (golf exports)"
    elif "/Resources/Golfer/" in p: owner, source, shared, reason = "golf (legacy V4)", "blender/golfer.blend (V4)", "golf fallback only", "fallback only: drawn only when the Hero golfer fails to build (GolferView logs an error); also the retarget source of matchhero_golf.py, whose frame numbers expect 30 fps"
    elif "/StandardCharacters/" in p:
        owner, source = "tennis (hidden gameplay rig)", "blender export_standard_*"
        reason = "not drawn: the hidden tennis gameplay rig (TennisHeroSetup disables its renderers); the heroes on screen play the MatchHeroes clips" if "tennis" in p else "not loaded by any code (standard_*_golf)"
    elif "/Tennis/Performance/" in p:
        owner, source, shared = "chat 4 (tennis clips)", "TennisArmStrokeBuild", "tennis"
        if "ForehandPolished" in c: reason = "not played by default: HeroTennisDriver swaps it for <Sex>_ForehandArmCorrected (60 Hz) unless TENNIS_ARM_REPAIR=0; chat 4's file"
    elif "hole_12_cinematic" in p: owner, source, shared = "chat 1", "blender/scripts/hole12_cinematic_export.py (source .blend gone); densified in place by work/frame-rate-60b/scripts/fbx_densify60.py", "golf intro (CinematicRig)"
    elif "/Tests/" in p or "/Archive/" in p: reason = "test fixture / archive, not in the build"
    if rate != "60" and rate != "static" and not reason: reason = "OPEN"
    rows.append(dict(kind="AnimationClip", path=p, clip=c, length_s=r["length_s"], clip_fps=r["clip_frameRate"], key_rate_hz=rate,
                     moving_curves_at_30hz=r["moving_curves_at_30hz"], shipped=played, shared_between=shared, built_by=owner, source=source, reason=reason))
extra = [
 ("baked track", "Unity/Assets/Resources/Course/hole_12_shot.json", "signature shot: ball, chase camera, wide camera, lens", "8.0", "30", "30 samples, played smooth", "", "yes", "golf intro (hole 12)", "chat 1", "SignatureShot.cs", "file is 30 fps; SignatureShot now plays it on a Catmull-Rom through every sample (shared frames identical, parity 1.0, proof/hole12_track_check.json)"),
 ("baked track", "GolfArcade/Unity/CharacterAssets/MatchHero_*_Rig.lzfse", "lobby/locker bone tracks (ready, serve, emotes, golf swings)", "", "60", "60", "", "yes", "SceneKit lobby/locker", "chat 6 re-export", "MatchHeroLockerExport.cs (ClipRate = 60)", "exporter samples every clip at 60 Hz; the clips it samples are now 60 Hz (ReadyIdle pending chat 4); full re-export = chat 6"),
 ("baked track", "GolfArcade/Unity/CharacterAssets/MatchHero_*_Swing_NN.lzfse", "loading-screen practice swing (12 morph poses of the Forehand)", "1.2", "~10", "replaced", "", "yes (until re-export)", "SceneKit loading screen", "chat 1", "MatchHeroLockerExport RigClips 'forehand' + CharacterModelPreview.practice", "replaced by the 'forehand' bone track (60 Hz) when the export has it; the morph path stays only as a fallback for older exports"),
 ("view rate", "GolfArcade/Unity/ClubEnvironmentView.swift", "club room SceneKit view + living cinemagraph (SpriteKit)", "", "30 -> 60", "60", "", "yes", "native menus", "chat 1", "", "preferredFramesPerSecond 30 -> 60"),
 ("view rate", "GolfArcade/Unity/ClubDesign.swift", "ClubBackdrop TimelineView (drift, light shafts)", "", "30 -> 60", "60", "", "yes", "native menus", "chat 1", "", "minimumInterval 1/30 -> 1/60"),
 ("input rate", "GolfArcade/Unity/GolfController.swift", "golf aim stick -> Unity (aim line, marker, golfer, camera)", "", "30 -> 60", "60", "", "yes", "golf aim on TV", "chat 1", "", "send interval 1/30 -> 1/60 s"),
 ("view rate", "GolfArcade/Unity/CharacterModelPreview.swift", "hero stages (locker, lobby, tiles) SCNView + CADisplayLink", "", "60", "60", "", "yes", "SceneKit lobby", "locker-mirror", "", "already 60 (preferredFramesPerSecond 60, CAFrameRateRange 60)"),
 ("input rate", "GolfArcade/Unity/LoadingModel.swift", "loading-screen practice-swing gyro trigger", "", "30", "30 (no motion)", "", "yes", "", "", "", "a shake detector that starts a practice swing; nothing on screen follows the 30 Hz samples"),
 ("runtime", "Unity/Assets/Scripts/Game/FrameProbe.cs (FrameRate)", "targetFrameRate floor", "", "60", "60", "", "yes", "all scenes", "chat 1", "", "60 floor at boot and on every scene load (phone default is 30); 120 only on request"),
 ("runtime", "Unity/Assets/Scripts/Tennis/TennisQuality.cs (StepDown)", "quality step-down", "", "", "60 @ >=1080p", "", "yes", "tennis, golf, plaza", "chat 1", "", "render scale step (0.85) removed: effects only"),
 ("runtime", "Unity/ProjectSettings/ProjectSettings.asset", "iOS thermal cap", "", "60 / 30 critical", "", "", "yes", "all", "10-16", "", "Serious 60; Critical 30 kept on purpose (device protection)"),
 ("runtime", "Unity/ProjectSettings/TimeManager.asset", "fixed timestep 0.02 s (50 Hz)", "", "50", "n/a", "", "yes", "", "", "", "no Rigidbody/FixedUpdate in game code: the ball, rackets and clubs move in Update, so nothing visible steps at 50 Hz (NO_STEP)"),
 ("procedural", "Unity/Assets/Scripts (cameras, HoleIntro flyovers, IntroGraphics, HUD tweens, plaza camera)", "camera rigs, flyovers, UI tweens", "", "per frame", "60", "", "yes", "all", "", "", "driven in Update/LateUpdate from Time.deltaTime: as smooth as the frame rate (NO_STEP camera tracks parity ~1.0)"),
]
cols = ["kind", "path", "clip", "length_s", "key_rate_hz", "status", "moving_curves_at_30hz", "shipped", "shared_between", "built_by", "source", "reason"]
with open(sys.argv[2], "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(cols)
    for r in rows:
        st = "60" if r["key_rate_hz"] in ("60",) else "static" if r["key_rate_hz"] == "static" else ("reason" if r["reason"] != "OPEN" else "OPEN")
        w.writerow([r["kind"], r["path"], r["clip"], r["length_s"], r["key_rate_hz"], st, r["moving_curves_at_30hz"], r["shipped"], r["shared_between"], r["built_by"], r["source"], r["reason"]])
    for e in extra: w.writerow(list(e))
from collections import Counter
print(Counter((r["shipped"][:3], r["key_rate_hz"], bool(r["reason"])) for r in rows))
print("OPEN:", [r["path"] + ":" + r["clip"] for r in rows if r["reason"] == "OPEN"])
