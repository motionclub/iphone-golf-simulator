from pathlib import Path
r=Path.cwd()
def edit(f,a,b):
 p=r/f;s=p.read_text();assert a in s,(f,a);p.write_text(s.replace(a,b))
edit('GolfArcade/Unity/SportsSession.swift','''        return Sport(rawValue: UserDefaults.standard.string(forKey: "sports.lastSport.\\(players[playerIndex].id.uuidString)") ?? "tennis") ?? .tennis''','''        let id = players[playerIndex].id.uuidString
        let defaults = UserDefaults.standard
        let history = defaults.array(forKey: "sports.sessions.v1") as? [[String: Any]] ?? []
        let saved = defaults.string(forKey: "sports.lastSport.\\(id)") ?? history.last(where: { $0["playerID"] as? String == id })?["sport"] as? String
        return Sport(rawValue: saved ?? "tennis") ?? .tennis''')
edit('GolfArcade/Unity/TennisMenu.swift','case "homeEmotes": show(.homeEmotes)','case "homeEmotes": homeEmote = nil; show(.homeEmotes)')
# Ensure main view remembers last-selected sport when user moves to Back in picker.
edit('GolfArcade/Unity/TennisMenu.swift','    var previewSport: Sport {\n        Sport(rawValue: focused.replacingOccurrences(of: "sport-", with: "")) ?? homeSport\n    }','''    private(set) var previewSport: Sport = .tennis
    private func updateSportPreview() {
        if screen == .gameSelect, focused.hasPrefix("sport-"), let sport = Sport(rawValue: String(focused.dropFirst(6))) { previewSport = sport }
    }''')
edit('GolfArcade/Unity/TennisMenu.swift','case .gameSelect: row = 0; column = 0','case .gameSelect: row = 0; column = Sport.allCases.filter(\\.playable).firstIndex(of: homeSport) ?? 0; updateSportPreview()')
edit('GolfArcade/Unity/TennisMenu.swift','            row = r; column = c; if screen == .campaign','            row = r; column = c; updateSportPreview(); if screen == .campaign')
edit('GolfArcade/Unity/TennisMenu.swift','{ row = r; column = c; return true }','{ row = r; column = c; updateSportPreview(); return true }')
# No non-emote animation on menu avatars, including automatic winner sequences.
edit('GolfArcade/Unity/CharacterModelPreview.swift','if state.winnerID != winner { winner = state.winnerID; if let winner, state.animate { heroes[winner]?.motion.play("matchWin",at:now,now:now) } }','winner = state.winnerID')
# Sport-specific outfit must also be respected by all legacy IslandPlayer users.
edit('GolfArcade/Unity/ClubDesign.swift','cameraDistance: 2.95, idleSport: sport','cameraDistance: 2.95, outfitSport: sport ?? .tennis, idleSport: sport')
# TV Beta branding in menus and in the rendered game controller overlay.
edit('GolfArcade/Unity/TennisPlayViews.swift','else { TennisMenuScreen(compact: false) }','''else { TennisMenuScreen(compact: false)
                        .overlay(alignment: .bottomTrailing) {
                            Text("BETA · Feedback on your phone").font(IslandUI.font(13, bold: true))
                                .foregroundStyle(IslandUI.navy).padding(8).background(IslandUI.paper, in: Capsule()).padding(12)
                                .allowsHitTesting(false)
                        }
                    }''')
edit('GolfArcade/Unity/SportsDisplays.swift','    func restorePhoneControls() {','''    private func installBetaMark(in root: UIViewController) {
        let tag = 9023
        guard root.view.viewWithTag(tag) == nil else { return }
        let label = UILabel(); label.tag = tag; label.text = " MOTION CLUB · BETA "
        label.font = .boldSystemFont(ofSize: 12); label.textColor = .white
        label.backgroundColor = UIColor.black.withAlphaComponent(0.5)
        label.layer.cornerRadius = 6; label.clipsToBounds = true; label.isUserInteractionEnabled = false
        root.view.addSubview(label); label.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            label.trailingAnchor.constraint(equalTo: root.view.safeAreaLayoutGuide.trailingAnchor, constant: -16),
            label.bottomAnchor.constraint(equalTo: root.view.safeAreaLayoutGuide.bottomAnchor, constant: -8),
            label.heightAnchor.constraint(equalToConstant: 24)
        ])
    }
    func restorePhoneControls() {
        if let root = external?.rootViewController { installBetaMark(in: root) }''')
# The full-screen loading cover itself also carries Beta branding.
edit('GolfArcade/Unity/ArcadeScreens.swift','                    Text(venue).font(IslandUI.font(compact ? 32 : 58, bold: true))','''                    Text("MOTION CLUB · BETA").font(IslandUI.font(12, bold: true)).tracking(1.5)
                    Text(venue).font(IslandUI.font(compact ? 32 : 58, bold: true))''')
# Hold full preview aspect ratio; avoid crop on gameplay HUD.
edit('GolfArcade/Unity/HowToCards.swift','    var playing = true','    var playing = true\n    var aspectFit = false')
edit('GolfArcade/Unity/HowToCards.swift','layer.player = player; layer.videoGravity = .resizeAspectFill','layer.player = player; layer.videoGravity = aspectFit ? .resizeAspect : .resizeAspectFill')
edit('GolfArcade/Unity/ClubScreens.swift','!SportsSession.shared.reduceMotion).id(clip)','!SportsSession.shared.reduceMotion, aspectFit: true).id(clip)')
