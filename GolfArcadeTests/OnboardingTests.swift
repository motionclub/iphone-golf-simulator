import XCTest
import UIKit
@testable import GolfArcade

/// Onboarding (PLAN_Onboarding_Tutorial_TennisQuickStart_1121.md): four tips over the menu with no TV required, the first PLAY runs the
/// Tutorial (golf → tennis → bowling), a gated sport asks lesson or skip, the play-safe card before lessons and games
/// (gates G1–G4 in proof/onboarding-1121/GATE_RESULTS.md).
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

    // G1: four tips before PLAY, over the live menu, the same with or without a TV
    func testFreshInstallRunsAShortIntroAsTipsOverTheMenu() {
        for tv in [false, true] {
            PlaySafeGate.shared.reset()
            let (_, store, progress) = fixture()
            let (f, _) = flow(store, progress, tv: tv)
            XCTAssertEqual(f.step, .welcome); XCTAssertFalse(f.holdsMenu, "the menu boots behind the intro: nothing waits for a TV")
            XCTAssertFalse(f.introOnPhone, "the TV is never dimmed for a phone-only intro screen")
            var tips: [String] = []
            f.menuScreenChanged("home")
            tips.append(f.coach(tv: tv)!.id)
            XCTAssertEqual(f.coach(tv: tv)?.id, "welcome"); XCTAssertEqual(f.coach(tv: tv)?.action, "next")
            XCTAssertTrue(f.coach(tv: tv)!.body.contains("golf, tennis and bowling"), "the welcome says what the game is")
            XCTAssertEqual(f.coach(tv: tv)?.body.contains("SELECT"), tv, "with a TV the tip teaches the phone's remote")
            f.coachNext("welcome"); XCTAssertEqual(f.step, .customize)
            tips.append(f.coach(tv: tv)!.id)
            XCTAssertEqual(f.coach(tv: tv)?.target, "tab-locker"); XCTAssertEqual(f.coach(tv: tv)?.action, "press")
            f.menuScreenChanged("locker"); tips.append(f.coach(tv: tv)!.id)
            XCTAssertEqual(f.coach(tv: tv)?.action, "hint", "in the Locker the tip does not hold the menu")
            f.menuScreenChanged("home"); XCTAssertEqual(f.step, .goPlay, "back from the Locker: straight to PLAY (no how-it-works pages)")
            tips.append(f.coach(tv: tv)!.id)
            XCTAssertEqual(f.coach(tv: tv)?.target, "play")
            XCTAssertEqual(tips, ["welcome", "customize", "locker", "goPlay"], "G1: four tips")
            f.menuScreenChanged("clubhouse"); XCTAssertEqual(f.coach(tv: tv)?.target, "tab-home", "wandered off: back to the Plaza first")
            f.menuScreenChanged("home"); f.menuScreenChanged("sport"); XCTAssertEqual(f.step, .tutorial)
            XCTAssertEqual(PlaySafeGate.shared.request?.kind, .tutorial, "G2: the first PLAY opens the Tutorial's card")
            XCTAssertNil(f.coach(tv: tv), "no tip over the card")
            XCTAssertTrue(store.sportGate, "a fresh install gates each sport behind its lesson")
            XCTAssertEqual(OnboardingFlow(store: store, progress: progress, arguments: []).step, .tutorial, "a quit resumes where it was")
        }
    }
    func testAPhoneSavedOnTheRetiredHowStepResumesAtPlay() {
        let (_, store, progress) = fixture()
        store.step = .how; store.explicitRun = true
        let (f, _) = flow(store, progress)
        XCTAssertEqual(f.step, .goPlay)
        f.partyWaits = { true }; XCTAssertEqual(f.coachJSON(tv: true), "", "no tips while a party is joining")
    }
    func testKeepThisLookGoesToPlay() {
        let (_, store, progress) = fixture()
        let (f, _) = flow(store, progress)
        f.next(); f.keepLook()
        XCTAssertEqual(f.step, .goPlay)
        f.back(); XCTAssertEqual(f.step, .customize)
    }
    func testThePlaySafeCardSaysTwoMetresFromTheTV() {
        XCTAssertEqual(PlaySafeGate.tutorialRows.map(\.sport), OnboardingFlow.lessons)
        XCTAssertTrue(PlaySafeGate.tutorialRows[0].what.lowercased().contains("putting"))
        XCTAssertTrue(PlaySafeGate.tutorialRows[1].what.lowercased().contains("calibrate"))
        XCTAssertTrue(PlaySafeGate.safety.contains { $0.text.contains("2 m (6 ft) back from the TV") })
        XCTAssertTrue(PlaySafeGate.safety.allSatisfy { !$0.text.lowercased().contains("swing hard") }, "App Review 1.4.5: never urge a hard swing")
        for sport in OnboardingFlow.lessons { XCTAssertGreaterThanOrEqual(PlaySafeGate.steps(sport, tvConnected: true).count, 2, sport.rawValue) }
        XCTAssertFalse(PlaySafeGate.steps(.tennis, tvConnected: true).joined().contains("calibration"), "calibration is gone from the game")
    }

    // G4: a gated sport asks, play the lesson or skip it
    func testAGatedSportAsksLessonOrSkip() {
        let (_, store, progress) = fixture()
        store.step = .tutorial; store.explicitRun = true; store.sportGate = true
        let (f, log) = flow(store, progress)
        XCTAssertFalse(f.locked, "Play itself is open")
        for bay in ["bay-tennis-exhibition", "bay-golf-round", "bay-bowling-play", "bay-golf-online", "sport-daily"] { XCTAssertFalse(f.allows(bay), bay) }
        for open in ["bay-tutorial-golf", "bay-gate-golf", "bay-tutorial-bowling", "look-mirror", "desk-settings", "screen-howto", "board-invite", "mailbox-feedback"] { XCTAssertTrue(f.allows(open), open) }
        XCTAssertTrue(OnboardingFlow.lessons.allSatisfy(f.available), "any lesson, in any order")
        XCTAssertEqual(f.menuState, #"{"locked":false,"next":"golf","done":[],"deferred":[],"gate":["golf","tennis","bowling"]}"#)
        var opened = 0
        f.lessonFirst("bay-bowling-play") { opened += 1 }
        XCTAssertEqual(PlaySafeGate.shared.request?.sport, .bowling)
        XCTAssertEqual(PlaySafeGate.shared.request?.kind, .gate, "the card asks: lesson or skip")
        XCTAssertNotNil(PlaySafeGate.shared.request?.onSkip)
        PlaySafeGate.shared.skipLesson()
        XCTAssertEqual(opened, 1, "Skip goes on to what was picked")
        XCTAssertTrue(f.allows("bay-bowling-play"), "skipped: bowling is open")
        XCTAssertTrue(store.lessonSkipped(.bowling)); XCTAssertFalse(progress.finishedTutorial(.bowling), "skipped is not done")
        XCTAssertEqual(log(), [], "a skip loads nothing")
        XCTAssertEqual(f.menuState, #"{"locked":false,"next":"golf","done":[],"deferred":[],"gate":["golf","tennis"]}"#)
        // Play the lesson
        f.gate(.golf)
        PlaySafeGate.shared.accept()
        XCTAssertEqual(log(), ["lesson:golf:0"], "Play the lesson starts it")
        XCTAssertFalse(f.chaining, "a gate's lesson is one lesson, not the whole Tutorial")
        f.completed(.golf)
        XCTAssertEqual(f.celebrating, .golf); XCTAssertNil(PlaySafeGate.shared.request, "no next card after a gate's lesson")
        // skipping the last gated sport ends the guided part
        f.lessonFirst("bay-tennis-exhibition"); PlaySafeGate.shared.skipLesson()
        XCTAssertEqual(f.step, .done); XCTAssertTrue(OnboardingFlow.lessons.allSatisfy { !f.needsLesson($0) })
    }
    func testPhonesWithoutTheGateKeepEverythingOpen() {
        let (_, store, progress) = fixture()
        store.step = .done; _ = store.installedAt   // (not a fresh install)
        let (f, _) = flow(store, progress)
        for bay in ["bay-tennis-exhibition", "bay-golf-round", "bay-bowling-play", "sport-daily"] { XCTAssertTrue(f.allows(bay), bay) }
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

    // G2 + G3: PLAY runs the Tutorial, golf → tennis → bowling, each finished lesson offering the next
    func testTheTutorialRunsAllThreeLessonsInOrder() {
        let (_, store, progress) = fixture()
        store.step = .goPlay; store.explicitRun = true; store.sportGate = true
        let (f, log) = flow(store, progress, tv: true)
        f.menuScreenChanged("sport")
        XCTAssertEqual(PlaySafeGate.shared.request?.kind, .tutorial); XCTAssertTrue(f.chaining)
        PlaySafeGate.shared.accept()
        XCTAssertEqual(log(), ["lesson:golf:0"], "G2: Start launches golf's first station")
        XCTAssertFalse(PlaySafeGate.shared.needsCard(.bowling), "the Tutorial's card covers every sport's safety")
        f.completed(.golf)
        XCTAssertEqual(f.step, .tutorial, "the run carries on")
        XCTAssertEqual(PlaySafeGate.shared.request?.sport, .tennis, "G3: golf done offers tennis")
        XCTAssertEqual(PlaySafeGate.shared.request?.note, "Golf done. Next up, tennis (2 of 3)")
        XCTAssertNotNil(PlaySafeGate.shared.request?.onSkip, "each next lesson can be skipped")
        PlaySafeGate.shared.accept()
        XCTAssertEqual(log().last, "lesson:tennis:0")
        f.completed(.tennis)
        XCTAssertEqual(PlaySafeGate.shared.request?.sport, .bowling, "G3: tennis done offers bowling")
        PlaySafeGate.shared.accept(); f.completed(.bowling)
        XCTAssertNil(PlaySafeGate.shared.request)
        XCTAssertEqual(f.step, .done); XCTAssertFalse(f.chaining)
        XCTAssertEqual(f.coach(tv: true)?.id, "unlocked-all")
        XCTAssertTrue(OnboardingFlow.lessons.allSatisfy { !f.needsLesson($0) }, "G3: nothing is gated after the Tutorial")
        f.coachNext("unlocked-all"); XCTAssertNil(f.coach(tv: true))
    }
    func testTheTutorialCanSkipOneAndStopLater() {
        let (_, store, progress) = fixture()
        store.step = .tutorial; store.explicitRun = true; store.sportGate = true
        let (f, log) = flow(store, progress, tv: true)
        f.startTutorial(); PlaySafeGate.shared.accept(); f.completed(.golf)
        PlaySafeGate.shared.skipLesson()
        XCTAssertTrue(store.lessonSkipped(.tennis))
        XCTAssertEqual(PlaySafeGate.shared.request?.sport, .bowling, "skipping tennis moves on to bowling")
        XCTAssertNil(PlaySafeGate.shared.request?.note, "(no 'done' line after a skip)")
        PlaySafeGate.shared.cancel()
        XCTAssertFalse(f.chaining); XCTAssertEqual(f.step, .done, "Later after a lesson ends the guided part")
        XCTAssertFalse(f.allows("bay-bowling-play"), "bowling still asks for its lesson")
        XCTAssertEqual(log(), ["lesson:golf:0"])
    }
    func testNotNowOnTheTutorialCardLeavesEachSportGated() {
        let (_, store, progress) = fixture()
        store.step = .goPlay; store.explicitRun = true; store.sportGate = true
        let (f, log) = flow(store, progress, tv: true)
        f.menuScreenChanged("sport"); PlaySafeGate.shared.cancel()
        XCTAssertEqual(f.step, .tutorial); XCTAssertFalse(f.chaining); XCTAssertEqual(log(), [])
        XCTAssertEqual(f.coach(tv: true)?.body, "Each one starts with a short lesson, or skip it.")
        XCTAssertFalse(f.allows("bay-golf-round"))
    }
    func testNoTVPutsTennisOffAndTheTutorialGoesOnToBowling() {
        let (_, store, progress) = fixture()
        store.step = .tutorial; store.explicitRun = true; store.sportGate = true
        let (f, log) = flow(store, progress, tv: false)
        f.startTutorial(); PlaySafeGate.shared.accept(); f.completed(.golf)
        XCTAssertEqual(PlaySafeGate.shared.request?.sport, .tennis)
        XCTAssertNotNil(PlaySafeGate.shared.request?.onDefer, "no TV: the tennis card offers to put it off")
        PlaySafeGate.shared.deferLesson()
        XCTAssertTrue(store.tennisDeferred)
        XCTAssertEqual(PlaySafeGate.shared.request?.sport, .bowling, "the Tutorial goes on to bowling")
        XCTAssertFalse(f.allows("bay-tennis-exhibition"), "tennis still waits for its lesson (or a skip)")
        XCTAssertEqual(log(), ["lesson:golf:0"])
    }
    func testASingleLessonEndsOnItsUnlockTip() {
        let (_, store, progress) = fixture()
        store.step = .tutorial; store.explicitRun = true; store.sportGate = true
        let (f, _) = flow(store, progress, tv: true)
        f.startLesson(.golf); PlaySafeGate.shared.accept()
        f.completed(.golf)
        XCTAssertEqual(f.step, .done)
        XCTAssertEqual(f.coach(tv: true)?.title, "Golf unlocked")
        XCTAssertTrue(f.allows("bay-golf-round")); XCTAssertFalse(f.allows("bay-tennis-exhibition"))
        XCTAssertEqual(f.menuState, #"{"locked":false,"next":"tennis","done":["golf"],"deferred":[],"gate":["tennis","bowling"]}"#)
    }

    // GATE SAFETY
    func testTheFirstGameOfEachSportWaitsForTheCardOncePerDay() {
        let gate = PlaySafeGate.shared
        var started = 0
        XCTAssertTrue(gate.hold(sport: "golf") { started += 1 }, "the first golf game waits on its loading screen")
        XCTAssertTrue(gate.request?.holding == true); XCTAssertEqual(started, 0)
        gate.accept(); XCTAssertEqual(started, 1)
        XCTAssertFalse(gate.hold(sport: "golf") { started += 1 }, "a second golf game goes straight in")
        XCTAssertTrue(gate.hold(sport: "bowling") { started += 1 }, "another sport asks once too")
        gate.sessionEnded(); XCTAssertNil(gate.request, "a game left while held drops its card")
        XCTAssertFalse(gate.hold(sport: "football") {}, "not a playable sport")
        // T8: kept across launches for a day
        XCTAssertTrue(PlaySafeGate(defaults: .standard).isAccepted(.golf), "a cold launch remembers it")
        XCTAssertFalse(gate.isAccepted(.golf, now: Date().addingTimeInterval(PlaySafeGate.acceptedFor + 60)), "a day later it asks again")
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
        XCTAssertEqual(center.sport, .bowling); XCTAssertEqual(center.station.index, 2)
        XCTAssertEqual(center.explaining, HowToGIF.available(.bowling), "the opening animation shows on the first station reported, whatever its index")
        center.introDone()
        XCTAssertEqual(center.line, "Move")
        XCTAssertEqual(OnboardingFlow.shared.store.lessonStation(.bowling), 2, "a lesson resumes at the station it reached")
        for n in 1...3 { center.receive(#"{"kind":"attempt","result":"miss","grade":"","text":"Move 3 boards","misses":\#(n),"read":[["Board","20",0]]}"#) }
        XCTAssertTrue(center.hintShown); XCTAssertTrue(center.skipOffered); XCTAssertEqual(center.line, "Arrows", "after two misses the fix replaces the line")
        center.receive(#"{"kind":"attempt","result":"pass","grade":"PASS","text":"Nice","misses":3,"read":[]}"#)
        XCTAssertEqual(center.shown, .pass); XCTAssertFalse(center.skipOffered)
        OnboardingFlow.shared.store.setLessonStation(.bowling, 0)
    }
    func testAStationsExplainCardShowsFirst() {
        let center = LessonCenter.shared
        defer { center.end() }
        center.receive(#"{"kind":"station","sport":"golf","index":0,"count":4,"key":"drive","name":"Drive","title":"Tee off","ask":"Swing","hint":"h","tips":[]}"#)
        center.introDone()
        center.receive(#"{"kind":"station","sport":"golf","index":2,"count":4,"key":"putt","name":"Putt","title":"Putting is sensitive","ask":"Rock","hint":"h","explain":{"title":"Putting is sensitive","body":"The putter moves only a few inches."},"tips":[]}"#)
        XCTAssertTrue(center.station.explains); XCTAssertTrue(center.explaining, "the putting station opens on its card")
        XCTAssertEqual(center.station.explainBody, "The putter moves only a few inches.")
        center.receive(#"{"kind":"attempt","result":"miss","grade":"PUTT","text":"Softer","misses":1,"read":[]}"#)
        XCTAssertFalse(center.explaining, "the first stroke puts the card away")
        OnboardingFlow.shared.store.setLessonStation(.golf, 0)
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
        f.next(); f.keepLook(); f.menuScreenChanged("home"); f.menuScreenChanged("sport")
        XCTAssertEqual(f.step, .done, "every lesson done: the Tutorial has nothing to run"); XCTAssertNil(f.nextLesson)
    }
}
