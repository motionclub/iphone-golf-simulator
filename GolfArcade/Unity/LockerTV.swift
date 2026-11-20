import Foundation

/// The TV menu's locker (Adnan 11-19: "clubs, mirror and emotes should not be phone only … all locker stuff should look the same, use the
/// same UI as when you select a shirt colour … top, bottom, shoes, accessories … sport subsections"). Unity's MenuHud draws every locker
/// pick the same way, as a block of swatches or word tiles, from the description here (`state`); each pick comes back as one
/// "key|value" (`set`) and the phone saves it to the player, which sends the look on to the plaza hero (SportsSession.savePlayers ->
/// HubSession.lookChanged). Nothing about the locker opens on the phone any more.
@MainActor
enum LockerTV {
    static let sports: [(id: String, label: String)] = [("tennis", "TENNIS"), ("golf", "GOLF"), ("bowling", "BOWLING")]
    /// Top, Bottom, Shoes and Accessories are the clothes (colours per sport); Body is the mirror (skin, player, hand); Emotes the three picks.
    static let sections: [(id: String, label: String)] = [("top", "TOP"), ("bottom", "BOTTOM"), ("shoes", "SHOES"), ("accessories", "ACCESSORIES"), ("body", "BODY"), ("emotes", "EMOTES")]
    /// The emote slot being filled (the TV's EMOTES section).
    static var emoteSlot = 0

    struct Choice: Encodable { let id, label, hex: String; let on: Bool }
    struct Block: Encodable { let key, label, kind: String; let choices: [Choice] }
    struct Item: Encodable { let id, label: String }
    struct State: Encodable { let sport, section, title: String; let sports: [Item]; let sections: [Item]; let blocks: [Block] }

    private static var player: Player? {
        let s = SportsSession.shared
        return s.players.indices.contains(s.playerIndex) ? s.players[s.playerIndex] : nil
    }

    /// The colour block for an outfit slot: the kit's own colour first, then the palette; the current pick lit.
    private static func colours(_ slot: String, _ label: String, _ p: Player) -> Block {
        let current = p.outfitHex(slot)?.uppercased()   // nil: the kit's own colour
        var choices = [Choice(id: "kit", label: "Kit", hex: "", on: current == nil)]
        choices += Outfit.palette.map { Choice(id: $0.hex, label: $0.name, hex: $0.hex, on: $0.hex.uppercased() == current) }
        return Block(key: "colour:\(slot)", label: label, kind: "colour", choices: choices)
    }
    private static func words(_ key: String, _ label: String, _ options: [(id: String, label: String)], on: String) -> Block {
        Block(key: key, label: label, kind: "text", choices: options.map { Choice(id: $0.id, label: $0.label, hex: "", on: $0.id == on) })
    }

    static func state(sport: String, section: String) -> State? {
        guard sports.contains(where: { $0.id == sport }), sections.contains(where: { $0.id == section }), let p = player else { return nil }
        let bottom = sport == "tennis" ? "SHORTS" : "PANTS"
        var title = "", blocks: [Block] = []
        switch section {
        case "top":
            title = "Top"; blocks = [colours("shirt", sport == "tennis" ? "POLO COLOUR" : "SHIRT COLOUR", p)]
        case "bottom":
            title = "Bottom"; blocks = [colours("shorts", "\(bottom) COLOUR", p)]
        case "shoes":
            title = "Shoes"; blocks = [colours("accent", "SHOE COLOUR", p)]
        case "accessories":
            title = "Accessories"
            if sport == "tennis" { blocks.append(colours("racket", "RACKET COLOUR", p)) }
            if sport == "golf" { blocks.append(colours("racket", "CLUB COLOUR", p)) }
            blocks.append(words("back", "ON YOUR BACK", [("racket", "Racket"), ("bag", "Golf bag")], on: p.backCarry == .racket ? "racket" : "bag"))
        case "body":
            title = "Body"
            let nearest = LockerColor.skinPresets.indices.min { abs(LockerColor.skinPresets[$0] - p.skinT) < abs(LockerColor.skinPresets[$1] - p.skinT) } ?? 0
            blocks = [Block(key: "skin", label: "SKIN TONE", kind: "colour", choices: LockerColor.skinPresets.enumerated().map { i, t in
                          let hex = LockerColor.ramp(LockerColor.skinStops, t); return Choice(id: String(i), label: "Tone \(i + 1)", hex: hex, on: i == nearest) }),
                      words("body", "PLAYER", [("boy", "Boy"), ("girl", "Girl")], on: p.standardFemale ? "girl" : "boy"),
                      words("hand", "PLAYS", [("right", "Right"), ("left", "Left")], on: p.handedness == .left ? "left" : "right")]
        default:
            title = "Emotes"
            let picks = p.equippedEmotes, slot = min(max(0, emoteSlot), 2)
            blocks = [words("slot", "EMOTE SLOT", (0..<3).map { (String($0), "Slot \($0 + 1)") }, on: String(slot)),
                      words("emote", "PICK AN EMOTE", EmoteCatalog.ids.indices.map { (EmoteCatalog.ids[$0], EmoteCatalog.names[$0]) }, on: picks[slot])]
        }
        return State(sport: sport, section: section, title: title, sports: sports.map { Item(id: $0.id, label: $0.label) },
                     sections: sections.map { Item(id: $0.id, label: $0.label) }, blocks: blocks)
    }

    static func json(sport: String, section: String) -> String? {
        guard let s = state(sport: sport, section: section), let data = try? JSONEncoder().encode(s) else { return nil }
        return String(data: data, encoding: .utf8)
    }

    /// One pick from the TV ("colour:shirt|F2F2F0", "skin|3", "body|girl", "emote|wave" ...). Saved at once (the plaza hero follows).
    static func set(_ key: String, _ value: String) {
        let s = SportsSession.shared
        guard s.players.indices.contains(s.playerIndex) else { return }
        var p = s.players[s.playerIndex]
        switch key {
        case let k where k.hasPrefix("colour:"):
            let slot = String(k.dropFirst(7))
            guard Player.outfitSlots.contains(slot) else { return }
            if value == "kit" { p.clearOutfit(slot) } else if value.count == 6, UInt64(value, radix: 16) != nil { p.setOutfitHex(slot, value) } else { return }
        case "skin":
            guard let i = Int(value), LockerColor.skinPresets.indices.contains(i) else { return }
            p.setSkin(LockerColor.skinPresets[i])
        case "body": p.standardFemale = value == "girl"
        case "hand": p.handedness = value == "left" ? .left : .right
        case "back": p.backCarry = value == "bag" ? .bag : .racket
        case "slot": emoteSlot = min(max(0, Int(value) ?? 0), 2); return
        case "emote": p.equipEmote(value, slot: min(max(0, emoteSlot), 2))
        default: return
        }
        s.players[s.playerIndex] = p
        s.savePlayers()
    }
}
