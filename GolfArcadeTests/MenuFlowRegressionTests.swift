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
        XCTAssertEqual(session.setupStage, .ready)
        XCTAssertTrue(session.paused, "Calibration completion must wait for Ready")
        XCTAssertFalse(session.checkingTiming)
        session.readyToPlay()
        XCTAssertEqual(session.setupStage, .playing)
        XCTAssertFalse(session.paused)
        session.tennisPhase = "serve"
        XCTAssertTrue(session.tossVisible)
    }
    /// Online tennis has no timing check (Unity ignores `timingCheck` in a network match, so its screens could never finish: the phone
    /// sat on "Swing on every bounce!" with no ball while the other player waited), and a pause during play starts the owner's 15 s
    /// forfeit clock. "Use the direction I'm pointing now" and "Re-check swing timing" both end in `offerTimingCalibration`, which
    /// online goes from the court scan straight to Ready and is otherwise a no-op.
    func testAnOnlineMatchNeverOffersTimingCalibration() {
        let session = SportsSession()
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.motion.fixtureSensors = true; session.loading.cancel()
        session.debugSetOnlineMatch("match-1")
        session.setupStage = .scan; session.paused = true
        session.offerTimingCalibration()
        XCTAssertEqual(session.setupStage, .ready, "the court scan ends at Ready, not at a timing check nobody can finish")
        XCTAssertFalse(session.timingPrompt); XCTAssertFalse(session.checkingTiming); XCTAssertFalse(session.measuringDelay)
        XCTAssertTrue(session.paused, "Ready is what starts play")

        // Re-aiming while the match is running leaves it running: a pause would start the owner's forfeit clock.
        session.setupStage = .playing; session.paused = false
        session.recheckTiming()
        XCTAssertEqual(session.setupStage, .playing); XCTAssertFalse(session.paused)
        XCTAssertFalse(session.timingPrompt); XCTAssertFalse(session.measuringDelay)

        // Practice and offline matches keep their timing check.
        session.debugSetOnlineMatch(nil)
        session.setupStage = .scan
        session.offerTimingCalibration(); session.debugFinishTVDelay()
        XCTAssertEqual(session.setupStage, .timing); XCTAssertTrue(session.timingPrompt)
    }
    func testOnlineSetupIsVisibleAndCanFinishBeforeTheRuntimeOrOpponentLoads() {
        let session = SportsSession()
        session.active = true; session.sport = "tennis"; session.motion.fixtureSensors = true
        session.debugSetOnlineMatch("independent-setup", seat: 0)
        session.loading.begin(now: LoadingModel.clockNow, multiplayer: true)
        session.setupStage = .scan
        XCTAssertFalse(session.ready); XCTAssertFalse(session.loading.finished)
        XCTAssertTrue(session.showsOnlineTennisSetup, "loading must never hide the local setup instruction")
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
        XCTAssertEqual(session.setupStage, .ready)
        XCTAssertTrue(session.paused)
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
    func testALessonLeftMidwayComesBackToItsResumeScreen() {
        let defaults = UserDefaults(suiteName: "lesson-resume-\(UUID())")!
        let store = OnboardingStore(defaults: defaults)
        store.step = .lesson(.tennis); store.explicitRun = true; store.setLessonStation(.tennis, 3)
        let flow = OnboardingFlow(store: store, progress: SportProgress(defaults: defaults), arguments: [])
        XCTAssertEqual(flow.step, .lesson(.tennis)); XCTAssertTrue(flow.holdsMenu, "no game is running, so the TV shows Resume")
        XCTAssertEqual(flow.rows(), [["resume"], ["choose"], ["skip"]])
        XCTAssertFalse(store.rewardClaimed(.tennis))
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
        store.step = .card; store.characterInitialized = true
        let flow = OnboardingFlow(store: store, progress: progress, arguments: [])
        flow.back()
        XCTAssertEqual(flow.step, .player)
        flow.exitToMenu()
        XCTAssertEqual(flow.step, .done)
        XCTAssertFalse(flow.holdsMenu)
        XCTAssertFalse(progress.finishedTutorial(.golf))
        XCTAssertFalse(store.rewardClaimed(.golf))
    }
    func testPhoneGameplayIsBlockedWithoutAnExternalScreen() {
        let displays = SportsDisplays.shared
        let saved = displays.external
        defer { displays.external = saved }
        displays.external = nil
        XCTAssertNil(displays.gameWindow(preview: true))
        XCTAssertNil(displays.gameWindow(preview: false))
        let menu = TennisMenu.shared
        menu.begin(MenuLaunch(sport: .golf, mode: .round), onPhone: true)
        menu.tap("map-cliffside")
        XCTAssertEqual(menu.screen, .connect)
        XCTAssertFalse(SportsSession.shared.active)
        XCTAssertFalse(menu.rows(.connect).flatMap { $0 }.contains("phone"))
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
