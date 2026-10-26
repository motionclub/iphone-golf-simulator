import XCTest
import UIKit
@testable import GolfArcade

@MainActor final class OnboardingTests: XCTestCase {
    private func fixture() -> (UserDefaults, OnboardingStore, SportProgress) {
        let d = UserDefaults(suiteName: "onboarding-tests-\(UUID())")!
        return (d, OnboardingStore(defaults: d), SportProgress(defaults: d))
    }
    func testFreshInstallStartsAtHelloAndResumesAcrossLaunches() {
        let (_, store, progress) = fixture()
        let flow = OnboardingFlow(store: store, progress: progress, arguments: [])
        XCTAssertEqual(flow.step, .hello); XCTAssertTrue(flow.holdsMenu)
        flow.next(); XCTAssertEqual(flow.step, .controller)
        XCTAssertEqual(OnboardingFlow(store: store, progress: progress, arguments: []).step, .controller, "a started onboarding carries on")
    }
    func testPhonesThatUsedTheAppBeforeSkipIt() {
        let (d, store, progress) = fixture()
        d.set(Date().timeIntervalSince1970 - 86_400, forKey: "ftue.installedAt.v1")
        d.set("account", forKey: "ftue.step.v1")   // an earlier build's onboarding key
        XCTAssertEqual(OnboardingFlow(store: store, progress: progress, arguments: []).step, .done)
    }
    func testAFinishedLessonSkipsOnboarding() {
        for sport in [Sport.tennis, .golf] {
            let (_, store, progress) = fixture(); progress.completeTutorial(sport)
            let flow = OnboardingFlow(store: store, progress: progress, arguments: [])
            XCTAssertEqual(flow.step, .done); XCTAssertFalse(flow.active)
        }
    }
    func testResetOnlyClearsFTUEKeys() {
        let (d, store, progress) = fixture()
        let roster = Data([1, 2, 3]); d.set(roster, forKey: "players.v1")
        progress.completeTutorial(.tennis)
        store.step = .card; store.characterInitialized = true; store.setLessonStation(.golf, 4)
        _ = OnboardingFlow(store: store, progress: progress, arguments: ["-resetOnboarding", "-forceOnboarding"])
        XCTAssertEqual(store.step, .hello); XCTAssertFalse(store.characterInitialized); XCTAssertEqual(store.lessonStation(.golf), 0)
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
        for step in [OnboardingStep.hello, .controller, .room, .player, .card, .choose, .lesson(.golf), .lesson(.tennis), .reward(.golf), .done] {
            XCTAssertEqual(OnboardingStep(key: step.key), step)
        }
        XCTAssertNil(OnboardingStep(key: "account")); XCTAssertNil(OnboardingStep(key: "tutorial:tennis"))
    }
    func testNameIsBounded() {
        XCTAssertEqual(OnboardingStore.name("  \n"), "Player 1")
        XCTAssertEqual(OnboardingStore.name(String(repeating: "a", count: 60)).count, 14)
        XCTAssertEqual(OnboardingStore.name(" Ray \n"), "Ray")
    }
    func testRemoteWalksTheStepsAndBackGoesBack() {
        let (_, store, progress) = fixture()
        store.characterInitialized = true   // (the player step would otherwise shuffle the shared test player)
        let flow = OnboardingFlow(store: store, progress: progress, arguments: [])
        XCTAssertEqual(flow.focused, "go"); flow.select(); XCTAssertEqual(flow.step, .controller)
        XCTAssertEqual(flow.focused, "try"); flow.select(); XCTAssertEqual(flow.step, .controller, "the practice press stays on the step")
        XCTAssertEqual(flow.focused, "next"); flow.select(); XCTAssertEqual(flow.step, .room)
        flow.back(); XCTAssertEqual(flow.step, .controller)
        flow.next(); flow.select()
        XCTAssertEqual(flow.step, .player)
        XCTAssertEqual(flow.rows(), [["male", "female"], ["skin"], ["shirt"], ["name"], ["shuffle", "save"]])
        flow.move(.down); flow.move(.down); flow.move(.down); flow.move(.down); flow.move(.right)
        XCTAssertEqual(flow.focused, "save"); flow.select(); XCTAssertEqual(flow.step, .card)
        flow.select(); XCTAssertEqual(flow.step, .choose)
        XCTAssertEqual(flow.rows(), [["golf", "tennis"], ["skip"]])
    }
    func testSwatchRowsChangeThePlayerSideways() {
        let (_, store, progress) = fixture()
        let session = SportsSession.shared
        guard session.players.indices.contains(session.playerIndex) else { return }
        let saved = session.players[session.playerIndex]
        defer { session.players[session.playerIndex] = saved; session.savePlayers() }
        store.step = .player; store.explicitRun = true; store.characterInitialized = true
        let flow = OnboardingFlow(store: store, progress: progress, arguments: [])
        flow.focus("shirt"); let shirt = flow.shirtIndex
        flow.move(.right); XCTAssertEqual(flow.shirtIndex, (shirt + 1) % OnboardingFlow.shirts.count)
        XCTAssertEqual(flow.focused, "shirt", "sideways on a swatch row changes the colour, not the focus")
        flow.focus("skin"); let skin = flow.skinIndex
        flow.move(.left); XCTAssertEqual(flow.skinIndex, (skin - 1 + LockerColor.skinPresets.count) % LockerColor.skinPresets.count)
        flow.tap("female"); XCTAssertTrue(flow.player?.standardFemale == true)
        flow.setName("  Birdie "); XCTAssertEqual(flow.player?.name, "Birdie")
    }
    func testLessonEventsDriveTheCoachAndResumeStation() {
        let center = LessonCenter.shared
        defer { center.end() }
        center.receive(#"{"kind":"station","sport":"golf","index":2,"count":8,"key":"commit","name":"Commit","title":"Swing through the ball","ask":"Hit two in a row","hint":"Don't stop","tips":["a","b"]}"#)
        XCTAssertEqual(center.sport, .golf); XCTAssertEqual(center.station.index, 2); XCTAssertTrue(center.explaining)
        XCTAssertEqual(OnboardingFlow.shared.store.lessonStation(.golf), 2, "a lesson resumes at the station it reached")
        for n in 1...3 {
            center.receive(#"{"kind":"attempt","result":"miss","grade":"THIN","text":"Slowed down","misses":\#(n),"read":[["COMMIT","62%",0],["BACK","75%",1]]}"#)
        }
        XCTAssertEqual(center.shown, .miss); XCTAssertEqual(center.grade, "THIN"); XCTAssertEqual(center.read.count, 2)
        XCTAssertFalse(center.explaining); XCTAssertTrue(center.hintShown); XCTAssertTrue(center.skipOffered)
        center.receive(#"{"kind":"attempt","result":"pass","grade":"GREAT","text":"Two committed swings","misses":3,"read":[]}"#)
        XCTAssertEqual(center.shown, .pass); XCTAssertFalse(center.skipOffered)
        OnboardingFlow.shared.store.setLessonStation(.golf, 0)
    }
    func testFinishedLessonPaysItsRewardOnceAndShowsIt() {
        let (_, store, progress) = fixture()
        store.step = .choose; store.explicitRun = true
        let flow = OnboardingFlow(store: store, progress: progress, arguments: [])
        store.setLessonStation(.tennis, 5)
        flow.completed(.tennis)
        XCTAssertEqual(flow.step, .reward(.tennis)); XCTAssertTrue(progress.finishedTutorial(.tennis))
        XCTAssertEqual(store.lessonStation(.tennis), 0)
        XCTAssertEqual(flow.rows(), [["play", "other"], ["menu"]], "the golf lesson is offered next")
        flow.tap("menu"); XCTAssertEqual(flow.step, .done); XCTAssertFalse(flow.active)
    }

    func testFirstTutorialFillsLevelTwoAndReplayPaysNothing() {
        let (_, store, _) = fixture(); let player = UUID()
        _ = Progression.shared.award(player: player, stats: MatchStats(), won: false, score: "", opponent: "", practice: false, difficulty: 0)
        let before = Progression.shared.entry(for: player)
        Analytics.clearEvents()
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .tennis, store: store), 200 - before.xp)
        let earned = Progression.shared.entry(for: player)
        XCTAssertEqual(earned.level, 2); XCTAssertEqual(earned.xp, 0)
        XCTAssertTrue(store.requestedHeadband)
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .tennis, store: store), 0)
        XCTAssertEqual(Progression.shared.entry(for: player), earned)
        XCTAssertEqual(Analytics.events.filter { $0.contains("reward_claimed") }.count, 1)
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .golf, store: store), 50)
        XCTAssertEqual(Progression.shared.entry(for: player).xp, 50)
        XCTAssertNil(store.rewardItem(.golf)); XCTAssertEqual(store.rewardItem(.tennis), "white-headband")
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .golf, store: store), 0)
        XCTAssertEqual(LevelRewards.rewards(for: 2).first?.id, "white-headband")
    }

    func testReplayPreservesHeroProgressAndLevel() {
        let (defaults, store, progress) = fixture()
        let hero = Data([9, 8, 7]); defaults.set(hero, forKey: "players.v1")
        progress.completeTutorial(.tennis)
        let flow = OnboardingFlow(store: store, progress: progress, arguments: [])
        let player = UUID(); let level = Progression.shared.entry(for: player)
        flow.replay()
        XCTAssertEqual(flow.step, .hello); XCTAssertTrue(store.characterInitialized)
        XCTAssertEqual(defaults.data(forKey: "players.v1"), hero); XCTAssertTrue(progress.finishedTutorial(.tennis))
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .tennis, store: store), 0)
        XCTAssertEqual(Progression.shared.entry(for: player), level)
        flow.exitToMenu()
    }

    func testInterruptedRewardJournalRecoversWithoutDoubleXP() throws {
        let (_, store, _) = fixture(); let player = UUID()
        let target = Progression.Entry(level: 2, xp: 0, totalXP: 200, matches: 0, wins: 0)
        let key = "ftue.pendingReward.tennis.v1"
        store.defaults.set(200, forKey: key + ".xp"); store.defaults.set("white-headband", forKey: key + ".item")
        store.defaults.set(try JSONEncoder().encode(target), forKey: key)
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .tennis, store: store), 200)
        XCTAssertEqual(Progression.shared.entry(for: player), target)
        XCTAssertEqual(Progression.shared.awardTutorial(player: player, sport: .tennis, store: store), 0)
        XCTAssertEqual(Progression.shared.entry(for: player).totalXP, 200)
    }
}
