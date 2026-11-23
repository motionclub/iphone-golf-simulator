import XCTest
import UIKit
@testable import GolfArcade

@MainActor final class MenuFlowRegressionTests: XCTestCase {
    /// Point and fill (11-22): Ready cannot skip the pointing, and once the direction is set the match starts. No flashes, no timing
    /// drill, no Ready tap.
    func testCalibrationPrecedesReadyAndDoesNotStartAPoint() {
        let session = SportsSession()
        session.timingStore = UserDefaults(suiteName: "solo-setup-\(UUID().uuidString)")!
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.motion.fixtureSensors = true; session.loading.cancel()
        session.readyToPlay()
        XCTAssertTrue(session.paused)
        XCTAssertEqual(session.setupStage, .scan)
        session.offerTimingCalibration()
        XCTAssertFalse(session.measuringDelay, "no flashes any more")
        XCTAssertFalse(session.timingPrompt, "no timing drill any more")
        XCTAssertEqual(session.setupStage, .playing, "the direction is set: play starts")
        XCTAssertFalse(session.paused)
        XCTAssertFalse(session.checkingTiming)
        session.tennisPhase = "serve"
        XCTAssertTrue(session.tossVisible)
    }
    /// Online tennis sets up exactly as solo does before its first serve (2026-10-28): the court scan, the TV's delay, the timing check,
    /// then Ready, and only then is the player reported set up. (Versus tennis runs the timing drill on this phone's own court; before,
    /// online went from the scan straight to Ready.) A player coming back into a match already being played still goes from the scan
    /// straight to Ready, and re-aiming mid-match never pauses it.
    func testAnOnlineMatchSetsUpAsSoloDoes() throws {
        let session = SportsSession()
        session.timingStore = UserDefaults(suiteName: "online-setup-\(UUID().uuidString)")!
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.motion.fixtureSensors = true; session.loading.cancel()
        session.debugSetOnlineMatch("match-1", seat: 0)
        let service = MultiplayerService.shared
        defer { service.leave("test over") }
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        service.mockState(phase: .calibrating)
        session.setupStage = .scan; session.paused = true
        session.offerTimingCalibration()
        XCTAssertFalse(session.measuringDelay); XCTAssertFalse(session.timingPrompt)
        XCTAssertEqual(session.setupStage, .waiting, "set up (and reported) as soon as the direction is set: no flashes, no drill, no Ready tap")

        // coming back into a match already being played: the direction is still set, so straight back in (no timing check, no Ready)
        service.mockState(phase: .playing)
        session.setupStage = .scan; session.paused = true
        session.offerTimingCalibration()
        XCTAssertEqual(session.setupStage, .waiting)
        XCTAssertFalse(session.timingPrompt); XCTAssertFalse(session.measuringDelay)

        // Re-aiming while the match is running leaves it running: a pause would start the owner's forfeit clock.
        session.setupStage = .playing; session.paused = false
        session.recheckTiming()
        XCTAssertEqual(session.setupStage, .playing); XCTAssertFalse(session.paused)
        XCTAssertFalse(session.timingPrompt); XCTAssertFalse(session.measuringDelay)
    }
    /// The court scan needs the court on the TV, so online setup starts when this phone's loading screen is gone, and from then on it
    /// does not wait for the opponent.
    func testOnlineSetupStartsOnceTheCourtIsShownAndDoesNotWaitForTheOpponent() {
        let session = SportsSession()
        session.active = true; session.sport = "tennis"; session.motion.fixtureSensors = true
        session.debugSetOnlineMatch("independent-setup", seat: 0)
        session.loading.begin(now: LoadingModel.clockNow, multiplayer: true)
        session.setupStage = .scan
        XCTAssertFalse(session.ready); XCTAssertFalse(session.loading.finished)
        XCTAssertFalse(session.showsOnlineTennisSetup, "no scan while the loading screen is on the TV")
        session.loading.cancel()
        XCTAssertTrue(session.showsOnlineTennisSetup, "the court is up: the setup shows")
        session.readyToPlay()
        XCTAssertEqual(session.setupStage, .scan, "Ready cannot bypass direction capture")
        session.setupStage = .ready
        session.readyToPlay()
        XCTAssertEqual(session.setupStage, .waiting, "the local Ready tap must not depend on the opponent or renderer")
        XCTAssertTrue(session.paused); XCTAssertTrue(session.showsOnlineTennisSetup)
        session.setupStage = .playing
        XCTAssertFalse(session.showsOnlineTennisSetup)
        session.active = false
    }

    /// One TV for two phones (11-20): nobody waits for a turn. Pointing at the TV needs neither the camera nor the TV, so the phone
    /// without the TV sets up while the other player is still setting up.
    func testSharingATVBothPlayersSetUpAtOnce() throws {
        let session = SportsSession(), service = MultiplayerService.shared
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        service.mockOneTV(otherStep: "direction")
        session.active = true; session.sport = "tennis"
        session.debugSetOnlineMatch("one-tv", seat: 0)
        session.motion.fixtureSensors = true
        session.loading.cancel(); session.setupStage = .scan
        session.debugBeginOnlineSetup()
        XCTAssertNil(session.setupTurnWaitingFor, "no turns: both phones point at the TV at the same time")
        XCTAssertEqual(session.setupStage, .scan); XCTAssertTrue(session.showsOnlineTennisSetup)
        XCTAssertTrue(session.glowActive, "the circle is up on both phones at once")
        XCTAssertEqual(session.glowMessage, "Get the TV inside the corners.")
    }

    /// One TV, two phones (11-22, Adnan): the circle fills only while both phones see the TV at the same time. This is the phone with
    /// the TV, which keeps the circle.
    func testTheSharedCircleFillsOnlyWhileBothPhonesSeeTheTV() throws {
        let session = SportsSession(), service = MultiplayerService.shared
        session.timingStore = UserDefaults(suiteName: "shared-circle-\(UUID().uuidString)")!
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        service.mockOneTV(otherStep: "glow:off", mineHasTV: true)
        session.active = true; session.ready = true; session.sport = "tennis"; session.displayConnected = true
        session.debugSetOnlineMatch("one-tv-circle", seat: 0)
        session.motion.fixtureSensors = true
        session.loading.cancel(); session.setupStage = .scan
        session.debugBeginOnlineSetup()
        XCTAssertTrue(session.glowActive); XCTAssertTrue(session.ownsTV); XCTAssertTrue(session.sharesTV)
        var t = 1000.0
        func look(_ n: Int) { for _ in 0..<n { t += 0.1; session.receiveGlow(.init(time: t, seeing: true, delay: 0.14, match: 0.95, heading: 0.4)) } }
        look(30)
        XCTAssertEqual(session.glowProgress, 0, "the other phone is not on the TV: nothing fills")
        XCTAssertTrue(session.glowMessage.hasSuffix("to point at the TV too."), session.glowMessage)
        service.mockOneTV(otherStep: "glow:on", mineHasTV: true)
        look(12)
        let filled = session.glowProgress
        XCTAssertGreaterThan(filled, 0.3, "both on the TV: it fills")
        service.mockOneTV(otherStep: "glow:off", mineHasTV: true)
        look(5)
        XCTAssertLessThan(session.glowProgress, filled, "one phone off the TV: the circle drains")
        service.mockOneTV(otherStep: "glow:on", mineHasTV: true)
        look(40)
        XCTAssertFalse(session.glowActive, "full")
        XCTAssertEqual(session.latencyReading ?? 0, 0.14 + SportsGlow.gameFrameLead, accuracy: 1e-9)
        XCTAssertEqual(SportsTiming.storedPicture(for: SportsTiming.currentTV(), defaults: session.timingStore) ?? 0, 0.14 + SportsGlow.gameFrameLead, accuracy: 1e-9)
        session.axisGate.locked = true; session.debugFinishPoint()
        XCTAssertEqual(session.setupStage, .waiting, "set up with no flashes and no drill")
    }

    /// The phone without the TV: it says when it sees the TV, mirrors the TV phone's circle, and is set up when that circle is full.
    func testThePhoneWithoutTheTVFollowsTheSharedCircle() throws {
        let session = SportsSession(), service = MultiplayerService.shared
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        service.mockOneTV(otherStep: "glow:off:0")
        session.active = true; session.ready = true; session.sport = "tennis"
        session.debugSetOnlineMatch("one-tv-guest", seat: 0, controllerOnly: true)
        session.motion.fixtureSensors = true
        session.loading.cancel(); session.setupStage = .scan
        session.debugBeginOnlineSetup()
        XCTAssertTrue(session.glowActive); XCTAssertFalse(session.ownsTV)
        var t = 50.0
        func look() { t += 0.1; session.receiveGlow(.init(time: t, seeing: true, delay: 0.3, match: 0.9, heading: -1)) }
        look()
        XCTAssertEqual(session.glowProgress, 0)
        service.mockOneTV(otherStep: "glow:on:60"); look()
        XCTAssertEqual(session.glowProgress, 0.6, accuracy: 1e-9, "the TV phone's circle")
        XCTAssertTrue(session.glowActive)
        service.mockOneTV(otherStep: SportsGlowStep.done); look()
        XCTAssertFalse(session.glowActive, "the TV phone's circle is full")
        session.axisGate.locked = true; session.debugFinishPoint()
        XCTAssertEqual(session.setupStage, .waiting, "no timing check here either, and no Ready tap")
    }

    /// The TV phone's own pointing is still under way: the phone without the TV waits for it after it is pointed.
    func testAPhoneWithoutTheTVWaitsForTheTVPhone() throws {
        let session = SportsSession(), service = MultiplayerService.shared
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        service.mockOneTV(otherStep: "glow:on:30")
        session.active = true; session.ready = true; session.sport = "tennis"
        session.debugSetOnlineMatch("one-tv-wait", seat: 0, controllerOnly: true)
        session.loading.cancel(); session.setupStage = .scan
        session.motion.fixtureSensors = true; session.axisGate.locked = true
        session.debugFinishPoint()
        XCTAssertEqual(session.calibrationStep, .waitingForTV)
        service.mockOneTV(otherStep: "ready"); session.advanceCalibration()
        XCTAssertEqual(session.setupStage, .waiting)
    }

    func testRepeatedRendererReadyDoesNotClearCompletedOnlineCalibration() throws {
        let session = SportsSession(), service = MultiplayerService.shared
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        session.active = true; session.sport = "tennis"; session.debugSetOnlineMatch("renderer-repeat", seat: 0)
        session.loading.begin(now: LoadingModel.clockNow, multiplayer: true)
        session.runtimeDidRender(renderedAt: nil)
        service.runtimeCalibrated()
        XCTAssertEqual(service.lobby?.participants.first { $0.id == service.localID }?.calibrated, true)
        session.runtimeDidRender(renderedAt: nil)
        XCTAssertEqual(service.lobby?.participants.first { $0.id == service.localID }?.calibrated, true,
                       "a repeated first-frame event is not a runtime reload and must not clear Ready")
    }

    func testAnOnlineSpectatorDoesNotGetAControllerCalibrationGate() {
        let session = SportsSession()
        session.active = true; session.sport = "tennis"
        session.debugSetOnlineMatch("spectator", seat: -1)
        XCTAssertFalse(session.showsOnlineTennisSetup)
        session.active = false
    }

    func testPointControlsAndCelebrationFollowActualPointPhase() {
        let session = SportsSession()
        session.active = true; session.ready = true; session.loading.cancel()
        session.sport = "tennis"; session.setupStage = .playing; session.paused = false
        for phase in ["serve", "toss", "receive", "rally"] {
            session.tennisPhase = phase
            XCTAssertTrue(session.pointControlsVisible)
            XCTAssertEqual(session.tossVisible, phase == "serve")
            XCTAssertFalse(session.canPlayEmote)
        }
        session.tennisPhase = "point"
        XCTAssertFalse(session.pointControlsVisible)
        session.emoteWindow = "intro"; XCTAssertFalse(session.canPlayEmote)
        session.emoteWindow = ""; XCTAssertFalse(session.canPlayEmote)
        // while the intro plays, the equipped emotes pick the player's intro emote
        session.tennisPhase = "intro"; session.emoteWindow = "intro"; XCTAssertTrue(session.canPlayEmote)
        session.tennisPhase = "point"
        session.emoteWindow = "point"; XCTAssertTrue(session.canPlayEmote)
        session.paused = true; XCTAssertFalse(session.canPlayEmote)
    }
    /// The timing drill is gone (11-22): nothing offers it, and asking for it does nothing.
    func testNoTimingDrillIsOffered() {
        let session = SportsSession()
        session.timingStore = UserDefaults(suiteName: "no-drill-\(UUID().uuidString)")!
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.motion.fixtureSensors = true; session.loading.cancel()
        session.setupStage = .scan; session.paused = true
        session.debugFinishPoint()
        XCTAssertEqual(session.setupStage, .playing)
        session.startTimingCheck()
        XCTAssertFalse(session.checkingTiming)
        XCTAssertNil(session.calibrationStep)
    }
    func testGolfHasOnePlayableRouteWithoutATutorialPrerequisite() {
        let menu = TennisMenu()
        XCTAssertEqual(TennisMenu.hubItems(.golf), ["round"])
        XCTAssertTrue(menu.hubUnlocked(.golf, "round"))
        menu.debugShow(.hub(.golf))
        XCTAssertEqual(menu.focused, "round")
    }
    func testBothSportsChooseMapsBeforeStartingTheRuntime() {
        let menu = TennisMenu()
        for sport in [Sport.golf, .tennis] {
            menu.debugShow(.hub(sport))
            menu.begin(MenuLaunch(sport: sport, mode: .tutorial), onPhone: true)
            XCTAssertEqual(menu.screen, .map)
            XCTAssertEqual(menu.launch?.mode, sport == .golf ? .round : .exhibition)
            XCTAssertEqual(menu.mapChoices.count, 3)   // golf: Cliffside, Wild Isles, Magma Open; tennis: three courts
            XCTAssertFalse(SportsSession.shared.active)
            menu.back()
            XCTAssertEqual(menu.screen, .hub(sport))
        }
        XCTAssertEqual(TennisMenu.hubItems(.tennis), ["exhibition", "campaign", "training"])
        for id in TennisMenu.hubItems(.tennis) { XCTAssertTrue(menu.hubUnlocked(.tennis, id)) }
    }
    func testStartupFailureStopsLoadingAndOffersTheSameMapAgain() {
        let menu = TennisMenu.shared
        menu.begin(MenuLaunch(sport: .golf, mode: .round), onPhone: true)
        SportsSession.shared.loading.begin(now: Date())
        SportsSession.shared.failStartup("Display unavailable")
        XCTAssertTrue(SportsSession.shared.loading.finished)
        XCTAssertFalse(SportsSession.shared.active)
        XCTAssertEqual(menu.screen, .map)
        XCTAssertEqual(menu.mapSport, .golf)
        XCTAssertEqual(menu.notice, "Display unavailable")
        menu.goHome()
    }
    func testALessonLeftMidwayComesBackToItsTutorialRow() {
        let defaults = UserDefaults(suiteName: "lesson-resume-\(UUID())")!
        let store = OnboardingStore(defaults: defaults)
        store.step = .tutorial; store.explicitRun = true; store.setLessonStation(.golf, 3)
        let flow = OnboardingFlow(store: store, progress: SportProgress(defaults: defaults), arguments: [])
        XCTAssertEqual(flow.step, .tutorial); XCTAssertFalse(flow.holdsMenu, "the menu is up, its Tutorial resumes the lesson")
        XCTAssertEqual(flow.nextLesson, .golf); XCTAssertEqual(store.lessonStation(.golf), 3)
        XCTAssertFalse(store.rewardClaimed(.golf))
    }
    func testMainMenuIsReachableFromLoadingStoryAndEverySetupRoute() {
        let menu = TennisMenu()
        for screen in [MenuScreen.loading, .connect, .story, .map, .character, .settings, .postMatch, .hub(.golf)] {
            menu.debugShow(screen)
            menu.goHome()
            XCTAssertEqual(menu.screen, .main, "\(screen)")
            XCTAssertNil(menu.launch)
        }
    }
    func testLoadingBackCancelsAndReturnsToAMenu() {
        let menu = TennisMenu()
        menu.debugShow(.loading)
        menu.back()
        XCTAssertEqual(menu.screen, .main)
        XCTAssertFalse(SportsSession.shared.active)
    }
    func testSetupCanGoBackAndExitWithoutCompletingATutorial() {
        let defaults = UserDefaults(suiteName: "navigation-\(UUID())")!
        let store = OnboardingStore(defaults: defaults)
        let progress = SportProgress(defaults: defaults)
        store.step = .how; store.characterInitialized = true
        let flow = OnboardingFlow(store: store, progress: progress, arguments: [])
        flow.stateChanged = {}
        flow.back()
        XCTAssertEqual(flow.step, .customize)
        flow.exitToMenu()
        XCTAssertEqual(flow.step, .done)
        XCTAssertFalse(flow.locked)
        XCTAssertFalse(progress.finishedTutorial(.golf))
        XCTAssertFalse(store.rewardClaimed(.golf))
    }
    /// Tennis needs a TV; golf and bowling play on the phone itself without one (handheld play, PLAN_PhonePlay_Handheld.md).
    func testTennisNeedsAnExternalScreenButGolfDoesNot() {
        let displays = SportsDisplays.shared
        let saved = displays.external
        defer { displays.external = saved }
        displays.external = nil
        XCTAssertNil(displays.gameWindow(preview: true))
        XCTAssertNil(displays.gameWindow(preview: false))
        let menu = TennisMenu.shared
        menu.begin(MenuLaunch(mode: .exhibition), onPhone: true)
        menu.tap("map-resort")
        XCTAssertEqual(menu.screen, .connect)
        XCTAssertFalse(SportsSession.shared.active)
        XCTAssertFalse(menu.rows(.connect).flatMap { $0 }.contains("phone"))
        menu.goHome()
        XCTAssertTrue(Sport.golf.playsOnPhone && Sport.bowling.playsOnPhone && !Sport.tennis.playsOnPhone)
        menu.begin(MenuLaunch(sport: .golf, mode: .round), onPhone: true)
        menu.tap("map-cliffside")
        XCTAssertNotEqual(menu.screen, .connect, "golf goes on to load on the phone")
        if SportsSession.shared.active { SportsSession.shared.end() }
        menu.goHome()
    }
    func testAirPlayWindowWinsOverRequestedPhonePreview() {
        let displays = SportsDisplays.shared
        let oldExternal = displays.external, oldPhone = displays.phone
        let oldConnected = SportsSession.shared.displayConnected
        defer {
            displays.external = oldExternal; displays.phone = oldPhone
            SportsSession.shared.displayConnected = oldConnected
        }
        let external = UIWindow(frame: CGRect(x: 0, y: 0, width: 1920, height: 1080))
        displays.external = external
        XCTAssertTrue(displays.gameWindow(preview: true) === external)
        XCTAssertTrue(SportsSession.shared.displayConnected)
    }
}
