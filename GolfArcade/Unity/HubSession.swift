import SwiftUI

/// What the player stands next to in the Plaza, from Unity's `hubZone` event ("kind|id|label|detail").
struct HubZone: Equatable {
    enum Kind: String { case door, station, bay }
    var kind: Kind, id: String, label: String, detail: String
    init?(line: String) {
        let parts = line.split(separator: "|", maxSplits: 3, omittingEmptySubsequences: false).map(String.init)
        guard parts.count >= 3, let kind = Kind(rawValue: parts[0]), !parts[1].isEmpty else { return nil }
        self.kind = kind; id = parts[1]; label = parts[2]; detail = parts.count > 3 ? parts[3] : ""
    }
    /// What the phone's strip says: "Locker · walk in", "Shirt · A to use", "Exhibition · A to sit".
    var prompt: String {
        switch kind {
        case .door: detail == "Coming soon" ? "\(label) · coming soon" : detail == "TV needed" ? "\(label) · connect a TV (AirPlay) to play" : "\(label) · walk in"
        case .station: "\(label) · A to use"
        case .bay: "\(label) · A to sit"
        }
    }
}

/// The walkable menu (PLAN_MenuHub_WalkableWorld): the Plaza in Unity is the game's only menu and the phone is its controller, an
/// analog stick. This owns that session: when to open the plaza, the runtime start, the stick stream (the binary sample channel:
/// target = x, aim = y, power = deflection), the buttons, and Unity's reports of where the player is.
///
/// With a TV the plaza is on the TV. With none it is on the phone itself, in the top part of the screen above the same controls,
/// and the PLAY hall is shut (a match needs a TV; connecting one moves the plaza onto it). It never runs during a match
/// (SportsSession owns the runtime then) or first-run onboarding. A station's own screen (the locker, settings, a bay's match
/// options) opens as a panel on the phone; nothing else ever replaces the controller: no lobby screens, no Game Center sheets.
@MainActor @Observable
final class HubSession {
    static let shared = HubSession()
    enum Phase: Equatable { case off, booting, live, suspended, failed }

    private(set) var phase: Phase = .off
    /// Where the player is: "plaza", "locker", "clubhouse", "play", "tennis", "golf".
    private(set) var place = "plaza"
    private(set) var zone: HubZone?
    /// The last station or bay the player pressed A at.
    private(set) var lastAction: String?
    /// The station or bay in use: the TV frames the hero, the phone shows its panel (the existing menu screen for it).
    private(set) var station: String?
    var notice = ""
    /// Unity's measured age of the stick samples it applied (p50, p95), milliseconds.
    private(set) var inputAge = (p50: 0.0, p95: 0.0)
    private(set) var speed = 0.0
    private(set) var sessionID = ""
    private var token: Int32 = 0
    /// The plaza scene is what Unity has loaded right now (false once a match replaced it).
    private(set) var loaded = false
    /// The TV's loading bar while the plaza boots, 0...1: the runtime starting, Unity's scene load, the plaza's build (Unity's
    /// loadProgress / buildProgress); 1 = ready, then the loading screen fades into the arrival fly-in.
    private(set) var loadProgress = 0.0
    /// What the loading bar is doing, from its progress.
    var loadStage: String {
        loadProgress >= 1 ? "Ready! Into the Plaza" : loadProgress >= 0.95 ? "Opening the gates"
            : loadProgress >= 0.72 ? "Getting your player ready" : loadProgress >= 0.12 ? "Building the Plaza" : "Starting up"
    }
    /// Seconds the full bar holds before the loading screen fades, and the fade (the fly-in starts with it).
    static let readyHold = 0.45, revealFade = 0.35
    private func progress(_ value: Double) {
        guard value.isFinite else { return }
        let next = max(loadProgress, min(1, value))
        if next > loadProgress { loadProgress = next; stageChanged = Date() }
    }

    /// What the bars draw: loadProgress, eased forward. Between two measured milestones it creeps toward the next one at the pace
    /// earlier boots took (never past 90 % of the gap, so it cannot run ahead of the real work), and a measured jump fills at
    /// `fillRate` instead of snapping, so the bar never sits still and never leaps (Adnan 10-26: "stuck on 12, then instantly fills").
    private(set) var loadShown = 0.0
    /// The bar's top speed while it catches up with a measured jump (whole bars per second).
    static let fillRate = 1.6
    /// The boot's milestones: the runtime up, Unity's first frame, the plaza scene loaded, the plaza built, ready.
    static let bootMilestones = [0.12, 0.15, 0.30, 0.95, 1.0]
    /// Seconds each stage took last time (what the creep paces itself by); first boots use these.
    static let defaultStageSeconds = [0.12: 1.5, 0.15: 0.8, 0.30: 1.6, 0.95: 0.3]
    @ObservationIgnored private var stageChanged = Date.distantPast
    @ObservationIgnored private var stageReached: [Double: Date] = [:]
    @ObservationIgnored private var lastShownTick = Date.distantPast

    static func stageSeconds(from milestone: Double) -> Double {
        let learned = UserDefaults.standard.dictionary(forKey: "hubBootStageSeconds") as? [String: Double]
        return learned?[String(format: "%.2f", milestone)] ?? defaultStageSeconds[milestone] ?? 1
    }
    /// The bar's creep target now: the last milestone passed, plus a share of the gap to the next one that grows with time.
    func creepTarget(now: Date = Date()) -> Double {
        guard loadProgress < 1 else { return 1 }
        let from = Self.bootMilestones.last { $0 <= loadProgress } ?? 0, to = Self.bootMilestones.first { $0 > loadProgress } ?? 1
        let t = max(0, now.timeIntervalSince(stageChanged))
        return loadProgress + (to - loadProgress) * 0.9 * (1 - exp(-t / max(0.2, Self.stageSeconds(from: from))))
    }
    /// Moves loadShown one step (the 60 Hz tick; tests pass `now`).
    func advanceShown(now: Date = Date()) {
        let dt = min(0.1, max(0, now.timeIntervalSince(lastShownTick))); lastShownTick = now
        let want = phase == .booting ? max(loadProgress, creepTarget(now: now)) : loadProgress
        if want > loadShown { loadShown = min(want, loadShown + Self.fillRate * dt) }
        for m in Self.bootMilestones where loadProgress >= m && stageReached[m] == nil { stageReached[m] = now }
    }
    /// A boot finished: remember how long each stage took (averaged with earlier boots), so the next bar keeps the right pace.
    private func learnStageSeconds() {
        var learned = UserDefaults.standard.dictionary(forKey: "hubBootStageSeconds") as? [String: Double] ?? [:]
        for (i, m) in Self.bootMilestones.dropLast().enumerated() {
            guard let a = stageReached[m], let b = stageReached[Self.bootMilestones[i + 1]] else { continue }
            let key = String(format: "%.2f", m), took = min(30, b.timeIntervalSince(a))
            learned[key] = learned[key].map { $0 * 0.5 + took * 0.5 } ?? took
        }
        UserDefaults.standard.set(learned, forKey: "hubBootStageSeconds")
    }
    @ObservationIgnored private var timer: Timer?
    @ObservationIgnored private var stick = (x: 0.0, y: 0.0, mag: 0.0)
    @ObservationIgnored private var lastSampleSent = 0.0
    @ObservationIgnored private var bootStarted = Date.distantPast
    @ObservationIgnored private var windowRetries = 0
    private(set) var foreground = true

    func setForeground(_ active: Bool) {
        guard active != foreground else { if active { evaluate() }; return }
        // Drop a held stick on every interruption; never replay it after returning.
        setStick(x: 0, y: 0, magnitude: 0)
        foreground = active
        if active { evaluate() } else { endNearbyBrowse(); updatePointer() }
    }

    private var session: SportsSession { .shared }
    private var menu: TennisMenu { .shared }

    // MARK: the pointer menu (PLAN_PointerMenu.md): the plaza is the menu's backdrop, the phone points at the TV

    /// The pointer menu instead of the walkable plaza (on unless switched off for a comparison: defaults hub.pointerMenu = false).
    static var pointerMenu: Bool { UserDefaults.standard.object(forKey: "hub.pointerMenu") as? Bool ?? true }
    /// This plaza session is the pointer menu (decided at boot).
    private(set) var menuMode = false
    /// The TV's screen: home, sport, modes:tennis, modes:golf, locker, clubhouse, loading.
    private(set) var menuScreen = "home"
    /// The mode the TV's match setup is open for (MenuSetup), nil before the first.
    private(set) var menuSetupMode: String?
    /// What the TV has lit under the pointer ("" = nothing).
    private(set) var menuHoverLabel = ""
    @ObservationIgnored private var menuHoverID = ""
    private(set) var recentred = false
    /// This phone drives the menu: no party, or the party's leader. Guests' TVs follow the leader's.
    var menuLeader: Bool { party == nil || partyService.isOwner }
    var menuLeaderName: String { party.flatMap { p in p.participants.first { $0.id == p.ownerID }?.name } ?? "The host" }
    var menuPlayerName: String? { session.players.indices.contains(session.playerIndex) ? session.players[session.playerIndex].name : nil }
    @ObservationIgnored private var menuPhoneSent = false
    @ObservationIgnored private var menuPartySent = ""
    @ObservationIgnored private var menuStateScreen = ""

    func menuSelect(_ down: Bool) {
        if down { if session.haptics { UIImpactFeedbackGenerator(style: .medium).impactOccurred() } }
        MenuPointerSource.shared.select(down)
    }
    /// The menu thumbstick moves the cursor.
    func menuStick(x: Double, y: Double, magnitude: Double) { MenuPointerSource.shared.stick(x: x, y: y, magnitude: magnitude) }
    func menuBack() { menuCommand("menuBack"); haptic() }
    func menuRecenter() {
        MenuPointerSource.shared.recenter(); menuCommand("menuRecenter"); haptic()
        recentred = true; DispatchQueue.main.asyncAfter(deadline: .now() + 1.4) { [weak self] in self?.recentred = false }
    }
    func menuTouch(x: Double, y: Double, down: Bool) {
        guard phase == .live, foreground, token != 0 else { return }
        MenuPointerSource.shared.touch(token: token, x: x, y: y, down: down, shown: true)
    }
    /// A menu command, under the menu's own session.
    private func menuCommand(_ action: String, mode: String? = nil, extra: [String: Any] = [:]) {
        guard menuMode, foreground, phase == .live else { return }
        var message: [String: Any] = ["version": 1, "session": sessionID, "action": action]
        if let mode { message["mode"] = mode }
        message.merge(extra) { _, new in new }
        sendJSON(message)
    }
    /// The pointer runs while this phone drives the menu on the TV (not with a detail screen open on the phone, never with a match).
    private func updatePointer() {
        let want = menuMode && foreground && !onPhone && menuLeader && !panelOpen && onlineBench == nil && !ClubHub.shared.hubOpen
            && phase == .live && !session.active && token != 0
        if want { MenuPointerSource.shared.start(token: token) } else if MenuPointerSource.shared.isRunning { MenuPointerSource.shared.stop() }
    }
    /// The phone's detail screen opened or closed: the TV dims ("Finish on your phone") or comes back.
    private func syncMenuPhone(force: Bool = false) {
        guard menuMode, phase == .live else { return }
        let open = panelOpen || onlineBench != nil || ClubHub.shared.hubOpen || (station.map { Self.partyBays.contains($0) } ?? false && party != nil)
        guard open != menuPhoneSent || force else { return }
        menuPhoneSent = open; menuCommand("menuPhone", mode: open ? "on" : "off")
    }
    /// Who drives (leader) and whether the solo modes are locked (friends here): the TV styles its lists by it.
    private func syncMenuParty() {
        guard menuMode, phase == .live else { return }
        let key = "\(menuLeader)|\(soloLocked)"
        guard key != menuPartySent else { return }
        menuPartySent = key
        menuCommand("menuParty", extra: ["leader": menuLeader, "soloLocked": soloLocked])
        if let p = party, !menuLeader { menuCommand("menuTag", mode: "HOST", extra: ["remote": p.ownerID]) }
    }
    /// The mode name for the TV's loader, from the bench the match was started from.
    var menuLaunchLabel: String {
        switch station ?? returnBay ?? "" {
        case "bay-tennis-exhibition": "Exhibition"; case "bay-tennis-campaign": "Campaign"; case "bay-tennis-training": "Training"
        case "bay-golf-round": "Round"; case "bay-golf-pass", "bay-bowling-pass": "Pass the phone"; case "bay-tennis-online", "bay-golf-online", "bay-bowling-online": "Online"
        case "bay-bowling-play": "10 frames"; case "bay-bowling-exhibition": "Exhibition"
        default: ""
        }
    }
    /// A menu event while a match loads behind the menu (SportsSession owns the runtime's events then).
    func menuEvent(_ type: String, _ message: String) { handleMenu(type, message) }

    private func handleMenu(_ type: String, _ message: String) {
        switch type {
        case "menuScreen": menuScreen = message
        case "menuHover":
            let f = message.split(separator: "|", maxSplits: 1, omittingEmptySubsequences: false).map(String.init)
            let id = f.first ?? "", label = f.count > 1 ? f[1] : ""
            if id != menuHoverID, !id.isEmpty, session.haptics { UISelectionFeedbackGenerator().selectionChanged() }
            menuHoverID = id; menuHoverLabel = label
        case "menuOpen":
            guard !message.isEmpty else { return }
            notice = ""
            useStation(message)
            syncMenuPhone(force: true); updatePointer()
        case "menuLook":
            let f = message.split(separator: "|", maxSplits: 1, omittingEmptySubsequences: false).map(String.init)
            guard f.count == 2, Player.outfitSlots.contains(f[0]), session.players.indices.contains(session.playerIndex) else { return }
            if f[1].isEmpty { session.players[session.playerIndex].clearOutfit(f[0]) } else { session.players[session.playerIndex].setOutfitHex(f[0], f[1]) }
            session.savePlayers()
        case "menuStart": if session.haptics { UINotificationFeedbackGenerator().notificationOccurred(.success) }
        // the TV's match setup (MenuSetup): describe the screen, apply a change, start
        case "menuSetup":
            menuSetupMode = message
            if let json = MenuSetup.json(message) { menuCommand("menuSetupState", mode: json) }
        case "menuSet":
            guard let mode = menuSetupMode else { return }
            if session.haptics { UISelectionFeedbackGenerator().selectionChanged() }
            MenuSetup.set(mode, message)
            if let json = MenuSetup.json(mode) { menuCommand("menuSetupState", mode: json) }
        case "menuSetupStart":
            guard MenuSetup.modes.contains(message) else { return }
            if session.haptics { UINotificationFeedbackGenerator().notificationOccurred(.success) }
            MenuSetup.start(message)
        case "menuCancel": if session.active { session.end() }
        case "menuState":
            // the leader's screen and cursor, for the party's TVs (≤15 a second; a screen change goes reliably)
            guard let party, partyService.isOwner, party.participants.count >= 2 else { return }
            let screen = message.split(separator: "|").first.map(String.init) ?? ""
            let changed = screen != menuStateScreen; menuStateScreen = screen
            partyService.sendHub("hubEvent", payload: "menu|" + message, reliable: changed)
        default: break
        }
    }

    /// Should the plaza be up right now? Whenever no match has the runtime: on the TV with one connected, on the phone without.
    var wanted: Bool {
        !session.active && !OnboardingFlow.shared.holdsMenu && !SportsSession.benchmark && phase != .failed && !menu.classic && !runtimeMissing
    }
    /// The plaza is on this phone's own screen (no TV): it draws above the controls (HubControllerView's phone layout).
    private(set) var onPhone = false
    /// The share of the phone's height the plaza takes on a phone with no TV (Unity's HubWorld.PhoneViewShare is the same).
    static let phoneViewShare = 0.56
    /// No Unity in this build (the simulator): the plaza cannot open at all.
    private(set) var runtimeMissing = false
    /// A station's own screen is open on the phone (the locker, settings, a bay's match options). Never a lobby or home screen.
    var panelOpen: Bool { station != nil && Self.panelScreens(menu.screen) }
    /// The phone is the plaza's controller (the plaza is opening, on, or could not open and offers Try again).
    var drivesPhone: Bool { wanted && (phase == .booting || phase == .live) }
    /// Screens a station's panel may show. Anything else (home, the old play / online / lobby screens) ends the station.
    static func panelScreens(_ screen: MenuScreen) -> Bool {
        switch screen {
        case .character, .settings, .howTo, .campaign, .training, .exhibition, .localPlayers, .map, .loading, .story, .results, .postMatch: true
        default: false
        }
    }

    /// Called whenever something the decision depends on changes (display, match, menu screen, settings).
    func evaluate() {
        guard foreground else { return }
        // the panel's own Back / Done went past the station's screens (home, or an old menu screen): the station is finished
        if let s = station, !Self.partyBays.contains(s), s != Self.nearbyBay, !Self.panelScreens(menu.screen) {
            station = nil; returnBay = nil; command("hubB")
            if menu.screen != .main && menu.screen != .title { menu.openFromPlaza(.main) }
        }
        // the plaza never shows a lobby screen: a party lives in the plaza itself
        if drivesPhone, menu.screen.isOnline { menu.openFromPlaza(.main) }
        if wanted { enter() } else if phase == .live || phase == .booting { suspend() }
        syncMenuPhone(); updatePointer()
    }

    // MARK: lifecycle

    private func enter() {
        let wantPhone = !session.displayConnected
        // a TV was connected or went away: the plaza moves to the screen there is now (it boots again there)
        if phase != .off, phase != .failed, onPhone != wantPhone {
            SportsDiagnostics.write("hub moves to the \(wantPhone ? "phone" : "TV")")
            endUnitySession()
            timer?.invalidate(); timer = nil; phase = .off; loaded = false; zone = nil; station = nil; arriving = false
            if onPhone { SportsDisplays.shared.endPhonePlaza() }
        }
        switch phase {
        case .live: reveal(); return
        case .booting: return
        case .suspended where loaded:
            SportsRuntime.shared().pause(false); phase = .live; reveal(); startTimer(); sendLook(); return
        default: break
        }
        onPhone = wantPhone
        guard let window = onPhone ? SportsDisplays.shared.phonePlazaWindow() : SportsDisplays.shared.external else {
            // (at launch the app's own window may not be registered yet: look again shortly)
            if onPhone, windowRetries < 20 { windowRetries += 1; DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { [weak self] in self?.evaluate() } }
            return
        }
        windowRetries = 0
        phase = .booting; bootStarted = Date(); lastBootSignal = bootStarted; heardFromUnity = false
        notice = ""; loadProgress = 0; loadShown = 0; stageReached = [:]; lastShownTick = Date(); progress(0.03); revealedOnPhone = false
        sessionID = UUID().uuidString; token = Int32.random(in: 1...Int32.max); loaded = false
        place = "plaza"; zone = nil; lastAction = nil
        menuMode = Self.pointerMenu; menuScreen = "home"; menuHoverLabel = ""; menuHoverID = ""; menuPhoneSent = false; menuPartySent = ""
        if onPhone { returnBay = nil }   // (no benches without a TV)
        SportsDiagnostics.write("hub boot session=\(sessionID) on \(onPhone ? "phone" : "TV")")
        // A display cycle first: the first Unity start blocks the main thread while it boots.
        let launch = sessionID, phone = onPhone
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) { [weak self] in
            guard let self, self.sessionID == launch, self.phase == .booting, self.wanted else { return }
            // UIKit may have become inactive before SwiftUI delivered scenePhase.
            // Starting Unity here could render after iOS has suspended Metal.
            guard self.foreground, UIApplication.shared.applicationState == .active else { self.phase = .off; return }
            do { try SportsRuntime.shared().load(in: window, controllerReplica: phone); RacketFeel.apply() }
            catch {
                // no Unity in this build (the simulator): there is no plaza to show at all
                if (error as NSError).domain == "SportsRuntime" && (error as NSError).code == 1 { self.runtimeMissing = true }
                if phone { SportsDisplays.shared.endPhonePlaza() }
                self.fail(error.localizedDescription); return
            }
            if phone { SportsDisplays.shared.showPhonePlaza() }
            self.progress(0.12)
            SportsRuntime.shared().pause(false)
            self.lastBootSignal = Date()   // (a cold Unity start blocked until now)
            self.startTimer()
            self.sendStart()
        }
    }

    /// A match takes the runtime: stop walking and idle Unity (the match's own screens take over).
    private func suspend() {
        setStick(x: 0, y: 0, magnitude: 0); endNearbyBrowse()
        if phase == .booting { phase = .off; timer?.invalidate(); timer = nil; if onPhone { SportsDisplays.shared.endPhonePlaza() }; return }
        phase = .suspended; timer?.invalidate(); timer = nil
        if onPhone { SportsDisplays.shared.endPhonePlaza() } else { SportsDisplays.shared.showMenu() }
        if !session.active { SportsRuntime.shared().pause(true) }
    }

    /// The bay you launched from: back from the match, you sit on its bench again (RETURN).
    private(set) var returnBay: String?

    // MARK: after an online match (a party's, or a quick match from an online bench)

    /// The match's result is on the TV: the phone offers Back to the Plaza (the line says who won). Nil otherwise.
    private(set) var matchOver: String?
    func onlineMatchFinished(_ line: String) { matchOver = line; searching = false }
    /// Back to the Plaza from an online match, at its end or mid-match (Exit). A party goes back to its bench together (staying
    /// seated and ready again is the rematch); a quick match with other players is left.
    func leaveOnlineMatch(_ lobby: MultiplayerService? = nil) {
        matchOver = nil
        let service = lobby ?? partyService
        guard service.lobby != nil else { if session.multiplayerMatchID != nil { session.end() }; return }
        if service.isParty, service.lobby?.phase != .interrupted {
            service.endPartyMatch()
            // a guest whose host has gone cannot be brought back by the host: leave after a moment
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
                guard let self, self.session.multiplayerMatchID != nil else { return }
                service.leave(); self.session.end()
            }
        } else { service.leave(); if session.multiplayerMatchID != nil { session.end() } }
    }
    /// The app is open again after `seconds` in the background (AwayPolicy): past the away limit an online match or a party is left
    /// (the others have already gone on without this phone), and the phone is back in the Plaza with a line saying why.
    func returned(after seconds: TimeInterval) {
        let service = partyService
        let inMatch = session.multiplayerMatchID != nil
        let outcome = AwayPolicy.outcome(away: seconds, inOnlineMatch: inMatch, inParty: service.lobby != nil || ClubHub.shared.party != nil,
                                         droppedFromMatch: service.droppedFromMatch)
        guard outcome != .stay else { return }
        SportsDiagnostics.write("away \(Int(seconds)) s: \(outcome)")
        matchOver = nil
        service.leave()
        if inMatch { session.end() }
        ClubHub.shared.leaveParty()
        notice = AwayPolicy.notice(for: outcome)
        if menu.screen != .main { menu.openFromPlaza(.main) }
        evaluate()
    }
    /// The online match stopped on this phone (its lobby is back in the plaza, or it was left).
    func onlineMatchEnded() { matchOver = nil; if menu.screen != .main { menu.openFromPlaza(.main) } }
    /// A match ended. Played to the end: back on the same bench. Stopped while loading or quit early: back on your feet (CANCEL).
    func sessionEnded(finished: Bool) { if !finished { returnBay = nil }; updatePointer() }
    /// The bay to launch from (the match loads behind the plaza), or nil for a normal launch.
    func bayForLaunch() -> String? {
        // the pointer menu: every match from it loads behind the menu on the TV (a party's guests too)
        if menuMode { guard phase == .live, loaded, !onPhone else { return nil }; return station.flatMap { $0.hasPrefix("bay-") ? $0 : nil } ?? "menu" }
        guard phase == .live, loaded, let s = station, s.hasPrefix("bay-") else { return nil }
        return s
    }
    /// A match took the runtime (SportsSession.start): its scene replaces the plaza (from a bay: once it is ready behind it).
    /// Launches made from a bay (behind the plaza), for tests and diagnostics.
    private(set) var bayLaunches = 0
    func runtimeTaken(bay: String? = nil) {
        if let bay { returnBay = bay; bayLaunches += 1 }
        timer?.invalidate(); timer = nil; station = nil; endNearbyBrowse(); nearbyJoining = nil
        if phase != .off { phase = .suspended }
        loaded = false
    }

    /// The TV went away: the plaza on it is gone (it opens again on the phone).
    func displayLost() {
        guard !onPhone else { return }
        timer?.invalidate(); timer = nil; endNearbyBrowse()
        endUnitySession()
        phase = .off; loaded = false; zone = nil; station = nil; returnBay = nil; arriving = false
    }

    private func fail(_ message: String) {
        SportsDiagnostics.write("hub failed: \(message)")
        timer?.invalidate(); timer = nil; loaded = false; endNearbyBrowse()
        phase = .failed; notice = message
        if !onPhone { SportsDisplays.shared.showMenu() }   // (the TV says so; the phone offers Try again)
    }
    /// Try the plaza again after a failure.
    func retry() { if phase == .failed { phase = .off; notice = ""; autoRetried = false; evaluate() } }

    /// Unity drops a plaza start while it is still loading another one, so a boot that is given up (the plaza moving to a TV that
    /// just connected, or a stalled boot) is ended first: otherwise the new boot waits forever and only a manual retry got through.
    private func endUnitySession() {
        if (loaded || phase == .booting) && !session.active { sendJSON(["version": 1, "session": sessionID, "action": "end"]) }
    }
    /// The boot's last sign of life from Unity (its start, a progress event), and whether Unity has answered this session at all.
    @ObservationIgnored private var lastBootSignal = Date.distantPast
    @ObservationIgnored private var lastStartSent = Date.distantPast
    @ObservationIgnored private var heardFromUnity = false
    @ObservationIgnored private var autoRetried = false
    /// A boot with no progress for this long is given up (Unity's own display and first-frame waits are 8 s each).
    static let bootStall: TimeInterval = 20
    /// Unity has not answered a start for this long: send it again (a start for the same session is ignored once it is loading).
    static let startResend: TimeInterval = 3
    /// No progress: end it and boot once more by itself, as a tap on Try again would; only a second stall shows the failure.
    private func bootStalled() {
        guard !autoRetried else { fail("The plaza did not open. Showing the classic menu."); return }
        autoRetried = true
        SportsDiagnostics.write("hub boot stalled after \(String(format: "%.1f", Date().timeIntervalSince(bootStarted))) s: booting again")
        endUnitySession()
        timer?.invalidate(); timer = nil; loaded = false; phase = .off
        if onPhone { SportsDisplays.shared.endPhonePlaza() }
        evaluate()
    }

    /// On a phone with no TV: the loading screen has faded and the plaza shows above the controls.
    private(set) var revealedOnPhone = false
    private func reveal() {
        guard phase == .live, !arriving else { return }
        if onPhone { revealedOnPhone = true } else { SportsDisplays.shared.external?.isHidden = true }
    }
    /// The loading screen fading into the arrival (between the full bar and the plaza on the TV).
    private(set) var arriving = false
    /// A fresh boot reached 100 %: the full bar holds a moment, then the loading screen fades off the TV as Unity's camera flies in
    /// from high over the plaza to behind the hero (hubArrive).
    /// The friends-list prompt (once ever), once the player is in the plaza: Apple only lists friends who both allowed it.
    private func askForFriendsOnce() { ClubSignIn.askForFriendsOnce() }
    private func arrive() {
        arriving = true
        let launch = sessionID
        // the bar fills the rest of the way (fillRate) before the full bar's hold starts
        DispatchQueue.main.asyncAfter(deadline: .now() + Self.readyHold + max(0, 1 - loadShown) / Self.fillRate) { [weak self] in
            guard let self, self.sessionID == launch else { return }
            self.command("hubArrive")
            if self.onPhone {
                withAnimation(.easeOut(duration: Self.revealFade)) { self.revealedOnPhone = true }
                DispatchQueue.main.asyncAfter(deadline: .now() + Self.revealFade) { self.arriving = false; self.askForFriendsOnce() }
                return
            }
            guard self.phase == .live, self.wanted, let tv = SportsDisplays.shared.external else { self.arriving = false; return }
            UIView.animate(withDuration: Self.revealFade, animations: { tv.alpha = 0 }) { _ in
                tv.isHidden = true; tv.alpha = 1; self.arriving = false; self.askForFriendsOnce()
            }
        }
    }

    /// A menu screen on the phone over the plaza (☰ shortcuts, the Party button), with `taps` made on it.
    func openPanel(_ screen: MenuScreen, taps: [String] = []) {
        menu.openFromPlaza(screen)
        for tap in taps { menu.tap(tap) }
        evaluate()
    }

    // MARK: stations and bays (phase 2: each opens the existing menu screen for it on the phone)

    /// What a station or bay opens: a menu screen (as a panel on the phone, with `taps` made on it), or an action.
    struct Route { var screen: MenuScreen?; var taps: [String] = []; var action: (@MainActor () -> Void)? = nil }
    /// Every spot in the Plaza (Unity's HubLayout.Spots; HubLayoutTests checks the same list).
    static let spotIDs = ["rack-shirt", "rack-shorts", "rack-shoes", "rack-racket", "rack-club", "look-mirror", "emote-mirror",
                          "desk-settings", "screen-howto", "shelf-trophies", "mailbox-feedback", "board-invite",
                          "bay-tennis-exhibition", "bay-tennis-campaign", "bay-tennis-training", "bay-tennis-online",
                          "bay-golf-round", "bay-golf-online", "bay-golf-pass"]
    static func route(_ id: String) -> Route? {
        switch id {
        case "rack-shirt": Route(screen: .character, taps: ["lk-tab-customize", "lk-shirt"])
        case "rack-shorts": Route(screen: .character, taps: ["lk-tab-customize", "lk-shorts"])
        case "rack-shoes": Route(screen: .character, taps: ["lk-sport-tennis", "lk-slot-shoes"])
        case "rack-racket": Route(screen: .character, taps: ["lk-sport-tennis", "lk-slot-racket"])
        case "rack-club": Route(screen: .character, taps: ["lk-sport-golf", "lk-slot-club"])
        case "look-mirror": Route(screen: .character, taps: ["lk-tab-customize"])
        case "emote-mirror": Route(screen: .character, taps: ["lk-tab-emotes"])
        case "desk-settings": Route(screen: .settings)
        case "screen-howto": Route(screen: .howTo)
        case "shelf-trophies", "bay-tennis-campaign": Route(screen: .campaign)
        case "mailbox-feedback": Route(action: { BetaFeedback.open() })
        case "board-invite": Route(action: { HubSession.shared.inviteFriends() })
        // every bench is one sport and one mode, straight to its own screen
        case "bay-tennis-exhibition": Route(screen: .exhibition)
        case "bay-tennis-training": Route(screen: .training)
        case "bay-golf-round": Route(action: { TennisMenu.shared.openFromPlaza(.main); TennisMenu.shared.begin(MenuLaunch(sport: .golf, mode: .round)) })   // the course picker
        case "bay-golf-pass": Route(screen: .localPlayers)   // how many players, then straight into the round
        // bowling (pointer menu rows): the venue picker; how many bowlers then the venue
        case "bay-bowling-play": Route(action: { TennisMenu.shared.openFromPlaza(.main); TennisMenu.shared.begin(MenuLaunch(sport: .bowling, mode: .round)) })
        case "bay-bowling-pass": Route(action: { TennisMenu.shared.passThePhone(.bowling) })
        case "bay-bowling-exhibition": Route(action: { TennisMenu.shared.openFromPlaza(.main); TennisMenu.shared.begin(MenuLaunch(sport: .bowling, mode: .exhibition)) })
        // the online benches: with your party, its bench (that sport); alone, a quick match with other players of that sport
        case "bay-tennis-online": Route(action: { HubSession.shared.useOnlineBench(.tennis) })
        case "bay-golf-online": Route(action: { HubSession.shared.useOnlineBench(.golf) })
        case "bay-bowling-online": Route(action: { HubSession.shared.useOnlineBench(.bowling) })
        // two phones in one room, one TV (a menu entry, not a place to walk to): hosts a nearby tennis game; the friend's phone offers "Join …?"
        case "bay-tennis-nearby": Route(action: { HubSession.shared.useNearbyBench() })
        default: nil
        }
    }

    /// Unity confirmed A at a spot (hubAction): open its panel.
    static let soloStations: Set<String> = ["bay-tennis-exhibition", "bay-tennis-campaign", "bay-tennis-training", "bay-golf-round", "bay-golf-pass", "shelf-trophies", "bay-tennis-nearby",
                                             "bay-bowling-play", "bay-bowling-exhibition", "bay-bowling-pass"]
    var soloLocked: Bool { partyService.hasFriendsInLobby }
    var zonePrompt: String? {
        guard let zone else { return nil }
        return soloLocked && Self.soloStations.contains(zone.id) ? "\(zone.label) · locked while in a party" : zone.prompt
    }
    static let soloLockMessage = "Single-player is locked while friends are in your party. Choose Party game to play together."
    static let friendJoiningMessage = "Your friend is still joining. One moment…"
    /// START on the TV's own match setup (MenuSetup): the bay is in use as if its panel had launched the match.
    func startFromMenu(_ id: String, _ go: () -> Void) {
        if soloLocked, Self.soloStations.contains(id) { notice = Self.soloLockMessage; toast(notice); return }
        station = id
        go()
        evaluate()
    }
    func useStation(_ id: String) {
        if soloLocked, Self.soloStations.contains(id) {
            notice = Self.soloLockMessage; command("hubB"); toast(notice); return
        }
        // a friend is still joining this phone's party (connected, their lobby on its way): an online game would leave them behind
        if Self.partyBays.contains(id), party == nil, partyService.isParty, partyService.joiningPeers > 0 {
            notice = Self.friendJoiningMessage; command("hubB"); toast(notice); return
        }
        if Self.partyBays.contains(id), let party {
            // a party's game: the bench's sport becomes the party's (leader), the phone shows the party, the leader picks the map and
            // settings and taps Start, and everyone taps Ready on their own phone
            station = id
            let sport = Self.benchSport(id)
            if partyService.isOwner, party.sport != sport { try? partyService.configure(sport, venue: sport == .golf ? session.golfCourse : sport == .bowling ? session.bowlingVenue : session.tennisVenue) }
            haptic(); evaluate(); return
        }
        if id == Self.nearbyBay { station = id; useNearbyBench(); evaluate(); return }
        guard let route = Self.route(id) else { command("hubB"); return }
        if let action = route.action {
            // a bench's action keeps you seated on it (its panel is the course picker / the search); a station's just happens
            if id.hasPrefix("bay-") { station = id; action(); evaluate() } else { action(); command("hubB") }
            return
        }
        if let screen = route.screen { menu.openFromPlaza(screen) }
        for tap in route.taps { menu.tap(tap) }
        station = id
        evaluate()
    }

    // MARK: quick match from an online bench (no party): other players of that sport, found by Game Center with no screen

    /// Sitting on an online bench with no party: that bench's sport (its panel finds other players of it). Nil otherwise.
    private(set) var onlineBench: MultiplayerSport?
    /// Game Center is looking for players for the online bench (it shows no screen of its own).
    private(set) var searching = false
    @ObservationIgnored private var searchTask: Task<Void, Never>?
    @ObservationIgnored private var returning = false
    /// An online bench with no party: look for players of its sport at once (not when you are put back on it after a match).
    func useOnlineBench(_ sport: MultiplayerSport) { onlineBench = sport; if !returning { findPlayers() } }
    func findPlayers() {
        guard party == nil, let sport = onlineBench else { return }
        guard partyService.authenticated else { notice = "Sign in to Game Center to play online (Friends › Sign in)."; return }
        searching = true; notice = ""
        searchTask?.cancel()
        searchTask = Task { @MainActor [weak self] in
            guard let self else { return }
            TennisMenu.shared.online.identity(TennisMenu.shared)
            self.partyService.setScreen(self.session.displayConnected)
            // (a party of one, waiting for an invite to be answered, is given up for the quick match; never one a friend is joining)
            if self.partyService.isParty, self.partyService.joiningPeers > 0 || self.partyService.hasFriendsInLobby {
                self.searching = false; self.notice = Self.friendJoiningMessage; return
            }
            if self.partyService.isParty { ClubHub.shared.leaveParty() } else if self.partyService.lobby != nil { self.partyService.leave() }
            do { try await self.partyService.quickMatch(sport, golfPlayers: 2) }
            catch is CancellationError {}
            catch {
                guard self.searching, self.onlineBench == sport else { return }
                self.searching = false; self.notice = error.localizedDescription
            }
        }
    }
    func stopSearching() {
        searchTask?.cancel(); searchTask = nil
        if searching { searching = false; partyService.cancelSearch() }
        if !partyService.isParty, partyService.lobby?.phase == .lobby { partyService.leave() }
    }
    /// B, Done or Leave seat: back to walking.
    func leaveStation() {
        guard station != nil || panelOpen else { return }
        if onlineBench != nil { stopSearching(); onlineBench = nil }
        if station == Self.nearbyBay { stopHostingNearby() }
        if station != nil { station = nil; returnBay = nil; command("hubB") }
        if menu.screen != .main && menu.screen != .title { menu.openFromPlaza(.main) }
        evaluate()
    }
    /// Friends: the Friends list over the controller (who is online, one tap to invite anyone, invites you got). It never
    /// opens Game Center or a lobby screen. `afterSheet`: called as one of the controller's own sheets (☰) closes.
    func inviteFriends(afterSheet: Bool = false) {
        haptic()
        if afterSheet { DispatchQueue.main.asyncAfter(deadline: .now() + 0.45) { [weak self] in self?.presentInvite() } }
        else { presentInvite() }
    }
    /// What Friends does: opens the Friends list. Tests count the calls instead.
    @ObservationIgnored var presentInvite: @MainActor () -> Void = { ClubHub.shared.hubOpen = true; ClubHub.shared.start() }
    /// Joined a friend's party: your hero goes to stand beside theirs (as soon as their position arrives).
    @ObservationIgnored private var meetHost: String?
    @ObservationIgnored private var partyJoinPending = false
    func joinedParty(host: String) {
        pendingPartyBay = nil; gatheredBay = nil; gatheredMembers = []
        meetHost = host == partyService.localID ? nil : host
        // Clear the actual Unity station too; clearing only the phone state leaves
        // Player.locked set when an invite is accepted from a locker or a bench.
        partyJoinPending = true; finishPartyJoin()
        station = nil; returnBay = nil; onlineBench = nil
        if menu.screen != .main { menu.openFromPlaza(.main) }
    }
    private func finishPartyJoin() {
        guard partyJoinPending, phase == .live, foreground else { return }
        partyJoinPending = false; command("hubB"); setStick(x: 0, y: 0, magnitude: 0)
    }
    /// A short message on the TV in the plaza (an invite arrived, a friend is joining): Unity draws it over the plaza.
    func toast(_ text: String) { command("hubToast", mode: text) }
    func showChat(_ message: PartyChatMessage) {
        guard party != nil, message.kind != .system else { return }
        command("hubChat", mode: message.text, remote: message.mine ? "" : message.senderID)
    }
    /// ☰ shortcut: walk there (a quick fade) and use it.
    func openStation(_ id: String) { command("hubUse", mode: id); haptic() }
    func backToPlaza() {
        if phase == .failed { retry(); return }
        // a party's lobby stays: the plaza is where it lives now
        if menu.screen != .main && menu.screen != .title { menu.openFromPlaza(.main) }
        evaluate()
    }

    // MARK: input

    /// The stick: direction (-1...1 each, +y = away from the camera) and deflection 0...1.
    func setStick(x: Double, y: Double, magnitude: Double) {
        let mag = max(0, min(1, magnitude.isFinite ? magnitude : 0))
        stick = foreground ? (x.isFinite ? max(-1, min(1, x)) : 0, y.isFinite ? max(-1, min(1, y)) : 0, mag) : (0, 0, 0)
        if mag == 0 || phase == .live { sendStick(force: mag == 0) }
    }
    func pressA() { command("hubA"); haptic() }
    func pressB() { command("hubB") }
    func emote(_ id: String) { command("hubEmote", mode: id); haptic() }
    func go(_ target: String) { command("hubGo", mode: target); haptic() }
    @ObservationIgnored private var lookSent = ""
    /// A locker change was saved: show it on the plaza hero now (LOCKER_LIVE).
    func lookChanged() {
        guard loaded, phase == .live || phase == .suspended, session.players.indices.contains(session.playerIndex) else { return }
        let signature = lookFields(session.players[session.playerIndex]).sorted { $0.key < $1.key }.map { "\($0.key)=\($0.value)" }.joined(separator: ";")
        guard signature != lookSent else { return }
        lookSent = signature; sendLook()
        // friends in your plaza see the change too (your party look)
        if party != nil { menu.online.identity(menu) }
    }
    /// The locker's look reached the plaza hero (live, on every change).
    func sendLook() {
        guard loaded, session.players.indices.contains(session.playerIndex) else { return }
        var message = lookFields(session.players[session.playerIndex])
        message["version"] = 1; message["session"] = sessionID; message["action"] = "hubLook"
        sendJSON(message)
    }

    private func haptic() { if session.haptics { UIImpactFeedbackGenerator(style: .light).impactOccurred() } }

    private func lookFields(_ p: Player) -> [String: Any] {
        ["female": p.standardFemale, "skin": p.standardSkin, "skinHex": p.skinHex,
         "shirt": p.outfitHex("shirt") ?? "", "shorts": p.outfitHex("shorts") ?? "", "accent": p.outfitHex("accent") ?? "", "racket": p.outfitHex("racket") ?? "",
         "back": p.backCarry.accessoryID]   // MENU HERO: the locker's back pick (HeroAccessories golf_bag | racket_back)
    }

    private func sendStart() {
        let p = session.players[min(session.playerIndex, max(0, session.players.count - 1))]
        var message = lookFields(p)
        message.merge(["version": 1, "session": sessionID, "action": "start", "sport": "hub", "token": Int(token),
                       "sound": session.sound, "haptics": session.haptics, "touch": true, "external": !onPhone, "phoneOnly": onPhone,
                       "fps": 60, "left": p.handedness == .left, "emotes": p.equippedEmotes]) { _, new in new }
        if let returnBay, !onPhone { message["bay"] = returnBay }
        lastStartSent = Date()
        if menuMode {
            message["menu"] = true; message["leader"] = menuLeader; message["soloLocked"] = soloLocked; message["playerName"] = p.name
            message["colour"] = party?.participants.firstIndex { $0.id == partyService.localID } ?? 0
            if returnBay != nil { message["screen"] = "home" }   // back from a match: straight onto the menu, no fly-in
        }
        sendJSON(message)
    }

    private func command(_ action: String, mode: String? = nil, remote: String? = nil) {
        guard phase == .live, foreground else { return }
        var message: [String: Any] = ["version": 1, "session": sessionID, "action": action]
        if let mode { message["mode"] = mode }
        if let remote { message["remote"] = remote }
        sendJSON(message)
    }
    #if DEBUG
    /// Tests: every message that would go to Unity.
    var debugSent: (([String: Any]) -> Void)?
    #endif
    private func sendJSON(_ object: [String: Any]) {
        #if DEBUG
        debugSent?(object)
        #endif
        guard let data = try? JSONSerialization.data(withJSONObject: object), let text = String(data: data, encoding: .utf8) else { return }
        SportsRuntime.shared().send(text)
    }

    /// One stick reading on the binary channel Unity polls every frame (no JSON, no allocation on the Unity side).
    private func sendStick(force: Bool = false) {
        guard loaded || force, token != 0 else { return }
        let now = SportsRuntime.shared().clock()
        let sample = SportsSample(version: Int32(SportsSampleVersion), session: token, time: now,
            target: Float(stick.x), power: Float(stick.mag), aim: Float(stick.y),
            swing: 0, swingStart: 0, swingAbort: 0, flags: Int32(SportsSampleValid),
            handSide: 0, lift: 0, strokeFacing: 0, qx: 0, qy: 0, qz: 0, qw: 0, rx: 0, ry: 0, rz: 0, gx: 0, gy: 0, gz: 0,
            onsetTime: 0, confirmationTime: 0, abortTime: 0)
        SportsRuntime.shared().push(sample)
        lastSampleSent = now
    }

    private func startTimer() {
        timer?.invalidate()
        // 60 Hz: the stick goes out on every tick while it is held (and a zero when it is let go); Unity's events come back here.
        let t = Timer(timeInterval: 1.0 / 60, repeats: true) { [weak self] _ in MainActor.assumeIsolated { self?.tick() } }
        RunLoop.main.add(t, forMode: .common); timer = t
    }

    private func tick() {
        guard foreground else { return }
        guard !session.active else { timer?.invalidate(); timer = nil; return }
        advanceShown()
        partyTick()
        if menuMode { syncMenuParty(); syncMenuPhone(); updatePointer() }
        if stick.mag > 0 && phase == .live { sendStick() }
        if phase == .booting {
            let now = Date()
            if now.timeIntervalSince(lastBootSignal) > Self.bootStall { bootStalled(); return }
            if !heardFromUnity && now.timeIntervalSince(lastStartSent) > Self.startResend { sendStart() }
        }
        for _ in 0..<64 {
            guard let json = SportsRuntime.shared().pollEvent(), let data = json.data(using: .utf8),
                  let event = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] else { break }
            receive(event)
        }
    }

    #if DEBUG
    /// Tests and snapshots: pretend the plaza is up (no Unity in the simulator) with this place and zone.
    func debugLive(place: String = "plaza", zone: String = "", session: String = "debug-hub", onPhone: Bool = false) {
        sessionID = session; phase = .live; loaded = true; self.onPhone = onPhone; revealedOnPhone = onPhone; runtimeMissing = false
        self.place = place; self.zone = HubZone(line: zone)
    }
    /// Tests: the boot message the plaza would send (no Unity in the simulator).
    func debugBoot(session: String, onPhone: Bool = false, menu: Bool = false) { sessionID = session; token = 7; phase = .booting; loadProgress = 0; loadShown = 0; lastBootSignal = Date(); heardFromUnity = false; self.onPhone = onPhone; menuMode = menu; sendStart() }
    /// Tests: the pointer menu up (no Unity in the simulator).
    func debugMenu(leader: Bool = true) { menuMode = true; menuScreen = "home"; menuPartySent = ""; menuPhoneSent = false }
    func debugPartyTick() { partyTick() }
    /// Tests: the arrival fly-in finished (or never ran).
    func debugArrived() { arriving = false }
    /// Snapshots: sitting on an online bench (searching or not), no Game Center.
    func debugOnlineBench(_ sport: MultiplayerSport, searching: Bool) { station = sport == .golf ? "bay-golf-online" : "bay-tennis-online"; onlineBench = sport; self.searching = searching }
    func debugReset() { timer?.invalidate(); timer = nil; phase = .off; autoRetried = false; heardFromUnity = false; loaded = false; loadProgress = 0; loadShown = 0; arriving = false; zone = nil; station = nil; returnBay = nil; place = "plaza"; notice = ""; lookSent = ""; debugSent = nil
        foreground = true; onPhone = false; revealedOnPhone = false; runtimeMissing = false; searching = false; onlineBench = nil; searchTask?.cancel(); meetHost = nil; matchOver = nil; partyStartAt = nil
        partyJoinPending = false; pendingPartyBay = nil; gatheredBay = nil; gatheredMembers = []; follow = nil
        nearbyHosting = false; nearbyJoining = nil; nearbyDismissed = []; nearbyBrowsing = false
        nearbyBrowse = Self.browseNearby; nearbyHost = Self.hostNearby; nearbyJoin = Self.joinNearby
        menuMode = false; menuScreen = "home"; menuHoverLabel = ""; menuHoverID = ""; menuPhoneSent = false; menuPartySent = ""; MenuPointerSource.shared.stop()
        presentInvite = { ClubHub.shared.hubOpen = true; ClubHub.shared.start() } }
    #endif

    // MARK: party (PLAN §4: friends in your plaza, sitting together, Call party)

    static let partyBays: Set<String> = ["bay-tennis-online", "bay-golf-online", "bay-bowling-online"]
    /// The sport a bench is for, by its id.
    static func benchSport(_ bay: String) -> MultiplayerSport { bay.contains("golf") ? .golf : bay.contains("bowling") ? .bowling : .tennis }
    /// The lobby the party lives in (tests inject their own service).
    @ObservationIgnored var partyService: MultiplayerService = .shared { didSet { installParty() } }
    /// The friends' party while it is idle (in the plaza) and someone has joined you; nil once a match is on, alone (an invite
    /// still on its way), or in a quick match's lobby.
    var party: MultiplayerLobby? {
        guard partyService.isParty, let lobby = partyService.lobby, lobby.phase == .lobby, lobby.participants.filter({ !$0.isGuest }).count >= 2 else { return nil }
        return lobby
    }
    /// Where each friend is sitting (bay id), and the place they are in, from their presence.
    private(set) var friendBays: [String: String] = [:]
    private(set) var friendPlaces: [String: String] = [:]
    private(set) var lastCall: (from: String, bay: String)?
    @ObservationIgnored private var lastPose = ""
    /// Seconds, for pacing the pose relay (tests run it on their own clock).
    @ObservationIgnored var uptime: () -> Double = { ProcessInfo.processInfo.systemUptime }
    @ObservationIgnored private var presenceSent = 0.0
    @ObservationIgnored private var reliablePresenceSent = -Double.infinity
    @ObservationIgnored private var presenceKey = (place: "", bay: "")
    @ObservationIgnored private var rosterSent = ""
    @ObservationIgnored private var partyInstalled = false

    struct Presence: Codable { var place: String; var x, y, z, yaw, speed: Double; var bay: String; var emote: String }

    func installParty() {
        partyService.onHub = { [weak self] kind, payload, sender in self?.partyMessage(kind, payload: payload, from: sender) }
        partyInstalled = true
    }

    /// My pose (Unity's hubPose, ~10 Hz) to the party.
    private func sendPresence() {
        guard party != nil, loaded, !lastPose.isEmpty else { return }
        let f = lastPose.split(separator: "|", omittingEmptySubsequences: false).map(String.init)
        guard f.count >= 8, let x = Double(f[1]), let y = Double(f[2]), let z = Double(f[3]), let yaw = Double(f[4]), let speed = Double(f[5]) else { return }
        let p = Presence(place: f[0], x: x, y: y, z: z, yaw: yaw, speed: speed, bay: f[6], emote: f[7])
        // ~10 a second, but sitting down, standing up or going through a door goes out at once (and reliably): the bench and the
        // friends' plazas must never miss it
        let now = uptime(), changed = p.bay != presenceKey.bay || p.place != presenceKey.place || now - reliablePresenceSent >= 1
        guard changed || now - presenceSent >= 0.09 else { return }
        guard let data = try? JSONEncoder().encode(p), let text = String(data: data, encoding: .utf8) else { return }
        presenceSent = now; if changed { reliablePresenceSent = now }; presenceKey = (p.place, p.bay); partyService.sendHub("hubPresence", payload: text, reliable: changed)
    }

    /// A friend's presence or event, from the lobby.
    func partyMessage(_ kind: String, payload: String, from sender: String) {
        guard let party, sender != partyService.localID else { return }
        switch kind {
        case "hubPresence":
            guard let p = try? JSONDecoder().decode(Presence.self, from: Data(payload.utf8)),
                  let index = party.participants.firstIndex(where: { $0.id == sender }) else { return }
            friendBays[sender] = p.bay.isEmpty ? nil : p.bay
            let was = friendPlaces[sender]
            friendPlaces[sender] = p.place
            let who = party.participants[index], look = who.loadout
            var remote: [String: Any] = ["id": sender, "name": who.name, "colour": index, "female": who.female, "place": p.place,
                                         "x": p.x, "y": p.y, "z": p.z, "yaw": p.yaw, "speed": p.speed, "bay": p.bay, "emote": p.emote]
            remote["skinHex"] = look?.skinHex ?? ""
            remote["shirt"] = look?.shirtHex ?? look?.colours["shirt"] ?? ""
            remote["shorts"] = look?.shortsHex ?? look?.colours["shorts"] ?? ""
            remote["accent"] = look?.colours["accent"] ?? ""
            guard let data = try? JSONSerialization.data(withJSONObject: remote), let text = String(data: data, encoding: .utf8) else { return }
            command("hubRemote", remote: text)
            // just joined their party: go and stand beside them
            if meetHost == sender, phase == .live, foreground { finishPartyJoin(); meetHost = nil; command("hubMeet", mode: sender) }
            // the leader went through a door (or travelled): the whole party goes with them (their pose has just reached Unity)
            if sender == party.ownerID, let was, was != p.place, p.place != place, pendingPartyBay == nil { followLeader(sender, to: p.place, name: who.name) }
        case "hubEvent":
            let f = payload.split(separator: "|", omittingEmptySubsequences: false).map(String.init)
            // the leader's menu (screen, lit item, cursor): this TV follows it
            if f.first == "menu", menuMode, sender == party.ownerID, !partyService.isOwner {
                menuCommand("menuMirror", mode: f.dropFirst().joined(separator: "|"))
                if let screen = f.dropFirst().first { menuScreen = screen }
                return
            }
            if f.first == "starting", f.count > 1 {
                notice = "Everyone's on the bench · starting \(Self.benchSport(f[1]).rawValue)…"
                if session.haptics { UINotificationFeedbackGenerator().notificationOccurred(.success) }
            }
            if f.first == "call", f.count == 2, Self.partyBays.contains(f[1]) {
                lastCall = (sender, f[1]); command("hubCall", mode: f[1])
                let name = party.participants.first { $0.id == sender }?.name ?? "A friend"
                notice = "Joining \(name) on the \(Self.benchSport(f[1]).rawValue.capitalized) bench…"
                meetHost = nil; pendingPartyBay = f[1]; expectCalledParty(at: f[1]); seatCalledParty()
                if session.haptics { UINotificationFeedbackGenerator().notificationOccurred(.warning) }
            }
        default: break
        }
    }

    // MARK: party follows its leader (the lobby's owner): rooms are entered together

    /// Going to stand beside the leader in their new place: retried until this phone's hero is there (a door or a fade may be
    /// running), for a few seconds at most.
    @ObservationIgnored private var follow: (leader: String, place: String, until: Double, next: Double)?
    private func followLeader(_ leader: String, to target: String, name: String) {
        let t = ProcessInfo.processInfo.systemUptime
        follow = (leader, target, t + 4, t)
        notice = "Following \(name) to \(HubControllerView.placeName(target).capitalized)"
        stepFollow()
    }
    private func stepFollow() {
        guard let f = follow else { return }
        let t = ProcessInfo.processInfo.systemUptime
        if party == nil || place == f.place || t > f.until || pendingPartyBay != nil { follow = nil; return }
        guard t >= f.next, phase == .live, foreground else { return }
        follow?.next = t + 0.5
        command("hubMeet", mode: f.leader)
    }

    @ObservationIgnored private var pendingPartyBay: String?
    @ObservationIgnored private var gatheredBay: String?
    @ObservationIgnored private var gatheredMembers: Set<String> = []
    private func expectCalledParty(at bay: String) {
        gatheredBay = bay
        gatheredMembers = Set(party?.participants.filter { $0.connected && !$0.isGuest }.map(\.id) ?? [])
    }
    private func seatCalledParty() {
        guard phase == .live, foreground, let bay = pendingPartyBay else { return }
        pendingPartyBay = nil; command("hubGather", mode: bay)
    }

    /// Bring everyone to this bench; hubAction/hubPose confirm their actual seats.
    func callParty() {
        guard party != nil, let bay = station, Self.partyBays.contains(bay) else { return }
        expectCalledParty(at: bay)
        partyService.sendHub("hubEvent", payload: "call|" + bay, reliable: true); haptic()
    }
    var partyHasUnseatedFriends: Bool {
        guard !menuMode, let party, let bay = station else { return false }
        return party.participants.contains { $0.connected && !$0.isGuest && $0.id != partyService.localID && friendBays[$0.id] != bay }
    }
    /// At least two players are on this online bench; nobody walking through the PLAY rooms is left behind.
    /// Everyone playing is here: the bench holds at least two of the party, and every friend who is in the play rooms (tennis or
    /// golf, so on their way) has sat down too. Friends elsewhere in the plaza (the locker, phone only) do not hold the match up.
    var partyAllSeated: Bool {
        guard let party, let bay = station, Self.partyBays.contains(bay) else { return false }
        let others = party.participants.filter { $0.connected && !$0.isGuest && $0.id != partyService.localID }
        // the pointer menu has no benches: everyone connected is in the line-up, so everyone is in
        if menuMode { return !others.isEmpty }
        let seated = others.filter { friendBays[$0.id] == bay }
        return !seated.isEmpty && partyWaitingFor.isEmpty
    }
    /// Friends in the PLAY hall or a sport room who have not sat on this bench yet.
    var partyWaitingFor: [String] {
        guard !menuMode, let party, let bay = station else { return [] }
        return party.participants.filter { $0.connected && !$0.isGuest && $0.id != partyService.localID && friendBays[$0.id] != bay
                                           && ((gatheredBay == bay && gatheredMembers.contains($0.id)) || ["play", "tennis", "golf"].contains(friendPlaces[$0.id] ?? "")) }.map(\.name)
    }
    func setPartyReady(_ ready: Bool) {
        do { try partyService.setReady(ready) } catch { notice = error.localizedDescription }
        if ready, session.haptics { UINotificationFeedbackGenerator().notificationOccurred(.success) } else { haptic() }
    }
    /// Leader: start the party's game (the sport, map and settings chosen on this panel). Every phone in the party asks its player
    /// to tap Ready; the match starts on all of them when the last one has.
    func forcePartyStart() {
        guard partyService.isOwner, party != nil else { return }
        do { try partyService.startPartyGame(); notice = "" } catch { notice = error.localizedDescription }
        haptic()
    }
    /// Leader: back to choosing (nobody is ready any more).
    func cancelPartyGame() { partyService.cancelPartyGame(); haptic() }
    /// Leader: the party's game is tennis, golf or bowling (on the same panel).
    func setPartySport(_ sport: MultiplayerSport) {
        guard partyService.isOwner, let lobby = party, lobby.sport != sport else { return }
        do { try partyService.configure(sport, venue: sport == .golf ? session.golfCourse : sport == .bowling ? session.bowlingVenue : session.tennisVenue) } catch { notice = error.localizedDescription }
        station = sport == .golf ? "bay-golf-online" : sport == .bowling ? "bay-bowling-online" : "bay-tennis-online"
        haptic()
    }
    /// The leader's Party game button (the phone, not the TV menu): the party panel for the party's sport.
    func openPartyGame() {
        guard let lobby = party else { inviteFriends(); return }
        useStation(lobby.sport == .golf ? "bay-golf-online" : lobby.sport == .bowling ? "bay-bowling-online" : "bay-tennis-online")
        syncMenuPhone(force: true); updatePointer()
    }
    func configureParty(venue: String? = nil, sets: Int? = nil, games: Int? = nil) {
        guard partyService.isOwner, let lobby = party else { return }
        do { try partyService.configure(lobby.sport, venue: venue ?? lobby.venue, sets: sets ?? lobby.sets, games: games ?? lobby.games) }
        catch { notice = error.localizedDescription }
    }
    private func updatePartySeats() {
        guard partyService.isOwner, let bay = station, Self.partyBays.contains(bay), let lobby = party else { return }
        let me = partyService.localID
        partyService.seatParty(lobby.participants.filter { $0.connected && !$0.isGuest && (menuMode || $0.id == me || friendBays[$0.id] == bay) }.map(\.id))
    }

    private func partyTick() {
        if !partyInstalled { installParty() }
        guard phase == .live else { return }
        if party == nil { pendingPartyBay = nil; gatheredBay = nil; gatheredMembers = [] }
        finishPartyJoin()
        seatCalledParty()
        stepFollow()
        // the member list: anyone who left walks off
        let ids = party?.participants.map(\.id).filter { $0 != partyService.localID }.sorted() ?? []
        let roster = ids.joined(separator: ",")
        if roster != rosterSent { rosterSent = roster; command("hubRoster", mode: roster); friendBays = friendBays.filter { ids.contains($0.key) }; friendPlaces = friendPlaces.filter { ids.contains($0.key) } }
        // the leader pressed Start: every other phone buzzes and the TV says so (the phone shows the big Ready button)
        let check = partyService.partyReadyCheck
        if check != readyCheckSeen {
            readyCheckSeen = check
            if check, !partyService.isOwner, let lobby = party {
                let game = lobby.sport == .golf ? "golf" : lobby.sport == .bowling ? "bowling" : "tennis"
                toast("\(menuLeaderName) started \(game) · tap READY on your phone")
                if session.haptics { UINotificationFeedbackGenerator().notificationOccurred(.warning) }
            }
        }
        if !check { updatePartySeats() }
        partyStartAt = nil
    }
    @ObservationIgnored private var readyCheckSeen = false

    // MARK: Nearby tennis (PLAN_Tennis_Latency_Online_Local §3): one menu action hosts, a friend's phone offers one-tap Join
    //
    // Nothing here depends on walking in the Plaza: the host's entry is a menu row (the phone's Play list, the pointer menu's Tennis
    // modes) that opens the "bay-tennis-nearby" station; the guest's banner shows over whatever menu is up (SportsHome), whenever
    // ClubHub.canJoinNow says this phone could join (the same rule the Game Center invite handshake uses), and SportsHome drives
    // nearbyTick.

    static let nearbyBay = "bay-tennis-nearby"
    /// Hosting a nearby tennis game from the menu (Bonjour, peer-to-peer Wi-Fi: no shared network needed). It starts by itself as
    /// soon as a friend's phone has joined.
    private(set) var nearbyHosting = false
    /// Joining a nearby game from the banner: whose, and since when (the banner says "Joining …" until the lobby arrives).
    private(set) var nearbyJoining: (id: String, name: String, since: Double)?
    @ObservationIgnored private var nearbyDismissed: Set<String> = []
    @ObservationIgnored private var nearbyBrowsing = false
    /// How long a join may take before the banner gives up (the transport's own connection timeout is 10 s).
    static let nearbyJoinSeconds = 15.0
    /// Network seams (tests use an in-memory link). Each gets the hub, so no closure keeps one alive.
    @ObservationIgnored var nearbyBrowse: @MainActor (HubSession, Bool) -> Void = HubSession.browseNearby
    @ObservationIgnored var nearbyHost: @MainActor (HubSession) throws -> Void = HubSession.hostNearby
    @ObservationIgnored var nearbyJoin: @MainActor (HubSession, LocalMultiplayerTransport.DiscoveredLobby) throws -> Void = HubSession.joinNearby
    static let browseNearby: @MainActor (HubSession, Bool) -> Void = { hub, on in if on { hub.partyService.browseLocal(quiet: true) } else { hub.partyService.stopBrowsing() } }
    static let hostNearby: @MainActor (HubSession) throws -> Void = { hub in
        let p = hub.session.players.indices.contains(hub.session.playerIndex) ? hub.session.players[hub.session.playerIndex].name : "Friends"
        try hub.partyService.hostLocal(name: p, quick: .tennis)
    }
    static let joinNearby: @MainActor (HubSession, LocalMultiplayerTransport.DiscoveredLobby) throws -> Void = { hub, lobby in try hub.partyService.joinLocal(lobby) }

    /// Look for nearby games in the background whenever this phone could join one: on a menu (ClubHub.canJoinNow: no match, nothing
    /// loading, not onboarding, in the foreground), in no lobby, not searching, and Local Network not refused. (The first browse is
    /// when iOS asks for Local Network access.)
    var wantsNearbyBrowse: Bool {
        foreground && !session.active && !SportsSession.benchmark && ClubHub.shared.canJoinNow && onlineBench == nil
            && nearbyJoining == nil && !nearbyHosting && partyService.lobby == nil && !partyService.searching && !partyService.localNetworkDenied
    }
    /// A nearby tennis game with room for this phone, shown as "Join <name>'s tennis game?" (one tap joins). Nil when there is none,
    /// the player dismissed it, or this phone is busy.
    var nearbyOffer: LocalMultiplayerTransport.DiscoveredLobby? {
        guard !session.active, ClubHub.shared.canJoinNow, nearbyJoining == nil, !nearbyHosting, partyService.lobby == nil else { return nil }
        return partyService.discoveredLobbies.first { $0.sport == MultiplayerSport.tennis.rawValue && $0.players < 2 && !nearbyDismissed.contains($0.id) }
    }
    /// The menu's "Tennis with a friend nearby": host a nearby tennis game (a quick lobby: it readies itself and starts when the
    /// friend's phone is in). Its panel (HubNearbyBenchPanel) shows while this station is open.
    func useNearbyBench() {
        // friends in your party play together from the Online modes; a nearby game would break the party up
        guard !soloLocked || nearbyHosting else {
            notice = Self.soloLockMessage; if station == Self.nearbyBay { station = nil; command("hubB") }; return
        }
        station = Self.nearbyBay
        endNearbyBrowse()
        if nearbyHosting, partyService.lobby != nil { return }   // (already hosting; a hosted game that went is hosted again)
        nearbyHosting = false
        // a party of one waiting on an invite, or a stale lobby, gives way to the nearby game
        if partyService.isParty { ClubHub.shared.leaveParty() } else if partyService.lobby != nil { partyService.leave() }
        nearbyIdentity()
        do { try nearbyHost(self); nearbyHosting = true; notice = "" }
        catch { notice = error.localizedDescription }
        SportsDiagnostics.write("nearby bench: hosting=\(nearbyHosting)\(notice.isEmpty ? "" : " (\(notice))")")
    }
    /// Leaving the nearby panel before a match: the game is no longer offered.
    private func stopHostingNearby() {
        guard nearbyHosting else { return }
        nearbyHosting = false
        if partyService.lobby?.phase == .lobby || partyService.lobby == nil { partyService.leave() }
    }
    /// The banner's Join: close any station, and join that game (the match then starts on its own: the host's lobby readies
    /// this phone and starts as soon as it is in).
    func joinNearby() {
        guard let offer = nearbyOffer else { return }
        haptic()
        if station != nil || panelOpen { leaveStation() }
        nearbyIdentity()
        do {
            try nearbyJoin(self, offer)
            nearbyBrowsing = false   // (joining ends the browse itself)
            nearbyJoining = (offer.id, offer.name, ProcessInfo.processInfo.systemUptime); notice = ""
            SportsDiagnostics.write("nearby join \(offer.name)")
        } catch { notice = error.localizedDescription }
    }
    /// This phone's player, look and TV, on the lobby it is about to host or join.
    private func nearbyIdentity() {
        if let p = menu.player { partyService.setIdentity(name: p.name, female: p.standardFemale, left: p.handedness == .left, loadout: p.multiplayerLoadout) }
        partyService.setScreen(session.displayConnected)
        partyService.clearError()
    }
    /// The banner's ✕: not this game (a new game from the same phone is offered again).
    func dismissNearby() { if let offer = nearbyOffer { nearbyDismissed.insert(offer.id) } }
    func cancelNearbyJoin() {
        guard nearbyJoining != nil else { return }
        nearbyJoining = nil; partyService.leave()
    }
    private func endNearbyBrowse() {
        guard nearbyBrowsing else { return }
        nearbyBrowsing = false; nearbyBrowse(self, false)
    }
    /// Four times a second from SportsHome (whatever menu is up): starts and stops the background browse, and follows a join.
    func nearbyTick() {
        let want = wantsNearbyBrowse
        if want != nearbyBrowsing { nearbyBrowsing = want; nearbyBrowse(self, want) }
        if let joining = nearbyJoining {
            if partyService.lobby != nil {
                nearbyJoining = nil; notice = "Joined \(joining.name)'s game · the match starts on the TV"
                if session.haptics { UINotificationFeedbackGenerator().notificationOccurred(.success) }
            } else if let error = partyService.lastError, !error.isEmpty {
                nearbyJoining = nil; partyService.leave(); notice = error
            } else if ProcessInfo.processInfo.systemUptime - joining.since > Self.nearbyJoinSeconds {
                nearbyJoining = nil; partyService.leave(); notice = "Couldn't reach \(joining.name)'s game. Keep the phones close and try again."
            }
        }
        // the hosted game went (left, or its match ended and was left): nothing is hosted any more
        if nearbyHosting, partyService.lobby == nil, station != Self.nearbyBay { nearbyHosting = false }
    }

    /// Seconds between everyone sitting down and the match starting (the panels count down).
    static var partyCountdown = 2.5
    /// When the host's phone starts the party's match (everyone seated); nil while waiting.
    private(set) var partyStartAt: Double?

    /// One Unity event (also called directly by tests).
    func receive(_ event: [String: Any]) {
        let type = event["type"] as? String ?? ""
        if type == "boot" { if phase == .booting { progress(0.15); sendStart() }; return }   // Unity's first frame: a milestone of its own
        guard event["session"] as? String == sessionID else { return }
        let message = event["message"] as? String ?? ""
        if phase == .booting { heardFromUnity = true; lastBootSignal = Date() }
        switch type {
        case "loadProgress": progress(0.12 + 0.18 * (Double(message) ?? 0))
        case "buildProgress": progress(0.30 + 0.65 * (Double(message) ?? 0))
        case "ready":
            loaded = true; progress(1); if phase == .booting { advanceShown(); learnStageSeconds() }
            let fresh = phase == .booting && returnBay == nil
            if phase == .booting { phase = .live; autoRetried = false; SportsDiagnostics.write("hub ready after \(String(format: "%.2f", Date().timeIntervalSince(bootStarted))) s") }
            // back from a match on the same bench: its panel again (staying seated = rematch, B = stand up); the menu opens on Home
            if let bay = returnBay, station == nil, !menuMode { returning = true; useStation(bay); returning = false }
            if menuMode { returnBay = nil; menuPartySent = ""; syncMenuParty(); updatePointer() }
            if !wanted { suspend() } else if fresh { arrive() } else { reveal() }
        case "hubPlace": place = message
        case "hubZone": zone = HubZone(line: message)
        case "hubAction": lastAction = message; useStation(message)
        case "hubPose": lastPose = message; sendPresence()
        case "hubState":
            let f = message.split(separator: "|", omittingEmptySubsequences: false).map(String.init)
            if f.count >= 5 { speed = Double(f[2]) ?? 0; inputAge = (Double(f[3]) ?? 0, Double(f[4]) ?? 0) }
        case "emoteResult": notice = message
        case "error": if phase == .booting { fail(message) } else { notice = message }
        default: if type.hasPrefix("menu") { handleMenu(type, message) }
        }
    }
}
