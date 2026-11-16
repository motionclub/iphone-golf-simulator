import XCTest
import UIKit
@testable import GolfArcade

/// Onboarding v3 (PLAN_Onboarding_v3_IntroTutorial.md): the intro over the menu with no TV required, Play locked to the Tutorial
/// (golf → tennis → bowling), the how-to-play / play-safe card before lessons and games, and the gates in GATE_RESULTS.md.
@MainActor final class OnboardingTests: XCTestCase {
    private func fixture() -> (UserDefaults, OnboardingStore, SportProgress) {
        let d = UserDefaults(suiteName: "onboarding-tests-\(UUID())")!
        return (d, OnboardingStore(defaults: d), SportProgress(defaults: d))
    }
    /// A flow whose menu, Locker and lessons are stand-ins (no runtime in unit tests).
    private func flow(_ store: OnboardingStore, _ progress: SportProgress, tv: Bool = false) -> (OnboardingFlow, () -> [String]) {
        let f = OnboardingFlow(store: store, progress: progress, arguments: [])
        var log: [String] = []
        f.partyWaits = { false }; f.tvConnected = { tv }
        f.beginLesson = { sport, station in log.append("lesson:\(sport.rawValue):\(station)") }
        f.stateChanged = {}
        return (f, { log })
    }
    override func setUp() async throws { PlaySafeGate.shared.reset() }
    override func tearDown() async throws { PlaySafeGate.shared.reset() }

    // GATE NO_AIRPLAY + INTRO_ORDER + OVERLAY: the intro is tips over the live menu (no screens of its own), the same with or without a TV
    func testFreshInstallRunsTheIntroAsTipsOverTheMenu() {
        for tv in [false, true] {
            let (_, store, progress) = fixture()
            let (f, _) = flow(store, progress, tv: tv)
            XCTAssertEqual(f.step, .welcome); XCTAssertFalse(f.holdsMenu, "the menu boots behind the intro: nothing waits for a TV")
            XCTAssertFalse(f.introOnPhone, "the TV is never dimmed for a phone-only intro screen")
            f.menuScreenChanged("home")
            XCTAssertEqual(f.coach(tv: tv)?.id, "welcome"); XCTAssertEqual(f.coach(tv: tv)?.action, "next")
            XCTAssertEqual(f.coach(tv: tv)?.body.contains("SELECT"), tv, "with a TV the tip teaches the phone's remote")
            f.coachNext("welcome"); XCTAssertEqual(f.step, .customize)
            XCTAssertEqual(f.coach(tv: tv)?.target, "tab-locker"); XCTAssertEqual(f.coach(tv: tv)?.action, "press")
            f.menuScreenChanged("locker"); XCTAssertEqual(f.coach(tv: tv)?.action, "hint", "in the Locker the tip does not hold the menu")
            f.menuScreenChanged("home"); XCTAssertEqual(f.step, .how, "back from the Locker: how it works")
            for page in 0..<3 { XCTAssertEqual(f.coach(tv: tv)?.id, "how-\(page)"); f.coachNext("how-\(page)") }
            XCTAssertTrue(f.coach(tv: tv)?.body.contains("2 m (6 ft)") == false, "Play safe was the card before")
            XCTAssertEqual(f.step, .goPlay); XCTAssertEqual(f.coach(tv: tv)?.target, "play")
            f.coachNext("how-1"); XCTAssertEqual(f.step, .goPlay, "a stale NEXT changes nothing")
            f.menuScreenChanged("clubhouse"); XCTAssertEqual(f.coach(tv: tv)?.target, "tab-home", "wandered off: back to the Plaza first")
            f.menuScreenChanged("home"); f.menuScreenChanged("sport"); XCTAssertEqual(f.step, .tutorial)
            XCTAssertEqual(f.coach(tv: tv)?.target, "sport-tutorial")
            f.menuScreenChanged("tutorial"); XCTAssertEqual(f.coach(tv: tv)?.target, "bay-tutorial-golf")
            XCTAssertEqual(OnboardingFlow(store: store, progress: progress, arguments: []).step, .tutorial, "a quit resumes where it was")
        }
    }
    func testTheTipsSaySafetyAndTheTVSideOfThings() {
        let (_, store, progress) = fixture()
        let (f, _) = flow(store, progress)
        f.menuScreenChanged("home"); f.coachNext("welcome"); f.keepLook(); f.coachNext("how-0")
        XCTAssertEqual(f.coach(tv: true)?.title, "You're on the big screen")
        XCTAssertTrue(f.coach(tv: false)?.body.contains("AirPlay") == true, "no TV: how to get one, and golf and bowling without")
        f.coachNext("how-1")
        let safe = f.coach(tv: true)
        XCTAssertTrue(safe?.body.contains("2 m (6 ft) back from the TV") == true)
        XCTAssertFalse(safe?.body.lowercased().contains("swing hard") == true)
        let json = f.coachJSON(tv: true)
        XCTAssertTrue(json.contains(#""id":"how-2""#) && json.contains(#""action":"next""#), json)
        f.partyWaits = { true }; XCTAssertEqual(f.coachJSON(tv: true), "", "no tips while a party is joining")
    }
    func testKeepThisLookSkipsTheLocker() {
        let (_, store, progress) = fixture()
        let (f, _) = flow(store, progress)
        f.next(); f.keepLook()
        XCTAssertEqual(f.step, .how)
    }
    func testThePlaySafeCardSaysTwoMetresFromTheTV() {
        XCTAssertTrue(PlaySafeGate.safety.contains { $0.text.contains("2 m (6 ft) back from the TV") })
        XCTAssertTrue(PlaySafeGate.safety.allSatisfy { !$0.text.lowercased().contains("swing hard") }, "App Review 1.4.5: never urge a hard swing")
        for sport in OnboardingFlow.lessons { XCTAssertGreaterThanOrEqual(PlaySafeGate.steps(sport, tvConnected: true).count, 3, sport.rawValue) }
        XCTAssertTrue(PlaySafeGate.steps(.tennis, tvConnected: true).joined().contains("calibration"), "tennis explains calibration first")
    }

    // GATE LOCK
    func testPlayIsLockedToTheTutorialInOrder() {
        let (_, store, progress) = fixture()
        store.step = .tutorial; store.explicitRun = true
        let (f, _) = flow(store, progress)
        XCTAssertTrue(f.locked)
        for bay in ["bay-tennis-exhibition", "bay-golf-round", "bay-bowling-play", "bay-golf-online", "bay-tennis-calibration", "sport-daily"] {
            XCTAssertFalse(f.allows(bay), bay)
        }
        for open in ["bay-tutorial-golf", "look-mirror", "desk-settings", "screen-howto", "board-invite", "mailbox-feedback"] { XCTAssertTrue(f.allows(open), open) }
        XCTAssertEqual(f.nextLesson, .golf)
        XCTAssertTrue(f.available(.golf)); XCTAssertFalse(f.available(.tennis)); XCTAssertFalse(f.available(.bowling))
        XCTAssertEqual(f.menuState, #"{"locked":true,"next":"golf","done":[],"deferred":[]}"#)
        f.startLesson(.bowling)
        XCTAssertNil(PlaySafeGate.shared.request, "a later lesson cannot start first")
    }
    func testALessonOpensItsHowToPlayCardThenStarts() {
        let (_, store, progress) = fixture()
        store.step = .tutorial; store.explicitRun = true; store.setLessonStation(.golf, 3)
        let (f, log) = flow(store, progress)
        f.startLesson(.golf)
        let r = try? XCTUnwrap(PlaySafeGate.shared.request)
        XCTAssertEqual(r?.sport, .golf); XCTAssertEqual(r?.tutorial, true); XCTAssertNil(r?.onDefer)
        XCTAssertEqual(log(), [], "nothing loads before the card is accepted")
        PlaySafeGate.shared.accept()
        XCTAssertEqual(log(), ["lesson:golf:3"], "accepted: the lesson starts (resuming its station)")
        XCTAssertFalse(PlaySafeGate.shared.needsCard(.golf), "and the game it loads does not ask again")
    }

    // GATE UNLOCK
    func testFinishingAllThreeUnlocksEverything() {
        let (_, store, progress) = fixture()
        store.step = .tutorial; store.explicitRun = true
        let (f, _) = flow(store, progress, tv: true)
        f.completed(.golf); f.menuScreenChanged("tutorial")
        XCTAssertEqual(f.celebrating, .golf); XCTAssertTrue(f.locked); XCTAssertEqual(f.nextLesson, .tennis)
        XCTAssertEqual(f.coach(tv: true)?.title, "Golf done! Tennis next"); XCTAssertEqual(f.coach(tv: true)?.target, "bay-tutorial-tennis")
        XCTAssertEqual(f.menuState, #"{"locked":true,"next":"tennis","done":["golf"],"deferred":[]}"#)
        f.completed(.tennis); XCTAssertEqual(f.nextLesson, .bowling); XCTAssertTrue(f.locked)
        f.completed(.bowling)
        XCTAssertEqual(f.step, .done); XCTAssertFalse(f.locked); XCTAssertTrue(f.allows("bay-golf-round"))
        XCTAssertEqual(f.celebrating, .bowling)
        XCTAssertEqual(f.coach(tv: true)?.id, "unlocked", "the last tip says everything is unlocked")
        f.coachNext("unlocked"); XCTAssertNil(f.celebrating); XCTAssertNil(f.coach(tv: true))
        XCTAssertTrue(OnboardingFlow.lessons.allSatisfy(progress.finishedTutorial))
    }
    func testNoTVPutsTennisOffAndStillUnlocks() {
        let (_, store, progress) = fixture()
        store.step = .tutorial; store.explicitRun = true
        let (f, log) = flow(store, progress, tv: false)
        f.completed(.golf); f.dismissCelebration(playNext: false)
        f.startLesson(.tennis)
        XCTAssertNotNil(PlaySafeGate.shared.request?.onDefer, "no TV: the tennis card offers to put it off")
        PlaySafeGate.shared.deferLesson()
        XCTAssertTrue(store.tennisDeferred); XCTAssertEqual(f.nextLesson, .bowling); XCTAssertEqual(log(), [])
        XCTAssertEqual(f.menuState, #"{"locked":true,"next":"bowling","done":["golf"],"deferred":["tennis"]}"#)
        f.completed(.bowling)
        XCTAssertEqual(f.step, .done, "golf and bowling done on a phone with no TV: free to play")
        XCTAssertTrue(f.available(.tennis), "the tennis lesson stays in the Tutorial for later")
    }
    func testTheCardAfterALessonStartsTheNextOne() {
        let (_, store, progress) = fixture()
        store.step = .tutorial; store.explicitRun = true
        let (f, _) = flow(store, progress, tv: true)
        f.completed(.golf)
        f.dismissCelebration(playNext: true)
        XCTAssertNil(f.celebrating); XCTAssertEqual(PlaySafeGate.shared.request?.sport, .tennis)
    }

    // GATE SAFETY
    func testTheFirstGameOfEachSportWaitsForTheCardOncePerRun() {
        let gate = PlaySafeGate.shared
        var started = 0
        XCTAssertTrue(gate.hold(sport: "golf") { started += 1 }, "the first golf game waits on its loading screen")
        XCTAssertTrue(gate.request?.holding == true); XCTAssertEqual(started, 0)
        gate.accept(); XCTAssertEqual(started, 1)
        XCTAssertFalse(gate.hold(sport: "golf") { started += 1 }, "a second golf game goes straight in")
        XCTAssertTrue(gate.hold(sport: "bowling") { started += 1 }, "another sport asks once too")
        gate.sessionEnded(); XCTAssertNil(gate.request, "a game left while held drops its card")
        XCTAssertFalse(gate.hold(sport: "football") {}, "not a playable sport")
    }

    // migration
    func testPhonesThatUsedTheAppBeforeSkipIt() {
        let (d, store, progress) = fixture()
        d.set(Date().timeIntervalSince1970 - 86_400, forKey: "ftue.installedAt.v1")
        XCTAssertEqual(OnboardingFlow(store: store, progress: progress, arguments: []).step, .done)
        let (d2, store2, progress2) = fixture()
        d2.set("done", forKey: "ftue.step.v2")
        XCTAssertEqual(OnboardingFlow(store: store2, progress: progress2, arguments: []).step, .done, "finished the 10-25 onboarding")
    }
    func testAFinishedLessonSkipsOnboarding() {
        for sport in [Sport.tennis, .golf] {
            let (_, store, progress) = fixture(); progress.completeTutorial(sport)
            XCTAssertFalse(OnboardingFlow(store: store, progress: progress, arguments: []).active)
        }
    }
    func testResetOnlyClearsFTUEKeys() {
        let (d, store, progress) = fixture()
        let roster = Data([1, 2, 3]); d.set(roster, forKey: "players.v1")
        progress.completeTutorial(.tennis)
        store.step = .how; store.characterInitialized = true; store.setLessonStation(.golf, 4); store.tennisDeferred = true
        _ = OnboardingFlow(store: store, progress: progress, arguments: ["-resetOnboarding", "-forceOnboarding"])
        XCTAssertEqual(store.step, .welcome); XCTAssertFalse(store.characterInitialized); XCTAssertEqual(store.lessonStation(.golf), 0)
        XCTAssertFalse(store.tennisDeferred)
        XCTAssertEqual(d.data(forKey: "players.v1"), roster)
        XCTAssertTrue(d.bool(forKey: "sport.tennis.tutorialDone.v1"))
    }
    func testLegacyArgumentsSkipUnlessForced() {
        for arg in ["-skipPlayerCalibration", "-startInCameraMode", "-startCourse", "--lobby-mock", "--lobby", "--character-editor", "--resume-tennis-round-3", "-benchTennis", "-range.swingInput"] {
            let (_, s, p) = fixture()
            XCTAssertFalse(OnboardingFlow(store: s, progress: p, arguments: [arg]).active, arg)
            XCTAssertTrue(OnboardingFlow(store: s, progress: p, arguments: [arg, "-forceOnboarding"]).active, arg)
        }
    }
    func testStepKeysRoundTrip() {
        for step in OnboardingStep.allCases { XCTAssertEqual(OnboardingStep(key: step.key), step) }
        XCTAssertNil(OnboardingStep(key: "lesson:golf"), "the 10-25 keys are not v3 steps")
    }
    func testNameIsBounded() {
        XCTAssertEqual(OnboardingStore.name("  \n"), "Player 1")
        XCTAssertEqual(OnboardingStore.name(String(repeating: "a", count: 60)).count, 14)
    }
    func testPartyPutsTheIntroAsideAndItComesBack() {
        let (_, store, progress) = fixture()
        let (f, _) = flow(store, progress)
        var party = false
        f.partyWaits = { party }
        XCTAssertTrue(f.introShowing)
        party = true; XCTAssertFalse(f.introShowing); XCTAssertTrue(f.active, "put off, not finished")
        party = false; XCTAssertTrue(f.introShowing); XCTAssertEqual(f.step, .welcome)
    }

    // lessons and rewards (unchanged from v2)
    func testLessonEventsDriveTheCoachAndResumeStation() {
        let center = LessonCenter.shared
        defer { center.end() }
        center.receive(#"{"kind":"station","sport":"bowling","index":2,"count":5,"key":"line","name":"Line up","title":"Pick your spot","ask":"Move","hint":"Arrows","tips":["a","b"]}"#)
        XCTAssertEqual(center.sport, .bowling); XCTAssertEqual(center.station.index, 2); XCTAssertTrue(center.explaining)
        XCTAssertEqual(OnboardingFlow.shared.store.lessonStation(.bowling), 2, "a lesson resumes at the station it reached")
        for n in 1...3 { center.receive(#"{"kind":"attempt","result":"miss","grade":"","text":"Move 3 boards","misses":\#(n),"read":[["Board","20",0]]}"#) }
        XCTAssertTrue(center.hintShown); XCTAssertTrue(center.skipOffered)
        center.receive(#"{"kind":"attempt","result":"pass","grade":"PASS","text":"Nice","misses":3,"read":[]}"#)
        XCTAssertEqual(center.shown, .pass); XCTAssertFalse(center.skipOffered)
        OnboardingFlow.shared.store.setLessonStation(.bowling, 0)
    }
    func testFirstTutorialFillsLevelTwoAndReplayPaysNothing() {
        let (_, store, _) = fixture(); let player = UUID()
        _ = Progression.shared.award(player: player, stats: MatchStats(), won: false, score: "", opponent: "", practice: false, difficulty: 0)
        let before = Progression.shared.entry(for: player)
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .golf, store: store), 200 - before.xp)
        XCTAssertEqual(Progression.shared.entry(for: player).level, 2)
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .golf, store: store), 0)
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .bowling, store: store), 50, "bowling's lesson pays too")
    }
    func testReplayRunsTheIntroAgainAndKeepsProgress() {
        let (defaults, store, progress) = fixture()
        let hero = Data([9, 8, 7]); defaults.set(hero, forKey: "players.v1")
        for s in OnboardingFlow.lessons { progress.completeTutorial(s) }
        let (f, _) = flow(store, progress)
        f.replay()
        XCTAssertEqual(f.step, .welcome); XCTAssertTrue(store.characterInitialized)
        XCTAssertEqual(defaults.data(forKey: "players.v1"), hero)
        XCTAssertNil(f.nextLesson, "every lesson is still done")
        f.next(); f.keepLook(); f.next(); f.next(); f.next(); f.menuScreenChanged("home"); f.menuScreenChanged("sport")
        XCTAssertEqual(f.step, .tutorial); XCTAssertNil(f.nextLesson)
    }
}
