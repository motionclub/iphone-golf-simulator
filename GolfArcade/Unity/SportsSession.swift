import SwiftUI
import AVFoundation
import Darwin

/// `waiting`: online tennis, this player is set up and the match starts when the other player is too.
enum ControllerSetupStage { case scan, timing, ready, waiting, playing }

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
    /// Phone casting (PLAN_PhoneCasting_GolfBowling.md): this phone is the match's screen. The game fills it sideways, like a TV, under
    /// a see-through app window that only offers Leave; it hosts the match and plays no one. The players' phones are their controllers.
    private(set) var castScreen = false
    /// A phone-casting match is on (this phone is its screen or a player's controller).
    private(set) var multiplayerCasting = false
    /// Handheld play (golf and bowling with no TV of this phone's own): the game draws in the top of the screen and the
    /// controller's deck covers this share of it at the bottom (Unity's NativeSportsSession.HandheldDeck is the same).
    static let handheldDeck: CGFloat = 0.25
    #if DEBUG
    /// `-handheldCheck` (simulator, no Unity): the handheld layout over a stand-in frame.
    func debugPhonePlay(_ on: Bool = true) { phonePlay = on }
    #endif
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
    /// Settings → Display → Phone frame rate, for games drawn on the phone's own screen (a TV is always 1080p at 60): "auto" (the
    /// default: 120 on a ProMotion phone with an A17 Pro or newer, 60 on the rest), "60" or "120". (11-22: replaces the old "120 fps on
    /// the phone" switch, which was off by default; a phone that had it on keeps 120.)
    var phoneFrameRate = (UserDefaults.standard.string(forKey:"sports.phoneFrameRate"))
        ?? ((UserDefaults.standard.object(forKey:"sports.highFrameRate") as? Bool) == true ? "120" : "auto") {
        didSet { UserDefaults.standard.set(phoneFrameRate,forKey:"sports.phoneFrameRate") }
    }
    /// Settings → Display → Picture: "smooth" (the default: the frame rate comes first, effects step down to hold it) or "sharp" (every
    /// effect and the panel's full resolution on the phone; older phones may drop frames). Unity TennisQuality.Sharp.
    var picture = UserDefaults.standard.string(forKey:"sports.picture") ?? "smooth" {
        didSet { UserDefaults.standard.set(picture,forKey:"sports.picture") }
    }
    /// The phone's own screen: 120 or 60 (Unity keeps it only if the panel reaches 120, and drops to 60 if the phone cannot hold it).
    var phoneFps: Int {
        let panel = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }
            .first { $0.session.role == .windowApplication }?.screen.maximumFramesPerSecond ?? 60
        if panel < 120 || ProcessInfo.processInfo.isLowPowerModeEnabled { return 60 }
        switch phoneFrameRate {
        case "60": return 60
        case "120": return 120
        default: return Self.chipGeneration >= 16 ? 120 : 60
        }
    }
    /// The hardware model's generation ("iPhone16,1" → 16: A17 Pro and newer are 16+), as Unity's TennisQuality.ForModel reads it; 0 off a phone.
    static let chipGeneration: Int = {
        var info = utsname(); uname(&info)
        let model = withUnsafeBytes(of: &info.machine) { String(decoding: $0.prefix { $0 != 0 }, as: UTF8.self) }
        guard model.hasPrefix("iPhone"), let comma = model.firstIndex(of: ",") else { return 0 }
        return Int(model[model.index(model.startIndex, offsetBy: 6)..<comma]) ?? 0
    }()
    /// A match is on with no other phone in it: the app's background checks (Game Center inbox, iCloud, friends) slow down or wait.
    var soloMatchActive: Bool { active && multiplayerMatchID == nil }
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
        // a tennis rematch goes straight into play (quick start T7: the swoop only); golf's still shows its short cut
        return rematchPresentation && presentationIntros != "off" ? (sport == "tennis" ? "off" : "short") : presentationIntros
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
    /// The bowling centre last picked (BowlingVenueChoice: rooftop, beachcourt, crater; an old indoor pick maps onto them).
    var bowlingVenue = BowlingVenueChoice.resolve(UserDefaults.standard.string(forKey: "sports.bowlingVenue"))?.rawValue ?? "rooftop" {
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
    /// The course the golf being played wears: `golfCourse`, but Cliffside during the golf lesson, whose Practice Tee is built on
    /// Cliffside's look (Unity Course.Lesson), so its loading screen, controller and HUD show the normal map, not the last pick.
    var shownGolfCourse: String { LessonCenter.shared.active && LessonCenter.shared.sport == .golf ? "cliffside" : golfCourse }
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
    /// Settings → Controls → 120 Hz swing input (off unless turned on, 11-22): on a TV the match loop reads the swing at 120 Hz while the
    /// TV is still drawn at 60 (Unity InputRate). It runs the whole game twice per TV frame, and any pass over 8.3 ms gave the TV a late
    /// frame: off by default so every TV gets a steady 60.
    var fastInput = (UserDefaults.standard.object(forKey:"sports.fastInput") as? Bool) ?? false {
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
    private(set) var aimFeedSequence=0
    private var aimFeedAt=0.0
    private(set) var aimWaiting=false
    private var aimSwing:TennisAimSwing?
    @ObservationIgnored private var aimFeedTask:Task<Void,Never>?
    @ObservationIgnored private var aimTimeoutTask:Task<Void,Never>?
    /// Play → Calibration: a practice court (Unity's aim drill) where the player swings at left / straight / right targets.
    var calibrationMode=false
    /// The lesson finished and the profile is saved: the phone offers Done.
    var calibrationComplete:Bool { aimLesson?.phase == .complete }
    /// Extra start fields for the tennis front end (mode, opponent, round).
    private var launchExtras: [String:Any] = [:]
    private(set) var multiplayerMatchID: String? {
        // An online match keeps playing while something only covers the app (a banner, Control Center, the AirPlay picker): Unity
        // froze the game there while the link stayed up, so the other phone heard a connected player whose game said nothing
        // (2026-11-11 log: 44 s of silence, the CPU took the player over). Only the background stops it (SportsRuntime).
        didSet { SportsRuntime.shared().keepPlayingWhenInactive = multiplayerMatchID != nil }
    }
    #if DEBUG
    /// For tests: puts the session in (or takes it out of) an online match without a TV and a Unity runtime.
    func debugSetOnlineMatch(_ id: String?, seat: Int = -1, controllerOnly: Bool = false) {
        multiplayerMatchID = id; multiplayerSeat = seat; multiplayerControllerOnly = id != nil && controllerOnly
    }
    func debugBeginOnlineSetup() { beginMultiplayerCalibration() }
    func debugPollSetupTurn() { if let lobby = MultiplayerService.shared.lobby { advanceSetupTurn(lobby) } }
    /// For tests: the hold is over (fixture sensors read as pointed at the TV).
    func debugFinishPoint() { tryFinishPoint() }
    func debugSetHolding(_ holding: Bool) { holdingPoint = holding }
    /// For tests and screen proofs: put the calibration at a step without a TV, a camera or Unity.
    func debugSetCalibration(prompt: Bool = false, flashes: Bool = false, flashing: Bool = false, goAt: Double? = nil, drill: Bool = false,
                             latency: Double? = nil, swings: Set<Int> = [], drillStart: Double? = nil) {
        setupStage = .timing; timingPrompt = prompt; measuringDelay = flashes; tvFlashing = flashing; timingGoAt = goAt
        checkingTiming = drill; latencyReading = latency; timingSwings = swings; timingDrillStart = drillStart
    }
    func debugStartTimingIfEveryoneAsked() { startTimingIfEveryoneAsked() }
    /// For tests: as the tennis lesson's launch sets it (startLesson), without starting Unity.
    func debugForceFullCalibration(_ on: Bool) { forceFullCalibration = on }
    func debugLearnedLag(_ lag: Double?) { learnedLag = lag }
    /// For tests and screen proofs: the match is over (or not), as Unity's finish would make it.
    func debugFinishMatch(_ result: (won: Bool, score: String)?) {
        finishedMatch = result; postGameStage = result == nil || sport != "tennis" ? nil : .victory; postGameChoice = 0
    }
    /// For tests and screen proofs: a golf round's or bowling game's end as Unity's card makes it with the app's window on the TV.
    func debugSetPostGameBoard(_ board: PostGameBoard?) {
        postGameBoard = board; postGameStage = board == nil ? nil : .victory; postGameChoice = 0
    }
    /// For tests and screen proofs: a Daily Hole in One round (0: none), without starting Unity.
    func debugSetHoleInOneDay(_ day: Int) { holeInOneDay = day }
    #endif
    private(set) var multiplayerControllerOnly = false
    /// The game's last bridge report (its frame number, paused, input age), for the logs.
    @ObservationIgnored private(set) var bridgeLine = "bridge (no report yet)"
    /// This phone's TV shows both players (one TV for two phones): the TV credit Unity gives its player goes to the lobby (screenLag).
    private var multiplayerSplit = false
    private var multiplayerSeat = -1
    /// The shared TV's delay the controller-only phone has already handed to Unity (so a change is applied once).
    private var appliedSharedDelay: Double?
    private var multiplayerSetupStarted = false
    /// One TV in the room: the player setting up on it before this one (MultiplayerLobby.setupTurnAhead). This phone's own setup
    /// starts when they are through their timing check; nil when it is this phone's turn.
    private(set) var setupTurnWaitingFor: String?
    var retainCourtDirectionForRematch = false
    var setupProblem = ""
    /// Point and hold (11-20): the whole tennis setup is "point your phone at the TV and hold the button", solo and online, every
    /// player at once. The button is down.
    private(set) var holdingPoint = false
    /// What the hold ring shows (0...1).
    var pointProgress: Double { axisGate.locked ? 1 : max(0, min(1, axisGate.progress)) }

    // MARK: Point and fill (SportsGlow, 11-22)

    /// The circle is up: the TV glows behind its card and this phone's camera reads it (setupStage .scan).
    private(set) var glowActive = false
    /// The circle on the TV and on every phone (0...1): kept by the phone with the TV, mirrored by the others.
    private(set) var glowProgress = 0.0
    /// This phone's camera sees the TV's glow now.
    private(set) var glowSeeing = false
    /// When the circle went up, and when this phone last saw the TV (host clock): after a while without it, the phone offers to use
    /// the direction it points instead (the camera may be covered, or the room too bright to read).
    private(set) var glowStartedAt = 0.0
    private(set) var glowLastSeenAt = 0.0
    static let glowHelpAfter = 8.0
    private var glowFill = SportsGlowFill()
    private var glowLastTick: Double?
    private var glowSharedStep = ""
    /// The glow clock minus the host clock: the network clock when phones share the TV (every phone reads the wave the TV phone draws).
    private var glowClockOffset: Double { sharesTV ? MultiplayerService.shared.networkTime - CACurrentMediaTime() : 0 }
    /// The players sharing this TV who are not on it yet (their camera does not see the glow).
    var playersOffTheTV: [MultiplayerParticipant] {
        guard sharesTV, let lobby = MultiplayerService.shared.lobby else { return [] }
        return lobby.competitors.filter { p in
            p.id != MultiplayerService.shared.localID && p.connected && !p.calibrated && SportsGlowStep.seeing(p.setupStep) != true
                && !["pointed", "ready", "quick", SportsGlowStep.done].contains(p.setupStep ?? "")
        }
    }
    /// The line under the circle on the phone.
    var glowMessage: String {
        if !glowSeeing {
            if CACurrentMediaTime() - max(glowStartedAt, glowLastSeenAt) > Self.glowHelpAfter {
                return "Can't see the TV's glow. Get the whole TV inside the corners."
            }
            return glowProgress > 0 ? "Point back at the TV. The circle drains until you do." : "Get the TV inside the corners."
        }
        if let first = playersOffTheTV.first { return "Waiting for \(first.name) to point at the TV too." }
        if !ownsTV, sharesTV, glowProgress <= 0 { return "Waiting for the TV…" }
        return "Keep it there…"
    }
    /// The fallback is offered: the TV has not been in view for a while, or the camera is off.
    var glowNeedsHelp: Bool {
        glowActive && !glowSeeing && (CACurrentMediaTime() - max(glowStartedAt, glowLastSeenAt) > Self.glowHelpAfter || !setupProblem.isEmpty)
    }

    /// The circle goes up: the TV starts to glow (TennisSetupTVView) and the camera reads it.
    private func beginGlow() {
        glowFill = SportsGlowFill(); glowProgress = 0; glowSeeing = false; glowActive = true; glowLastTick = nil; glowSharedStep = ""
        glowStartedAt = CACurrentMediaTime(); glowLastSeenAt = 0; latencyReading = nil; timingNote = ""
        SportsGlow.clockOffset = glowClockOffset
        shareGlowStep(seeing: false, progress: ownsTV && sharesTV ? 0 : nil)
        #if DEBUG
        if motion.fixtureSensors { return }   // tests have no camera: they hand receiveGlow its sightings
        #endif
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            motion.beginGlowRead(clockOffset: SportsGlow.clockOffset, travel: travel)
        case .notDetermined:
            motion.beginPointing(travel: travel)   // motion runs meanwhile, for the fallback
            let launched = sessionID
            Task { @MainActor [weak self] in
                let allowed = await AVCaptureDevice.requestAccess(for: .video)
                guard let self, self.active, self.sessionID == launched, self.glowActive else { return }
                if allowed { self.motion.beginGlowRead(clockOffset: SportsGlow.clockOffset, travel: self.travel) }
                else { self.setupProblem = "Camera access is off, so the phone can't see your TV. Use where you're pointing instead." }
            }
        default:
            motion.beginPointing(travel: travel)
            setupProblem = "Camera access is off, so the phone can't see your TV. Turn it on in Settings, or use where you're pointing."
        }
        SportsDiagnostics.write("glow begin ownsTV=\(ownsTV) sharesTV=\(sharesTV) offset=\(SportsGlow.clockOffset)")
    }
    private func endGlow() {
        guard glowActive else { return }
        glowActive = false; glowSeeing = false
        motion.endGlowRead()
    }
    private func shareGlowStep(seeing: Bool, progress: Int?) {
        guard multiplayerMatchID != nil else { return }
        let step = SportsGlowStep.encode(seeing: seeing, progress: progress)
        guard step != glowSharedStep else { return }
        glowSharedStep = step
        MultiplayerService.shared.runtimeSetupStep(step)
    }
    /// A look from the camera (ten a second): this phone on or off the TV, and the circle's progress.
    func receiveGlow(_ sighting: SportsGlowSighting) {
        guard active, sport == "tennis", setupStage == .scan, glowActive else { return }
        let dt = glowLastTick.map { max(0, min(0.25, sighting.time - $0)) } ?? 0
        glowLastTick = sighting.time
        glowSeeing = sighting.seeing
        if sighting.seeing { glowLastSeenAt = sighting.time; glowFill.add(delay: sighting.delay, heading: sighting.heading) }
        let offset = glowClockOffset
        if abs(offset - SportsGlow.clockOffset) > 0.002 { SportsGlow.clockOffset = offset; motion.setGlowClockOffset(offset) }
        if ownsTV || !sharesTV {
            // the circle is this phone's: it fills only while every phone sharing the TV sees it
            glowFill.step(dt, everyoneOn: sighting.seeing && playersOffTheTV.isEmpty)
            glowProgress = glowFill.progress
            shareGlowStep(seeing: sighting.seeing, progress: sharesTV ? Int(glowFill.progress * 10) * 10 : nil)
            if glowFill.done { finishGlow() }
        } else {
            // the circle is the TV phone's: this phone says whether it sees the TV, and finishes when the circle is full
            shareGlowStep(seeing: sighting.seeing, progress: nil)
            let tv = tvPhone
            let full = tv == nil || !(tv!.connected) || tv!.calibrated || SportsGlowStep.pastCircle(tv!.setupStep)
            glowProgress = full ? 1 : SportsGlowStep.progress(tv?.setupStep) ?? 0
            if full { finishGlow() }
        }
    }
    /// The circle is full: the phone with the TV keeps the TV's delay; every phone takes its direction from where it pointed through the
    /// TV while it filled.
    private func finishGlow() {
        guard glowActive else { return }
        glowActive = false; glowProgress = 1
        if ownsTV || !sharesTV, let raw = glowFill.delay {
            let delay = raw + SportsGlow.gameFrameLead
            tvDelay = delay; latencyReading = delay; checkTimingOnResume = false
            SportsTiming.storePicture(delay, for: SportsTiming.currentTV(), defaults: timingStore)
            // this TV's timing as play last left it, unless the picture has moved since (a new picture mode, another box)
            let lag = timingCalibration.map { abs($0 - delay) < 0.06 ? $0 : delay } ?? delay
            command("latency", value: lag)
            if multiplayerSplit, lag > 0 { MultiplayerService.shared.setScreenDelay(lag) }
            timingNote = String(format: "TV delay %.0f ms. Your first few swings fine-tune it.", delay * 1000)
            delayTip = SportsTiming.advice(link: SportsTiming.currentLink(), delay: delay, gameModeHint: Self.gameModeHint)
            SportsDiagnostics.write(String(format: "glow done delay=%.3f lag=%.3f readings=%d spread=%.3f link=%@", delay, lag, glowFill.delays.count,
                                           (glowFill.delays.max() ?? 0) - (glowFill.delays.min() ?? 0), "\(SportsTiming.currentLink())"))
            if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep(SportsGlowStep.done) }
        } else {
            SportsDiagnostics.write("glow done (following the TV phone) headings=\(glowFill.headings.count)")
        }
        if haptics { UINotificationFeedbackGenerator().notificationOccurred(.success) }
        motion.lockGlowDirection(heading: glowFill.heading)
    }
    /// The line under the hold button.
    var pointMessage: String {
        if holdingPoint { return axisGate.message }
        // (the card already says what to do: under the button, only how long)
        return [SportsMotion.pointPrompt, "Keep holding…", "Hold still…", ""].contains(axisGate.message) ? "Hold until the ring is full." : axisGate.message
    }
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
    var tvDelay = 0.0
    var measuringDelay = false
    /// The timing check is running on the TV (swing with the bouncing ball).
    var checkingTiming = false
    /// The timing check is offered, not sprung: the phone explains it and waits for Start.
    var timingPrompt = false
    /// When the TV's get-ready countdown ends (the phone mirrors it).
    var timingCountdownEnds: Date?
    /// What the last timing check found, for the controller.
    var timingNote = ""
    /// Settings → Controls → timing: the next match runs the whole setup (flashes and timing check) even on a TV it knows.
    private var checkTimingOnResume = false
    /// The timing check's result for the TV in use (seconds of lag from what the player sees
    /// to the swing registering): the whole chain, picture delay and swing detection alike, refined
    /// by play at the end of every match. Kept per output route (SportsTiming.currentTV).
    var timingCalibration: Double? { SportsTiming.storedChain(for: SportsTiming.currentTV(), defaults: timingStore) }
    /// Where the per-TV timing lives (tests use their own suite).
    var timingStore: UserDefaults = .standard
    /// The lag Unity should start from: the timing check, else the camera's measurement.
    var startingLag: Double { timingCalibration ?? tvDelay }
    /// The tennis lesson teaches the setup, so it always runs all of it (point, flashes, timing check), whatever this TV's saved
    /// timing; it opens on the calibrate card (calibrationExplain). Set by startLesson, cleared by end().
    private(set) var forceFullCalibration = false
    /// The setup's opening card ("Calibrate once"): up until Continue, or a few seconds.
    private(set) var calibrationExplain = false
    static let calibrationExplainSeconds = 6.0
    /// Quick start (11-21): this TV's whole chain is known, so after pointing the match starts at once, with no flashes, no timing
    /// check and no Ready tap. Not in the lesson, nor after "check my timing" in Settings, nor for a player coming back mid-match.
    var quickStartAvailable: Bool { timingCalibration != nil && !forceFullCalibration && !checkTimingOnResume && !calibrationMode }
    /// The lag Unity learned in play this match (seconds, from its learnedLag event; nil until it has seen enough swings).
    private(set) var learnedLag: Double?
    /// The phone was pointed at the TV while the court loaded (T4): the setup carries on from there once it has.
    private var pointedWhileLoading = false
    /// Point and hold already works under the loading screen (it is motion only): solo, not in the lesson (it opens on its card).
    /// (11-22: off. The circle needs the court on the TV to glow behind it; pointing under the loading screen comes back if the circle is
    /// ever drawn over the loading cover too.)
    static let pointUnderLoading = false
    var pointsWhileLoading: Bool {
        Self.pointUnderLoading && active && sport == "tennis" && multiplayerMatchID == nil && !loading.finished && setupStage == .scan
            && !forceFullCalibration && !calibrationMode && !Self.benchmark && displayConnected
    }
    /// The calibrate card is up (the lesson's setup); Continue, or calibrationExplainSeconds, takes it down.
    func showCalibrationExplain() {
        calibrationExplain = true
        let launched = sessionID
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(SportsSession.calibrationExplainSeconds))
            guard let self, self.active, self.sessionID == launched else { return }
            self.continueCalibrationExplain()
        }
    }
    func continueCalibrationExplain() { calibrationExplain = false }
    /// Shown only when the measured delay is high enough that the TV is probably processing
    /// the picture: the one setting outside the app that helps most.
    var delayTip = ""
    private var flashDelays: [Double] = []
    private var flashProbeID = UUID()
    /// The scan's blinks under way (a new id ends the ones before it).
    private var scanFlashID = UUID()
    /// Blinks a scan asks for at a time, until two agree.
    private static let scanFlashes = 2
    private static let flashes = 4, gameModeHint = 0.14
    /// TennisBeatCalibration (Unity): a 3 s countdown, the ball drops in over 1.2 s, then 9 bounces 1.2 s apart; the first 2 are warm-up
    /// (it ends early once 5 scored swings agree).
    static let timingCountdown = 3.0, timingLeadIn = 1.2, timingInterval = 1.2, timingBeats = 9, timingWarmUp = 2
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
        motion.onGlow = { [weak self] sighting in self?.receiveGlow(sighting) }
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
        measuringDelay = true; timingPrompt = false; flashDelays = []; flashProbeID = UUID(); tvFlashing = false
        let probeID = flashProbeID, launched = sessionID
        status = "Keep your phone pointed at the TV."
        Task { @MainActor [weak self] in
            // the camera reads the flashes: ask for it now if it was never asked (the TV says "Get ready for flashes" meanwhile)
            if AVCaptureDevice.authorizationStatus(for: .video) == .notDetermined { _ = await AVCaptureDevice.requestAccess(for: .video) }
            guard let self, self.active, self.sessionID == launched, self.flashProbeID == probeID, self.measuringDelay else { return }
            self.motion.setDelayProbe(true)
            // "Get ready for flashes" (ArtDir/ui/tv-results-calibration): long enough for the camera's exposure to settle (11-21: 1.5 s → 1 s)
            try? await Task.sleep(for: .milliseconds(1000))
            guard self.active, self.sessionID == launched, self.flashProbeID == probeID, self.measuringDelay else { return }
            self.tvFlashing = true
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
    /// The scan: the TV blinks black then white, two at a time until the phone has seen two in the same place (SportsMotion.scanFlash).
    /// The same blinks time the TV's delay, so no separate measurement follows.
    private func startScanFlashes() {
        scanFlashID = UUID()
        let id = scanFlashID, launched = sessionID
        SportsDisplays.shared.external?.isHidden = true   // the game itself on the TV: it draws the blink
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .milliseconds(700))   // the camera is up and its exposure settled
            while let self, self.active, self.sessionID == launched, self.scanFlashID == id, self.setupStage == .scan, !self.motion.axisLocked {
                self.command("flash", value: Double(Self.scanFlashes))
                try? await Task.sleep(for: .seconds(Double(Self.scanFlashes) * 1.7 + 1.1))
            }
        }
    }
    private func flashShown(at rendered: Double) {
        if setupStage == .scan, !measuringDelay {
            let launched = sessionID, id = scanFlashID
            Task { @MainActor [weak self] in
                try? await Task.sleep(for: .milliseconds(800))   // the white frame has reached the TV and the camera by now
                guard let self, self.active, self.sessionID == launched, self.scanFlashID == id, self.setupStage == .scan else { return }
                self.motion.scanFlash(rendered: rendered)
            }
            return
        }
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
        measuringDelay = false; tvFlashing = false; motion.setDelayProbe(false); timingPrompt = true
        if let delay = SportsDelayProbe.combine(flashDelays) {
            tvDelay = delay; SportsTiming.storePicture(delay, for: SportsTiming.currentTV(), defaults: timingStore)
            timingNote = String(format: "Screen delay measured: %.0f ms. The swing check will verify your timing.", delay * 1000)
        } else {
            tvDelay = SportsTiming.storedPicture(for: SportsTiming.currentTV(), defaults: timingStore) ?? timingCalibration ?? 0
            timingNote = tvDelay > 0 ? "Flashes were unclear. Using this screen's last measurement; you can retry."
                : "Flashes were unclear. Point the rear camera at the screen and retry, or use the swing check."
        }
        command("latency", value: tvDelay)
        latencyReading = tvDelay > 0 ? tvDelay : nil
        // the other phones sharing this TV are judged against the same picture
        if multiplayerSplit, tvDelay > 0 { MultiplayerService.shared.setScreenDelay(tvDelay) }
        if setupStage == .timing { offerTimingCheck() }
        status = "Start the timing check on your phone."
        delayTip = SportsTiming.advice(link: SportsTiming.currentLink(), delay: tvDelay, gameModeHint: Self.gameModeHint)
        SportsDiagnostics.write("tv link=\(SportsTiming.currentLink()) ports=\(AVAudioSession.sharedInstance().currentRoute.outputs.map { $0.portType.rawValue })")
        SportsDiagnostics.write("tv delay flashes=\(flashDelays.map { String(format: "%.3f", $0) }) chosen=\(tvDelay)")
    }
    func savePlayers() { PlayerRosterStore.save(players); HubSession.shared.lookChanged() }
    /// Start tennis from the front end: a campaign round against `opponent`, or training.
    func startTennis(opponent: TennisOpponent?, round: Int?, mode: String? = nil, difficulty: Double, coach: [String] = [], preview: Bool, sets: Int? = nil, games: Int? = nil) {
        calibrationMode = mode == "calibration"
        // (Unity knows the calibration court as plain training: the aim drill is switched on once the player is ready)
        let mode = mode == "tutorial" ? "exhibition" : mode == "calibration" ? "training" : mode
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
        sport = "golf"; opponentName = ""; lastGolfRound = nil; holeInOneDay = 0
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
    /// The Daily Hole in One (DailyHoleInOne.swift): Unity builds the day's three holes, cups and spawns from `day` alone (the same
    /// for everyone), plays one shot on each and reports them ("holeInOne"); the world board goes back to it for the last card.
    func startHoleInOne(day: Int, preview: Bool) {
        sport = "golf"; opponentName = ""; lastGolfRound = nil; holeInOneDay = day
        DailyShare.shared.begin(day: day)
        launchExtras = ["mode": "round", "course": "holeinone", "noTwists": true, "noChallenges": true, "daily": 0, "holeInOne": day]
        start(preview: preview)
        launchExtras = [:]
    }
    /// The day of the Daily Hole in One being played, or 0.
    private(set) var holeInOneDay = 0
    /// Today's world standing to the round's last card (Unity: GolfGame.SetHoleInOneBoard).
    func sendHoleInOneBoard() {
        guard active, sport == "golf", holeInOneDay != 0 else { return }
        sendJSON(["version": 1, "session": sessionID, "action": "holeInOneBoard", "mode": DailyHoleInOne.shared.boardJSON()])
    }
    /// A lesson (PLAN_Onboarding_GolfLesson.md): Unity runs the sport's lesson from `station` and reports it ("lesson" events).
    func startLesson(_ sport: Sport, station: Int) {
        self.sport = sport.rawValue; opponentName = sport == .tennis ? "Ray" : ""; lastGolfRound = nil
        // the tennis lesson teaches the setup: all of it, every time, opening on the calibrate card
        forceFullCalibration = sport == .tennis
        LessonCenter.shared.begin(sport)
        if sport == .bowling {
            // the bowling lesson (BowlingLesson.cs): one bowler, this phone's player, on the venue last picked
            opponentName = ""; bowlingState = ""
            launchExtras = ["mode": players[min(playerIndex, players.count - 1)].name, "lesson": true, "lessonStation": station]
            start(preview: !displayConnected)
            launchExtras = [:]
            return
        }
        launchExtras = sport == .golf
            ? ["mode": "lesson", "course": "lesson", "noTwists": true, "noChallenges": true, "daily": 0, "lesson": true, "lessonStation": station]
            : ["mode": "lesson", "opponent": "", "opponentName": "Ray", "round": "", "difficulty": 0.1, "sets": 1, "games": 1, "coach": "",
               "lesson": true, "lessonStation": station]
        start(preview: false)
        launchExtras = [:]
        if !active { forceFullCalibration = false }
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
        castScreen=configuration.castScreenLocal; multiplayerCasting=configuration.hasCastScreen
        multiplayerSplit=configuration.sport == "tennis" && configuration.localView == .split
        multiplayerSeat=configuration.participants.first { $0.id == configuration.localID }?.seat ?? -1
        sport=configuration.sport; tennisVenue=configuration.venue
        if configuration.sport == "golf" { golfCourse=MultiplayerLobby.currentGolfVenue(MultiplayerLobby.golfRoundParts(configuration.venue).course) }
        launchExtras=["course":configuration.venue,"mode":"multiplayer", "network":json, "sets":configuration.sets, "games":configuration.games, "tips":false]
        start(preview: !displayConnected)
        launchExtras=[:]
        if !active { multiplayerMatchID=nil; multiplayerControllerOnly=false; multiplayerSplit=false; castScreen=false; multiplayerCasting=false }
        else {
            // (the court scan waits for the loading screen to finish: the camera has to see the court on the TV, see loadingFinished)
            // On a shared TV both players use the same display delay.
            if configuration.localView == .split, startingLag > 0 { MultiplayerService.shared.setScreenDelay(startingLag) }
        }
    }
    func start(preview: Bool = false) {
        guard !active else { return }
        guard multiplayerMatchID != nil || !MultiplayerService.shared.hasFriendsInLobby else { status = HubSession.soloLockMessage; return }
        // 11-21: tennis finds the TV with the camera, so it is asked for right before tennis loads (never at launch), with our card
        // first; refused, the card says how to turn it on and the launch goes on by itself once it is on. Every tennis launch
        // passes here (menu, lesson, nearby, online), so the launch is kept whole and made again from the card.
        if sport == "tennis", !Self.benchmark, displayConnected || multiplayerMatchID != nil, PermissionGate.shared.cameraNeedsCard {
            let extras = launchExtras, match = (multiplayerMatchID, multiplayerControllerOnly, multiplayerSplit, multiplayerSeat)
            let full = forceFullCalibration, venue = tennisVenue
            PermissionGate.shared.requireCamera(then: { [weak self] in
                guard let self, !self.active else { return }
                self.sport = "tennis"; self.tennisVenue = venue; self.launchExtras = extras; self.forceFullCalibration = full
                (self.multiplayerMatchID, self.multiplayerControllerOnly, self.multiplayerSplit, self.multiplayerSeat) = match
                self.start(preview: preview)
                self.launchExtras = [:]
                if !self.active { self.multiplayerMatchID = nil; self.multiplayerControllerOnly = false; self.multiplayerSplit = false; self.forceFullCalibration = false }
                else if self.multiplayerSplit, self.startingLag > 0 { MultiplayerService.shared.setScreenDelay(self.startingLag) }
            })
            status = "Tennis needs the camera to find your TV."
            return
        }
        SportsDisplays.shared.refresh()
        let preview = Self.benchmark && !displayConnected
        NSLog("[SportsSession] launch sport=%@ mode=%@",sport,preview ? "phone-preview" : "external-controller")
        // From the menu on the TV: what the launch is made from (a mode's station, or "menu"); nil for any other launch.
        let bay = Self.benchmark || multiplayerControllerOnly || (castScreen && !displayConnected) ? nil : HubSession.shared.bayForLaunch()
        // golf and bowling never need a TV: with none, they play on this phone, held upright (handheld play). A party guest
        // without a TV plays its own copy of the round there too, whoever else has one. Tennis still asks for one.
        // With a phone as the screen (phone casting), that phone shows the game full screen and every other phone is only a controller.
        let castOnPhone = castScreen && !displayConnected && !Self.benchmark
        let phoneGame = (sport == "bowling" || sport == "golf") && !displayConnected && !Self.benchmark && bay == nil && !castScreen && !multiplayerCasting
        guard let window = castOnPhone || phoneGame ? SportsDisplays.shared.phonePlayWindow() : bay != nil ? SportsDisplays.shared.external : Self.benchmark ? SportsDisplays.shared.benchmarkWindow() : multiplayerControllerOnly ? SportsDisplays.shared.multiplayerControllerWindow() : SportsDisplays.shared.gameWindow(preview:preview) else {
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
        tvDelay = SportsTiming.storedPicture(for: SportsTiming.currentTV(), defaults: timingStore) ?? 0; appliedSharedDelay = nil; learnedLag = nil; calibrationExplain = false
        golfController = .waiting; golfControllerMap = nil
        setupStage = .scan; axisGate = SportsAxisGate(); phase="calibrating"; feedback=""; golfPhase=""; golfHasNextHole=false; golfShotReady=false; golfSwingState=0; golfTap=GolfTapSwing(); stamina=1
        multiplayerSetupStarted = false; setupTurnWaitingFor = nil; setupProblem = ""; pointedWhileLoading = false
        // T4: the phone can be pointed at the TV under the loading screen (a direction still held from the last match is kept)
        if sport == "tennis", multiplayerMatchID == nil, !forceFullCalibration, !calibrationMode, !Self.benchmark, displayConnected,
           !motion.hasUsableCourtDirection {
            axisGate.message = SportsMotion.pointPrompt; motion.beginPointing(travel: travel)
        }
        holdingPoint = false; tvFlashing = false; timingGoAt = nil; timingSwings = []; timingDrillStart = nil; latencyReading = nil
        timingStartTask?.cancel(); timingStartTask = nil
        let p=players[min(playerIndex,players.count-1)]
        UserDefaults.standard.set(sport, forKey: "sports.lastSport.\(p.id.uuidString)")
        matchEmotes = p.equippedEmotes; emoteWindow = ""; emoteNotice = ""; tennisPhase = ""; introSkip = nil
        if let network = launchExtras["network"] as? String, let data = network.data(using: .utf8),
           let configuration = try? JSONDecoder().decode(MultiplayerMatchConfiguration.self, from: data),
           let local = configuration.participants.first(where: { $0.id == configuration.localID }) {
            matchEmotes = EmoteCatalog.normalized(local.loadout?.emotes)
        }
        motion.setAimProfile(storedAimProfile())
        pending=["holeFlyover":holeFlyover,"intros":consumePresentationIntroCut(),"bigMoments":presentationBigMoments,"presentationConstrained":reduceMotion || ProcessInfo.processInfo.thermalState == .serious || ProcessInfo.processInfo.thermalState == .critical,"version":1,"session":sessionID,"action":"start","sport":sport,"playerID":p.id.uuidString,"playerName":p.name,"female":p.standardFemale,"skin":p.standardSkin,"left":p.handedness == .left,"sound":sound && !(multiplayerControllerOnly && !phonePlay && (sport == "tennis" || !displayConnected)),"phonePlay":phonePlay,"castScreen":castOnPhone,"castController":multiplayerCasting && !castScreen,"haptics":haptics,"touch":preview,"token":Int(sessionToken),"fps":phoneFps,"picture":picture,"inputHz":inputHz,"bench":SportsSession.benchmark,"difficulty":tennisDifficulty,"venue":sport == "tennis" ? tennisVenue : sport == "bowling" ? bowlingVenue : "resort",
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
        let fromMenu = bay != nil
        // No match builds behind the menu ("seamless" is never sent): under the loading cover nobody sees the menu, and keeping its
        // scene loaded while the round builds is what got the app killed for memory (10-26 20:39, party golf at Cliffside: JETSAM
        // per-process limit at the end of the load; 2026-10-28: 171 MB left as online tennis loaded). The scene swaps instead.
        if let bay { pending?["bay"] = bay }
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
        loading.begin(now: LoadingModel.clockNow, multiplayer: multiplayerMatchID != nil,
                      key: sport == "golf" ? "golf-\(golfCourse)" : sport == "tennis" ? "tennis-\(tennisVenue)" : sport)
        loading.onFinish = { [weak self] in self?.loadingFinished() }
        // never put a TV loading window over the controller-only phone
        if multiplayerCalibrates && multiplayerControllerOnly { loading.cardAppeared(); loadCoveredRuntime(in: window) }
        else { SportsDisplays.shared.beginLoadingCover(in: window) { [weak self] in self?.loadCoveredRuntime(in: window) } }
    }
    private func loadCoveredRuntime(in window: UIWindow) {
        // (the runtime lends its view to a window on this phone for a controller replica and for handheld play alike)
        do { try SportsRuntime.shared().load(in:window,controllerReplica:multiplayerControllerOnly || phonePlay || castScreen) }
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
    /// The app's window over the game on the TV (tennis setup, every sport's post-game). Golf and bowling: with it up Unity leaves
    /// its end cards out (postGameTV 1); handheld play, a controller-only phone, or the TV gone keep Unity's own (postGameTV 0).
    func showGameTVWindow() {
        guard active else { return }
        SportsDisplays.shared.showTennisSetupOnTV()
        if sport != "tennis" { command("postGameTV", value: SportsDisplays.shared.showsTVOverlay ? 1 : 0) }
    }

    func command(_ action:String, value:Double=0, value2:Double=0) {
        guard active else { return }
        NSLog("[SportsSession] command=%@ value=%.2f",action,value)
        sendJSON(["version":1,"session":sessionID,"action":action,"value":value,"value2":value2])
    }

    private var aimProfileKey:String {
        let player=players[min(playerIndex,players.count-1)]
        // v3 (11-16): swing directions with the acceleration sign fixed; v2 ones were learned inverted, v1 ones are racket-face angles
        return "tennis.aim.v3.\(player.id.uuidString).\(player.handedness == .left ? "left" : "right")"
    }
    func storedAimProfile() -> TennisAimProfile? {
        guard !players.isEmpty, let data=UserDefaults.standard.data(forKey:aimProfileKey),
              let profile=try? JSONDecoder().decode(TennisAimProfile.self,from:data), profile.valid else { return nil }
        return profile
    }

    // MARK: Aim calibration (Play → Calibration)

    /// Start the lesson on the live practice court: Unity feeds one ball per target ("aimFeed"), and the landing it reports
    /// ("aimLanding") says where the swing really sent it. Twelve takes learn this player's racket angles for left, straight and right
    /// on each wing; twelve fresh ones check them. Every take is also written to the diagnostics log with its raw face-angle trace.
    func beginAimingSetup() {
        guard active, ready, !paused, sport == "tennis", calibrationMode else { return }
        aimFeedTask?.cancel(); aimTimeoutTask?.cancel()
        aimLesson=TennisAimLesson()
        aimLessonMessage=aimLesson?.message ?? ""
        motion.setAimProfile(aimLesson?.profile)
        command("aimPractice",value:1)
        setShotDepth(0.75)
        queueAimFeed()
        SportsDiagnostics.write("aimcal begin source=swing-direction")
    }
    /// Throw the learned profile away and learn it again.
    func restartCalibration() {
        UserDefaults.standard.removeObject(forKey:aimProfileKey)
        beginAimingSetup()
    }
    private func queueAimFeed() {
        aimFeedTask?.cancel(); aimTimeoutTask?.cancel(); aimWaiting=false; aimSwing=nil
        guard let lesson=aimLesson else { return }
        motion.setAimProfile(lesson.profile)
        guard lesson.phase != .complete else { return }
        let launched=sessionID
        aimFeedTask=Task { @MainActor [weak self] in
            do { try await Task.sleep(for:.milliseconds(650)) } catch { return }
            guard let self, self.sessionID == launched, !self.paused, let trial=self.aimLesson?.current else { return }
            self.aimFeedSequence+=1; self.aimFeedAt=SportsRuntime.shared().clock(); self.aimWaiting=true
            let sequence=self.aimFeedSequence
            self.sendJSON(["version":1,"session":self.sessionID,"action":"aimFeed","value":trial.lane,"value2":trial.wing == 0 ? 1 : -1,"aimSequence":sequence])
            self.aimTimeoutTask=Task { @MainActor [weak self] in
                do { try await Task.sleep(for:.seconds(7)) } catch { return }
                guard let self, self.sessionID == launched, self.aimWaiting, self.aimFeedSequence == sequence else { return }
                self.aimWaiting=false; self.aimLessonMessage="Take another comfortable swing toward the target."; self.queueAimFeed()
            }
        }
    }
    /// Unity: where the aim-drill ball the player just hit landed (court x in metres, left negative) and whether the hit was legal.
    func receiveAimLanding(_ message:String) {
        let f=message.split(separator:"|").map(String.init)
        guard f.count == 4, let sequence=Int(f[0]), let x=Double(f[1]), x.isFinite, let legal=Int(f[3]) else { return }
        receiveAimLanding(sequence:sequence,x:x,legal:legal == 1)
    }
    private func receiveAimLanding(sequence:Int,x:Double,legal:Bool) {
        guard sequence == aimFeedSequence, aimWaiting, !paused, var lesson=aimLesson else { return }
        aimWaiting=false; aimTimeoutTask?.cancel()
        guard let swing=aimSwing else { aimLessonMessage="Swing through toward the target and try again."; queueAimFeed(); return }
        let phase=lesson.phase, trial=lesson.current
        let accepted=lesson.record(swing,landingX:x,legal:legal)
        let t0=swing.time
        let trace=swing.trace.map { String(format:"%d:%.1f:%.2f:%.2f:%.2f",Int((($0.time-t0)*1000).rounded()),$0.angle,$0.rate,$0.side,$0.forward) }.joined(separator:",")
        SportsDiagnostics.write(String(format:"aimcal take phase=%@ wing=%d lane=%d angle=%.2f face=%.2f facing=%.0f landingX=%.3f legal=%d accepted=%d trace=%@",
            phase == .capture ? "capture" : "check",trial?.wing ?? -1,trial?.lane ?? 9,swing.angle,swing.face,swing.facing,x,legal ? 1 : 0,accepted ? 1 : 0,trace))
        aimLesson=lesson; aimLessonMessage=lesson.message
        motion.setAimProfile(lesson.profile)
        if lesson.phase == .complete, let profile=lesson.profile, let data=try? JSONEncoder().encode(profile) {
            UserDefaults.standard.set(data,forKey:aimProfileKey)
            SportsDiagnostics.write("aimcal saved fore=\(profile.forehand) back=\(profile.backhand)")
            if haptics { UINotificationFeedbackGenerator().notificationOccurred(.success) }
        }
        queueAimFeed()
    }
    /// Done: keep the saved profile, close the practice court and go back to the Play list.
    func finishCalibration() {
        aimFeedTask?.cancel(); aimTimeoutTask?.cancel(); aimWaiting=false; aimSwing=nil; aimLesson=nil
        command("aimPractice",value:0)
        calibrationMode=false
        end()
    }
    /// Court scanning finishes before timing. The match remains held until Ready.
    func offerTimingCalibration() {
        guard active, ready, loading.finished, sport == "tennis" else { return }
        // Online tennis sets up exactly as solo does before its first serve: the court scan, the TV's delay and the timing check, then
        // Ready (versus tennis runs the timing drill on this phone's own court; the match only starts once everyone is ready). A player
        // coming back into a match already being played goes from the scan straight to Ready: the other player is waiting for them.
        if multiplayerMatchID != nil {
            if onlineComeback { if setupStage == .scan { multiplayerScanComplete() }; return }
            MultiplayerService.shared.runtimeSetupStep("timing")
        }
        // (11-22) no flashes and no timing drill any more: the direction is set, so on to Ready with this TV's timing
        setupStage = .timing; timingPrompt = false; checkingTiming = false
        menuPauseVisible = false; measuringDelay = false
        command("cancelTimingCheck"); command("controllerSetup", value: 1)
        SportsDisplays.shared.external?.isHidden = true
        advanceCalibration()
    }
    func skipTimingCheck() {
        guard setupStage == .timing, !measuringDelay else { return }
        timingStartTask?.cancel(); timingStartTask = nil; timingGoAt = nil
        command("cancelTimingCheck")
        completeTimingCalibration(message: timingCalibration == nil ? "The game will refine your timing as you play." : "Using the saved timing for this screen.")
    }
    func completeTimingCalibration(message: String) {
        guard setupStage == .timing else { return }
        timingPrompt = false; checkingTiming = false; timingCountdownEnds = nil; timingGoAt = nil; timingDrillStart = nil
        timingNote = message; setupStage = .ready
        if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep("ready") }
        pause(reason: "Timing calibration complete. Tap Ready to play.")
        autoReady()
    }
    /// No Ready tap (quick start T5): the centre Ready took is taken as the setup ends. Only if the sensors cannot give one yet does the
    /// Ready card stay up (its button, and the reason under it).
    private func autoReady() {
        guard setupStage == .ready else { return }
        if multiplayerCalibrates { finishMultiplayerCalibration() } else { readyToPlay() }
    }
    /// Quick start (T3): a TV whose whole chain is known needs no flashes and no timing check, so pointing was the whole setup. The
    /// phone without the TV (one TV for two phones) follows the TV phone: it plays against that same picture (the lobby's screenDelay).
    @discardableResult private func quickStart() -> Bool {
        guard active, sport == "tennis", setupStage == .timing, !(multiplayerMatchID != nil && onlineComeback) else { return false }
        let quick = ownsTV ? quickStartAvailable
            : !forceFullCalibration && !checkTimingOnResume && sharesTV && tvPhone?.setupStep == "quick"
        guard quick else { return false }
        if ownsTV { command("latency", value: startingLag) }
        if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep("quick") }
        timingPrompt = false; checkingTiming = false; measuringDelay = false; tvFlashing = false; latencyReading = nil
        timingNote = "Using this TV's saved timing."
        setupStage = .ready
        SportsDiagnostics.write(String(format: "quick start tv=%@ lag=%.3f", SportsTiming.currentTV(), startingLag))
        autoReady()
        return true
    }
    func receiveTimingResult(_ message: String) {
        guard checkingTiming, setupStage == .timing else { return }
        let note: String
        if let ms = Double(message), ms.isFinite, ms >= 0 {
            if ownsTV { SportsTiming.storeChain(ms / 1000, for: SportsTiming.currentTV(), defaults: timingStore); checkTimingOnResume = false }
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
        if multiplayerMatchID != nil { MultiplayerService.shared.shareDiagnostic("pause reason=\(reason) setup=\(setupStage)") }
        sendJSON(["version":1,"session":sessionID,"action":"pause","reason":reason]); paused=true; status=reason
        // Bowling's controller has no Ready button: whatever paused it (Unity's own pause, the TV dropping), the pause menu comes up
        // so Resume is one tap away. Before, such a pause left the bowler frozen with "Hold to start" still on the phone (11-21 playtest).
        if reason == "Paused on phone — tap Ready to continue" || sport == "bowling", ready, loading.finished, finishedMatch == nil {
            menuPauseVisible = true
            if sport != "golf" { SportsDisplays.shared.showMenu(); if !displayConnected { SportsDisplays.shared.showMatchControls() } }
        }
    }
    func resume() {
        guard displayConnected || multiplayerControllerOnly || phonePlay || castScreen else { pause(reason: "Reconnect your TV or Mac to continue."); return }
        guard sport != "tennis" || setupStage == .playing else { status = SportsMotion.pointPrompt; return }
        guard ready, phase == "steering" else { status="Tap Ready to set your center and play."; return }
        menuPauseVisible = false; SportsDisplays.shared.external?.isHidden = true
        if !displayConnected && !phonePlay { SportsDisplays.shared.restorePhoneControls() }
        command("resume"); paused=false; status="Playing"
        if sport == "tennis" { tennisControllerActive=true }
        SportsDiagnostics.write("resume phase=\(phase) target=\(target)")
    }
    func readyToPlay() {
        if showsOnlineTennisSetup { finishMultiplayerCalibration(); return }
        // bowling with no TV plays on this phone (phonePlay): it is its own display
        guard displayConnected || multiplayerControllerOnly || phonePlay || castScreen, active, ready, loading.finished else { return }
        if multiplayerCalibrates { finishMultiplayerCalibration(); return }
        if sport == "tennis", setupStage == .scan || setupStage == .timing {
            menuPauseVisible = false; SportsDisplays.shared.external?.isHidden = true
            status = setupStage == .scan ? SportsMotion.pointPrompt : "Start the timing calibration to continue."
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
        if calibrationMode { if aimLesson == nil { beginAimingSetup() } else { queueAimFeed() } }
    }
    /// Unity renders the timing ball on the TV; motion samples keep flowing from the phone.
    func startTimingCheck() {
        guard active, ready, loading.finished, displayConnected || multiplayerControllerOnly, sport == "tennis",
              setupStage == .timing, !checkingTiming, !measuringDelay, timingGoAt == nil else { return }
        guard motion.axisLocked, motion.calibrate() else { return }
        // one TV: the ball on it is everyone's, so it starts when every player has tapped Start (2.5 s after the last tap)
        if sharesTV {
            let at = MultiplayerService.shared.networkTime + 2.5
            timingGoAt = at; MultiplayerService.shared.runtimeSetupStep("go:\(at)")
            status = "Waiting for everyone to tap Start."
            startTimingIfEveryoneAsked()
            return
        }
        beginTimingDrill()
    }
    /// The drill itself: Unity bounces the ball (drawn on the TV by TennisSetupTVView) and grades the swings.
    private func beginTimingDrill() {
        guard active, sport == "tennis", setupStage == .timing, !checkingTiming else { return }
        phase = "steering"
        menuPauseVisible = false; SportsDisplays.shared.external?.isHidden = true
        command("controllerSetup", value: 1)
        command("resume"); paused = false
        timingPrompt = false; checkingTiming = true; timingNote = ""
        timingCountdownEnds = Date().addingTimeInterval(Self.timingCountdown); timingSwings = []; timingDrillStart = nil
        status = "Swing with the bouncing ball on your TV."
        command("timingCheck")
        if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep("check:0") }
    }
    func recheckTiming() {
        guard multiplayerMatchID == nil else { return }   // the timing check is solo only: its commands are not passed on in a match
        // (11-22) the circle again: it re-times the TV and re-takes the direction
        beginAxisCapture()
    }
    /// Locking the court direction is a separate, gated step. Once it is done the phone can
    /// be held at any angle — which is the whole point, since forehands and backhands flip it.
    func beginAxisCapture() {
        if sport == "tennis" {
            aimFeedTask?.cancel(); aimTimeoutTask?.cancel(); aimLesson=nil; aimWaiting=false; aimSwing=nil; aimChecked=false
        }
        setupStage = .scan; timingPrompt = false; checkingTiming = false
        holdingPoint = false; tvFlashing = false; timingGoAt = nil
        timingStartTask?.cancel(); timingStartTask = nil
        command("cancelTimingCheck"); command("controllerSetup", value: 1)
        pause(reason: "Point your phone at the TV.")
        axisGate=SportsAxisGate(); axisGate.message = "Point the back of your phone at the TV."
        status = axisGate.message
        // point and fill (11-22): the circle on the TV, read by the camera, replaces the hold button, the flashes and the timing check
        if sport == "tennis", displayConnected || sharesTV { endGlow(); beginGlow() } else { motion.beginPointing(travel:travel) }
    }
    /// The hold button went down.
    func pressPoint() {
        guard active, loading.finished ? ready : pointsWhileLoading, sport == "tennis", setupStage == .scan, !holdingPoint,
              !motion.axisLocked, !calibrationExplain else { return }
        holdingPoint = true; setupProblem = ""
        motion.beginPointHold(timeTV: false)
        if haptics { UIImpactFeedbackGenerator(style: .light).impactOccurred() }
        if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep("hold") }
        SportsDiagnostics.write("point hold down")
    }
    /// The hold button came up.
    func releasePoint() {
        guard holdingPoint else { return }
        holdingPoint = false
        if motion.axisLocked { tryFinishPoint(); return }
        motion.endPointHold()
        if haptics { UINotificationFeedbackGenerator().notificationOccurred(.warning) }
        if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep("direction") }
    }
    /// VoiceOver (a hold cannot be performed there): take the direction the phone points now.
    func pointNow() {
        guard setupStage == .scan else { return }
        useCurrentDirection()
    }
    /// The phone is pointed at the TV. Next the TV is calibrated (its flashes), then the timing check (CalibrationStep).
    private func tryFinishPoint() {
        guard active, sport == "tennis", setupStage == .scan, motion.axisLocked else { return }
        holdingPoint = false
        if haptics { UINotificationFeedbackGenerator().notificationOccurred(.success) }
        // pointed while the court loads (T4): the rest of the setup needs the court on the TV, so it carries on at loadingFinished
        if !loading.finished { pointedWhileLoading = true; status = "Pointed at the TV. Loading the court…"; return }
        // back into a match already being played: nothing more to set up, the others are waiting
        if multiplayerMatchID != nil, onlineComeback {
            setupStage = .ready; MultiplayerService.shared.runtimeSetupStep("ready"); finishMultiplayerCalibration(); return
        }
        // (latencyReading and timingNote are the circle's, set as it filled: beginGlow clears them)
        setupStage = .timing; timingPrompt = false; checkingTiming = false; measuringDelay = false; tvFlashing = false
        timingGoAt = nil; timingSwings = []; timingDrillEnds = nil
        endGlow()
        if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep("pointed") }
        status = "Pointed at the TV."
        advanceCalibration()
    }

    // MARK: Calibration after pointing (2026-11-20): flashes → TV latency → timing check, the same for every player

    /// Where this player is between pointing at the TV and Ready (setupStage .timing), for the phone and the TV.
    enum CalibrationStep: Equatable { case waitingToPoint, waitingForTV, flashes, prompt, startWaiting, drill }
    var calibrationStep: CalibrationStep? {
        guard setupStage == .timing else { return nil }
        if checkingTiming { return .drill }
        if timingGoAt != nil { return .startWaiting }
        if timingPrompt { return .prompt }
        if measuringDelay { return .flashes }
        return ownsTV ? .waitingToPoint : .waitingForTV
    }
    /// This phone's game is the one on the TV (solo, the phone with the shared TV, or a TV of one's own).
    var ownsTV: Bool { displayConnected && !multiplayerControllerOnly }
    /// One TV for every player in the room (a split view).
    var sharesTV: Bool {
        multiplayerMatchID != nil && (MultiplayerService.shared.lobby?.competitors.contains { $0.view == .split } ?? false)
    }
    /// The TV is blinking for its delay: the setup screens on the TV step aside so the camera sees the whole picture turn.
    private(set) var tvFlashing = false
    /// The TV's delay, as the latency card shows it (seconds); nil when the flashes could not be read.
    private(set) var latencyReading: Double?
    /// Shared TV: when this phone asked for the timing check to begin (network clock), waiting for the other players to ask too.
    private(set) var timingGoAt: Double?
    /// The timing check's beats this player hit (from Unity's timingSwing), and when its countdown ends (this phone's clock).
    private(set) var timingSwings: Set<Int> = []
    private(set) var timingDrillStart: Double?
    private var timingDrillEnds: Double?
    private var timingStartTask: Task<Void, Never>?
    /// The other players still pointing at the TV (connected, not set up, not yet pointed).
    var playersStillPointing: [MultiplayerParticipant] {
        guard multiplayerMatchID != nil, let lobby = MultiplayerService.shared.lobby else { return [] }
        return lobby.competitors.filter { $0.id != MultiplayerService.shared.localID && $0.connected && !$0.calibrated
            && ["direction", "hold", "", nil].contains($0.setupStep) }
    }
    /// The phone with the shared TV, when it is not this one.
    private var tvPhone: MultiplayerParticipant? {
        MultiplayerService.shared.lobby?.competitors.first { $0.view == .split && $0.id != MultiplayerService.shared.localID }
    }
    /// Moves this player on when what they wait for has happened. Called after pointing and from the lobby poll.
    func advanceCalibration() {
        guard active, sport == "tennis", setupStage == .timing, !timingPrompt, !checkingTiming, !measuringDelay else {
            if setupStage == .timing, timingGoAt != nil { startTimingIfEveryoneAsked() }
            return
        }
        // Point and fill (11-22): the circle timed the TV as it filled, so pointing is the whole setup. No flashes and no timing drill:
        // the game refines the timing from the first few swings (TennisLagLearner), starting from the circle's reading.
        if ownsTV {
            if latencyReading == nil {
                // the direction came another way (still held from the last match, or set by hand): this TV's saved timing, if any
                tvDelay = SportsTiming.storedPicture(for: SportsTiming.currentTV(), defaults: timingStore) ?? timingCalibration ?? 0
                command("latency", value: startingLag)
                if multiplayerSplit, startingLag > 0 { MultiplayerService.shared.setScreenDelay(startingLag) }
                timingNote = startingLag > 0 ? "Using this TV's saved timing." : "Your first few swings set the timing."
                SportsDiagnostics.write(String(format: "setup without the circle's timing tv=%@ lag=%.3f", SportsTiming.currentTV(), startingLag))
            }
            completeTimingCalibration(message: timingNote)
        } else {
            // no TV on this phone: it plays against the TV phone's picture (the lobby's screenDelay), once that phone's circle is done
            let tv = tvPhone
            let tvDone = tv == nil || !(tv!.connected) || tv!.calibrated || SportsGlowStep.pastCircle(tv!.setupStep)
            guard tvDone else { status = "Waiting for the TV."; return }
            completeTimingCalibration(message: "Set. Your first few swings fine-tune the timing.")
        }
    }
    /// The timing check is offered: the phone asks for Start (the TV shows the latency card).
    private func offerTimingCheck() {
        setupStage = .timing; timingPrompt = true; checkingTiming = false; measuringDelay = false; tvFlashing = false
        command("cancelTimingCheck"); command("controllerSetup", value: 1)
        if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep("timing") }
        pause(reason: "Start the timing check on your phone.")
        status = "Start the timing check on your phone."
    }
    /// Shared TV: every player taps Start; the one ball on the TV starts for everyone at the same moment.
    private func startTimingIfEveryoneAsked() {
        guard let mine = timingGoAt, timingStartTask == nil, setupStage == .timing, !checkingTiming else { return }
        let service = MultiplayerService.shared
        var at = mine
        for p in service.lobby?.competitors ?? [] where p.id != service.localID && p.connected && !p.calibrated {
            let step = p.setupStep ?? ""
            if step.hasPrefix("go:"), let t = Double(step.dropFirst(3)) { at = max(at, t) }
            else if step == "ready" || step == "quick" || step.hasPrefix("check:") { continue }   // skipped it, or already under way
            else { return }   // still to tap Start
        }
        let wait = max(0, at - service.networkTime), launched = sessionID
        SportsDiagnostics.write(String(format: "timing check starts together in %.2fs", wait))
        timingStartTask = Task { @MainActor [weak self] in
            if wait > 0 { try? await Task.sleep(for: .seconds(wait)) }
            guard let self, self.active, self.sessionID == launched, self.setupStage == .timing else { return }
            self.timingStartTask = nil; self.timingGoAt = nil
            self.beginTimingDrill()
        }
    }

    /// Escape hatch when the gate will not settle, so motion tennis is never unreachable.
    func useCurrentDirection() {
        guard motion.forceAxisFromCurrentPose() else { return }
        motion.start(tennis:true,travel:travel)
        scanFinished()
    }
    func retryCourtDirection() {
        guard active, sport == "tennis" else { return }
        setupProblem = ""
        beginAxisCapture()
        if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep("direction") }
    }
    /// The court direction is locked (by the scan, or by "use the direction I'm pointing now"): on to the timing check, solo and online
    /// alike (offerTimingCalibration sends a player coming back mid-match straight to Ready).
    private func scanFinished() {
        guard setupStage == .scan else { return }
        tryFinishPoint()
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
    /// The TV's aiming camera looking up the hole (1, the aerial view) or back at the golfer (0); the game drops it for each new shot.
    func lookGolf(_ look: Double) {
        guard active, sport == "golf", ready, !paused, golfPhase == "Aim", look.isFinite else { return }
        sendJSON(["version":1,"session":sessionID,"action":"golfLook","value":max(-1,min(1,look))])
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
    /// A player whose match is already being played (they came back into it): the quick setup, so the others are not kept waiting.
    var onlineComeback: Bool { multiplayerMatchID != nil && MultiplayerService.shared.lobby?.phase == .playing }
    /// Online tennis sets up as solo does: point the phone at the TV, the TV's delay and the timing check, then Ready (and only then is
    /// this player reported set up). Only a player coming back mid-match with their direction still set goes straight to Ready.
    private func beginMultiplayerCalibration() {
        guard !multiplayerSetupStarted else { return }
        multiplayerSetupStarted = true
        // a player coming back mid-match, or a rematch: the phone still knows where the TV is, so there is nothing to set up
        if motion.hasUsableCourtDirection {
            paused = true
            command("controllerSetup", value: 1)
            motion.start(tennis: true, travel: travel)
            multiplayerScanComplete()
            return
        }
        // (no turns, 11-20: pointing at the TV needs neither the camera nor the TV, so every player sets up at the same time)
        beginOwnMultiplayerSetup()
    }
    private func beginOwnMultiplayerSetup() {
        setupTurnWaitingFor = nil
        beginAxisCapture()
        MultiplayerService.shared.runtimeSetupStep("direction")
    }
    /// The player ahead is through (or gone): this phone's turn. Polled while waiting.
    private func advanceSetupTurn(_ lobby: MultiplayerLobby) {
        guard setupTurnWaitingFor != nil, showsOnlineTennisSetup else { return }
        if let first = lobby.setupTurnAhead(of: MultiplayerService.shared.localID), !onlineComeback {
            if first.name != setupTurnWaitingFor { setupTurnWaitingFor = first.name }
            return
        }
        SportsDiagnostics.write("online setup turn: this phone sets up now")
        beginOwnMultiplayerSetup()
    }
    /// "Set up now": do not wait for the player ahead (they can finish on the TV after).
    func skipSetupTurn() {
        guard setupTurnWaitingFor != nil, showsOnlineTennisSetup else { return }
        SportsDiagnostics.write("online setup turn skipped by the player")
        beginOwnMultiplayerSetup()
    }
    /// A player coming back mid-match: the direction is locked, straight to Ready.
    private func multiplayerScanComplete() {
        setupStage = .ready; setupProblem = ""
        status = "Your phone still knows where the TV is."
        MultiplayerService.shared.runtimeSetupStep("ready")
        finishMultiplayerCalibration()
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
        command("controllerSetup", value: 0)   // (the in-game setup held the court while this phone set up, as in solo)
        command("resume")
    }

    /// The loading screen has run its course: show the game, and start the setup that the
    /// player sees (court direction, motion) only now.
    private func loadingFinished() {
        guard active, ready else { return }
        // Play safe (PLAN_Onboarding_v3): the first game of each sport this run waits on its loading screen for the phone's card
        if multiplayerMatchID == nil, !Self.benchmark, PlaySafeGate.shared.hold(sport: sport, then: { [weak self] in self?.loadingFinished() }) {
            status = "Read the card on your phone, then tap Got it"; return
        }
        SportsDisplays.shared.finishLoadingCover()
        SportsDiagnostics.write("loaded \(sport) \(SportsDiagnostics.memory)")
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("presentation/\(sessionID)", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        if let data = try? JSONSerialization.data(withJSONObject: loading.timing, options: [.prettyPrinted, .sortedKeys]) {
            try? data.write(to: directory.appendingPathComponent("L1_load_timing.json"), options: .atomic)
        }
        if displayConnected { SportsDisplays.shared.external?.isHidden=true }
        else if phonePlay || castScreen { SportsDisplays.shared.showPhonePlay(); if castScreen { SportsDisplays.shared.phoneOrientationChanged() } }
        else { SportsDisplays.shared.restorePhoneControls() }
        // Compensate from the first point with the last measurement of this TV; the
        // setup re-times it when the camera is aimed at it.
        if displayConnected && startingLag>0 { command("latency",value:startingLag) }
        showGameTVWindow()
        if multiplayerMatchID != nil {
            guard SportsRuntime.shared().multiplayerAvailable() else {
                MultiplayerService.shared.runtimeUnavailable("This Unity export does not contain multiplayer. Re-export and rebuild the integrated app.")
                return
            }
            // Tennis players first point their phone at the TV and tap Ready; the owner starts the match when all have.
            if multiplayerCalibrates { SportsDisplays.shared.showTennisSetupOnTV(); beginMultiplayerCalibration(); return }
            setupStage = .playing; paused=false; status=multiplayerSeat<0 ? "Watching" : "Playing"
            if multiplayerSeat>=0 { motion.start(tennis:sport == "tennis",travel:travel) }
            command("controllerSetup", value: 0); command("resume"); return
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
            beginTennisSetup()
        } else {
            motion.start(tennis:false,travel:travel)
            readyToPlay()
        }
    }
    /// The tennis setup the player sees, once the court is on the TV (loadingFinished): point and hold, then, on a TV whose timing is
    /// not known yet, the flashes and the timing check.
    func beginTennisSetup() {
        SportsDisplays.shared.showTennisSetupOnTV()
        // the lesson: the calibrate card, then all of the setup from pointing
        if forceFullCalibration { beginAxisCapture(); showCalibrationExplain(); return }
        // (Settings → TV timing check asks for the circle even when the direction is still held)
        if pointedWhileLoading || (motion.hasUsableCourtDirection && !checkTimingOnResume) {
            // pointed while it loaded, or the phone still knows where the TV is (a rematch, the next match): on from pointing,
            // which is the whole setup on a TV whose timing is known (quickStart)
            pointedWhileLoading = false
            command("cancelTimingCheck"); command("controllerSetup", value: 1)
            pause(reason: "Pointed at the TV.")
            motion.start(tennis: true, travel: travel)
            tryFinishPoint()
            if setupStage != .scan { return }
        }
        beginAxisCapture()
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
        if sport == "tennis" { postGameStage = .victory; postGameChoice = 0 }
        SportsDiagnostics.write("match finished: phone Next enabled; external=\(displayConnected)")
        // Tennis keeps the court direction for the next match (quick start T1: stopping the sensors here is what made every rematch
        // point and calibrate again); end() decides how long the sensors stay up.
        if sport == "tennis" { motion.idle() } else { motion.stop() }
        saveLearnedLag()
        TennisMenu.shared.matchFinished(won: won, score: score)
        // Keep explicit phone actions visible until the player chooses one.
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
    // MARK: Post-game (ArtDir/ui/tv-results-calibration): winner plaque → standings (golf: and the hole-by-hole card) → XP →
    // play again, on the TV (PostGameTV), stepped from the phone (MatchFinishControls). Tennis, and golf and bowling with a TV;
    // golf and bowling in handheld play keep Unity's own end cards.

    enum PostGameStage: Int, CaseIterable { case victory, results, scorecard, xp, again }
    /// Which post-game screen the TV shows (nil before the end, or when the app does not draw it).
    var postGameStage: PostGameStage?
    /// A golf round's or bowling game's final sheet, everyone's (Unity's "golfCard" / "bowlingCard").
    var postGameBoard: PostGameBoard?
    /// Golf and bowling are over: with the app's window on the TV, its post-game starts (Unity has left the screen to it).
    func receivePostGameBoard(_ board: PostGameBoard) {
        guard active, sport != "tennis", !board.players.isEmpty else { return }
        postGameBoard = board
        guard postGameStage == nil, SportsDisplays.shared.showsTVOverlay else { return }
        postGameStage = .victory; postGameChoice = 0
        SportsDiagnostics.write("postGame \(sport): \(board.players.count) players, TV plaque up")
    }
    /// The highlighted "Play again?" choice.
    var postGameChoice = 0
    struct PostGameChoice: Identifiable, Equatable { let id: String; let title: String; let after: TennisMenu.AfterMatch }
    /// What "Play again?" offers: the match's own choices (TennisMenu.postMatchChoices); a match with friends, rematch or leave.
    var postGameChoices: [PostGameChoice] {
        if multiplayerMatchID != nil { return [.init(id: "pm-replay", title: "Rematch", after: .replay), .init(id: "pm-menu", title: "Leave", after: .menu)] }
        let menu = TennisMenu.shared
        let campaign = menu.launch?.mode == .campaign
        let place = sport == "golf" ? "Course" : sport == "bowling" ? "Lanes" : "Court"
        return menu.postMatchChoices.map { id in
            switch id {
            // (outside the campaign "Play Again" is the same match again: TennisMenu.sessionEnded only goes on to a next round)
            case "pm-next": return .init(id: id, title: campaign ? "Next Round" : "Play Again", after: campaign ? .next : .replay)
            case "pm-replay": return .init(id: id, title: "Rematch", after: .replay)
            case "pm-court": return .init(id: id, title: "Change \(place)", after: .court)
            default: return .init(id: id, title: "Main Menu", after: .menu)
            }
        }
    }
    /// Continue on the phone: the next post-game screen (the XP one only when there is XP to show).
    func advancePostGame() {
        guard let stage = postGameStage else { return }
        switch stage {
        case .victory: postGameStage = .results
        // (a match with friends ends on the standings: what comes next is the party's, on the phone)
        case .results, .scorecard: postGameStage = multiplayerMatchID != nil ? stage : TennisMenu.shared.postMatch != nil ? .xp : .again
        case .xp: postGameStage = .again
        case .again: break
        }
        if haptics { UIImpactFeedbackGenerator(style: .light).impactOccurred() }
    }
    /// Golf: the standings ⇄ the hole-by-hole card.
    func togglePostGameScorecard() {
        guard sport == "golf", postGameBoard != nil, postGameStage == .results || postGameStage == .scorecard else { return }
        postGameStage = postGameStage == .results ? .scorecard : .results
        if haptics { UIImpactFeedbackGenerator(style: .light).impactOccurred() }
    }
    /// A "Play again?" choice, picked on the phone.
    func choosePostGame(_ index: Int) {
        let choices = postGameChoices
        guard choices.indices.contains(index) else { return }
        postGameChoice = index
        if sport == "tennis" { advanceAfterMatch(choices[index].after) }
        else if active, postGameBoard != nil {
            SportsDiagnostics.write("postGame \(sport) chose \(choices[index].id)")
            TennisMenu.shared.finishMatch(choices[index].after)
        }
    }

    /// The last golf round's tally, as Unity reported it.
    var lastGolfRound: GolfRoundStats?

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
        if loading.finished { showGameTVWindow() }
        SportsDisplays.shared.endPreview()
        SportsDisplays.shared.restorePhoneControls()
        status = "Display connected. Waiting for a gameplay frame…"
    }
    func exitGame() {
        // an online match: back to the Plaza (a party goes back to its bench together)
        if multiplayerMatchID != nil { HubSession.shared.leaveOnlineMatch() }
        else if OnboardingFlow.shared.lessonSport != nil || LessonCenter.shared.active { OnboardingFlow.shared.gameLeft() }
        else { TennisMenu.shared.goHome() }
    }
    /// How long the motion sensors stay up after a tennis match, keeping the court direction for the next one.
    static let directionKeepAlive: Double = 600
    /// Play's learned lag becomes this TV's whole chain (quick start T6), once per match: at its finish, or when it is left.
    func saveLearnedLag() {
        guard sport == "tennis", ownsTV, !calibrationMode, !Self.benchmark, let lag = learnedLag else { return }
        learnedLag = nil
        let tv = SportsTiming.currentTV(), before = timingCalibration
        let after = SportsTiming.learn(lag, for: tv, defaults: timingStore)
        SportsDiagnostics.write(String(format: "timing learned tv=%@ lag=%.3f before=%@ stored=%@", tv, lag, before.map { String(format: "%.3f", $0) } ?? "-",
                                       after.map { String(format: "%.3f", $0) } ?? "-"))
    }
    func end() {
        PlaySafeGate.shared.sessionEnded()
        if active { saveLearnedLag(); SportsDisplays.shared.beginExitCover() }
        menuPauseVisible = false
        if active && ready {
            var history=UserDefaults.standard.array(forKey:"sports.sessions.v1") as? [[String:Any]] ?? []
            history.append(["session":sessionID,"sport":sport,"playerID":players[playerIndex].id.uuidString,"endedAt":Date().timeIntervalSince1970,"summary":feedback])
            UserDefaults.standard.set(Array(history.suffix(100)),forKey:"sports.sessions.v1")
        }
        pointClips.reset()
        HubSession.shared.sessionEnded(finished: finishedMatch != nil || multiplayerMatchID != nil)   // a party comes back to its bay together
        multiplayerMatchID=nil; multiplayerSeat = -1; multiplayerControllerOnly=false; multiplayerSplit=false; multiplayerCasting=false
        if phonePlay || castScreen { phonePlay = false; castScreen = false; SportsDisplays.shared.endPhonePlay(); SportsDisplays.shared.phoneOrientationChanged() }
        if unityControllerShown { unityControllerShown = false; SportsRuntime.shared().showUnity(onPhone: false) }
        command("end")
        if sport == "tennis", retainCourtDirectionForRematch || motion.axisLocked {
            let ended = sessionID
            // The next tennis match keeps the live tracking origin (no pointing again): a rematch, a new match from the menu, the
            // match after the lesson (quick start T1; 90 s and rematch-only before 11-21). If none comes, release the sensors.
            motion.idle()
            Task { @MainActor [weak self] in
                try? await Task.sleep(for: .seconds(SportsSession.directionKeepAlive))
                guard let self, !self.active, self.sessionID == ended else { return }
                self.motion.stop()
            }
        } else { motion.stop() }
        retainCourtDirectionForRematch = false; multiplayerSetupStarted = false; setupTurnWaitingFor = nil
        forceFullCalibration = false; calibrationExplain = false
        holdingPoint = false; tvFlashing = false; timingGoAt = nil
        timingStartTask?.cancel(); timingStartTask = nil
        SportsDisplays.shared.hideTennisSetupOnTV()
        timer?.invalidate(); timer=nil; pending=nil; measuringDelay=false; checkingTiming=false
        loading.cancel(); tutorialStep=nil; finishedMatch=nil; postGameStage = nil; postGameBoard = nil; postGameChoice = 0; timingPrompt=false; endGlow(); setupStage = .scan
        SportsRuntime.shared().pause(true); active=false; ready=false; paused=true; tennisControllerActive=false; calibrationMode=false
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
        // 2026-11-16 (Adnan: "it had the old controller … make sure … the old controller is gone"): the native controller
        // (GolfPhoneController, the UI overhaul's) plays every shot; Unity's standalone sheet never comes in front of it again
        let want = false
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
        loading.markReady(now: Date(timeIntervalSince1970: renderedAt.flatMap { $0.isFinite && $0 > 0 ? $0 : nil } ?? ProcessInfo.processInfo.systemUptime))
        if multiplayerMatchID != nil, firstReady {
            MultiplayerService.shared.runtimeLoaded(readyAfter: loading.secondsUntilLift)
        }
        if Self.benchmark { loading.skip() }
    }

    private func poll() {
        if multiplayerMatchID != nil, let lobby = MultiplayerService.shared.lobby {
            // The cover lifts once everyone has loaded (tennis then sets up its controllers behind it).
            // Tennis lifts its LOCAL cover after its own first frame. Opponent loading belongs in setup status, never over calibration.
            loading.updatePlayers(waiting: sport == "tennis" ? [] : lobby.competitors.filter { !$0.loaded }.map(\.name), allReady: sport == "tennis" || lobby.phase == .calibrating || lobby.phase == .playing)
            if setupStage == .waiting, lobby.phase == .playing { beginMultiplayerPlay() }
            advanceSetupTurn(lobby)
            advanceCalibration()
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
                if holeInOneDay != 0 { DailyShare.shared.unityEvent() }   // (Unity is loaded now: its shot filming can reach the share)
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
            case "bowlingCard": receivePostGameBoard(PostGameBoard(bowling: event["message"] as? String ?? ""))
            case "golfCard": receivePostGameBoard(PostGameBoard(golf: event["message"] as? String ?? ""))
            case "lesson": LessonCenter.shared.receive(event["message"] as? String ?? "")
            case "feedback":
                receiveMatchSnapshot(event)
                feedback=event["message"] as? String ?? ""; stamina=event["stamina"] as? Double ?? 1
                if SportsRuntime.shared().clock()>=nextDiagnostic {
                    nextDiagnostic=SportsRuntime.shared().clock()+4   // every 4 s: at 1 s the log held only the last few minutes, too little to explain a crash
                    bridgeLine = "bridge nativePaused=\(paused) phase=\(phase) target=\(target) unityFrame=\(event["frame"] ?? "unknown") unityPaused=\(event["paused"] ?? "unknown") playerX=\(event["playerX"] ?? "unknown") inputAge=\(event["inputAge"] ?? "unknown") \(SportsDiagnostics.memory)"
                    SportsDiagnostics.write(bridgeLine)
                    // (in an online match the other phone logs it too: whether this phone's game is running, seen from both logs)
                    if multiplayerMatchID != nil { MultiplayerService.shared.shareDiagnostic(bridgeLine) }
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
            case "timingStart":
                // when the drill's countdown ends, on the shared clock: the TV's drill card bounces its ball from this
                if let end = Double(event["message"] as? String ?? ""), end.isFinite {
                    timingDrillStart = end; timingCountdownEnds = Date().addingTimeInterval(end - SportsRuntime.shared().clock())
                }
            case "timingSwing":
                if let beat = Int(event["message"] as? String ?? ""), checkingTiming {
                    timingSwings.insert(beat)
                    if multiplayerMatchID != nil { MultiplayerService.shared.runtimeSetupStep("check:\(timingSwings.filter { $0 >= Self.timingWarmUp }.count)") }
                }
            case "aimLanding": receiveAimLanding(event["message"] as? String ?? "")
            case "aimMiss": break   // the aim drill's ball got past the player: the feed timeout asks for another
            case "learnedLag":
                // what play has learned of this player's lag on this TV (ms), kept for the end of the match (saveLearnedLag)
                if let ms = Double(event["message"] as? String ?? ""), ms.isFinite, ms >= 0, ms <= 1000 { learnedLag = ms / 1000 }
            case "screenLag":
                // one TV for two phones: the TV credit this phone's game gives its player, for the controller-only phone (same picture)
                if multiplayerSplit, multiplayerMatchID != nil, let ms = Double(event["message"] as? String ?? ""), ms.isFinite {
                    MultiplayerService.shared.setScreenDelay(ms / 1000)
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
            case "holeInOne":
                if let result = HoleInOneResult(line: event["message"] as? String ?? "") {
                    DailyHoleInOne.shared.finished(result)
                    DailyShare.shared.finished(result)   // the one-tap share: the clip of the three shots is made now
                }
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

/// Per-TV timing, kept apart (quick start, 11-21): the picture delay the flashes measure, and the whole chain (picture + swing detection
/// + the player's habit) the timing check measures and play keeps refining. Only the whole chain lets a match skip the setup's
/// flashes and drill. Keyed by the output route (type, uid, name) plus the external screen's size, so two TVs whose sound is not on
/// AirPlay no longer share the "Speaker" slot.
enum SportsTiming {
    /// (11-20 and before: one slot per route name for both measurements; read only as a picture prior, see `storedPicture`)
    private static let legacyKey = "sports.tv.timing.v2"
    static let pictureKey = "sports.tv.picture.v3", chainKey = "sports.tv.chain.v3", pendingKey = "sports.tv.chainPending.v3"
    static func currentTV() -> String {
        let outputs = AVAudioSession.sharedInstance().currentRoute.outputs
        let port = outputs.first(where: { $0.portType == .airPlay }) ?? outputs.first(where: { $0.portType == .HDMI }) ?? outputs.first
        let screen = UIScreen.screens.dropFirst().first?.nativeBounds.size
        return routeKey(type: port?.portType.rawValue, uid: port?.uid, name: port?.portName, screen: screen)
    }
    /// The key for one route: "type|uid|name|WxH" (pure, for tests).
    static func routeKey(type: String?, uid: String?, name: String?, screen: CGSize?) -> String {
        let size = screen.map { "\(Int($0.width))x\(Int($0.height))" } ?? "-"
        return [type ?? "-", uid ?? "-", name ?? "screen", size].joined(separator: "|")
    }
    /// The route's name alone (the 11-20 key): what the old slot was filed under.
    static func legacyName(of key: String) -> String {
        let parts = key.split(separator: "|", omittingEmptySubsequences: false)
        return parts.count == 4 ? String(parts[2]) : key
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
    private static func read(_ key: String, _ tv: String, _ defaults: UserDefaults) -> Double? { (defaults.dictionary(forKey: key) as? [String: Double])?[tv] }
    private static func write(_ value: Double?, _ key: String, _ tv: String, _ defaults: UserDefaults) {
        var all = defaults.dictionary(forKey: key) as? [String: Double] ?? [:]
        if let value { guard value.isFinite else { return }; all[tv] = max(0, min(1.0, value)) } else { all[tv] = nil }
        defaults.set(all, forKey: key)
    }
    /// The whole chain for this TV (the timing check, or what play learned); nil = this TV was never timed.
    static func storedChain(for tv: String, defaults: UserDefaults = .standard) -> Double? { read(chainKey, tv, defaults) }
    static func storeChain(_ lag: Double, for tv: String, defaults: UserDefaults = .standard) {
        write(lag, chainKey, tv, defaults); write(nil, pendingKey, tv, defaults)
    }
    /// The picture delay the flashes measured (else the old shared slot, as a prior only: never as the whole chain).
    static func storedPicture(for tv: String, defaults: UserDefaults = .standard) -> Double? {
        read(pictureKey, tv, defaults) ?? read(legacyKey, legacyName(of: tv), defaults)
    }
    static func storePicture(_ delay: Double, for tv: String, defaults: UserDefaults = .standard) { write(delay, pictureKey, tv, defaults) }
    /// How far play's learned lag may move the stored chain at once; further than this it has to say so twice (one bad match,
    /// a TV switched out of Game Mode for an evening) before it replaces it.
    static let learnedJump = 0.15
    /// Play's learned lag at the end of a match (T6). Returns what is stored after.
    @discardableResult static func learn(_ lag: Double, for tv: String, defaults: UserDefaults = .standard) -> Double? {
        guard lag.isFinite, lag >= 0, lag <= 1 else { return storedChain(for: tv, defaults: defaults) }
        guard let stored = storedChain(for: tv, defaults: defaults), abs(lag - stored) > learnedJump else {
            storeChain(lag, for: tv, defaults: defaults); return lag
        }
        // an outlier: kept aside; a second one near it replaces the stored value, anything else replaces the one kept aside
        if let pending = read(pendingKey, tv, defaults), abs(pending - lag) <= learnedJump {
            storeChain((pending + lag) / 2, for: tv, defaults: defaults)
        } else { write(lag, pendingKey, tv, defaults) }
        return storedChain(for: tv, defaults: defaults)
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
