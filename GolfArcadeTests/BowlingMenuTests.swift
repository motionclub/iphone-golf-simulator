import XCTest
@testable import GolfArcade

/// Bowling in the menus (the pointer menu's rows route through HubSession): its venues, the game against the computer,
/// pass the phone, and a finished game's XP.
@MainActor final class BowlingMenuTests: XCTestCase {
    func testBowlingIsPlayable() {
        XCTAssertTrue(Sport.bowling.playable)
    }

    func testPlayOpensTheFourVenues() {
        let menu = TennisMenu.shared
        menu.debugShow(.main)
        HubSession.route("bay-bowling-play")?.action?()
        XCTAssertEqual(menu.screen, .map)
        XCTAssertEqual(menu.mapSport, .bowling)
        XCTAssertEqual(menu.mapChoices.map(\.id), ["club", "neon", "tiki", "magma"])
        XCTAssertFalse(menu.bowlingExhibition)
    }

    func testExhibitionPicksTheComputerBowler() {
        let menu = TennisMenu.shared, session = SportsSession.shared
        menu.debugShow(.main)
        HubSession.route("bay-bowling-exhibition")?.action?()
        XCTAssertEqual(menu.screen, .map)
        XCTAssertTrue(menu.bowlingExhibition)
        XCTAssertTrue(menu.rows(.map).contains(["bowl-cpu"]), "the venue screen offers the opponent")
        let before = session.bowlingOpponent
        menu.tap("bowl-cpu")
        XCTAssertNotEqual(session.bowlingOpponent, before, "a tap moves to the next opponent")
        XCTAssertTrue(session.bowlingOpponent.launchName.hasPrefix("cpu:"))
    }

    func testPassThePhoneAsksHowManyThenTheVenue() {
        let menu = TennisMenu.shared
        menu.debugShow(.main)
        HubSession.route("bay-bowling-pass")?.action?()
        XCTAssertEqual(menu.screen, .localPlayers)
        menu.tap("localPlayers3")
        XCTAssertEqual(menu.screen, .map)
        XCTAssertEqual(menu.mapSport, .bowling)
        XCTAssertEqual(menu.bowlerNames(3).count, 3)
    }

    func testAFinishedGameIsCountedAndPaid() {
        let stats = BowlingGameStats(line: "score=212;strikes=7;spares=2;opens=1;gutters=0;splits=1;streak=4;players=2;rank=1;venue=neon")
        XCTAssertEqual(stats.score, 212); XCTAssertEqual(stats.strikes, 7); XCTAssertEqual(stats.streak, 4)
        XCTAssertTrue(stats.won); XCTAssertEqual(stats.venueTitle, "Neon Nights")
        let lines = Progression.bowlingBreakdown(stats).map(\.title)
        XCTAssertTrue(lines.contains("200 club")); XCTAssertTrue(lines.contains("Hambone")); XCTAssertTrue(lines.contains("Top of the sheet"))
        XCTAssertTrue(lines.contains("Splits picked up")); XCTAssertFalse(lines.contains("Clean game"))
        XCTAssertFalse(BowlingGameStats(line: "score=120;players=1;rank=1").won, "a solo game under 150 is not a win")
    }
}
