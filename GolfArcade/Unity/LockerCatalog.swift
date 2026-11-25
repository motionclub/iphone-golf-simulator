import SwiftUI

/// What a player can equip, per sport. Gear is data: the locker shelf draws `LockerCatalog.items(...)` and a `Player`
/// stores stable item ids (`Player.loadout`). Party skins add original equipment silhouettes and surface finishes —
/// the shelf, the slots and the save format exist, but no gear ships yet. Adding gear later means adding rows here
/// (and the matching asset on the Unity side); no screen or save format changes.
enum LockerSlot: String, CaseIterable, Identifiable, Codable, Sendable {
    /// A whole-character costume (the kit). Not the skin tone — that is a colour on the Customize tab.
    case skin
    case racket, club, ball, accessory
    case shoes
    var id: String { rawValue }
    func title(for sport: Sport) -> String {
        switch self {
        case .skin: "Skin"
        case .racket: "Racket"
        case .club: "Club"
        case .ball: "Ball"
        case .accessory: "Extras"
        case .shoes: "Shoes"
        }
    }
    var icon: String {
        switch self {
        case .skin: "tshirt.fill"
        case .racket: "tennis.racket"
        case .club: "figure.golf"
        case .ball: "circle.hexagongrid.fill"
        case .accessory: "baseballcap.fill"
        case .shoes: "shoeprints.fill"
        }
    }
    /// The continuous-colour key (`Player.look`) an equipped item of this slot is tinted with; nil = colours are edited elsewhere.
    var colourSlot: String? {
        switch self {
        case .skin: "shirt"
        case .racket, .club: "racket"
        case .shoes: "accent"
        case .ball, .accessory: nil
        }
    }
}

struct LockerItem: Identifiable, Equatable, Sendable {
    let id: String
    let slot: LockerSlot
    let name: String
    /// Sports that can equip it.
    let sports: Set<Sport>
    /// Whether the locker offers a colour row for it.
    let tintable: Bool
    var isStandard: Bool { id == LockerCatalog.standardID }
}

enum LockerCatalog {
    static let standardID = "standard"
    static let golfKitID = "golf-classic-kit"
    static let golfShoesID = "golf-spikeless"
    static let bowlingKitID = "bowling-camp-kit"
    static let bowlingShoesID = "bowling-saddle"
    static func defaultID(sport: Sport, slot: LockerSlot) -> String {
        switch (sport, slot) {
        case (.golf, .skin): return golfKitID
        case (.golf, .shoes): return golfShoesID
        case (.bowling, .skin): return bowlingKitID
        case (.bowling, .shoes): return bowlingShoesID
        default: return standardID
        }
    }
    /// Sports with a locker (and a gear shelf).
    static let sports: [Sport] = [.tennis, .golf, .bowling]

    /// Slots a sport shows, in shelf order. Bowling has no held gear (the house ball).
    static func slots(for sport: Sport) -> [LockerSlot] {
        switch sport {
        case .golf: [.skin, .club, .ball, .accessory, .shoes]
        case .bowling: [.skin, .shoes]
        default: [.skin, .racket, .accessory, .shoes]
        }
    }

    /// Free original party cosmetics; existing defaults and saved IDs retain their meaning.
    static let all: [LockerItem] = [
        LockerItem(id: standardID, slot: .ball, name: "Classic", sports: [.golf], tintable: false),
        LockerItem(id: standardID, slot: .accessory, name: "Classic", sports: [.tennis, .golf], tintable: false),
        LockerItem(id: "party.hockey", slot: .club, name: "Icebreaker", sports: [.golf], tintable: false),
        LockerItem(id: "party.slugger", slot: .club, name: "Home Run", sports: [.golf], tintable: false),
        LockerItem(id: "party.balloon", slot: .club, name: "Pop Hound", sports: [.golf], tintable: false),
        LockerItem(id: "party.candy", slot: .club, name: "Sugar Rush", sports: [.golf], tintable: false),
        LockerItem(id: "ball.orbit", slot: .ball, name: "Orbit", sports: [.golf], tintable: false),
        LockerItem(id: "ball.melon", slot: .ball, name: "Watermelon", sports: [.golf], tintable: false),
        LockerItem(id: "ball.checker", slot: .ball, name: "Race Day", sports: [.golf], tintable: false),
        LockerItem(id: "ball.sunset", slot: .ball, name: "Sunset", sports: [.golf], tintable: false),
        LockerItem(id: "skin.coastal", slot: .skin, name: "Coastal Club", sports: [.tennis, .golf, .bowling], tintable: false),
        LockerItem(id: "skin.arcade", slot: .skin, name: "Arcade Nights", sports: [.tennis, .golf, .bowling], tintable: false),
        LockerItem(id: "skin.citrus", slot: .skin, name: "Citrus Rally", sports: [.tennis, .golf, .bowling], tintable: false),
        LockerItem(id: "extra.mint", slot: .accessory, name: "Mint Condition", sports: [.tennis, .golf], tintable: false),
        LockerItem(id: "extra.neon", slot: .accessory, name: "Neon League", sports: [.tennis, .golf], tintable: false),
        LockerItem(id: "extra.caramel", slot: .accessory, name: "Caramel Club", sports: [.tennis, .golf], tintable: false),

        LockerItem(id: standardID, slot: .skin, name: "Standard", sports: [.tennis], tintable: false),
        LockerItem(id: golfKitID, slot: .skin, name: "Golf Polo", sports: [.golf], tintable: true),
        LockerItem(id: standardID, slot: .racket, name: "Standard", sports: [.tennis], tintable: true),
        LockerItem(id: standardID, slot: .club, name: "Standard", sports: [.golf], tintable: true),
        LockerItem(id: standardID, slot: .shoes, name: "Standard", sports: [.tennis], tintable: true),
        LockerItem(id: golfShoesID, slot: .shoes, name: "Spikeless", sports: [.golf], tintable: true),
        LockerItem(id: bowlingKitID, slot: .skin, name: "Bowling Shirt", sports: [.bowling], tintable: true),
        LockerItem(id: bowlingShoesID, slot: .shoes, name: "Saddle Shoes", sports: [.bowling], tintable: true),
    ]

    static func items(sport: Sport, slot: LockerSlot) -> [LockerItem] {
        let pool = all.filter { $0.slot == slot && $0.sports.contains(sport) }
        let fallback = defaultID(sport: sport, slot: slot)
        return pool.filter { $0.id == fallback } + pool.filter { $0.id != fallback }
    }

    /// The item for an id, or the slot's Standard item when the catalog no longer has it (saves outlive catalog changes).
    static func item(id: String?, sport: Sport, slot: LockerSlot) -> LockerItem {
        let pool = items(sport: sport, slot: slot)
        let fallback = defaultID(sport: sport, slot: slot)
        let resolved = id == nil || id == standardID ? fallback : id
        return pool.first { $0.id == resolved } ?? pool.first { $0.id == fallback } ?? LockerItem(id: fallback, slot: slot, name: "Standard", sports: [sport], tintable: false)
    }
}

extension Player {
    var multiplayerLoadout: MultiplayerLoadout {
        // gear for tennis and golf only: older builds reject a loadout naming another sport, and bowling has one kit per slot (its colours travel below)
        MultiplayerLoadout(gear: Dictionary(uniqueKeysWithValues: [Sport.tennis, .golf].map { ($0.rawValue, loadoutPayload(sport: $0).filter { !["ball", "accessory"].contains($0.key) }) }),
                           skinHex: skinHex, colours: Dictionary(uniqueKeysWithValues: Player.outfitSlots.compactMap { slot in outfitHex(slot).map { (slot, $0) } }), emotes: equippedEmotes, shirtHex: outfitHex("shirt"), shortsHex: outfitHex("shorts"),
                           hairHex: hairHex, haircut: haircut, shoesHex: outfitHex("accent"), clubSkin: equipped(.club, sport: .golf).id, ballSkin: equipped(.ball, sport: .golf).id, accessorySkin: equipped(.accessory, sport: .golf).id, tennisAccessorySkin: equipped(.accessory, sport: .tennis).id)
    }
    func equipped(_ slot: LockerSlot, sport: Sport) -> LockerItem {
        LockerCatalog.item(id: loadout?[sport.rawValue]?[slot.rawValue], sport: sport, slot: slot)
    }
    mutating func equip(_ item: LockerItem, sport: Sport) {
        var all = loadout ?? [:]
        var forSport = all[sport.rawValue] ?? [:]
        if item.isStandard { forSport[item.slot.rawValue] = nil } else { forSport[item.slot.rawValue] = item.id }
        all[sport.rawValue] = forSport.isEmpty ? nil : forSport
        loadout = all.isEmpty ? nil : all
        if item.slot == .skin {
            let palette: [String]?
            switch item.id {
            case "skin.coastal": palette = ["36BDB0", "183248", "FFF4DC"]
            case "skin.arcade": palette = ["8048D6", "252343", "FF73AA"]
            case "skin.citrus": palette = ["FF8B36", "234C44", "F6F0D8"]
            default: palette = nil
            }
            if let palette { for (slot, hex) in zip(["shirt", "shorts", "accent"], palette) { setOutfitHex(slot, hex) } }
        }
    }
    /// What the launch message carries for a sport: slot -> item id for every slot (Standard included), so the game never guesses.
    func loadoutPayload(sport: Sport) -> [String: String] {
        Dictionary(uniqueKeysWithValues: LockerCatalog.slots(for: sport).map { ($0.rawValue, equipped($0, sport: sport).id) })
    }
}

extension MultiplayerParticipant {
    /// A transient locker profile for the preview; each peer supplies cosmetic values only.
    var lobbyPlayer: Player {
        var p = Player(id:UUID(uuidString:id) ?? UUID(uuidString:"00000000-0000-0000-0000-000000000000")!,name:name,colorIndex:0,handedness:left ? .left : .right)
        p.standardFemale = female
        if let loadout {
            p.emoteIDs = loadout.emotes
            p.loadout = loadout.gear
            if let id = loadout.clubSkin { p.equip(LockerCatalog.item(id: id, sport: .golf, slot: .club), sport: .golf) }
            if let id = loadout.ballSkin { p.equip(LockerCatalog.item(id: id, sport: .golf, slot: .ball), sport: .golf) }
            if let id = loadout.accessorySkin { p.equip(LockerCatalog.item(id: id, sport: .golf, slot: .accessory), sport: .golf) }
            if let id = loadout.tennisAccessorySkin { p.equip(LockerCatalog.item(id: id, sport: .tennis, slot: .accessory), sport: .tennis) }
            let skin = LockerColor.rgb(loadout.skinHex)
            p.look["skin"] = [0,skin.0,skin.1,skin.2]
            for (slot,hex) in loadout.colours { p.setOutfitHex(slot,hex) }
        }
        return p
    }
}
