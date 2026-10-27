import SwiftUI
import AVFoundation
import Darwin

/// `waiting`: online tennis, this player is set up and the match starts when the other player is too.
enum ControllerSetupStage { case scan, timing, ready, waiting, playing }

enum TennisUltimate: Int, CaseIterable, Identifiable {
    case skybreaker = 0, rescueLob = 1, curveball = 2
    var id: Int { rawValue }
    var title: String { switch self { case .skybreaker: "Skybreaker"; case .rescueLob: "Rescue Lob"; case .curveball: "Curveball" } }
    var detail: String { switch self {
    case .skybreaker: "Your next hit is a rocket: 30% faster, straight where you aim."
    case .rescueLob: "Your next hit floats sky-high and deep, buying time to get back in position."
    case .curveball: "Your next hit bends sideways in the air toward your aim side."
    } }
    var icon: String { switch self { case .skybreaker: "bolt.fill"; case .rescueLob: "arrow.up.forward.circle.fill"; case .curveball: "tornado" } }
}

@MainActor @Observable
final class SportsSession {
    static let shared = SportsSession()
    var players = PlayerRosterStore.load()
    var playerIndex = 0
    var sport = "golf"
    /// Unity's bowling state line (BowlingControllerState), 4 a second while bowling.
    var bowlingState = ""
    /// Bowling on this phone with no TV: the lane fills the screen under the controls (PLAN_PhonePlay_NoTV_GolfBowling.md).
    private(set) var phonePlay = false
    var lastPlayedSport: Sport {
        guard players.indices.contains(playerIndex) else { return .tennis }
        let id = players[playerIndex].id.uuidString
        let defaults = UserDefaults.standard
        let history = defaults.array(forKey: "sports.sessions.v1") as? [[String: Any]] ?? []
        let saved = defaults.string(forKey: "sports.lastSport.\(id)") ?? history.last(where: { $0["playerID"] as? String == id })?["sport"] as? String
        return Sport(rawValue: saved ?? "tennis") ?? .tennis
    }
    var menuPauseVisible = false
    var travel = 0.85
    var sound = (UserDefaults.standard.object(forKey:"range.soundEnabled") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(sound,forKey:"range.soundEnabled") }
    }
    /// Render at 120fps on ProMotion phones. Off by default: 60 is the guaranteed target,
    /// 120 is smoother where the phone can hold it.
    var highFrameRate = (UserDefaults.standard.object(forKey:"sports.highFrameRate") as? Bool) ?? false {
        didSet { UserDefaults.standard.set(highFrameRate,forKey:"sports.highFrameRate") }
    }
    var tennisCamera = UserDefaults.standard.string(forKey: "sports.tennisCamera") ?? "chase" {
        didSet { UserDefaults.standard.set(tennisCamera, forKey: "sports.tennisCamera") }
    }
    /// The in-match coaching cards (first serve, first backhand…).
    var coachingTips = (UserDefaults.standard.object(forKey:"sports.coachingTips") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(coachingTips,forKey:"sports.coachingTips") }
    }
    /// TVs that crop the picture's edges: shrink the menus and HUD by this fraction.
    var overscan = UserDefaults.standard.double(forKey:"sports.overscan") {
        didSet { UserDefaults.standard.set(overscan,forKey:"sports.overscan") }
    }
    /// Accessibility: larger text on the phone remote, and still frames instead of moving b-roll.
    var bigText = UserDefaults.standard.bool(forKey:"sports.bigText") {
        didSet { UserDefaults.standard.set(bigText,forKey:"sports.bigText") }
    }
    var reduceMotion = UserDefaults.standard.bool(forKey:"sports.reduceMotion") {
        didSet { UserDefaults.standard.set(reduceMotion,forKey:"sports.reduceMotion") }
    }
    var presentationIntros = UserDefaults.standard.string(forKey: "sports.presentationIntros") ?? "full" {
        didSet { UserDefaults.standard.set(presentationIntros, forKey: "sports.presentationIntros") }
    }
    private var rematchPresentation = false
    func prepareRematchPresentation() { rematchPresentation = true }
    func consumePresentationIntroCut() -> String {
        defer { rematchPresentation = false }
        return rematchPresentation && presentationIntros != "off" ? "short" : presentationIntros
    }
    var holeFlyover = (UserDefaults.standard.object(forKey: "sports.holeFlyover") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(holeFlyover, forKey: "sports.holeFlyover") }
    }
    var presentationBigMoments = (UserDefaults.standard.object(forKey: "sports.presentationBigMoments") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(presentationBigMoments, forKey: "sports.presentationBigMoments") }
    }
    /// A short loading transition, gated by actual runtime readiness.
    let loading = LoadingModel()
    let pointClips = PointClips()
    /// The tennis tutorial's current step, from Unity: (index, count, text).
    var finishedMatch: (won: Bool, score: String)?
    private var resultPresentationReady = true
    /// Unity's numbers for the match just finished (aces, winners, rally, timing...), for the XP screen.
    var lastMatchStats: MatchStats?
    var tutorialStep: (index: Int, count: Int, text: String)?
    /// Opponent strength for tennis: 0 relaxed, 0.45 standard, 0.8 tough.
    var tennisDifficulty = (UserDefaults.standard.object(forKey:"sports.tennisDifficulty") as? Double) ?? 0.45 {
        didSet { UserDefaults.standard.set(tennisDifficulty,forKey:"sports.tennisDifficulty") }
    }
    /// The court for tennis matches: "resort", "skyscraper" or "volcano" (Unity's TennisVenue keys).
    /// Picked on the map screen before each match and remembered for the next.
    /// The bowling centre last picked (BowlingVenueChoice: club, neon, tiki, magma).
    var bowlingVenue = BowlingVenueChoice(rawValue: UserDefaults.standard.string(forKey: "sports.bowlingVenue") ?? "")?.rawValue ?? "club" {
        didSet { UserDefaults.standard.set(bowlingVenue, forKey: "sports.bowlingVenue") }
    }
    /// Bowling exhibition's opponent (BowlingOpponent), the one last picked.
    var bowlingOpponent = BowlingOpponent(rawValue: UserDefaults.standard.integer(forKey: "sports.bowlingOpponent")) ?? .sam {
        didSet { UserDefaults.standard.set(bowlingOpponent.rawValue, forKey: "sports.bowlingOpponent") }
    }
    var tennisVenue = UserDefaults.standard.string(forKey: "sports.tennisVenue") ?? "resort" {
        didSet { UserDefaults.standard.set(tennisVenue, forKey: "sports.tennisVenue") }
    }
    /// The golf course: "cliffside", "wildisles" or "magma". A saved "postcards" (retired) loads as "cliffside".
    var golfCourse = MultiplayerLobby.currentGolfVenue(UserDefaults.standard.string(forKey: "sports.golfCourse") ?? "cliffside") {
        didSet { UserDefaults.standard.set(golfCourse, forKey: "sports.golfCourse") }
    }
    /// How long a golf round is: 0 plays the course's own holes (five or six); 9 or 18 go past them, on into the next courses
    /// when `golfLinkCourses` is on, else round the same course again (Unity's Course.Round). Set on the course screen or a
    /// lobby's Match Options, and remembered.
    var golfHoles = UserDefaults.standard.integer(forKey: "sports.golfHoles") {
        didSet { UserDefaults.standard.set(golfHoles, forKey: "sports.golfHoles") }
    }
    var golfLinkCourses = (UserDefaults.standard.object(forKey: "sports.golfLinkCourses") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(golfLinkCourses, forKey: "sports.golfLinkCourses") }
    }
    /// The round lengths the course screen steps through: the course's own, 9, 18.
    static let golfRoundLengths = [0, 9, 18]
    /// Golf's match setting, set before the round (the course screen, Settings → Gameplay) and remembered.
    /// (The round twists, two random modifiers dealt before the first tee, were taken out 10-27: no round has them.)
    /// A bounty on every hole, paying coins (and XP at the round's end).
    var golfChallenges = (UserDefaults.standard.object(forKey: "sports.golfChallenges.v2") as? Bool) ?? false {
        didSet { UserDefaults.standard.set(golfChallenges, forKey: "sports.golfChallenges.v2") }
    }
    /// Set by the `-benchTennis` launch argument: Unity plays itself and logs frame times.
    static let benchmark = ProcessInfo.processInfo.arguments.contains("-benchTennis") || ProcessInfo.processInfo.arguments.contains("-benchGolf")
    var haptics = (UserDefaults.standard.object(forKey:"arcade.hapticsEnabled") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(haptics,forKey:"arcade.hapticsEnabled") }
    }
    /// Settings → Controls → Swing prediction (on unless turned off): a strong swing counts the moment its rotation peaks
    /// (SteeringFilter.peakConfirm, read when the next match or court direction starts).
    var swingPrediction = (UserDefaults.standard.object(forKey:"sports.swingPrediction") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(swingPrediction,forKey:"sports.swingPrediction") }
    }
    /// Settings → Controls → 120 Hz swing input (on unless turned off): on a TV the match loop reads the swing at 120 Hz
    /// while the TV is still drawn at 60 (Unity InputRate).
    var fastInput = (UserDefaults.standard.object(forKey:"sports.fastInput") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(fastInput,forKey:"sports.fastInput") }
    }
    /// 120 only when it is on, this phone's panel reaches 120 (ProMotion) and Low Power Mode (which caps it at 60) is off.
    private var inputHz: Int {
        let panel = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }
            .first { $0.session.role == .windowApplication }?.screen.maximumFramesPerSecond ?? 60
        return fastInput && panel >= 120 && !ProcessInfo.processInfo.isLowPowerModeEnabled ? 120 : 60
    }
    /// How hard hits land in the hand, 0.55 soft .. 1 full (RacketFeel.strengths).
    var hapticStrength = (UserDefaults.standard.object(forKey:"arcade.hapticStrength") as? Double) ?? 1 {
        didSet { UserDefaults.standard.set(hapticStrength,forKey:"arcade.hapticStrength"); RacketFeel.apply(self) }
    }
    /// A short knock from the phone's own speaker on each hit (system sounds skip the AirPlay route, so it is on time).
    /// On unless turned off (latency plan P1: the hand and ears are the instant channel; the TV's sound is a TV delay late).
    var racketSound = (UserDefaults.standard.object(forKey:"arcade.racketSound") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(racketSound,forKey:"arcade.racketSound"); RacketFeel.apply(self) }
    }
    var status = "Connect a TV or Mac to play. This phone is your controller."
    var feedback = ""
    var ultimateChoice = TennisUltimate(rawValue: UserDefaults.standard.integer(forKey: "tennis.ultimate")) ?? .skybreaker
    var ultimateMeter = 0.0
    var ultimateArmed = false
    var diveCooldown = 0.0
    var canDive = false
    var canArmUltimate = false
    var loadoutLocked = false
    // Retained API for older callers; ultimates are no longer a gameplay action.
    func chooseUltimate(_ choice: TennisUltimate) {}
    func dive() { guard pointControlsVisible && canDive else { return }; command("dive"); canDive = false }
    func armUltimate() {}
    var stamina = 1.0
    var phase = "calibrating"
    var tracking: SportsTrackingQuality = .lost
    var trackingWarning = ""
    var setupStage: ControllerSetupStage = .scan
    var axisGate = SportsAxisGate()
    /// A motion-controlled match has no touches, so iOS would auto-lock the phone mid-point: stay awake while a session is active.
    var active = false { didSet { if active != oldValue { UIApplication.shared.isIdleTimerDisabled = active } } }
    var tennisControllerActive = false
    var paused = true { didSet { routeSamples() } }
    var ready = false
    var displayConnected = false {
        didSet {
            guard displayConnected != oldValue else { return }
            TennisMenu.shared.displayChanged(connected: displayConnected)
            // A tennis lobby needs a TV on one of its two phones, and shows who has it.
            MultiplayerService.shared.setScreen(displayConnected || Self.benchmark)
        }
    }
    /// For the racket controller: the scoreboard and where recent hits met the strings.
    var score = TennisScore()
    var contacts: [TennisContact] = []
    var opponentName = ""
    /// What the match is doing, from Unity, for the controller: "serve", "toss", "receive",
    /// "rally" or "point"; and which court a serve goes from.
    var tennisPhase = ""
    private(set) var matchEmotes = EmoteCatalog.defaults
    var emoteWindow = ""
    var emoteNotice = ""
    /// Tennis: celebrate a won point, or pick the intro emote while the intro plays ("intro").
    var canPlayEmote: Bool {
        active && ready && loading.finished && !paused && finishedMatch == nil && sport == "tennis"
        && setupStage == .playing && (emoteWindow == "point" || (emoteWindow == "intro" && ["intro", ""].contains(tennisPhase)))
    }
    /// Golf: the golfer up picks the emote they greet the gallery with while the hole's flyover plays.
    var canPickGolfIntroEmote: Bool {
        active && ready && loading.finished && !paused && finishedMatch == nil && sport == "golf" && golfPhase == "Intro" && emoteWindow == "intro"
    }
    /// The intro's flyover can be skipped (nil when not: the character intros always play). Online, everyone must ask:
    /// `voted` of `needed` have, `mine` when this phone has.
    struct IntroSkip: Equatable { var voted: Int; var needed: Int; var mine: Bool }
    var introSkip: IntroSkip?
    var pointControlsVisible: Bool {
        active && ready && loading.finished && !paused && setupStage == .playing
        && finishedMatch == nil && sport == "tennis"
        && ["serve", "toss", "receive", "rally"].contains(tennisPhase)
    }
    var tossVisible: Bool { pointControlsVisible && tennisPhase == "serve" }
    func playEmote(slot: Int) {
        guard canPlayEmote, matchEmotes.indices.contains(slot) else { return }
        command("emote", value: Double(slot))
        emoteWindow = ""
        emoteNotice = "\(EmoteCatalog.name(matchEmotes[slot])) selected"
    }
    var serveFromDeuce = true
    /// The controller serve's aim in the target box: across (T -1 .. wide +1), depth (0..1).
    var serveAim = (across: 0.0, depth: 0.8)
    var shotDepth=0.75
    var shotAim=0.0
    var aimLesson:TennisAimLesson?
    var aimLessonMessage=""
    private var aimChecked=false
    private var aimFeedSequence=0
    private var aimFeedAt=0.0
    private var aimWaiting=false
    private var aimSwing:TennisAimSwing?
    @ObservationIgnored private var aimFeedTask:Task<Void,Never>?
    @ObservationIgnored private var aimTimeoutTask:Task<Void,Never>?
    var aimingSetup:Bool { aimLesson != nil }
    /// Extra start fields for the tennis front end (mode, opponent, round).
    private var launchExtras: [String:Any] = [:]
    private(set) var multiplayerMatchID: String?
    #if DEBUG
    /// For tests: puts the session in (or takes it out of) an online match without a TV and a Unity runtime.
    func debugSetOnlineMatch(_ id: String?, seat: Int = -1) { multiplayerMatchID = id; multiplayerSeat = seat }
    #endif
    private(set) var multiplayerControllerOnly = false
    /// This phone's TV shows both players (one TV for two phones): the TV credit Unity gives its player goes to the lobby (screenLag).
    private var multiplayerSplit = false
    private var multiplayerSeat = -1
    /// The shared TV's delay the controller-only phone has already handed to Unity (so a change is applied once).
    private var appliedSharedDelay: Double?
    private var multiplayerSetupStarted = false
    var retainCourtDirectionForRematch = false
    var setupProblem = ""
    /// Setup belongs to this phone, independently of the opponent's renderer or connection. It starts once this phone's loading
    /// screen is gone, so the court is on the TV for the scan to find.
    var showsOnlineTennisSetup: Bool {
        active && multiplayerCalibrates && loading.finished && setupStage != .playing && finishedMatch == nil
    }
    private(set) var sessionID = ""
    /// Numeric stand-in for the session id on the binary sample channel.
    private var sessionToken: Int32 = 0
    private var pending: [String:Any]?
    private var timer: Timer?
    private var swingSequence = 0
    private var target = 0.0
    private var power = 0.0
    private var aim = 0.0
    /// How far the TV's picture lags the game (seconds), measured with the camera during
    /// setup and remembered for next time. 0 = never measured, so no compensation.
    var tvDelay = UserDefaults.standard.double(forKey:"sports.tv.delay.v1")
    var measuringDelay = false
    /// The timing check is running on the TV (swing with the bouncing ball).
    var checkingTiming = false
    /// The timing check is offered, not sprung: the phone explains it and waits for Start.
    var timingPrompt = false
    /// When the TV's get-ready countdown ends (the phone mirrors it).
    var timingCountdownEnds: Date?
    /// What the last timing check found, for the controller.
    var timingNote = ""
    private var checkTimingOnResume = false
    /// The timing check's result for the TV in use (seconds of lag from what the player sees
    /// to the swing registering): the whole chain, picture delay and swing detection alike.
    /// Kept per AirPlay receiver, since each TV has its own delay.
    var timingCalibration: Double? { SportsTiming.stored(for: SportsTiming.currentTV()) }
    /// The lag Unity should start from: the timing check, else the camera's measurement.
    var startingLag: Double { timingCalibration ?? tvDelay }
    /// Shown only when the measured delay is high enough that the TV is probably processing
    /// the picture: the one setting outside the app that helps most.
    var delayTip = ""
    private var flashDelays: [Double] = []
    private var flashProbeID = UUID()
    private static let flashes = 4, gameModeHint = 0.14
    private var nextDiagnostic=0.0
    let motion = SportsMotion()
    init() {
        UserDefaults.standard.removeObject(forKey: "sports.golfWeather.v2")
        UserDefaults.standard.removeObject(forKey: "sports.golfWeather")
        // The phone-preview benchmark plays without a TV, so for the lobby it counts as having one.
        if Self.benchmark { MultiplayerService.shared.setScreen(true) }
        motion.onAimSwing = { [weak self] swing in
            guard let self, self.aimWaiting, self.aimLesson != nil, swing.time >= self.aimFeedAt else { return }
            self.aimSwing=swing
        }
        if players.isEmpty { players=[Player(name:"Player 1",colorIndex:0)] }
        motion.onProblem = { [weak self] message in
            guard let self else { return }
            if self.showsOnlineTennisSetup { self.setupProblem = message; self.status = message }
            else { self.pause(reason: message); self.status = message }
        }
        motion.onGate = { [weak self] gate in
            guard let self, self.active, self.sport == "tennis", self.setupStage == .scan else { return }
            self.axisGate=gate
            if gate.locked {
                self.motion.start(tennis:true,travel:self.travel)
                if self.haptics { UINotificationFeedbackGenerator().notificationOccurred(.success) }
                self.scanFinished()
            }
        }
        // Unity gets every sample straight from the sensor queue; this is only for the screens.
        motion.onStatus = { [weak self] update in
            guard let self, self.active else { return }
            self.phase=update.phase; self.target=update.target
            let quality=update.quality
            self.tracking=quality
            // A blurred frame mid-swing warns and holds position; only a real outage pauses.
            switch quality {
            case .good: self.trackingWarning=""
            case .degraded: self.trackingWarning="Tracking degraded — keep the lens clear"
            case .lost where self.sport == "tennis":
                // Tennis needs the camera only for the lean hint: swings and aim run on the
                // motion sensors, so play goes on and steering simply holds.
                self.trackingWarning="Camera can't see the room — swings still count"
            case .lost:
                self.trackingWarning="Tracking lost"
                if self.ready && !self.paused {
                    self.status="Tracking lost — play paused. Keep the camera uncovered, then tap Ready."
                    self.pause(reason:self.status)
                }
            }
        }
    }
    /// Motion samples flow from the sensor queue straight to Unity while a session is playing.
    private func routeSamples() {
        motion.setOutput(token:sessionToken,live:active && !paused && (multiplayerMatchID == nil || multiplayerSeat >= 0),swingBase:swingSequence)
    }

    /// Time the TV: flash it black-then-white a few times while the camera still looks at it,
    /// and take the median delay. Unity then judges swings against what the player saw.
    func measureTVDelay() {
        guard active, ready, displayConnected, sport == "tennis", setupStage == .timing,
              !measuringDelay, !checkingTiming else { return }
        measuringDelay = true; timingPrompt = false; flashDelays = []; flashProbeID = UUID()
        let probeID = flashProbeID, launched = sessionID
        status = "Keep the rear camera aimed at the screen while it flashes."
        motion.setDelayProbe(true)
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .milliseconds(500))
            guard let self, self.active, self.sessionID == launched, self.flashProbeID == probeID, self.measuringDelay else { return }
            self.command("flash", value: Double(Self.flashes))
            try? await Task.sleep(for: .seconds(Double(Self.flashes) * 1.7 + 1.5))
            guard self.active, self.sessionID == launched, self.flashProbeID == probeID else { return }
            self.finishTVDelay()
        }
    }
    #if DEBUG
    /// Tests have no camera to time the screen flashes: end the measurement as if they were unclear.
    func debugFinishTVDelay() { finishTVDelay() }
    #endif
    private func flashShown(at rendered: Double) {
        guard measuringDelay else { return }
        let launched = sessionID, probeID = flashProbeID
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .milliseconds(1250))
            guard let self, self.active, self.sessionID == launched, self.flashProbeID == probeID, self.measuringDelay else { return }
            if let delay = self.motion.delayAfterFlash(rendered: rendered) { self.flashDelays.append(delay) }
        }
    }
    private func finishTVDelay() {
        guard measuringDelay else { return }
        measuringDelay = false; motion.setDelayProbe(false); timingPrompt = true
        if let delay = SportsDelayProbe.combine(flashDelays) {
            tvDelay = delay; SportsTiming.store(delay, for: SportsTiming.currentTV())
            timingNote = String(format: "Screen delay measured: %.0f ms. The swing check will verify your timing.", delay * 1000)
        } else {
            tvDelay = timingCalibration ?? 0
            timingNote = tvDelay > 0 ? "Flashes were unclear. Using this screen's last measurement; you can retry."
                : "Flashes were unclear. Point the rear camera at the screen and retry, or use the swing check."
        }
        command("latency", value: tvDelay)
        status = "Screen measurement finished. Start the swing timing check."
        delayTip = SportsTiming.advice(link: SportsTiming.currentLink(), delay: tvDelay, gameModeHint: Self.gameModeHint)
        SportsDiagnostics.write("tv link=\(SportsTiming.currentLink()) ports=\(AVAudioSession.sharedInstance().currentRoute.outputs.map { $0.portType.rawValue })")
        SportsDiagnostics.write("tv delay flashes=\(flashDelays.map { String(format: "%.3f", $0) }) chosen=\(tvDelay)")
    }
    func savePlayers() { PlayerRosterStore.save(players); HubSession.shared.lookChanged() }
    /// Start tennis from the front end: a campaign round against `opponent`, or training.
    func startTennis(opponent: TennisOpponent?, round: Int?, mode: String? = nil, difficulty: Double, coach: [String] = [], preview: Bool, sets: Int? = nil, games: Int? = nil) {
        let mode = mode == "tutorial" ? "exhibition" : mode
        sport = "tennis"
        opponentName = opponent?.name.components(separatedBy: " ").first ?? (mode == "tutorial" ? "Ray" : "Coach")
        launchExtras = ["mode": mode ?? (opponent == nil ? "training" : "campaign"), "opponent": opponent?.key ?? "",
                        "opponentName": opponentName, "round": opponent?.round ?? "", "difficulty": difficulty,
                        "sets": sets ?? opponent?.sets ?? 1, "games": games ?? opponent?.games ?? 3,
                        "coach": coach.joined(separator: "|")]
        start(preview: preview)
        launchExtras = [:]
    }
    /// Start a golf round; legacy tutorial requests use the same playable round.
    func startGolf(tutorial: Bool, preview: Bool, daily: Int? = nil) {
        sport = "golf"; opponentName = ""; lastGolfRound = nil
        // the day's forecast round has everything on, whatever the match settings say
        let daily = tutorial ? 0 : daily ?? 0
        let course = GolfCourseChoice(rawValue: golfCourse)?.rawValue ?? "cliffside"
        // (the lesson and the day's forecast are the course's own round; anything else is as long as the player chose)
        launchExtras = ["mode": "round", "course": tutorial || daily != 0 ? course : MultiplayerLobby.golfRound(course, holes: golfHoles, link: golfLinkCourses),
                        // (the lesson is plain golf, whatever the match settings say)
                        "noTwists": true,
                        "noChallenges": tutorial || (daily == 0 && !golfChallenges), "daily": daily]
        start(preview: preview)
        launchExtras = [:]
    }
    /// A lesson (PLAN_Onboarding_GolfLesson.md): Unity runs the sport's lesson from `station` and reports it ("lesson" events).
    func startLesson(_ sport: Sport, station: Int) {
        self.sport = sport.rawValue; opponentName = sport == .tennis ? "Ray" : ""; lastGolfRound = nil
        LessonCenter.shared.begin(sport)
        launchExtras = sport == .golf
            ? ["mode": "lesson", "course": "lesson", "noTwists": true, "noChallenges": true, "daily": 0, "lesson": true, "lessonStation": station]
            : ["mode": "lesson", "opponent": "", "opponentName": "Ray", "round": "", "difficulty": 0.1, "sets": 1, "games": 1, "coach": "",
               "lesson": true, "lessonStation": station]
        start(preview: false)
        launchExtras = [:]
    }
    /// Start bowling (PLAN_Bowling.md): one lane, these players taking turns frame by frame (pass the phone).
    func startBowling(players names: [String], preview: Bool) {
        sport = "bowling"; opponentName = ""; bowlingState = ""
        let names = names.isEmpty ? [players[min(playerIndex, players.count - 1)].name] : names
        launchExtras = ["mode": names.prefix(4).joined(separator: "|")]
        start(preview: preview)
        launchExtras = [:]
    }
    /// Settings → Controls: run the timing check at the start of the next match.
    func forceTimingCheckNextMatch() { checkTimingOnResume = true }
    func startMultiplayer(_ configuration: MultiplayerMatchConfiguration) {
        guard !active, let data=try? JSONEncoder().encode(configuration), let json=String(data:data,encoding:.utf8) else { return }
        multiplayerMatchID=configuration.matchID
        multiplayerControllerOnly=configuration.controllerOnly
        multiplayerSplit=configuration.sport == "tennis" && configuration.localView == .split
        multiplayerSeat=configuration.participants.first { $0.id == configuration.localID }?.seat ?? -1
        sport=configuration.sport; tennisVenue=configuration.venue
        if configuration.sport == "golf" { golfCourse=MultiplayerLobby.currentGolfVenue(MultiplayerLobby.golfRoundParts(configuration.venue).course) }
        launchExtras=["course":configuration.venue,"mode":"multiplayer", "network":json, "sets":configuration.sets, "games":configuration.games, "tips":false]
        start(preview: !displayConnected)
        launchExtras=[:]
        if !active { multiplayerMatchID=nil; multiplayerControllerOnly=false; multiplayerSplit=false }
        else {
            // (the court scan waits for the loading screen to finish: the camera has to see the court on the TV, see loadingFinished)
            // On a shared TV both players use the same display delay.
            if configuration.localView == .split, startingLag > 0 { MultiplayerService.shared.setScreenDelay(startingLag) }
        }
    }
    func start(preview: Bool = false) {
        guard !active else { return }
        guard multiplayerMatchID != nil || !MultiplayerService.shared.hasFriendsInLobby else { status = HubSession.soloLockMessage; return }
        SportsDisplays.shared.refresh()
        let preview = Self.benchmark && !displayConnected
        NSLog("[SportsSession] launch sport=%@ mode=%@",sport,preview ? "phone-preview" : "external-controller")
        // From a bay in the Plaza (PLAN_MenuHub_WalkableWorld §5): the match loads behind the plaza while you sit, no TV cover.
        let bay = Self.benchmark || multiplayerControllerOnly ? nil : HubSession.shared.bayForLaunch()
        // bowling never needs a TV: with none, it plays on this phone (golf and tennis still ask for one)
        let phoneGame = sport == "bowling" && !displayConnected && !Self.benchmark && bay == nil
        guard let window = phoneGame ? SportsDisplays.shared.phonePlayWindow() : bay != nil ? SportsDisplays.shared.external : Self.benchmark ? SportsDisplays.shared.benchmarkWindow() : multiplayerControllerOnly ? SportsDisplays.shared.multiplayerControllerWindow() : SportsDisplays.shared.gameWindow(preview:preview) else {
            status="Connect a TV or Mac with AirPlay or a wired display to play. This phone is your controller."; return
        }
        phonePlay = phoneGame
        HubSession.shared.runtimeTaken(bay: bay)   // the match scene replaces the Plaza (behind it, from a bay)
        // the menu's heroes are off screen for the whole match: let their decoded meshes go (the menu decodes them again)
        MatchHeroData.releaseCache()
        SportsDiagnostics.write("launch \(sport) bay=\(bay ?? "none") \(SportsDiagnostics.memory)")
        savePlayers(); sessionID=UUID().uuidString; sessionToken=Int32.random(in:1...Int32.max); ready=false; paused=true; active=true; tennisControllerActive=false
        aimFeedTask?.cancel(); aimTimeoutTask?.cancel(); aimLesson=nil; aimChecked=false; aimWaiting=false; aimSwing=nil; shotAim=0; shotDepth=0.75
        resultPresentationReady = true; finishedMatch=nil; lastMatchStats=nil; swingSequence=0; target=0; power=0; aim=0; measuringDelay=false; delayTip=""; checkingTiming=false; timingPrompt=false; timingNote=""
        tvDelay = timingCalibration ?? 0; appliedSharedDelay = nil
        golfController = .waiting; golfControllerMap = nil
        setupStage = .scan; axisGate = SportsAxisGate(); phase="calibrating"; feedback=""; golfPhase=""; golfHasNextHole=false; golfShotReady=false; golfSwingState=0; golfTap=GolfTapSwing(); stamina=1
        multiplayerSetupStarted = false; setupProblem = ""
        ultimateMeter=0; ultimateArmed=false; diveCooldown=0; canDive=false; canArmUltimate=false; loadoutLocked=false
        let p=players[min(playerIndex,players.count-1)]
        UserDefaults.standard.set(sport, forKey: "sports.lastSport.\(p.id.uuidString)")
        matchEmotes = p.equippedEmotes; emoteWindow = ""; emoteNotice = ""; tennisPhase = ""; introSkip = nil
        if let network = launchExtras["network"] as? String, let data = network.data(using: .utf8),
           let configuration = try? JSONDecoder().decode(MultiplayerMatchConfiguration.self, from: data),
           let local = configuration.participants.first(where: { $0.id == configuration.localID }) {
            matchEmotes = EmoteCatalog.normalized(local.loadout?.emotes)
        }
        motion.setAimProfile(storedAimProfile())
        pending=["holeFlyover":holeFlyover,"intros":consumePresentationIntroCut(),"bigMoments":presentationBigMoments,"presentationConstrained":reduceMotion || ProcessInfo.processInfo.thermalState == .serious || ProcessInfo.processInfo.thermalState == .critical,"version":1,"session":sessionID,"action":"start","sport":sport,"playerID":p.id.uuidString,"playerName":p.name,"female":p.standardFemale,"skin":p.standardSkin,"left":p.handedness == .left,"sound":sound && !(multiplayerControllerOnly && (sport == "tennis" || !displayConnected)),"haptics":haptics,"touch":preview,"token":Int(sessionToken),"fps":highFrameRate ? 120 : 60,"inputHz":inputHz,"bench":SportsSession.benchmark,"difficulty":tennisDifficulty,"venue":sport == "tennis" ? tennisVenue : sport == "bowling" ? bowlingVenue : "resort",
                 "shirt":p.outfitHex("shirt") ?? "","shorts":p.outfitHex("shorts") ?? "","accent":p.outfitHex("accent") ?? "","racket":p.outfitHex("racket") ?? "",
                 "skinHex":p.skinHex,"hairHex":p.hairHex,
                 "tips":false,"overscan":overscan,"tennisCamera":tennisCamera,
                 "hairStyle":p.hairStyle,"haircut":p.shownHaircut,"hairColor":p.hairColor,"faceShape":p.faceShape,
                 "heightChoice":p.heightChoice,"buildChoice":p.buildChoice,"bodySize":p.bodySize,
                 "loadout":p.loadoutPayload(sport:Sport(rawValue:sport) ?? .tennis)]
        runtimeExternalDisplay = displayConnected
        pending?["external"] = runtimeExternalDisplay
        pending?["emotes"] = matchEmotes
        for (key, value) in launchExtras { pending?[key] = value }
        // from the pointer menu: the match loads under the loading screen and starts as soon as it is built (no START to press: a
        // party's guests tap Ready before the launch, on their phones)
        let fromMenu = bay != nil && HubSession.shared.menuMode
        // Only a walkable-Plaza bench builds the match behind the plaza (the plaza stays on the TV, no cover). Under the menu's
        // loading cover nobody sees the plaza, and keeping it loaded while the round builds is what got the app killed for memory
        // (10-26 20:39, party golf at Cliffside: JETSAM per-process limit at the end of the load): the scene swaps instead.
        if let bay { pending?["seamless"] = !fromMenu; pending?["bay"] = bay }
        if fromMenu { pending?["menuLabel"] = HubSession.shared.menuLaunchLabel }
        if Self.benchmark {
            // Verification flags affect this explicit benchmark launch only;
            // they do not save frame-rate, venue, or character preferences.
            let args = ProcessInfo.processInfo.arguments
            func value(_ flag: String) -> String? {
                guard let index = args.firstIndex(of: flag), index + 1 < args.count else { return nil }
                return args[index + 1]
            }
            if let fps = value("--visual-fps").flatMap(Int.init), [60, 120].contains(fps) { pending?["fps"] = fps }
            if let venue = value("--visual-venue"), ["resort", "skyscraper", "volcano"].contains(venue) { pending?["venue"] = venue }
            if sport == "golf", let course = value("--visual-course"), GolfCourseChoice.allCases.map(\.rawValue).contains(course) { pending?["course"] = course }
            if args.contains("--visual-female") { pending?["female"] = true }
            if sport == "tennis" && !args.contains("--postgame-check") {
                // Keep the real scoring match active throughout sustained performance capture.
                pending?["sets"] = 3; pending?["games"] = 6
            }
        }
        // Explicit device verification uses a real, short match (no fabricated finish event).
        if Self.benchmark && ProcessInfo.processInfo.arguments.contains("--postgame-check") {
            pending?["sets"] = 1; pending?["games"] = 1
        }

        score = TennisScore(); contacts = []; tutorialStep = nil
        loading.begin(now: LoadingModel.clockNow, multiplayer: multiplayerMatchID != nil)
        loading.onFinish = { [weak self] in self?.loadingFinished() }
        // never put a TV loading window over the controller-only phone; a walkable-Plaza bench loads behind the plaza with none
        if (bay != nil && !fromMenu) || (multiplayerCalibrates && multiplayerControllerOnly) { loading.cardAppeared(); loadCoveredRuntime(in: window) }
        else { SportsDisplays.shared.beginLoadingCover(in: window) { [weak self] in self?.loadCoveredRuntime(in: window) } }
    }
    private func loadCoveredRuntime(in window: UIWindow) {
        do { try SportsRuntime.shared().load(in:window,controllerReplica:multiplayerControllerOnly) }
        catch { failStartup(error.localizedDescription); return }
        RacketFeel.apply(self)
        SportsRuntime.shared().clearTennisResult()
        SportsDisplays.shared.restorePhoneControls()
        SportsRuntime.shared().pause(false)
        status="Loading Unity…"
        timer?.invalidate()
        timer=Timer(timeInterval:1.0/60,repeats:true) { [weak self] _ in
            MainActor.assumeIsolated { self?.poll() }
        }
        if let timer { RunLoop.main.add(timer, forMode: .common) }
        // A persistent runtime is already ready after the first launch.
        sendPending()
        let launchingSession=sessionID
        Task { @MainActor [weak self] in
            try? await Task.sleep(for:.seconds(20))
                guard let self, self.sessionID == launchingSession, self.active, !self.ready, self.pending != nil else { return }
            if self.multiplayerMatchID == nil { self.loading.fail("The venue could not finish loading. Retry or leave the match.") }
            // Multiplayer retains its cover and offers a shared Keep waiting / Leave choice.
        }
    }
    func failStartup(_ message: String) {
        SportsDiagnostics.write("startup failed: \(message)")
        end()
        status = message
        TennisMenu.shared.launchFailed(message)
    }
    private func sendPending() {
        guard let pending else { return }
        sendJSON(pending)
    }
    private func sendJSON(_ object:[String:Any]) {
        guard let data=try? JSONSerialization.data(withJSONObject:object),let text=String(data:data,encoding:.utf8) else { return }
        SportsRuntime.shared().send(text)
    }
    func command(_ action:String, value:Double=0, value2:Double=0) {
        guard active else { return }
        NSLog("[SportsSession] command=%@ value=%.2f",action,value)
        sendJSON(["version":1,"session":sessionID,"action":action,"value":value,"value2":value2])
    }

    private var aimProfileKey:String {
        let player=players[min(playerIndex,players.count-1)]
        return "tennis.aim.v1.\(player.id.uuidString).\(player.handedness == .left ? "left" : "right")"
    }
    private func storedAimProfile() -> TennisAimProfile? {
        guard !players.isEmpty, let data=UserDefaults.standard.data(forKey:aimProfileKey),
              let profile=try? JSONDecoder().decode(TennisAimProfile.self,from:data), profile.valid else { return nil }
        return profile
    }
    /// Court scanning finishes before timing. The match remains held until Ready.
    func offerTimingCalibration() {
        guard active, ready, loading.finished, sport == "tennis" else { return }
        // An online match has no timing check: Unity ignores `timingCheck` in a network match, so the screens below could never finish
        // (the phone would sit on "Swing on every bounce!" with no ball while the other player waits). It also sends a pause, which
        // starts the owner's 15 s forfeit clock if the match is running. "Use the direction I'm pointing now" and "Re-check swing
        // timing" both end up here, so online they go from the court scan straight to Ready.
        if multiplayerMatchID != nil {
            if setupStage == .scan { multiplayerScanComplete() }
            return
        }
        setupStage = .timing; timingPrompt = true; checkingTiming = false
        menuPauseVisible = false; measuringDelay = false
        status = "TV scan complete. Calibrate your swing timing on the TV."
        command("cancelTimingCheck"); command("controllerSetup", value: 1)
        pause(reason: status)
        SportsDisplays.shared.external?.isHidden = true
        measureTVDelay()
    }
    func skipTimingCheck() {
        guard setupStage == .timing else { return }
        command("cancelTimingCheck")
        completeTimingCalibration(message: timingCalibration == nil ? "The game will refine your timing as you play." : "Using the saved timing for this screen.")
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
        SportsDiagnostics.write("timing check tv=\(SportsTiming.currentTV()) result=\(message)")
        completeTimingCalibration(message: note)
    }
    /// Recenter the racket without entering the retired aiming lesson.
    func recalibrateAiming() {
        guard active, ready, motion.axisLocked, motion.calibrate() else { return }
        phase = "steering"; command("recalibrate")
        pause(reason: "Center set. Tap Ready to continue.")
    }

    // MARK: Controller serve

    /// TOSS pressed. The game judges it against the toss meter under the player's feet on the
    /// TV, as the player saw it then (value -1: "read your meter").
    func toss() {
        guard tossVisible else { return }
        sendJSON(["version":1,"session":sessionID,"action":"toss","value":-1])
    }
    func setServeAim(across: Double, depth: Double) {
        serveAim=(max(-1,min(1,across)),max(0,min(1,depth)))
        guard active else { return }
        sendJSON(["version":1,"session":sessionID,"action":"serveAim","value":serveAim.across,"value2":serveAim.depth])
    }
    /// Walk along the baseline before a serve: -1 left, 0 stop, 1 right (held buttons).
    func nudge(_ direction: Double) { command("nudge",value:direction) }

    func pause(reason:String="Paused on phone — tap Ready to continue") {
        guard active else { return }
        if checkingTiming {
            command("cancelTimingCheck"); checkingTiming = false; timingPrompt = true; timingCountdownEnds = nil
        }
        SportsDiagnostics.write("pause reason=\(reason) phase=\(phase)")
        sendJSON(["version":1,"session":sessionID,"action":"pause","reason":reason]); paused=true; status=reason
        if reason == "Paused on phone — tap Ready to continue", ready, loading.finished, finishedMatch == nil {
            menuPauseVisible = true
            if sport != "golf" { SportsDisplays.shared.showMenu(); if !displayConnected { SportsDisplays.shared.showMatchControls() } }
        }
    }
    func resume() {
        guard displayConnected || multiplayerControllerOnly || phonePlay else { pause(reason: "Reconnect your TV or Mac to continue."); return }
        guard sport != "tennis" || setupStage == .playing else { status = "Finish TV scan and timing calibration, then tap Ready."; return }
        guard ready, phase == "steering" else { status="Tap Ready to set your center and play."; return }
        menuPauseVisible = false; SportsDisplays.shared.external?.isHidden = true
        if !displayConnected && !phonePlay { SportsDisplays.shared.restorePhoneControls() }
        command("resume"); paused=false; status="Playing"; if sport == "tennis" { loadoutLocked=true }
        if sport == "tennis" { tennisControllerActive=true }
        SportsDiagnostics.write("resume phase=\(phase) target=\(target)")
    }
    func readyToPlay() {
        if showsOnlineTennisSetup { finishMultiplayerCalibration(); return }
        // bowling with no TV plays on this phone (phonePlay): it is its own display
        guard displayConnected || multiplayerControllerOnly || phonePlay, active, ready, loading.finished else { return }
        if multiplayerCalibrates { finishMultiplayerCalibration(); return }
        if sport == "tennis", setupStage == .scan || setupStage == .timing {
            menuPauseVisible = false; SportsDisplays.shared.external?.isHidden = true
            status = setupStage == .scan ? "Scan your TV to continue." : "Start the timing calibration to continue."
            return
        }
        if sport == "golf" {
            phase = "steering"; setupStage = .playing
            sendGolfReady("recalibrate")
            resume()
            return
        }
        guard sport != "tennis" || motion.axisLocked else { return }
        // bowling reads its swing from the moment the ball is held, not from this centre: a phone that is not held still yet must not keep it paused
        guard motion.calibrate() || sport == "bowling" else { return }
        phase = "steering"
        if sport == "golf" { sendGolfReady("recalibrate") } else { command("recalibrate") }
        setupStage = .playing
        command("controllerSetup", value: 0)
        resume()
    }
    /// Unity renders the timing ball on the TV; motion samples keep flowing from the phone.
    func startTimingCheck() {
        guard active, ready, loading.finished, displayConnected, sport == "tennis",
              setupStage == .timing, !checkingTiming, !measuringDelay else { return }
        guard motion.axisLocked, motion.calibrate() else { return }
        phase = "steering"
        menuPauseVisible = false; SportsDisplays.shared.external?.isHidden = true
        command("controllerSetup", value: 1)
        command("resume"); paused = false
        timingPrompt = false; checkingTiming = true; timingNote = ""
        timingCountdownEnds = Date().addingTimeInterval(5)
        status = "Swing with the bouncing ball on your TV."
        command("timingCheck")
    }
    func recheckTiming() {
        guard multiplayerMatchID == nil else { return }   // the timing check is solo only: its commands are not passed on in a match
        guard motion.axisLocked else { beginAxisCapture(); return }
        offerTimingCalibration()
    }
    /// Locking the court direction is a separate, gated step. Once it is done the phone can
    /// be held at any angle — which is the whole point, since forehands and backhands flip it.
    func beginAxisCapture() {
        if sport == "tennis" {
            aimFeedTask?.cancel(); aimTimeoutTask?.cancel(); aimLesson=nil; aimWaiting=false; aimSwing=nil; aimChecked=false
        }
        setupStage = .scan; timingPrompt = false; checkingTiming = false
        command("cancelTimingCheck"); command("controllerSetup", value: 1)
        pause(reason: "Scan your TV to set the court direction.")
        axisGate=SportsAxisGate()
        status="Stand about 2.5 m back, point the back of your phone at the TV and hold still."
        motion.beginAxisCapture(travel:travel)
    }
    /// Escape hatch when the gate will not settle, so motion tennis is never unreachable.
    func useCurrentDirection() {
        guard motion.forceAxisFromCurrentPose() else { return }
        motion.start(tennis:true,travel:travel)
        scanFinished()
    }
    func retryCourtDirection() {
        guard active, sport == "tennis" else { return }
        setupStage = .scan; axisGate = SportsAxisGate(); setupProblem = ""
        status = "Point the back of your phone at the TV and hold still."
        MultiplayerService.shared.runtimeSetupStep("direction")
        motion.beginAxisCapture(travel: travel)
    }
    /// The court direction is locked (by the scan, or by "use the direction I'm pointing now"). Solo play goes on to the timing check;
    /// online tennis has no timing check yet, so it goes straight to Ready.
    private func scanFinished() {
        guard setupStage == .scan else { return }
        if multiplayerMatchID != nil { multiplayerScanComplete() } else { offerTimingCalibration() }
    }
    /// One tap to mirror steering, for when left and right come out swapped.
    func flipSteering() {
        motion.courtSign = -motion.courtSign
        status=motion.courtSign<0 ? "Steering flipped. Tap Ready to recenter." : "Steering restored. Tap Ready to recenter."
    }
    func setAim(_ value:Double) { if sport == "tennis" { setShotAim(across:value,depth:shotDepth) } else { command("aim",value:value) } }
    /// The swing button tapped: starts the swing at once, or cancels the one under way. Unity takes the
    /// grip from the phone as it settles from the tap, not from this touch.
    func tapGolfSwing() {
        let canArm = active && sport == "golf" && ready && !paused && golfPhase == "Aim" && golfShotReady
        switch golfTap.tap(canArm: canArm, now: ProcessInfo.processInfo.systemUptime) {
        case .start?:
            command("golfStartSwing")
            if haptics { UIImpactFeedbackGenerator(style: .medium).impactOccurred() }
        case .cancel?: command("golfReleaseSwing")
        case nil: break
        }
    }
    private func observeGolfTap() {
        switch golfTap.observe(phase: golfPhase, shotReady: golfShotReady, unityState: golfSwingState, now: ProcessInfo.processInfo.systemUptime) {
        case .reset?: if haptics { UINotificationFeedbackGenerator().notificationOccurred(.warning) }
        case nil: break
        }
    }
    /// A direction in the phone course map: +x right, +y toward the top of the map.
    func aimGolf(across: Double, forward: Double) {
        guard active, sport == "golf", ready, !paused, golfPhase == "Aim" || golfMenuOpen,
              across.isFinite, forward.isFinite else { return }
        sendJSON(["version":1,"session":sessionID,"action":"golfAimDirection",
                  "value":max(-1,min(1,across)),"value2":max(-1,min(1,forward))])
    }
    func setShotAim(across:Double,depth:Double) {
        shotAim=max(-1,min(1,across)); shotDepth=max(0,min(1,depth)); aim=shotAim
        sendJSON(["version":1,"session":sessionID,"action":"rallyAim","value":shotAim,"value2":shotDepth])
    }
    func setShotDepth(_ depth:Double) { setShotAim(across:shotAim,depth:depth) }
    func setPointRecording(_ enabled: Bool) {
        guard active, ready, sport == "tennis", finishedMatch == nil else { return }
        pointClips.bufferingEnabled = enabled
        pointClips.state = enabled ? "checking" : "off"
        pointClips.message = enabled
            ? (paused ? "Resume play to check 1080p · 60 fps." : "Checking 1080p · 60 fps…")
            : "Point buffering off."
        command("recordPoints", value: enabled ? 1 : 0)
    }

    // MARK: Online tennis setup

    /// An online or Nearby tennis player (not a spectator): their phone is set up before the match starts.
    private var multiplayerCalibrates: Bool { multiplayerMatchID != nil && sport == "tennis" && multiplayerSeat >= 0 }
    /// Point the phone at the TV (so swings count), then Ready.
    private func beginMultiplayerCalibration() {
        guard !multiplayerSetupStarted else { return }
        multiplayerSetupStarted = true
        paused = true
        if motion.hasUsableCourtDirection {
            motion.start(tennis: true, travel: travel)
            multiplayerScanComplete()
            status = "Your direction is still set. Tap Ready to set your centre again."
            return
        }
        setupStage = .scan; axisGate = SportsAxisGate()
        status = "Point the back of your phone at your TV. Hold still for one second."
        MultiplayerService.shared.runtimeSetupStep("direction")
        motion.beginAxisCapture(travel: travel)
    }
    /// The court direction is locked. Online tennis has no timing check yet, so it goes straight to Ready.
    private func multiplayerScanComplete() {
        setupStage = .ready; setupProblem = ""
        status = "Direction set. Stand where you'll play, then tap Ready."
        MultiplayerService.shared.runtimeSetupStep("ready")
    }
    /// Ready was tapped: take the centre, tell the owner, then wait for the others.
    /// When play is already running (the player came back mid-match, or re-aimed from the menu) it carries straight on.
    private func finishMultiplayerCalibration() {
        guard setupStage == .ready else { return }
        guard motion.axisLocked, motion.calibrate() else { return }
        MultiplayerService.shared.runtimeCalibrated()
        menuPauseVisible = false; SportsDisplays.shared.external?.isHidden = true
        setupStage = .waiting; status = "Ready. Waiting for the other player."
        SportsDiagnostics.write("online setup complete session=\(sessionID) runtimeReady=\(ready)")
    }
    /// The owner has started play. Take the centre again, since the player may have moved while waiting, and let go.
    private func beginMultiplayerPlay() {
        let service = MultiplayerService.shared
        guard setupStage == .waiting, ready, loading.finished, service.scheduledRunAt > 0,
              service.networkTime >= service.scheduledRunAt else { return }
        motion.calibrate(quiet: true)
        setupStage = .playing; paused = false; menuPauseVisible = false; status = "Playing"
        SportsDisplays.shared.external?.isHidden = true
        command("resume")
    }

    /// The loading screen has run its course: show the game, and start the setup that the
    /// player sees (court direction, motion) only now.
    private func loadingFinished() {
        guard active, ready else { return }
        SportsDisplays.shared.finishLoadingCover()
        SportsDiagnostics.write("loaded \(sport) \(SportsDiagnostics.memory)")
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("presentation/\(sessionID)", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        if let data = try? JSONSerialization.data(withJSONObject: loading.timing, options: [.prettyPrinted, .sortedKeys]) {
            try? data.write(to: directory.appendingPathComponent("L1_load_timing.json"), options: .atomic)
        }
        if displayConnected { SportsDisplays.shared.external?.isHidden=true }
        else if phonePlay { SportsDisplays.shared.showPhonePlay() }
        else { SportsDisplays.shared.restorePhoneControls() }
        // Compensate from the first point with the last measurement of this TV; the
        // setup re-times it when the camera is aimed at it.
        if displayConnected && startingLag>0 { command("latency",value:startingLag) }
        if multiplayerMatchID != nil {
            guard SportsRuntime.shared().multiplayerAvailable() else {
                MultiplayerService.shared.runtimeUnavailable("This Unity export does not contain multiplayer. Re-export and rebuild the integrated app.")
                return
            }
            // Tennis players first point their phone at the TV and tap Ready; the owner starts the match when all have.
            if multiplayerCalibrates { beginMultiplayerCalibration(); return }
            setupStage = .playing; paused=false; status=multiplayerSeat<0 ? "Watching" : "Playing"
            if multiplayerSeat>=0 { motion.start(tennis:sport == "tennis",travel:travel) }
            command("resume"); return
        }
        if Self.benchmark {
            SportsBenchmarkThermals.start(sport: sport)
            setupStage = .playing; paused = false; menuPauseVisible = false
            if sport == "golf" { sendGolfReady("recalibrate") }
            command("controllerSetup", value: 0); command("resume")
            SportsDisplays.shared.external?.isHidden = true
            status = "Automated device verification"
            return
        }
        if sport == "tennis" {
            beginAxisCapture()
        } else {
            motion.start(tennis:false,travel:travel)
            readyToPlay()
        }
    }
    private func recordPresentationEvent(_ event: [String: Any]) {
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("presentation/\(sessionID)", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let path = directory.appendingPathComponent("beat_events.jsonl")
        guard let data = try? JSONSerialization.data(withJSONObject: event, options: .sortedKeys) else { return }
        if !FileManager.default.fileExists(atPath: path.path) { FileManager.default.createFile(atPath: path.path, contents: nil) }
        if let file = try? FileHandle(forWritingTo: path) { defer { try? file.close() }; try? file.seekToEnd(); try? file.write(contentsOf: data + Data([10])) }
    }
    /// Completion is part of every Unity heartbeat, independently of one-shot result events.
    func receiveMatchSnapshot(_ event: [String: Any]) {
        guard event["presentationResultReady"] as? Bool != false, event["matchComplete"] as? Bool == true,
              let won = event["matchWon"] as? Bool else { return }
        receiveMatchFinish(won: won, score: event["finalScore"] as? String ?? "")
    }

    func receiveMatchFinish(won: Bool, score: String) {
        guard active, finishedMatch == nil else { return }
        finishedMatch = (won, score)
        SportsDiagnostics.write("match finished: phone Next enabled; classic=\(TennisMenu.shared.classic) external=\(displayConnected)")
        motion.stop()
        TennisMenu.shared.matchFinished(won: won, score: score)
        // Keep explicit phone actions visible until the player chooses one.
        canDive = false
        timingPrompt = false; checkingTiming = false; measuringDelay = false
        aimFeedTask?.cancel(); aimTimeoutTask?.cancel(); aimLesson=nil; aimWaiting=false
        SportsDisplays.shared.showMatchControls()
        if Self.benchmark {
            Task { @MainActor in
                try? await Task.sleep(for: .seconds(1))
                SportsDisplays.shared.captureBenchmarkFinish()
            }
        }
    }

    func advanceAfterMatch(_ choice: TennisMenu.AfterMatch = .menu) {
        guard active, finishedMatch != nil else {
            SportsDiagnostics.write("postMatch ignored: active=\(active) finished=\(finishedMatch != nil)")
            return
        }
        SportsDiagnostics.write("postMatch tapped: \(choice) mode=\(TennisMenu.shared.launch?.mode.rawValue ?? "none") round=\(TennisMenu.shared.launch?.round ?? -1)")
        TennisMenu.shared.finishMatch(choice)
    }

    /// A result screen with buttons is on the TV: the shot's result (its emotes and NEXT SHOT), the hole's end, the round's end.
    /// (Not a multiplayer round's, where the lobby owns what comes next.)
    var golfMenuOpen: Bool { active && sport == "golf" && multiplayerMatchID == nil && ["Result", "HoleDone", "RoundDone"].contains(golfPhase) }
    /// The pad's centre: tap whichever TV button the ring is on.
    func selectGolfMenu() {
        guard golfMenuOpen, !paused else { return }
        command("golfSelect")
        if haptics { UIImpactFeedbackGenerator(style: .light).impactOccurred() }
    }

    func continueGolfRound() {
        guard active, sport == "golf", golfPhase == "RoundDone", multiplayerMatchID == nil else { return }
        if golfHasNextHole { command("golfContinue") }
        // the round's over: its XP (banked when Unity reported the round) on the rewards screen
        else if TennisMenu.shared.postMatch?.golf != nil { TennisMenu.shared.beginPostMatch() }
        else { TennisMenu.shared.finishMatch(.replay) }
    }
    /// The last golf round's tally, as Unity reported it.
    var lastGolfRound: GolfRoundStats?

    func showMatchRewards() {
        guard active, finishedMatch != nil else { return }
        TennisMenu.shared.beginPostMatch()
    }

    private func sendGolfReady(_ action: String) {
        guard active else { return }
        var message: [String: Any] = ["version": 1, "session": sessionID, "action": action]
        if let grip = motion.golfReadyGrip() {
            message["hasReadyPose"] = true
            message["qx"] = grip.x; message["qy"] = grip.y; message["qz"] = grip.z; message["qw"] = grip.w
        }
        sendJSON(message)
    }
    var golfShotReady = false
    /// Motion golf reads a swing only after the swing button is tapped: 0 not armed, 2 swinging (tap again
    /// to cancel). Unity owns it and reports it.
    var golfSwingState = 0
    /// The phone's side of tap to swing: the tap, and what Unity has said about it.
    var golfTap = GolfTapSwing()
    var golfController = GolfControllerReading.waiting
    var golfControllerMap: UIImage?
    var golfPhase = ""
    var golfHasNextHole = false
    private var runtimeExternalDisplay = false
    /// A display can arrive after a phone game has begun, including while it is loading.
    func routeGameToExternalDisplay() {
        guard active, ready, let window = SportsDisplays.shared.external else { return }
        runtimeExternalDisplay = true
        SportsRuntime.shared().attach(to: window)
        command("display")
        SportsDisplays.shared.endPreview()
        SportsDisplays.shared.restorePhoneControls()
        status = "Display connected. Waiting for a gameplay frame…"
    }
    func exitGame() {
        // an online match: back to the Plaza (a party goes back to its bench together)
        if multiplayerMatchID != nil { HubSession.shared.leaveOnlineMatch() }
        else if OnboardingFlow.shared.active { OnboardingFlow.shared.gameLeft() }
        else { TennisMenu.shared.goHome() }
    }
    func end() {
        if active { SportsDisplays.shared.beginExitCover() }
        menuPauseVisible = false
        if active && ready {
            var history=UserDefaults.standard.array(forKey:"sports.sessions.v1") as? [[String:Any]] ?? []
            history.append(["session":sessionID,"sport":sport,"playerID":players[playerIndex].id.uuidString,"endedAt":Date().timeIntervalSince1970,"summary":feedback])
            UserDefaults.standard.set(Array(history.suffix(100)),forKey:"sports.sessions.v1")
        }
        pointClips.reset()
        HubSession.shared.sessionEnded(finished: finishedMatch != nil || multiplayerMatchID != nil)   // a party comes back to its bay together
        multiplayerMatchID=nil; multiplayerSeat = -1; multiplayerControllerOnly=false; multiplayerSplit=false
        if phonePlay { phonePlay = false; SportsDisplays.shared.endPhonePlay() }
        if unityControllerShown { unityControllerShown = false; SportsRuntime.shared().showUnity(onPhone: false) }
        command("end")
        if retainCourtDirectionForRematch, sport == "tennis" {
            let ended = sessionID
            // The immediate rematch keeps the live tracking origin. If it never arrives, release the sensors.
            Task { @MainActor [weak self] in
                try? await Task.sleep(for: .seconds(10))
                guard let self, !self.active, self.sessionID == ended else { return }
                self.motion.stop()
            }
        } else { motion.stop() }
        retainCourtDirectionForRematch = false; multiplayerSetupStarted = false
        timer?.invalidate(); timer=nil; pending=nil; measuringDelay=false; checkingTiming=false
        loading.cancel(); tutorialStep=nil; finishedMatch=nil; timingPrompt=false; setupStage = .scan
        SportsRuntime.shared().pause(true); active=false; ready=false; paused=true; tennisControllerActive=false
        SportsDisplays.shared.endPreview(); status="Choose a sport."
        SportsDisplays.shared.showMenu()
        TennisMenu.shared.sessionEnded()
    }
    /// Golf as it played on the standalone build: while a shot is lined up and flies, Unity's own
    /// phone screen (the controller sheet: the map with the landing zones, the club card, the aim
    /// pad) is in front. The app's screens take over for Ready, pause, the shot's result and the
    /// hole's end and onboarding. A multiplayer round plays the same: the phone with the
    /// player up (the TV's, a guest's, or the one being passed round) has the sheet for that shot; the
    /// party screen is in front while others play, for the hole's intro and the results.
    private var unityControllerShown = false
    private func updateGolfPhoneController() {
        let upHere = multiplayerMatchID == nil || (golfController.party?.myTurn == true && ["Aim", "Flight", "Replay"].contains(golfPhase))
        let want = active && sport == "golf" && ready && loading.finished && !paused && !menuPauseVisible
            && (displayConnected || multiplayerControllerOnly) && upHere
            && !OnboardingFlow.shared.holdsMenu && finishedMatch == nil
            && ["Intro", "Aim", "Flight", "Replay", "HoleDone"].contains(golfPhase)
            && (golfPhase != "Aim" || golfShotReady || multiplayerMatchID != nil)
        guard want != unityControllerShown else { return }
        unityControllerShown = want
        // (a guest without a TV of its own keeps Unity in a window of its own, under the native controller)
        if multiplayerControllerOnly && !runtimeExternalDisplay { SportsDisplays.shared.showMultiplayerRenderer(want) }
        else {
            SportsRuntime.shared().showUnity(onPhone: want)
            if !want { SportsDisplays.shared.phone?.makeKeyAndVisible() }
        }
        SportsDiagnostics.write("golf phone controller \(want ? "shown" : "hidden") phase=\(golfPhase)")
    }
    /// A renderer may repeat its first-frame event when a display is reattached. Acknowledge this session only once.
    func runtimeDidRender(renderedAt: Double?) {
        let firstReady = !ready
        pending = nil; ready = true
        if displayConnected && !runtimeExternalDisplay { routeGameToExternalDisplay() }
        if UserDefaults.standard.bool(forKey: "sports.resetCoaching") {
            UserDefaults.standard.set(false, forKey: "sports.resetCoaching"); command("coaching")
        }
        loading.markReady(now: Date(timeIntervalSince1970: renderedAt.flatMap { $0.isFinite && $0 > 0 ? $0 : nil } ?? ProcessInfo.processInfo.systemUptime))
        if multiplayerMatchID != nil, firstReady {
            MultiplayerService.shared.runtimeLoaded(readyAfter: max(0, LoadingModel.multiplayerMinimum - loading.elapsed) + LoadingModel.finishDuration)
        }
        if Self.benchmark { loading.skip() }
    }

    private func poll() {
        if multiplayerMatchID != nil, let lobby = MultiplayerService.shared.lobby {
            // The cover lifts once everyone has loaded (tennis then sets up its controllers behind it).
            // Tennis lifts its LOCAL cover after its own first frame. Opponent loading belongs in setup status, never over calibration.
            loading.updatePlayers(waiting: sport == "tennis" ? [] : lobby.competitors.filter { !$0.loaded }.map(\.name), allReady: sport == "tennis" || lobby.phase == .calibrating || lobby.phase == .playing)
            if setupStage == .waiting, lobby.phase == .playing { beginMultiplayerPlay() }
            // MultiplayerService retries loaded/calibrated reports until the lobby acknowledges them, including during loading.
            // A phone with no TV is judged against the shared TV's delay, which the phone with the TV reports to the lobby: at launch,
            // and again whenever its game's TV credit (learned from play) moves (Unity's screenLag). It becomes this phone's starting
            // credit, which its own swings then refine (sharedLatency keeps them).
            if multiplayerControllerOnly, sport == "tennis", ready, loading.finished,
               let shared = lobby.participants.first(where: { $0.view == .split })?.screenDelay, shared != appliedSharedDelay {
                appliedSharedDelay = shared; command("sharedLatency", value: shared)
            }
        }
        loading.tick(now: LoadingModel.clockNow)
        for _ in 0..<64 {
            guard let json=SportsRuntime.shared().pollEvent(),let data=json.data(using:.utf8),
                  let event=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any] else { break }
            if !["feedback", "golfController"].contains(event["type"] as? String ?? "") { NSLog("[SportsSession] %@",json) }
            if event["type"] as? String == "boot" { loading.markBoot(); sendPending(); continue }
            guard event["session"] as? String == sessionID else { continue }
            // the pointer menu is still on the TV while this match loads behind it: its events are the menu's
            if let type = event["type"] as? String, type.hasPrefix("menu") { HubSession.shared.menuEvent(type, event["message"] as? String ?? ""); continue }
            if sport == "golf", let state = event["golfState"] as? String, !state.isEmpty {
                golfPhase = state
                golfHasNextHole = event["golfHasNextHole"] as? Bool ?? false
                golfShotReady = event["golfShotReady"] as? Bool ?? false
                golfSwingState = event["golfSwingState"] as? Int ?? 0
                observeGolfTap()
            }
            if let allowed = event["presentationResultReady"] as? Bool { resultPresentationReady = allowed }
            switch event["type"] as? String {
            case "ready":
                runtimeDidRender(renderedAt: event["renderedAt"] as? Double)
            case "sceneReady": loading.markSceneReady(now: Date(timeIntervalSince1970: event["clock"] as? Double ?? ProcessInfo.processInfo.systemUptime))
            case "loadProgress":
                if let p=Double(event["message"] as? String ?? "") { loading.reach(p) }
            case "golfController":
                if let object = event["golfController"], let data = try? JSONSerialization.data(withJSONObject: object),
                   var reading = try? JSONDecoder().decode(GolfControllerReading.self, from: data) {
                    // Unity's JsonUtility cannot write a null party: a solo round sends an empty one
                    // (no players, never "my turn"), which turned the controller into a local party's
                    // waiting screen. Only a multiplayer match has a party.
                    if multiplayerMatchID == nil || reading.party?.players.isEmpty == true { reading.party = nil }
                    if reading.hole != golfController.hole { golfControllerMap = nil }
                    golfController = reading
                    if let encoded = reading.mapImage, !encoded.isEmpty, let bytes = Data(base64Encoded: encoded),
                       let image = UIImage(data: bytes) { golfControllerMap = image }
                }
            case "bowling": bowlingState = event["message"] as? String ?? ""
            case "bowlCue": BowlingHaptics.cue(event["message"] as? String ?? "")
            case "bowlingGame": TennisMenu.shared.bowlingFinished(BowlingGameStats(line: event["message"] as? String ?? ""))
            case "lesson": LessonCenter.shared.receive(event["message"] as? String ?? "")
            case "feedback":
                receiveMatchSnapshot(event)
                feedback=event["message"] as? String ?? ""; stamina=event["stamina"] as? Double ?? 1
                if SportsRuntime.shared().clock()>=nextDiagnostic {
                    nextDiagnostic=SportsRuntime.shared().clock()+4   // every 4 s: at 1 s the log held only the last few minutes, too little to explain a crash
                    SportsDiagnostics.write("bridge nativePaused=\(paused) phase=\(phase) target=\(target) unityFrame=\(event["frame"] ?? "unknown") unityPaused=\(event["paused"] ?? "unknown") playerX=\(event["playerX"] ?? "unknown") inputAge=\(event["inputAge"] ?? "unknown") \(SportsDiagnostics.memory)")
                }
            case "displayReady":
                if displayConnected { SportsDisplays.shared.external?.isHidden=true }
                status="Display reconnected. Tap Ready to set your center and play."
            case "recording": pointClips.receive(event)
            case "perf": SportsDiagnostics.write("perf \(event["message"] as? String ?? "")")
            case "stroke": SportsDiagnostics.write("stroke \(event["message"] as? String ?? "")")
            case "score":
                score = TennisScore(line: event["message"] as? String ?? "")
                // The final scoreboard ("YOU WIN 6–4 3–6 7–5" / "OPPONENT WINS …") also ends the
                // match here, so the phone's Next never depends on one event arriving.
                for (prefix, won) in [("YOU WIN ", true), ("OPPONENT WINS ", false)] where score.detail.hasPrefix(prefix) {
                    receiveMatchFinish(won: won, score: String(score.detail.dropFirst(prefix.count)))
                }
            case "emoteState":
                let window = event["message"] as? String ?? ""
                if window != emoteWindow { emoteNotice = "" }
                emoteWindow = window
            case "emoteResult": emoteNotice = event["message"] as? String ?? ""
            case "introSkip":
                let fields = (event["message"] as? String ?? "").split(separator: "|").compactMap { Int($0) }
                let skip = fields.count == 3 ? IntroSkip(voted: fields[0], needed: fields[1], mine: fields[2] == 1) : nil
                if skip != introSkip { introSkip = skip }
            case "timing": receiveTimingResult(event["message"] as? String ?? "failed")
            case "screenLag":
                // one TV for two phones: the TV credit this phone's game gives its player, for the controller-only phone (same picture)
                if multiplayerSplit, multiplayerMatchID != nil, let ms = Double(event["message"] as? String ?? ""), ms.isFinite {
                    MultiplayerService.shared.setScreenDelay(ms / 1000)
                }
            case "abilities":
                let fields = (event["message"] as? String ?? "").split(separator: "|")
                if fields.count == 5, let meter = Double(fields[0]), let cooldown = Double(fields[2]), meter.isFinite, cooldown.isFinite {
                    ultimateMeter = 0; ultimateArmed = false
                    diveCooldown = max(0, cooldown); canDive = fields[3] == "1"; canArmUltimate = false
                }
            case "contact":
                if let contact = TennisContact(line: event["message"] as? String ?? "") { contacts = Array((contacts + [contact]).suffix(12)) }
            case "flash": if let rendered=Double(event["message"] as? String ?? "") { flashShown(at:rendered) }
            case "phase":
                let parts=(event["message"] as? String ?? "").split(separator:"|").map(String.init)
                let phase=parts.first ?? ""
                if phase != tennisPhase {
                    // A held move button must not carry on into the rally.
                    if phase != "serve" && phase != "receive" { nudge(0) }
                    // A new serve starts from the aim the player last chose.
                    if phase == "serve" { setServeAim(across:serveAim.across,depth:serveAim.depth) }
                }
                if tennisPhase != phase { SportsDiagnostics.write("tennis phase=\(phase)") }
                tennisPhase=phase
                if phase == "finished" { receiveMatchSnapshot(event) }
                if parts.count>1 { serveFromDeuce=parts[1] == "deuce" }
            case "golfHoleDone":
                let parts = (event["message"] as? String ?? "").split(separator: "|").map(String.init)
                if parts.count == 2 { Analytics.track("golf_hole_done", ["strokes": parts[0], "capped": parts[1]]) }
            case "rally": if let n=Int(event["message"] as? String ?? "") { SportProgress.shared.recordRally(n); SportsDiagnostics.write("rally persisted \(n)") }
            case "matchStats": lastMatchStats = MatchStats(line: event["message"] as? String ?? "")
            case "golfRound":
                let stats = GolfRoundStats(line: event["message"] as? String ?? "")
                if lastGolfRound == nil { lastGolfRound = stats; TennisMenu.shared.golfRoundFinished(stats) }
            case "presentation":
                recordPresentationEvent(event)
            case "matchOver":
                guard resultPresentationReady else { continue }
                let parts = (event["message"] as? String ?? "").split(separator: "|")
                receiveMatchFinish(won: parts.first == "won", score: parts.count > 1 ? String(parts[1]) : "")
            case "pauseRequest": if active && !paused { pause() }
            case "exit": if active { exitGame() }
            case "error":
                let message = event["message"] as? String ?? "Unity error"
                if !ready { failStartup(message) }
                else { status = message; pause(reason: message) }
            default: break
            }
        }
        updateGolfPhoneController()
        // The durable copy of the result, read after the events so their stats are already in.
        if active && resultPresentationReady && finishedMatch == nil, let result = SportsRuntime.shared().tennisResult() {
            let parts = result.split(separator: "|", maxSplits: 1).map(String.init)
            receiveMatchFinish(won: parts.first == "won", score: parts.count > 1 ? parts[1] : "")
        }
    }
}


/// Games and the point score, from Unity's "score" event ("playerGames,opponentGames,scoreboard").
struct TennisScore: Equatable {
    var player = 0, opponent = 0
    var detail = ""
    init() {}
    init(line: String) {
        let parts = line.split(separator: ",", maxSplits: 2).map(String.init)
        player = parts.count > 0 ? Int(parts[0]) ?? 0 : 0
        opponent = parts.count > 1 ? Int(parts[1]) ?? 0 : 0
        detail = parts.count > 2 ? parts[2] : ""
    }
}

/// Where a hit met the strings (x, y in half-widths of the string bed, so the frame is at ±1)
/// and how well it was timed, from Unity's "contact" event.
struct TennisContact: Equatable, Identifiable {
    let id = UUID()
    var x: Double, y: Double
    /// TennisRules.Timing: 0 missed ... 5 perfect.
    var grade: Int
    var supercharged: Bool
    /// How late the swing was, milliseconds (negative: early).
    var lateMs: Int
    init?(line: String) {
        // Double("nan") and Double("inf") parse, and Int() of NaN, Infinity or a huge value traps (the app would be killed), so a
        // value Unity formatted badly reads as 0 and the whole numbers are clamped before the conversion.
        let parts = line.split(separator: ",").map { part -> Double in
            guard let value = Double(part), value.isFinite else { return 0 }
            return value
        }
        guard parts.count >= 4 else { return nil }
        func whole(_ value: Double) -> Int { Int(max(-1_000_000, min(1_000_000, value))) }
        x = parts[0]; y = parts[1]; grade = whole(parts[2]); supercharged = parts[3] > 0
        lateMs = parts.count > 4 ? whole(parts[4]) : 0
    }
    /// "LATE" / "EARLY" when the swing was off by more than a perfect one's margin.
    var timingWord: String { lateMs > 35 ? "LATE" : lateMs < -35 ? "EARLY" : "ON TIME" }
    static let gradeNames = ["MISS", "OK", "GOOD", "GREAT", "EXCELLENT", "PERFECT"]
    var gradeName: String { supercharged ? "SUPER SHOT" : Self.gradeNames[max(0, min(5, grade))] }
}

/// Per-TV timing check results, keyed by the AirPlay receiver's name.
enum SportsTiming {
    private static let key = "sports.tv.timing.v2"
    static func currentTV() -> String {
        let outputs = AVAudioSession.sharedInstance().currentRoute.outputs
        return outputs.first(where: { $0.portType == .airPlay })?.portName ?? outputs.first?.portName ?? "screen"
    }
    /// How the picture reaches the TV, read from the audio route (it follows the picture). A cable (USB-C or the Lightning
    /// AV adapter to HDMI) shows it about a frame late plus the TV's own processing; AirPlay streams it, adding ~100-250 ms
    /// that no setting removes. Unknown when the sound goes elsewhere (headphones) or nothing is connected.
    enum Link: String { case cable, airPlay, unknown }
    static func currentLink() -> Link { link(ports: AVAudioSession.sharedInstance().currentRoute.outputs.map(\.portType)) }
    static func link(ports: [AVAudioSession.Port]) -> Link {
        if ports.contains(.airPlay) { return .airPlay }
        if ports.contains(.HDMI) { return .cable }
        return .unknown
    }
    /// The setup line under the timing step: the TV's measured delay, and what would make it faster.
    static func advice(link: Link, delay: Double, gameModeHint: Double) -> String {
        let ms = Int((delay * 1000).rounded())
        let slow = delay > gameModeHint
        switch link {
        case .airPlay:
            return (delay > 0 ? "Your TV over AirPlay: \(ms) ms. " : "AirPlay adds picture delay. ")
                + (slow ? "A USB-C to HDMI cable or the TV's Game Mode makes it faster." : "A USB-C to HDMI cable makes it faster still.")
        case .cable:
            return (delay > 0 ? "Your TV on a cable: \(ms) ms." : "Connected by cable: the fastest way to play.")
                + (slow ? " Turn on the TV's Game Mode to make it faster." : "")
        case .unknown:
            return delay > 0 ? "Your TV: \(ms) ms." + (slow ? " Game Mode or a cable makes it faster." : "") : ""
        }
    }
    static func stored(for tv: String, defaults: UserDefaults = .standard) -> Double? {
        (defaults.dictionary(forKey: key) as? [String: Double])?[tv]
    }
    static func store(_ lag: Double, for tv: String, defaults: UserDefaults = .standard) {
        var all = defaults.dictionary(forKey: key) as? [String: Double] ?? [:]
        guard lag.isFinite else { return }
        all[tv] = max(0, min(1.0, lag))
        defaults.set(all, forKey: key)
    }
}

/// Companion device evidence for explicit benchmark launches. Unity records
/// rendered frame intervals; this records iOS thermal state and process footprint.
@MainActor private enum SportsBenchmarkThermals {
    private static var timer: Timer?
    private static var samples: [[String: Any]] = []
    private static var startTime = Date()
    private static var destination: URL?
    private static var sport = ""

    static func start(sport: String) {
        guard SportsSession.benchmark else { return }
        timer?.invalidate(); samples = []; startTime = Date(); self.sport = sport
        let root = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
            .appendingPathComponent("visual-overhaul/native-device", isDirectory: true)
        do {
            try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
            destination = root.appendingPathComponent("\(sport)-\(UUID().uuidString).json")
            sample()
            timer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
                Task { @MainActor in sample() }
            }
        } catch { print("[VisualDeviceProof] Thermal recorder failed: \(error)") }
    }

    private static func sample() {
        guard let destination else { return }
        let seconds = Date().timeIntervalSince(startTime)
        var info = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size / MemoryLayout<integer_t>.size)
        let status = withUnsafeMutablePointer(to: &info) { pointer in
            pointer.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        let process = ProcessInfo.processInfo
        let thermal: String
        switch process.thermalState {
        case .nominal: thermal = "nominal"
        case .fair: thermal = "fair"
        case .serious: thermal = "serious"
        case .critical: thermal = "critical"
        @unknown default: thermal = "unknown"
        }
        samples.append(["seconds": seconds, "thermalState": thermal,
                        "processFootprintBytes": status == KERN_SUCCESS ? Int64(info.phys_footprint) : -1,
                        "lowPowerMode": process.isLowPowerModeEnabled,
                        "applicationState": UIApplication.shared.applicationState.rawValue])
        let report: [String: Any] = [
            "scope": "Real iOS thermal state and whole integrated process footprint; rendered FPS is recorded independently by Unity.",
            "sport": sport, "startedUtc": ISO8601DateFormatter().string(from: startTime),
            "arguments": process.arguments, "operatingSystem": process.operatingSystemVersionString,
            "status": seconds >= 150 ? "complete" : "recording", "samples": samples
        ]
        do { try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]).write(to: destination, options: .atomic) }
        catch { print("[VisualDeviceProof] Thermal report write failed: \(error)") }
        if seconds >= 150 { timer?.invalidate(); timer = nil }
    }
}

/// Tap to swing, on the phone: tapping the swing button starts the swing at once, whatever the phone is
/// doing; tapping it again before contact cancels it. Unity owns the swing; this keeps the finger's side
/// of it, so the button answers the touch straight away and the haptics follow what Unity reports
/// (golfSwingState and the phase) rather than guessing.
struct GolfTapSwing: Equatable {
    enum Face: Equatable { case tap, swinging }
    enum Action: Equatable { case start, cancel }
    enum Feel: Equatable { case reset }
    /// A swing started by this tap is live (or about to be: Unity has not answered yet).
    private(set) var armed = false
    /// Unity has reported this tap's swing (state 2).
    private var acknowledged = false
    /// Tapped again: waiting to hear whether that reset the swing or a shot was already struck.
    private var cancelling = false
    private var armedAt: TimeInterval = 0
    /// How long Unity gets to answer a tap before the button stops waiting for it.
    static let answerSeconds: TimeInterval = 1.2

    var face: Face { armed ? .swinging : .tap }

    /// A tap: start a swing when none is live, cancel it when one is. nil when there is nothing to do.
    mutating func tap(canArm: Bool, now: TimeInterval) -> Action? {
        if armed { armed = false; cancelling = true; return .cancel }
        guard canArm else { return nil }
        armed = true; acknowledged = false; cancelling = false; armedAt = now
        return .start
    }
    /// Unity's report. Returns the feel to play: reset when a cancel (or Unity itself: a new aim, a club
    /// change, a swing left alone or stopped short) ends the swing before contact. A struck shot (the
    /// phase leaves Aim) ends the swing with no reset.
    mutating func observe(phase: String, shotReady: Bool, unityState state: Int, now: TimeInterval) -> Feel? {
        guard phase == "Aim", shotReady || cancelling else {
            armed = false; acknowledged = false; cancelling = false
            return nil
        }
        if cancelling {
            guard state == 0 else { return nil }   // (still mid-swing: a cancel in the downswing waits a moment for contact)
            cancelling = false; acknowledged = false
            return .reset
        }
        guard armed else { return nil }
        if state != 0 { acknowledged = true; return nil }
        if acknowledged { armed = false; acknowledged = false; return .reset }
        if now - armedAt > Self.answerSeconds { armed = false }   // Unity never took the tap: the button is free again
        return nil
    }
}
