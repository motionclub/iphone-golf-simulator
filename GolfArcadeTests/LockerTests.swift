import XCTest
import SceneKit
@testable import GolfArcade

/// The locker's data model (Standard-only catalog, loadout saves), its focus grid and its Revert, and the roster safety net.
@MainActor
final class LockerTests: XCTestCase {
    private var savedPlayers: [Player] = []
    private var savedIndex = 0

    override func setUp() {
        let s = SportsSession.shared
        savedPlayers = s.players; savedIndex = s.playerIndex
        s.players = [Player(name: "Tester", colorIndex: 0)]; s.playerIndex = 0
    }
    override func tearDown() {
        let s = SportsSession.shared
        s.players = savedPlayers; s.playerIndex = savedIndex
        TennisMenu.shared.debugShow(.title)
    }

    // MARK: catalog and saves

    func testEachSportShipsItsOwnDefaultItems() {
        for sport in LockerCatalog.sports {
            for slot in LockerCatalog.slots(for: sport) {
                let items = LockerCatalog.items(sport: sport, slot: slot)
                XCTAssertEqual(items.count, 1, "\(sport) \(slot): the shelf holds its existing starter item")
                XCTAssertEqual(items[0].id, LockerCatalog.defaultID(sport: sport, slot: slot))
            }
        }
        XCTAssertEqual(LockerCatalog.slots(for: .tennis), [.skin, .racket, .shoes])
        XCTAssertEqual(LockerCatalog.slots(for: .golf), [.skin, .club, .shoes])
        XCTAssertEqual(LockerCatalog.slots(for: .bowling), [.skin, .shoes])
        XCTAssertEqual(Player(name: "B", colorIndex: 0).loadoutPayload(sport: .bowling), ["skin": "bowling-camp-kit", "shoes": "bowling-saddle"])
        XCTAssertNil(Player(name: "B", colorIndex: 0).multiplayerLoadout.gear["bowling"], "older peers reject unknown sports; bowling's colours travel without gear ids")
        XCTAssertTrue(Player(name: "B", colorIndex: 0).multiplayerLoadout.valid())
    }

    func testLoadoutSurvivesSavingAndOldProfilesStillDecode() throws {
        var p = Player(name: "Old", colorIndex: 0)
        XCTAssertNil(p.loadout)
        let old = try JSONEncoder().encode(p)
        XCTAssertFalse(String(decoding: old, as: UTF8.self).contains("loadout"), "an untouched player writes no loadout key")
        // A profile saved before the field existed decodes with nil.
        let decoded = try JSONDecoder().decode(Player.self, from: old)
        XCTAssertNil(decoded.loadout)
        // Equipping Standard keeps the save clean; a real id would be stored per sport and slot.
        p.equip(LockerCatalog.item(id: nil, sport: .tennis, slot: .racket), sport: .tennis)
        XCTAssertNil(p.loadout)
        let ghost = LockerItem(id: "future-racket", slot: .racket, name: "Future", sports: [.tennis], tintable: true)
        p.equip(ghost, sport: .tennis)
        XCTAssertEqual(p.loadout?["tennis"]?["racket"], "future-racket")
        let again = try JSONDecoder().decode(Player.self, from: JSONEncoder().encode(p))
        XCTAssertEqual(again.loadout, p.loadout)
        // The game never sees an id the catalog does not have: it falls back to Standard.
        XCTAssertTrue(again.equipped(.racket, sport: .tennis).isStandard)
        XCTAssertEqual(again.loadoutPayload(sport: .tennis), ["skin": "standard", "racket": "standard", "shoes": "standard"])
        XCTAssertEqual(again.loadoutPayload(sport: .golf), ["skin": "golf-classic-kit", "club": "standard", "shoes": "golf-spikeless"])
    }

    func testLegacyGolfDefaultsAndPerSportSelectionsSurviveRoundTrip() throws {
        var p = Player(name: "Golfer", colorIndex: 0)
        p.loadout = ["golf": ["skin": "standard", "shoes": "standard"], "tennis": ["racket": "future-racket"]]
        let saved = try JSONDecoder().decode(Player.self, from: JSONEncoder().encode(p))
        XCTAssertEqual(saved.equipped(.skin, sport: .golf).id, "golf-classic-kit")
        XCTAssertEqual(saved.equipped(.shoes, sport: .golf).id, "golf-spikeless")
        XCTAssertEqual(saved.equipped(.skin, sport: .tennis).id, "standard")
        XCTAssertEqual(saved.loadout, p.loadout, "resolving defaults preserves the saved per-sport dictionary")
        for id in [nil, "standard", "removed-kit"] as [String?] {
            XCTAssertEqual(LockerCatalog.item(id: id, sport: .golf, slot: .skin).id, "golf-classic-kit")
        }
        p.equip(LockerCatalog.item(id: nil, sport: .golf, slot: .skin), sport: .golf)
        XCTAssertEqual(p.loadout?["tennis"]?["racket"], "future-racket")
    }

    func testAnUnreadableRosterIsKeptNotOverwritten() throws {
        let suite = UserDefaults(suiteName: "LockerTests.roster")!
        suite.removePersistentDomain(forName: "LockerTests.roster")
        defer { suite.removePersistentDomain(forName: "LockerTests.roster") }
        let garbage = Data("{ not a roster".utf8)
        suite.set(garbage, forKey: "players.v1")
        let loaded = PlayerRosterStore.load(defaults: suite)
        XCTAssertEqual(loaded.count, 1, "a fresh default player is returned")
        let backups = suite.dictionaryRepresentation().filter { $0.key.hasPrefix(PlayerRosterStore.unreadablePrefix) }
        XCTAssertEqual(backups.count, 1)
        XCTAssertEqual(backups.first?.value as? Data, garbage, "the old bytes are preserved")
        PlayerRosterStore.save(loaded, defaults: suite)   // the next save overwrites players.v1 but not the backup
        XCTAssertEqual(suite.dictionaryRepresentation().filter { $0.key.hasPrefix(PlayerRosterStore.unreadablePrefix) }.count, 1)
    }

    // MARK: focus grid

    func testLockerOpensOnTheShelfAndTheGridFollowsTheTab() {
        let menu = TennisMenu.shared
        menu.debugShow(.character)
        XCTAssertEqual(menu.lockerTab, .gear)
        XCTAssertEqual(menu.focused, "lk-item-standard", "opens on the shelf, on the item you wear")
        let gear = menu.rows(.character)
        XCTAssertEqual(gear[0], ["lk-sport-tennis", "lk-sport-golf", "lk-sport-bowling"])
        XCTAssertEqual(gear[1], ["lk-tab-gear", "lk-tab-customize", "lk-tab-emotes"])
        XCTAssertEqual(gear[2], ["lk-slot-skin", "lk-slot-racket", "lk-slot-shoes"])
        XCTAssertEqual(gear[3], ["lk-item-standard"])
        XCTAssertFalse(gear.contains(["lk-colour"]), "the Standard skin has no colour row: colours live in Customize")
        menu.tap("lk-slot-racket")
        XCTAssertTrue(menu.rows(.character).contains(["lk-colour"]), "a racket has a colour row")
        menu.tap("lk-tab-customize")
        let customize = menu.rows(.character)
        XCTAssertEqual(customize[0], ["lk-sport-tennis", "lk-sport-golf", "lk-sport-bowling"], "Customize switches sports too")
        XCTAssertEqual(customize.dropFirst(2).prefix(7).map { $0 }, [["lk-body"], ["lk-hand"], ["lk-back"], ["lk-skin"], ["lk-shirt"], ["lk-shorts"], ["lk-shoes"]])
    }

    /// MENU HERO: the Customize tab's "Back" row flips racket / golf bag, the pick is part of the saved player, and a profile saved before it existed carries the bag.
    func testBackPickTogglesAndIsSaved() throws {
        let menu = TennisMenu.shared
        menu.debugShow(.character)
        menu.tap("lk-tab-customize")
        let before = menu.player?.backCarry ?? .bag
        menu.tap("lk-back")
        XCTAssertNotEqual(menu.player?.backCarry, before)
        menu.tap("lk-back")
        XCTAssertEqual(menu.player?.backCarry, before)
        var p = Player(name: "P", colorIndex: 0); XCTAssertEqual(p.backCarry, .bag)
        p.backCarry = .racket
        let decoded = try JSONDecoder().decode(Player.self, from: JSONEncoder().encode(p))
        XCTAssertEqual(decoded.backCarry, .racket)
        XCTAssertEqual(BackCarry.racket.accessoryID, "racket_back"); XCTAssertEqual(BackCarry.bag.accessoryID, "golf_bag")
    }

    func testSportToggleSwapsRacketForClubAndBack() {
        let menu = TennisMenu.shared
        menu.debugShow(.character)
        menu.tap("lk-slot-racket"); XCTAssertEqual(menu.lockerSlot, .racket)
        menu.tap("lk-sport-golf"); XCTAssertEqual(menu.lockerSport, .golf)
        XCTAssertEqual(menu.lockerSlot, .club, "the racket slot becomes the club slot for golf")
        XCTAssertEqual(menu.rows(.character)[2], ["lk-slot-skin", "lk-slot-club", "lk-slot-shoes"])
        menu.tap("lk-sport-tennis"); XCTAssertEqual(menu.lockerSlot, .racket)
    }

    func testBowlingPreviewWearsTheBowlingKit() throws {
        for female in [false, true] {
            var p = Player(name: "B", colorIndex: 0); p.standardFemale = female
            XCTAssertNotNil(MatchHeroData.asset(female: female, bowling: true), "BowlingKitHero export is in the app")
            let hero = try XCTUnwrap(MatchHero.build(p, sport: .bowling))
            XCTAssertTrue(try XCTUnwrap(hero.childNode(withName: MatchHero.racketName, recursively: false)).isHidden, "no racket in the alley")
            p.setOutfitHex("shirt", "1E2A6E")
            let c = CharacterModelPreview.Coordinator(cameraDistance: 2.7)
            c.update(p, sport: .bowling)
            let view = SCNView(frame: CGRect(x: 0, y: 0, width: 400, height: 700)); view.scene = c.scene; view.pointOfView = c.camera
            if let dir = ProcessInfo.processInfo.environment["MENU_SNAP_DIR"] {
                try view.snapshot().pngData()?.write(to: URL(fileURLWithPath: dir).appendingPathComponent("bowling_\(female ? "female" : "male").png"))
            }
        }
    }

    func testBowlingKitInTheLocker() {
        let menu = TennisMenu.shared
        menu.debugShow(.character)
        menu.tap("lk-slot-racket")
        menu.tap("lk-sport-bowling"); XCTAssertEqual(menu.lockerSport, .bowling)
        XCTAssertEqual(menu.lockerSlot, .skin, "bowling has no racket slot")
        XCTAssertEqual(menu.rows(.character)[2], ["lk-slot-skin", "lk-slot-shoes"])
        XCTAssertEqual(menu.rows(.character)[3], ["lk-item-bowling-camp-kit"])
        XCTAssertTrue(menu.rows(.character).contains(["lk-colour"]), "the bowling shirt takes a colour")
        menu.tap("lk-slot-shoes"); XCTAssertEqual(menu.lockerShelf.map(\.id), ["bowling-saddle"])
        XCTAssertEqual(menu.lockerBottomName, "Pants")
        menu.tap("lk-tab-customize"); XCTAssertEqual(menu.lockerSport, .bowling, "the sport stays picked on Customize")
        menu.tap("lk-shoes"); XCTAssertEqual(menu.lockerRange, "accent", "shoe colour opens its own range")
        menu.tap("lk-range-close"); menu.tap("lk-tab-gear"); menu.tap("lk-sport-tennis"); menu.tap("lk-slot-skin")   // the menu is shared between tests
    }

    func testClickingAlongSwatchesChangesColourAndRevertRestores() throws {
        let menu = TennisMenu.shared, session = SportsSession.shared
        menu.debugShow(.character)
        let opening = session.players[0]
        XCTAssertFalse(menu.lockerDirty)
        menu.tap("lk-tab-customize"); XCTAssertTrue(menu.focus("lk-shirt"))
        XCTAssertEqual(menu.lockerSwatchIndex("shirt"), -1, "starts on the kit colour")
        menu.move(.right)
        XCTAssertEqual(menu.lockerSwatchIndex("shirt"), 0, "one click right = the first swatch")
        XCTAssertEqual(session.players[0].outfitHex("shirt"), "F2F2F0", "a swatch is stored as its exact colour, so White is really white")
        menu.move(.right)
        XCTAssertEqual(menu.lockerSwatchIndex("shirt"), 1)
        menu.move(.left); menu.move(.left)
        XCTAssertEqual(menu.lockerSwatchIndex("shirt"), -1, "wraps back to the kit colour")
        menu.move(.right)
        XCTAssertTrue(menu.lockerDirty)
        XCTAssertTrue(menu.rows(.character).last?.contains("lk-revert") == true, "Revert appears once something changed")
        menu.tap("lk-revert")
        XCTAssertEqual(session.players[0], opening)
        XCTAssertFalse(menu.lockerDirty)
    }

    func testCustomRangeOpensClosesAndBackLeavesItBeforeTheLocker() {
        let menu = TennisMenu.shared
        menu.debugShow(.character)
        menu.tap("lk-tab-customize"); menu.tap("lk-shirt")
        XCTAssertEqual(menu.lockerRange, "shirt")
        XCTAssertEqual(menu.rows(.character), [["lk-range-hue"], ["lk-range-shade"], ["lk-range-close"]])
        let before = SportsSession.shared.players[0].hueShade("shirt").0
        menu.move(.right)
        XCTAssertNotEqual(SportsSession.shared.players[0].hueShade("shirt").0, before, "right on Hue moves the hue")
        menu.back()
        XCTAssertNil(menu.lockerRange)
        XCTAssertEqual(menu.screen, .character, "Back closes the range first, then the locker")
        XCTAssertEqual(menu.focused, "lk-shirt", "focus returns to the row that opened it")
        menu.back(); XCTAssertEqual(menu.screen, .main)
    }

    func testShuffleChangesColoursButNeverGear() {
        let menu = TennisMenu.shared, session = SportsSession.shared
        menu.debugShow(.character)
        menu.tap("lk-shuffle")
        XCTAssertTrue(menu.lockerDirty)
        XCTAssertNil(session.players[0].loadout, "shuffle never touches equipped gear")
    }

    func testHomePlayInviteEmotesAndFeedbackHaveFocusTargets() {
        let menu = TennisMenu.shared
        menu.debugShow(.main)
        XCTAssertEqual(menu.rows(.main).first, ["play", "homeInvite"])
        XCTAssertEqual(menu.rows(.main).flatMap { $0 }, ["play", "homeInvite", "character", "homeEmotes", "settings", "betaFeedback"])
    }
    func testThreeEmoteSlotsPersistAndOldProfilesGetDefaults() throws {
        var p = Player(name: "Emoter", colorIndex: 0)
        let old = try JSONDecoder().decode(Player.self, from: JSONEncoder().encode(p))
        XCTAssertNil(old.emoteIDs)
        XCTAssertEqual(old.equippedEmotes, ["wave", "scuba", "spike"])
        p.equipEmote("pushups", slot: 0)
        p.equipEmote("bringIt", slot: 1)
        p.equipEmote("thrust", slot: 2)
        let saved = try JSONDecoder().decode(Player.self, from: JSONEncoder().encode(p))
        XCTAssertEqual(saved.equippedEmotes, ["pushups", "bringIt", "thrust"])
        XCTAssertEqual(saved.multiplayerLoadout.emotes, saved.equippedEmotes)
        XCTAssertTrue(saved.multiplayerLoadout.valid())
        let peer = MultiplayerParticipant(id: p.id.uuidString, name: p.name, loadout: p.multiplayerLoadout)
        XCTAssertEqual(peer.lobbyPlayer.equippedEmotes, p.equippedEmotes)
    }

    func testEquippedEmotesSwapWithoutDuplicatesAndRejectInvalidChoices() {
        var p = Player(name: "Emoter", colorIndex: 0)
        p.equipEmote("spike", slot: 0)
        XCTAssertEqual(p.equippedEmotes, ["spike", "scuba", "wave"])
        let before = p
        p.equipEmote("deleted", slot: 0); p.equipEmote("wave", slot: 3)
        XCTAssertEqual(p, before)
        p.emoteIDs = ["deleted", "spike", "spike", "thrust", "pushups", "scuba"]
        XCTAssertEqual(p.equippedEmotes, ["spike", "thrust", "pushups"])
        var loadout = p.multiplayerLoadout
        loadout.emotes = ["wave", "wave", "spike"]
        XCTAssertFalse(loadout.valid())
        loadout.emotes = nil
        XCTAssertTrue(loadout.valid(), "older peer profiles stay compatible")
    }

    func testLockerEmoteTabSupportsRemoteSlotsAndRevert() {
        let menu = TennisMenu.shared, session = SportsSession.shared
        menu.debugShow(.character)
        let original = session.players[0]
        menu.tap("lk-tab-emotes")
        XCTAssertEqual(menu.lockerTab, .emotes)
        XCTAssertEqual(menu.rows(.character)[1], ["lk-emote-slot-0", "lk-emote-slot-1", "lk-emote-slot-2"])
        XCTAssertTrue(menu.focus("lk-emote-slot-1"))
        menu.select(); XCTAssertEqual(menu.lockerEmoteSlot, 1)
        menu.tap("lk-emote-pushups")
        XCTAssertEqual(session.players[0].equippedEmotes, ["wave", "pushups", "spike"])
        XCTAssertTrue(menu.lockerDirty)
        menu.tap("lk-revert")
        XCTAssertEqual(session.players[0], original)
        XCTAssertFalse(menu.lockerDirty)
    }

}
