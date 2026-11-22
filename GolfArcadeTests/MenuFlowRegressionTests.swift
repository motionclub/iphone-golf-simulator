import XCTest
import UIKit
@testable import GolfArcade

@MainActor final class MenuFlowRegressionTests: XCTestCase {
    func testCalibrationPrecedesReadyAndDoesNotStartAPoint() {
        let session = SportsSession()
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.motion.fixtureSensors = true; session.loading.cancel()
        session.readyToPlay()
        XCTAssertTrue(session.paused)
        XCTAssertEqual(session.setupStage, .scan)
        session.offerTimingCalibration()
        XCTAssertTrue(session.measuringDelay, "the screen flashes run first")
        session.debugFinishTVDelay()
        XCTAssertEqual(session.setupStage, .timing)
        XCTAssertTrue(session.timingPrompt)
        session.readyToPlay(); session.resume()
        XCTAssertTrue(session.paused, "Ready/Resume must not bypass calibration")
        session.startTimingCheck()
        XCTAssertTrue(session.checkingTiming)
        XCTAssertFalse(session.paused, "Phone samples must flow during TV calibration")
        XCTAssertFalse(session.pointControlsVisible)
        session.receiveTimingResult("failed")
        // (quick start T5, 11-21: no Ready tap; the centre is taken as the setup ends)
        XCTAssertEqual(session.setupStage, .playing, "the end of the timing check starts play")
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
        XCTAssertTrue(session.measuringDelay, "the screen flashes run first, as in solo")
        session.debugFinishTVDelay()
        XCTAssertEqual(session.setupStage, .timing); XCTAssertTrue(session.timingPrompt)
        session.startTimingCheck()
        XCTAssertTrue(session.checkingTiming)
        session.receiveTimingResult("120")
        XCTAssertEqual(session.setupStage, .waiting, "set up (and reported) as the timing check ends: no Ready tap (T5)")

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
        session.loading.cancel(); session.setupStage = .scan
        session.debugBeginOnlineSetup()
        XCTAssertNil(session.setupTurnWaitingFor, "no turns: both phones point at the TV at the same time")
        XCTAssertEqual(session.setupStage, .scan); XCTAssertTrue(session.showsOnlineTennisSetup)
        XCTAssertEqual(session.pointMessage, "Hold until the ring is full.")
    }

    /// One TV, two phones (11-20, Adnan): both point and hold → the TV phone calibrates the TV → both get the timing check → it starts
    /// for both at once. This is the phone without the TV.
    func testSharedTVSetupPointsThenCalibratesThenTimesBothTogether() async throws {
        let session = SportsSession(), service = MultiplayerService.shared
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        service.mockOneTV(otherStep: "direction")
        session.active = true; session.ready = true; session.sport = "tennis"
        session.debugSetOnlineMatch("one-tv-flow", seat: 0, controllerOnly: true)
        session.loading.cancel(); session.setupStage = .scan
        session.debugBeginOnlineSetup()
        XCTAssertEqual(session.setupStage, .scan, "both phones point at the TV at the same time")
        session.motion.fixtureSensors = true; session.axisGate.locked = true
        session.debugFinishPoint()
        XCTAssertEqual(session.calibrationStep, .waitingForTV, "pointed: the phone with the TV calibrates the TV first")
        service.mockOneTV(otherStep: "pointed"); session.advanceCalibration()
        XCTAssertEqual(session.calibrationStep, .waitingForTV, "the TV phone is still flashing")
        service.mockOneTV(otherStep: "timing"); session.advanceCalibration()
        XCTAssertEqual(session.calibrationStep, .prompt, "the TV is calibrated: this phone is offered the timing check")
        session.startTimingCheck()
        XCTAssertEqual(session.calibrationStep, .startWaiting, "one ball on one TV: wait for the other player's Start")
        XCTAssertFalse(session.checkingTiming)
        service.mockOneTV(otherStep: "go:\(service.networkTime + 0.2)")
        session.debugStartTimingIfEveryoneAsked()
        try await Task.sleep(for: .seconds(3))
        XCTAssertEqual(session.calibrationStep, .drill, "both tapped Start: the drill starts together")
        session.receiveTimingResult("130")
        XCTAssertEqual(session.setupStage, .waiting, "after the timing check: set up, no Ready tap (T5)")
    }

    /// Skipping the timing check on one phone does not hold up the other's.
    func testSkippingTheTimingCheckGoesStraightToReady() throws {
        let session = SportsSession(), service = MultiplayerService.shared
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        service.mockOneTV(otherStep: "timing")
        session.active = true; session.ready = true; session.sport = "tennis"
        session.debugSetOnlineMatch("one-tv-skip", seat: 0, controllerOnly: true)
        session.loading.cancel(); session.setupStage = .scan
        session.motion.fixtureSensors = true; session.axisGate.locked = true
        session.debugFinishPoint()
        XCTAssertEqual(session.calibrationStep, .prompt)
        session.skipTimingCheck()
        XCTAssertEqual(session.setupStage, .waiting, "skipped: set up at once (T5)")
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
    func testInterruptedTimingReturnsToCalibrationWithoutStartingPlay() {
        let session = SportsSession()
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.motion.fixtureSensors = true; session.loading.cancel()
        session.offerTimingCalibration(); session.debugFinishTVDelay(); session.startTimingCheck()
        session.pause(reason: "Display disconnected")
        XCTAssertTrue(session.timingPrompt)
        XCTAssertFalse(session.checkingTiming)
        XCTAssertEqual(session.setupStage, .timing)
        session.menuPauseVisible = true
        session.readyToPlay()
        XCTAssertFalse(session.menuPauseVisible, "Resume must return to the interrupted setup screen")
        XCTAssertTrue(session.paused)
        session.receiveTimingResult("100")
        XCTAssertEqual(session.setupStage, .timing, "Ignore late results from a cancelled check")
        session.skipTimingCheck()
        XCTAssertEqual(session.setupStage, .playing, "skipped: play starts (no Ready tap, T5)")
        XCTAssertFalse(session.paused)
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
