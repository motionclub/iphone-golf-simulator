from pathlib import Path
root=Path.cwd()
def edit(file,a,b):
 p=root/file;s=p.read_text();assert a in s,(file,a[:100]);p.write_text(s.replace(a,b,1))
edit('GolfArcade/Unity/TennisMenu.swift','case .multiplayer: return [["partyOnline"], ["partyNearby"], ["back"]]','case .multiplayer: return [["partyLocalGolf"], ["partyOnline"], ["partyNearby"], ["back"]]')
edit('GolfArcade/Unity/TennisMenu.swift','case "partyMultiplayer": show(.multiplayer)', 'case "partyLocalGolf": online.select(id, menu: self)\n        case "partyMultiplayer": show(.multiplayer)')
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
edit('GolfArcade/Unity/IslandScreens.swift','IslandLobbyRow(title: "Online",','IslandLobbyRow(title:"Local Golf",subtitle:"Pass one phone · 2–4 players",icon:"figure.golf",id:"partyLocalGolf",menu:menu,compact:compact)\n                    IslandLobbyRow(title: "Online",')
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
