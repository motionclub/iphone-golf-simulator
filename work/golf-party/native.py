from pathlib import Path
root=Path.cwd()
def edit(file,a,b):
 p=root/file;s=p.read_text();assert a in s,(file,a[:100]);p.write_text(s.replace(a,b,1))
edit('GolfArcade/Multiplayer/MultiplayerModels.swift','    var paused: Bool?','''    var paused: Bool?
    /// Nil for a real device; guests are controlled only by the host that created them.
    var controllerID: String?
    var isGuest: Bool { controllerID != nil }
''')
edit('GolfArcade/Multiplayer/MultiplayerModels.swift','    var emotes: [String]?','''    var emotes: [String]?
    // Flat colour fields are also readable by Unity JsonUtility.
    var shirtHex: String?
    var shortsHex: String?
''')
edit('GolfArcade/Multiplayer/MultiplayerModels.swift','return (emotes.map(EmoteCatalog.valid) ?? true) && hex(skinHex)', 'return (shirtHex.map(hex) ?? true) && (shortsHex.map(hex) ?? true) && (emotes.map(EmoteCatalog.valid) ?? true) && hex(skinHex)')
edit('GolfArcade/Multiplayer/MultiplayerModels.swift','&& participants.allSatisfy { !$0.id.isEmpty', '&& participants.allSatisfy { $0.controllerID == nil || (sport == .golf && $0.controllerID == ownerID && $0.id != ownerID) }\n            && participants.allSatisfy { !$0.id.isEmpty')
edit('GolfArcade/Multiplayer/MultiplayerModels.swift','static let version = 2','static let version = 3')
edit('GolfArcade/Unity/LockerCatalog.swift','emotes: equippedEmotes)','emotes: equippedEmotes, shirtHex: outfitHex("shirt"), shortsHex: outfitHex("shorts"))')
edit('GolfArcade/Multiplayer/LocalMultiplayerTransport.swift','    private var token = ""','''    private var token = ""
    var joinCode: String { Self.joinCode(for: token) }
    static func joinCode(for token: String) -> String {
        String(token.replacingOccurrences(of: "-", with: "").prefix(6)).uppercased()
    }
''')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','    var authenticated: Bool', '''    var localJoinCode: String? { isNearby && isOwner ? local?.joinCode : nil }
    func joinLocal(code: String) throws {
        let clean = code.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        let matches = discoveredLobbies.filter { LocalMultiplayerTransport.joinCode(for: $0.id.components(separatedBy: "~").last ?? "") == clean }
        guard clean.count == 6, matches.count == 1, let item = matches.first else {
            throw MultiplayerError.invalidOperation("Lobby not found. Check the six-character code and use the same Wi-Fi.")
        }
        try joinLocal(item)
    }
    func addLocalGuest() throws {
        try requireOwnerIdle()
        guard isNearby, lobby?.sport == .golf else { throw MultiplayerError.invalidOperation("Shared-phone guests are available in local golf.") }
        let number = (1...4).first { n in !lobby!.participants.contains { $0.name == "Guest \\(n)" } } ?? 4
        let palette = ["F4A65A", "78C5E8", "C997DF", "8AD0AD", "F19DAB", "F5DD7C"]
        let used = Set(lobby!.participants.compactMap { $0.loadout?.colours["shirt"] })
        let shirt = palette.filter { !used.contains($0) }.randomElement() ?? palette[0]
        let shorts = ["23344D", "F0E2CC", "425D4D"].randomElement()!
        let skin = ["F2D0AF", "D5A17C", "A8704E", "754B37"].randomElement()!
        let look = MultiplayerLoadout(skinHex: skin, colours: ["shirt":shirt,"shorts":shorts], emotes: EmoteCatalog.defaults, shirtHex:shirt, shortsHex:shorts)
        try lobby?.add(MultiplayerParticipant(id: UUID().uuidString, name: "Guest \\(number)", ready: true, female: Bool.random(), loadout:look, controllerID:localID))
        publishLobby()
    }
    func removeLocalGuest() throws {
        try requireOwnerIdle()
        guard let index = lobby?.participants.lastIndex(where: { $0.controllerID == localID }) else { return }
        lobby?.participants.remove(at:index); lobby?.revision += 1; publishLobby()
    }
    var authenticated: Bool''')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','lobby?.configure(sport: sport, venue: venue); lobby?.sets', '''if sport != .golf { lobby?.participants.removeAll { $0.isGuest } }
        lobby?.configure(sport: sport, venue: venue)
        for i in lobby!.participants.indices where lobby!.participants[i].isGuest { lobby!.participants[i].ready = true }
        lobby?.sets''')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','where lobby!.participants[i].id != localID {','where lobby!.participants[i].id != localID && !lobby!.participants[i].isGuest {')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','p.id = peer; p.name', 'p.controllerID = nil; p.id = peer; p.name')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','case "ready": if lobby?.phase == .lobby { lobby!.participants[i].ready = p.payload == "true" }','''case "ready": if lobby?.phase == .lobby {
            lobby!.participants[i].ready = p.payload == "true"
            for g in lobby!.participants.indices where lobby!.participants[g].controllerID == p.sender { lobby!.participants[g].ready = p.payload == "true" }
        }''')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','lobby!.participants[i].loaded = true\n', '''lobby!.participants[i].loaded = true
            for g in lobby!.participants.indices where lobby!.participants[g].controllerID == p.sender {
                lobby!.participants[g].loaded = true
                presentationReadyAt[lobby!.participants[g].id] = presentationReadyAt[p.sender]
            }
''')
# Host guests return ready; no disconnected ghosts or fake device load requirement.
edit('GolfArcade/Multiplayer/MultiplayerService.swift','lobby!.participants[i].ready = false; lobby!.participants[i].loaded = false','lobby!.participants[i].ready = lobby!.participants[i].isGuest; lobby!.participants[i].loaded = false')
# Menu actions and focus rows.
edit('GolfArcade/Unity/TennisMenu.swift','    var nearbyPage = 0','    var nearbyPage = 0\n    var joinCode = ""')
edit('GolfArcade/Unity/TennisMenu.swift','case .party: return [["partySolo"], ["partyOnline"], ["partyNearby"], ["back"]]','case .party: return [["partySolo"], ["partyLocalGolf"], ["partyOnline"], ["partyNearby"], ["back"]]')
edit('GolfArcade/Unity/TennisMenu.swift','id == "partyOnline" || id == "partyNearby"','id == "partyOnline" || id == "partyNearby" || id == "partyLocalGolf"')
edit('GolfArcade/Unity/TennisMenu.swift','+ [["net-host"],["back"]]','+ [["net-join-code"],["net-host"],["back"]]')
edit('GolfArcade/Unity/TennisMenu.swift','case .lobby: return [["net-ready"]','case .lobby: return (service.isNearby && service.isOwner && service.lobby?.sport == .golf ? [["net-add-guest","net-remove-guest"]] : []) + [["net-ready"]')
edit('GolfArcade/Unity/TennisMenu.swift','case "partyNearby": identity(menu);', '''case "partyLocalGolf":
                identity(menu); try service.hostLocal(name: menu.player?.name ?? "Friends")
                try service.configure(.golf, venue:"postcards"); try service.addLocalGuest(); menu.showOnline(.lobby)
            case "net-add-guest": try service.addLocalGuest()
            case "net-remove-guest": try service.removeLocalGuest()
            case "net-join-code":
                identity(menu); try service.joinLocal(code:joinCode); searchStarted = Date(); menu.showOnline(.searching)
            case "partyNearby": identity(menu);''')
edit('GolfArcade/Unity/IslandScreens.swift','IslandLobbyRow(title:"Play Online",','IslandLobbyRow(title:"Local Golf",subtitle:"Pass one phone · 2–4 players",icon:"figure.golf",id:"partyLocalGolf",menu:menu,compact:compact)\n                    IslandLobbyRow(title:"Play Online",')
edit('GolfArcade/Unity/IslandScreens.swift','Text("Choose a friend\'s lobby on the same Wi-Fi.")','Text("Join on the same Wi-Fi to bring your saved player and look.")')
edit('GolfArcade/Unity/IslandScreens.swift','if online.nearbyItems.isEmpty {', '''HStack {
                            TextField("6-character code", text: Binding(get: { online.joinCode }, set: { online.joinCode = String($0.uppercased().filter { $0.isASCII && $0.isHexDigit }.prefix(6)) }))
                                .textInputAutocapitalization(.characters).autocorrectionDisabled().textFieldStyle(.roundedBorder)
                                .accessibilityIdentifier("golf-join-code")
                            Button("Join") { menu.tap("net-join-code") }.disabled(online.joinCode.count != 6)
                                .accessibilityIdentifier("net-join-code")
                        }
                        if online.nearbyItems.isEmpty {''')
edit('GolfArcade/Unity/IslandScreens.swift','case .lobby:\n                    action("net-ready"','''case .lobby:
                    if let code = service.localJoinCode {
                        Text("JOIN CODE  \\(code)").islandType(compact ? 19 : 24,bold:true).monospaced().textSelection(.enabled)
                        Text("Friends: Nearby → enter code. Guests: pass this phone.").islandType(compact ? 12 : 15).foregroundStyle(IslandUI.muted)
                    }
                    if service.isNearby && service.isOwner && lobby?.sport == .golf {
                        HStack {
                            action("net-add-guest","Add Guest",icon:"person.badge.plus",enabled:(lobby?.participants.count ?? 4) < 4)
                            action("net-remove-guest","Remove Guest",icon:"person.badge.minus",enabled:lobby?.participants.contains(where: \\.isGuest) == true)
                        }
                    }
                    action("net-ready"''')
print('Native lobby implemented')
