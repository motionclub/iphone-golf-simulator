import XCTest
@testable import GolfArcade

/// The TV locker (LockerTV): Top / Bottom / Shoes / Accessories (clothes, per sport), Body and Emotes, every pick drawn the same way,
/// and each pick applied to the player on the phone.
@MainActor final class LockerTVTests: XCTestCase {
    private func withPlayer(_ body: () -> Void) {
        let s = SportsSession.shared, saved = (s.players, s.playerIndex)
        if s.players.isEmpty { s.players = [Player(name: "Tester", colorIndex: 0)] }
        s.playerIndex = min(s.playerIndex, s.players.count - 1)
        defer { s.players = saved.0; s.playerIndex = saved.1 }
        body()
    }

    func testSectionsAreTopBottomShoesAccessoriesThenBodyAndEmotes() {
        XCTAssertEqual(LockerTV.sections.map(\.id), ["top", "bottom", "shoes", "accessories", "body", "emotes"])
        XCTAssertEqual(LockerTV.sports.map(\.id), ["tennis", "golf", "bowling"])
    }

    func testClothesBlocksAreColourSwatchesPerSport() {
        withPlayer {
            let top = LockerTV.state(sport: "tennis", section: "top")!
            XCTAssertEqual(top.blocks.map(\.key), ["colour:shirt"]); XCTAssertEqual(top.blocks[0].kind, "colour")
            XCTAssertEqual(top.blocks[0].choices.count, 1 + Outfit.palette.count, "the kit's own colour, then the palette")
            XCTAssertEqual(top.blocks[0].choices.filter(\.on).count, 1, "one pick lit")
            XCTAssertEqual(LockerTV.state(sport: "tennis", section: "bottom")!.blocks[0].label, "SHORTS COLOUR")
            XCTAssertEqual(LockerTV.state(sport: "golf", section: "bottom")!.blocks[0].label, "PANTS COLOUR", "shorts and pants are one Bottom")
            XCTAssertEqual(LockerTV.state(sport: "bowling", section: "shoes")!.blocks.map(\.key), ["colour:accent"])
            XCTAssertEqual(LockerTV.state(sport: "tennis", section: "accessories")!.blocks.map(\.key), ["colour:racket", "back"])
            XCTAssertEqual(LockerTV.state(sport: "golf", section: "accessories")!.blocks.map(\.label), ["CLUB COLOUR", "ON YOUR BACK"], "clubs live under Accessories now")
            XCTAssertEqual(LockerTV.state(sport: "bowling", section: "accessories")!.blocks.map(\.key), ["back"])
        }
    }

    func testMirrorAndEmotesAreOnTheTVToo() {
        withPlayer {
            let body = LockerTV.state(sport: "tennis", section: "body")!
            XCTAssertEqual(body.blocks.map(\.key), ["skin", "body", "hand"])
            XCTAssertEqual(body.blocks[0].choices.count, LockerColor.skinPresets.count)
            let emotes = LockerTV.state(sport: "tennis", section: "emotes")!
            XCTAssertEqual(emotes.blocks.map(\.key), ["slot", "emote"]); XCTAssertEqual(emotes.blocks[1].choices.count, EmoteCatalog.ids.count)
            XCTAssertNil(LockerTV.state(sport: "squash", section: "top")); XCTAssertNil(LockerTV.state(sport: "tennis", section: "hat"))
            XCTAssertNotNil(LockerTV.json(sport: "golf", section: "emotes"))
        }
    }

    func testPicksAreSavedToThePlayer() {
        withPlayer {
            let s = SportsSession.shared
            LockerTV.set("colour:shirt", "FF6B4A"); XCTAssertEqual(s.players[s.playerIndex].outfitHex("shirt"), "FF6B4A")
            XCTAssertTrue(LockerTV.state(sport: "tennis", section: "top")!.blocks[0].choices.first { $0.id == "FF6B4A" }!.on)
            LockerTV.set("colour:shirt", "kit"); XCTAssertNil(s.players[s.playerIndex].look["shirt"])
            LockerTV.set("colour:shirt", "nonsense"); XCTAssertNil(s.players[s.playerIndex].look["shirt"], "a bad value changes nothing")
            LockerTV.set("body", "girl"); XCTAssertTrue(s.players[s.playerIndex].standardFemale)
            LockerTV.set("hand", "left"); XCTAssertEqual(s.players[s.playerIndex].handedness, .left)
            LockerTV.set("back", "bag"); XCTAssertEqual(s.players[s.playerIndex].backCarry, .bag)
            LockerTV.set("skin", "3"); XCTAssertEqual(LockerTV.state(sport: "tennis", section: "body")!.blocks[0].choices.first { $0.on }?.id, "3")
            LockerTV.set("slot", "2"); LockerTV.set("emote", "victory"); XCTAssertEqual(s.players[s.playerIndex].equippedEmotes[2], "victory")
            LockerTV.emoteSlot = 0
        }
    }
}
