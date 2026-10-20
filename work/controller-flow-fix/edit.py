from pathlib import Path
import json
root=Path.cwd()
files=[]
def edit(path, fn):
 p=root/path; s=p.read_text(); result=fn(s)
 if result!=s: p.write_text(result); files.append(path)
def session(s):
 s=s.replace('enum TennisUltimate:', 'enum ControllerSetupStage { case scan, timing, ready, playing }\n\nenum TennisUltimate:',1)
 s=s.replace('    var axisGate = SportsAxisGate()', '    var setupStage: ControllerSetupStage = .scan\n    var axisGate = SportsAxisGate()',1)
 s=s.replace('&& (emoteWindow == "intro" || emoteWindow == "point")','&& setupStage == .playing && emoteWindow == "point"')
 pos=s.index('    func playEmote(slot: Int)')
 s=s[:pos]+'''    var pointControlsVisible: Bool {
        active && ready && loading.finished && !paused && setupStage == .playing
        && finishedMatch == nil && sport == "tennis"
        && ["serve", "toss", "receive", "rally"].contains(tennisPhase)
    }
    var tossVisible: Bool { pointControlsVisible && tennisPhase == "serve" }
'''+s[pos:]
 s=s.replace('            let justLocked = gate.locked && !self.axisGate.locked\n','')
 s=s.replace('''                self.status="Court direction locked. Stand at your center, then tap Ready."
                // Still aimed at the TV: time its delay now, while it costs the player nothing.
                if justLocked { self.measureTVDelay() }''','''                if self.setupStage == .scan { self.offerTimingCalibration() }''')
 s=s.replace('phase="calibrating"; feedback="";', 'setupStage = .scan; axisGate = SportsAxisGate(); phase="calibrating"; feedback="";',1)
 start=s.index('    func skipTimingCheck()')
 end=s.index('    // MARK: Controller serve',start)
 s=s[:start]+'''    /// Court scanning finishes before timing. The match remains held until Ready.
    func offerTimingCalibration() {
        guard active, ready, loading.finished, sport == "tennis" else { return }
        setupStage = .timing; timingPrompt = true; checkingTiming = false
        menuPauseVisible = false; measuringDelay = false
        status = "TV scan complete. Calibrate your swing timing on the TV."
        command("controllerSetup", value: 1)
        pause(reason: status)
        SportsDisplays.shared.external?.isHidden = true
    }
    func skipTimingCheck() {
        guard setupStage == .timing else { return }
        command("cancelTimingCheck")
        completeTimingCalibration(message: "Using the saved timing for this screen.")
    }
    func completeTimingCalibration(message: String) {
        guard setupStage == .timing else { return }
        timingPrompt = false; checkingTiming = false; timingCountdownEnds = nil
        timingNote = message; setupStage = .ready
        pause(reason: "Timing calibration complete. Tap Ready to play.")
    }
    func receiveTimingResult(_ message: String) {
        guard checkingTiming, setupStage == .timing else { return }
        let note: String
        if let ms = Double(message), ms.isFinite, ms >= 0 {
            SportsTiming.store(ms / 1000, for: SportsTiming.currentTV())
            note = String(format: "Timing set — %.0f ms.", ms)
        } else {
            note = "The game will refine your timing as you play."
        }
        SportsDiagnostics.write("timing check tv=\\(SportsTiming.currentTV()) result=\\(message)")
        completeTimingCalibration(message: note)
    }
    /// Recenter the racket without entering the retired aiming lesson.
    func recalibrateAiming() {
        guard active, ready, !touch, motion.axisLocked, motion.calibrate() else { return }
        phase = "steering"; command("recalibrate")
        pause(reason: "Center set. Tap Ready to continue.")
    }

'''+s[end:]
 s=s.replace('guard active, !paused else { return }\n        sendJSON(["version":1,"session":sessionID,"action":"toss"', 'guard tossVisible else { return }\n        sendJSON(["version":1,"session":sessionID,"action":"toss"')
 s=s.replace('    func skipTutorialStep() { command("tutorialNext") }\n','')
 s=s.replace('''        SportsDiagnostics.write("pause reason=''', '''        if checkingTiming {
            command("cancelTimingCheck"); checkingTiming = false; timingPrompt = true; timingCountdownEnds = nil
        }
        SportsDiagnostics.write("pause reason=''',1)
 s=s.replace('''        guard ready, touch || phase == "steering" else''','''        guard sport != "tennis" || setupStage == .playing else { status = "Finish TV scan and timing calibration, then tap Ready."; return }
        guard ready, touch || phase == "steering" else''',1)
 start=s.index('    func readyToPlay()'); end=s.index('    func useTouch()',start)
 s=s[:start]+'''    func readyToPlay() {
        guard displayConnected, active, ready, loading.finished else { return }
        guard sport != "tennis" || setupStage == .ready || setupStage == .playing else { return }
        if !touch {
            guard sport != "tennis" || motion.axisLocked else { return }
            guard motion.calibrate() else { return }
            phase = "steering"; command("recalibrate")
        }
        setupStage = .playing
        command("controllerSetup", value: 0)
        resume()
    }
    /// Unity renders the timing ball on the TV; motion samples keep flowing from the phone.
    func startTimingCheck() {
        guard active, ready, loading.finished, displayConnected, sport == "tennis",
              setupStage == .timing, !checkingTiming else { return }
        if !touch {
            guard motion.axisLocked, motion.calibrate() else { return }
            phase = "steering"
        }
        menuPauseVisible = false; SportsDisplays.shared.external?.isHidden = true
        command("controllerSetup", value: 1)
        command("resume"); paused = false
        timingPrompt = false; checkingTiming = true; timingNote = ""
        timingCountdownEnds = Date().addingTimeInterval(5)
        status = "Swing with the bouncing ball on your TV."
        command("timingCheck")
    }
    func recheckTiming() {
        guard touch || motion.axisLocked else { beginAxisCapture(); return }
        offerTimingCalibration()
    }
'''+s[end:]
 s=s.replace('            finishAimingSetup(resumePlay:false)','            command("cancelTimingCheck"); aimLesson = nil; setupStage = .ready')
 s=s.replace('        axisGate=SportsAxisGate()','        setupStage = .scan; timingPrompt = false; checkingTiming = false\n        command("cancelTimingCheck"); command("controllerSetup", value: 1)\n        pause(reason: "Scan your TV to set the court direction.")\n        axisGate=SportsAxisGate()',1)
 s=s.replace('        status="Court direction set. Stand at your center, then tap Ready. Use flip if left/right are swapped."','        if setupStage == .scan { offerTimingCalibration() }')
 s=s.replace('''        if touch { readyToPlay() }
        else if sport == "tennis" && !motion.axisLocked { beginAxisCapture() }
        else { motion.start(tennis:sport == "tennis",travel:travel); status="Stand at your center, then tap Ready." }''','''        if Self.benchmark { setupStage = .ready; readyToPlay(); return }
        if sport == "tennis" {
            if touch { offerTimingCalibration() } else { beginAxisCapture() }
        } else {
            setupStage = .ready
            if !touch { motion.start(tennis:false,travel:travel) }
            status = "Stand at your center, then tap Ready."
        }''')
 start=s.index('            case "timing":');end=s.index('            case "abilities":',start)
 s=s[:start]+'''            case "timing": receiveTimingResult(event["message"] as? String ?? "failed")
'''+s[end:]
 s=s.replace('                if TennisMenu.shared.launch?.mode == .tutorial { OnboardingFlow.shared.hit() }\n','')
 start=s.index('            case "tutorialStep":');end=s.index('            case "golfHoleDone":',start);s=s[:start]+s[end:]
 s=s.replace('            case "tutorialDone": TennisMenu.shared.tutorialFinished()\n','').replace('            case "shot": if TennisMenu.shared.launch?.mode == .tutorial { OnboardingFlow.shared.hit() }\n','')
 s=s.replace('loading.cancel(); tutorialStep=nil; finishedMatch=nil','loading.cancel(); tutorialStep=nil; finishedMatch=nil; timingPrompt=false; setupStage = .scan')
 return s
edit('GolfArcade/Unity/SportsSession.swift',session)
def views(s):
 s=s.replace('            if let step = session.tutorialStep { TutorialPanel(step: step, onSkip: { session.skipTutorialStep() }) }\n','')
 s=s.replace('} else if !session.touch && !session.axisGate.locked {','} else if session.setupStage == .scan {',1)
 s=s.replace('''            } else if session.aimingSetup {
                AimingCalibrationPanel(session:session)''','''            } else if session.setupStage == .ready {
                ControllerReadyPanel(session: session)''',1)
 start=s.index('                    .overlay(alignment: .top) { if session.tutorialStep');end=s.index('                stamina',start);s=s[:start]+s[end:]
 s=s.replace('''                        if session.tutorialStep == nil {
                        Slider''','''                        Slider''',1).replace('''                            .onChange(of: steering) { _, v in session.steer(v) }
                        }''','''                            .onChange(of: steering) { _, v in session.steer(v) }''',1)
 s=s.replace('if session.tutorialStep == nil || (session.tutorialStep?.index ?? 0) >= 2 { RallyAimPad(session:session).frame(height:150) }','RallyAimPad(session:session).frame(height:150)')
 s=s.replace('''                            if session.tutorialStep == nil {
                            Slider(value: $power, in: 0.15...1) { Text("Swing power") }
                            }''','''                            Slider(value: $power, in: 0.15...1) { Text("Swing power") }''')
 s=s.replace('session.swing(session.tutorialStep == nil ? power : 0.7)','session.swing(power)')
 s=s.replace('if !session.paused && session.tennisPhase == "rally" { TennisAbilityControls(session: session) }\n                TennisEmoteControls(session: session)','if session.pointControlsVisible { TennisAbilityControls(session: session) }\n                if session.canPlayEmote { TennisEmoteControls(session: session) }')
 start=s.index('            if session.finishedMatch == nil && session.ready && session.paused');end=s.index('            if session.ready && session.loading.finished',start)
 s=s[:start]+'''            if session.finishedMatch == nil && session.ready && session.paused && session.setupStage == .playing {
                Text(session.status).font(IslandUI.font(14, bold: true)).multilineTextAlignment(.center)
                ControllerButton(title: "Resume", icon: "play.fill") { session.readyToPlay() }
            }
'''+s[end:]
 s=s.replace('Text(session.emoteWindow == "intro" ? "YOUR INTRO · PICK AN EMOTE" : session.emoteWindow == "point" ? "YOUR POINT · CELEBRATE" : "EMOTES")','Text("YOUR POINT · CELEBRATE")')
 s=s.replace('Available for your intro and after you score a point.','Choose an emote to celebrate your point.')
 s=s.replace('''                    session.toss()
                }''','''                    session.toss()
                }.accessibilityIdentifier("tennisToss")''',1)
 s=s.replace('Text("Timing check").font','Text("2 · Timing calibration").font')
 s=s.replace('''{ session.startTimingCheck() }
            Button''','''{ session.startTimingCheck() }.accessibilityIdentifier("timing-start")
            Button''',1)
 s=s.replace('''{ session.skipTimingCheck() }
                .font''','''{ session.skipTimingCheck() }.accessibilityIdentifier("timing-skip")
                .font''',1)
 start=s.index('/// The tutorial\'s current step');end=s.index('/// Shared by the regular controller',start);s=s[:start]+s[end:]
 start=s.index('struct AimingCalibrationPanel:');end=s.index('struct RallyAimPad:',start)
 s=s[:start]+'''struct ControllerReadyPanel: View {
    let session: SportsSession
    var body: some View {
        VStack(spacing: 18) {
            Spacer()
            Image(systemName: "checkmark.circle.fill").font(.system(size: 64)).foregroundStyle(IslandUI.lime)
            Text("3 · Ready to play").font(IslandUI.font(28, bold: true))
            if !session.timingNote.isEmpty { Text(session.timingNote).multilineTextAlignment(.center) }
            Text("Watch the TV. Your phone stays your controller.").multilineTextAlignment(.center)
            ControllerButton(title: "Ready to play", icon: "play.fill") { session.readyToPlay() }
                .accessibilityIdentifier("controller-ready")
            Spacer()
        }.frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// Compatibility for archived previews; the aiming exercise has been retired.
struct AimingCalibrationPanel: View {
    let session: SportsSession
    var body: some View { ControllerReadyPanel(session: session) }
}

'''+s[end:]
 return s
edit('GolfArcade/Unity/TennisPlayViews.swift',views)
edit('GolfArcade/Unity/SportsHome.swift',lambda s:s.replace('Text("Set the court direction")','Text("1 · TV scan")').replace('Leave enough room to swing; no scan or code is needed.','Leave enough room to swing.').replace('        .task(id: onboarding.step.key) { onboarding.launchTutorialIfNeeded() }\n',''))
edit('GolfArcade/Unity/ClubScreens.swift',lambda s:s.replace('Button("Recalibrate aiming")','Button("Recenter racket")'))
edit('GolfArcade/Onboarding/GolfTutorialController.swift',lambda s:'''import SwiftUI

// Old saved tutorial routes use the normal controller now.
struct GolfTutorialController: View {
    @Bindable var session: SportsSession
    var body: some View { GolfPhoneController(session: session) }
}
''')
def native(s):
 s=s.replace('            public int tutorialStart;\n','')
 start=s.index('            // The tutorial\'s steps');end=s.index('            TennisGame.Landed +=',start)
 s=s[:start]+'''            TennisGame.RallyEnded+=shots=>Emit("rally",shots.ToString());
            GolfGame.NativeExitRequested+=GolfExit;
'''+s[end:]
 start=s.index('                    case "tutorialNext":');end=s.index('                    case "timingCheck":',start);s=s[:start]+'''                    case "controllerSetup": if(tennis) tennis.SetControllerSetup(m.value>0); break;
                    case "cancelTimingCheck": if(tennis) tennis.CancelTimingCheck(); break;
'''+s[end:]
 s=s.replace('case "toss": if(tennis)', 'case "toss": if(tennis && !paused && !tennis.ControllerSetup)')
 s=s.replace('TennisCoach.TipsEnabled=m.tips;', 'TennisCoach.TipsEnabled=false;')
 s=s.replace('                TennisTutorial.StartIndex = mode == TennisGame.Mode.Tutorial ? m.tutorialStart : 0;\n','')
 s=s.replace('            if(tennis) tennis.EquipEmotes(m.emotes);','            if(tennis) { tennis.EquipEmotes(m.emotes); tennis.SetControllerSetup(!m.bench && !multiplayerSession); }')
 return s
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs',native)
def game(s):
 s=s.replace('        public void StartTimingCheck()','''        public bool ControllerSetup { get; private set; }
        /// Keep the court visible but hold point play while the phone scans and calibrates.
        public void SetControllerSetup(bool active) {
            if (ControllerSetup == active) return;
            ControllerSetup = active;
            CancelTimingCheck();
            if (active && presentation) presentation.Skip();
            if (hud) hud.MatchVisible = !active;
            if (!active) Refeed();
        }

        public void StartTimingCheck()''',1)
 s=s.replace('            if (calibration != null) { TimingCheckSwing(); return; }','            if (calibration != null) { TimingCheckSwing(); return; }\n            if (ControllerSetup) return;',1)
 s=s.replace('''            int sets = 1, int games = TennisMatch.GamesToWin, string[] coachLines = null)
        {''','''            int sets = 1, int games = TennisMatch.GamesToWin, string[] coachLines = null)
        {
            if (mode == Mode.Tutorial) mode = Mode.Exhibition;''',1)
 s=s.replace('            if (mode == Mode.Tutorial) { if (!tutorial) tutorial = gameObject.AddComponent<TennisTutorial>(); tutorial.Begin(this, coach); }\n            else if (tutorial)', '            if (tutorial)')
 s=s.replace('if (mode == Mode.Training || mode == Mode.Tutorial) presentation.Finish();','if (mode == Mode.Training) presentation.Finish();')
 s=s.replace('''                if (calibration != null) TickTimingCheck();
                else if (hitStop''','''                if (calibration != null) TickTimingCheck();
                else if (ControllerSetup) { Player.Tick(Time.deltaTime, 0); Opponent.Tick(Time.deltaTime, 0); }
                else if (hitStop''',1)
 return s
edit('Unity/Assets/Scripts/Tennis/TennisGame.cs',game)
edit('Unity/Assets/Scripts/Tennis/TennisAbilities.cs',lambda s:s.replace('bool LiveAbilityInput =>', 'bool LiveAbilityInput => !ControllerSetup &&'))
(root/'work/controller-flow-fix/changes.json').write_text(json.dumps(files,indent=2))
print('\n'.join(files))
