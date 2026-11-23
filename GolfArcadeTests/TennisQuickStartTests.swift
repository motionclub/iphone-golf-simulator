import XCTest
import UIKit
@testable import GolfArcade

/// Quick tennis start (PLAN_Onboarding_Tutorial_TennisQuickStart_1121.md T1–T7, gates G7–G9).
@MainActor final class TennisQuickStartTests: XCTestCase {
    private func freshStore() -> UserDefaults { UserDefaults(suiteName: "quick-start-\(UUID().uuidString)")! }
    private func soloTennis(_ store: UserDefaults) -> SportsSession {
        let session = SportsSession()
        session.timingStore = store
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.motion.fixtureSensors = true; session.loading.cancel()
        session.setupStage = .scan; session.paused = true
        return session
    }

    // MARK: G7: a TV whose whole chain is known: pointing is the whole setup

    func testKnownTVGoesFromPointingStraightToPlay() {
        let store = freshStore()
        SportsTiming.storeChain(0.18, for: SportsTiming.currentTV(), defaults: store)
        let session = soloTennis(store)
        XCTAssertTrue(session.quickStartAvailable)
        session.debugFinishPoint()
        XCTAssertEqual(session.setupStage, .playing, "no flashes, no timing check, no Ready tap")
        XCTAssertFalse(session.measuringDelay); XCTAssertFalse(session.timingPrompt); XCTAssertFalse(session.checkingTiming)
        XCTAssertFalse(session.paused)
        XCTAssertEqual(session.startingLag, 0.18, accuracy: 1e-9, "Unity starts from the saved whole chain")
    }

    /// Point and fill (11-22): a new TV is timed by the circle as it fills, so it needs no flashes and no timing drill either.
    func testUnknownTVGoesFromTheCircleStraightToPlay() {
        let store = freshStore()
        let session = soloTennis(store)
        XCTAssertFalse(session.quickStartAvailable)
        session.beginAxisCapture()
        XCTAssertTrue(session.glowActive, "the circle is up")
        var t = 10.0
        for _ in 0..<40 { t += 0.1; session.receiveGlow(.init(time: t, seeing: true, delay: 0.2, match: 0.93, heading: 0.1)) }
        XCTAssertFalse(session.glowActive, "full in a few seconds")
        XCTAssertEqual(session.latencyReading ?? 0, 0.2 + SportsGlow.gameFrameLead, accuracy: 1e-9)
        session.axisGate.locked = true; session.debugFinishPoint()
        XCTAssertEqual(session.setupStage, .playing, "no flashes, no timing check, no Ready tap")
        XCTAssertFalse(session.measuringDelay); XCTAssertFalse(session.timingPrompt)
        XCTAssertEqual(session.startingLag, 0.2 + SportsGlow.gameFrameLead, accuracy: 1e-9, "Unity starts from the circle's reading")
    }

    /// A phone pointed away drains the circle; the direction comes from where it pointed through the TV.
    func testTheCircleDrainsWhenThePhoneLeavesTheTV() {
        let session = soloTennis(freshStore())
        session.beginAxisCapture()
        var t = 10.0
        for _ in 0..<10 { t += 0.1; session.receiveGlow(.init(time: t, seeing: true, delay: 0.1, match: 0.9, heading: 0.1)) }
        let filled = session.glowProgress
        for _ in 0..<5 { t += 0.1; session.receiveGlow(.init(time: t, seeing: false, delay: nil, match: 0.2, heading: nil)) }
        XCTAssertLessThan(session.glowProgress, filled)
        XCTAssertFalse(session.glowSeeing)
        XCTAssertTrue(session.glowActive)
    }

    func testTheLessonAlwaysRunsTheWholeSetupAndOpensOnTheCalibrateCard() {
        let store = freshStore()
        SportsTiming.storeChain(0.18, for: SportsTiming.currentTV(), defaults: store)
        let session = soloTennis(store)
        session.debugForceFullCalibration(true)
        XCTAssertFalse(session.quickStartAvailable, "the lesson teaches the setup")
        session.beginTennisSetup()
        XCTAssertTrue(session.calibrationExplain, "the lesson's setup opens on why it times the TV")
        XCTAssertEqual(session.setupStage, .scan)
        session.continueCalibrationExplain()
        XCTAssertFalse(session.calibrationExplain)
        XCTAssertTrue(session.glowActive, "the circle, even on a TV whose timing is saved")
    }

    /// Settings → check my timing: the next match runs the circle again (it re-times the TV) and then plays.
    func testSettingsTimingCheckRunsTheCircleOnce() {
        let store = freshStore()
        SportsTiming.storeChain(0.18, for: SportsTiming.currentTV(), defaults: store)
        let session = soloTennis(store)
        session.forceTimingCheckNextMatch()
        XCTAssertFalse(session.quickStartAvailable)
        session.beginAxisCapture()
        XCTAssertTrue(session.glowActive)
        var t = 10.0
        for _ in 0..<40 { t += 0.1; session.receiveGlow(.init(time: t, seeing: true, delay: 0.15, match: 0.9, heading: 0)) }
        session.axisGate.locked = true; session.debugFinishPoint()
        XCTAssertEqual(session.setupStage, .playing)
        XCTAssertEqual(session.startingLag, 0.18, accuracy: 1e-9, "the saved whole chain stays the prior while play has not moved it")
    }

    /// One TV for two phones: the TV phone with a known TV goes quick, and the phone without the TV follows it (same picture).
    func testSharedTVPhoneFollowsTheTVPhonesQuickStart() throws {
        let session = SportsSession(), service = MultiplayerService.shared
        session.timingStore = freshStore()
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        service.mockOneTV(otherStep: "glow:on:30")
        session.active = true; session.ready = true; session.sport = "tennis"
        session.debugSetOnlineMatch("one-tv-quick", seat: 0, controllerOnly: true)
        session.loading.cancel(); session.setupStage = .scan
        session.motion.fixtureSensors = true; session.axisGate.locked = true
        session.debugFinishPoint()
        XCTAssertEqual(session.calibrationStep, .waitingForTV, "the TV phone has not said yet")
        service.mockOneTV(otherStep: "quick"); session.advanceCalibration()
        XCTAssertEqual(session.setupStage, .waiting, "the TV phone went quick: no timing check here either, and no Ready tap")
    }

    // MARK: G8: the court direction is kept between matches

    func testAFinishedTennisMatchKeepsTheSensorsAndTheNextMatchSkipsPointing() {
        let store = freshStore()
        SportsTiming.storeChain(0.2, for: SportsTiming.currentTV(), defaults: store)
        let session = soloTennis(store)
        session.setupStage = .playing; session.paused = false
        session.motion.fixtureCourtDirection = true
        session.receiveMatchFinish(won: true, score: "3–0")
        XCTAssertEqual(session.motion.lastLifecycle, "idle", "the match's end keeps the sensors (stopping them lost the direction)")
        session.end()
        XCTAssertEqual(session.motion.lastLifecycle, "idle", "leaving keeps them too, for the next match")
        XCTAssertTrue(session.motion.hasUsableCourtDirection)
        // the next match, on the same TV
        session.active = true; session.ready = true; session.loading.cancel(); session.setupStage = .scan; session.paused = true
        session.beginTennisSetup()
        XCTAssertEqual(session.setupStage, .playing, "nothing to set up: no pointing, no flashes, no Ready")
        session.active = false
    }

    func testGolfStillStopsTheSensors() {
        let session = soloTennis(freshStore())
        session.sport = "golf"
        session.receiveMatchFinish(won: true, score: "")
        XCTAssertEqual(session.motion.lastLifecycle, "stop")
        session.active = false
    }

    // MARK: G9: the stores and the key

    func testFlashesAndTimingCheckKeepSeparateValues() {
        let store = freshStore(), tv = "AirPlay|uid-1|Living Room|1920x1080"
        SportsTiming.storePicture(0.12, for: tv, defaults: store)
        XCTAssertNil(SportsTiming.storedChain(for: tv, defaults: store), "a picture delay is never taken for the whole chain")
        SportsTiming.storeChain(0.19, for: tv, defaults: store)
        XCTAssertEqual(SportsTiming.storedPicture(for: tv, defaults: store), 0.12)
        XCTAssertEqual(SportsTiming.storedChain(for: tv, defaults: store), 0.19)
        XCTAssertNotEqual(SportsTiming.pictureKey, SportsTiming.chainKey)
    }

    func testRouteKeyHoldsTheUIDSoTwoTVsWithOneNameDoNotShare() {
        let a = SportsTiming.routeKey(type: "AirPlay", uid: "uid-a", name: "Speaker", screen: CGSize(width: 1920, height: 1080))
        let b = SportsTiming.routeKey(type: "AirPlay", uid: "uid-b", name: "Speaker", screen: CGSize(width: 1920, height: 1080))
        XCTAssertNotEqual(a, b)
        XCTAssertTrue(a.contains("uid-a"))
        XCTAssertEqual(SportsTiming.legacyName(of: a), "Speaker")
        XCTAssertNotEqual(a, SportsTiming.routeKey(type: "AirPlay", uid: "uid-a", name: "Speaker", screen: CGSize(width: 3840, height: 2160)))
    }

    func testTheOldSharedSlotIsOnlyAPicturePrior() {
        let store = freshStore(), tv = SportsTiming.routeKey(type: "Speaker", uid: "u", name: "Living Room", screen: nil)
        store.set(["Living Room": 0.21], forKey: "sports.tv.timing.v2")
        XCTAssertEqual(SportsTiming.storedPicture(for: tv, defaults: store), 0.21)
        XCTAssertNil(SportsTiming.storedChain(for: tv, defaults: store), "an 11-20 value never skips the timing check")
    }

    // MARK: T6: play's learned lag

    func testLearnedLagMovesTheStoredTimingButAnOutlierNeedsToRepeat() {
        let store = freshStore(), tv = "t"
        XCTAssertEqual(SportsTiming.learn(0.20, for: tv, defaults: store), 0.20, "a first value is kept")
        XCTAssertEqual(SportsTiming.learn(0.23, for: tv, defaults: store), 0.23, "a near one replaces it")
        XCTAssertEqual(SportsTiming.learn(0.45, for: tv, defaults: store), 0.23, "one outlier is kept aside")
        XCTAssertEqual(SportsTiming.learn(0.21, for: tv, defaults: store), 0.21)
        _ = SportsTiming.learn(0.50, for: tv, defaults: store)
        XCTAssertEqual(SportsTiming.learn(0.48, for: tv, defaults: store) ?? 0, 0.49, accuracy: 1e-9, "said twice: it replaces the stored value")
    }

    func testTheEndOfAMatchSavesWhatPlayLearned() {
        let store = freshStore()
        let session = soloTennis(store)
        session.setupStage = .playing
        session.debugLearnedLag(0.17)
        session.receiveMatchFinish(won: false, score: "1–3")
        XCTAssertEqual(SportsTiming.storedChain(for: SportsTiming.currentTV(), defaults: store) ?? 0, 0.17, accuracy: 1e-9)
        session.active = false
    }

    // MARK: T7: the rematch intro

    func testATennisRematchSkipsTheIntroButGolfKeepsItsShortCut() {
        let session = SportsSession()
        let before = session.presentationIntros
        defer { session.presentationIntros = before }
        session.presentationIntros = "full"
        session.sport = "tennis"; session.prepareRematchPresentation()
        XCTAssertEqual(session.consumePresentationIntroCut(), "off")
        XCTAssertEqual(session.consumePresentationIntroCut(), "full", "only the rematch")
        session.sport = "golf"; session.prepareRematchPresentation()
        XCTAssertEqual(session.consumePresentationIntroCut(), "short")
    }

    // MARK: the setup steps the host passes on

    func testHostKeepsEverySetupStepThePhonesSend() {
        for step in ["direction", "hold", "pointed", "timing", "go:12.5", "check:3", "quick", "ready"] {
            XCTAssertTrue(MultiplayerLobby.isSetupStep(step), step)
        }
        for step in ["", "go:x", "check:", "anything", String(repeating: "g", count: 40)] { XCTAssertFalse(MultiplayerLobby.isSetupStep(step), step) }
    }
}
