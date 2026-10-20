from pathlib import Path
r=Path.cwd()
def edit(f,a,b):
 p=r/f;s=p.read_text();assert a in s,(f,a[:60]);p.write_text(s.replace(a,b))
edit('GolfArcade/Unity/TennisMenu.swift','func openOnlineParty() { show(.party) }','func openOnlineParty() { show(.multiplayer) }')
p=r/'GolfArcadeTests/TennisCampaignTests.swift';s=p.read_text();a=s.index('        XCTAssertEqual(menu.focused, "homeContinue",');b=s.index('        XCTAssertFalse(menu.rows(.main)',a);s=s[:a]+'''        XCTAssertEqual(menu.focused, "play", "Home lands on the play entry point")
        menu.select(); XCTAssertEqual(menu.screen, .party)
        menu.tap("partySolo"); XCTAssertEqual(menu.screen, .gameSelect)
        menu.back(); XCTAssertEqual(menu.screen, .party)
        menu.back(); XCTAssertEqual(menu.screen, .main)
        menu.move(.down); XCTAssertEqual(menu.focused, "character")
        menu.move(.down); XCTAssertEqual(menu.focused, "homeEmotes")
        menu.move(.down); XCTAssertEqual(menu.focused, "settings")
'''+s[b:];s=s.replace('XCTAssertEqual(menu.focused, "homeContinue")','XCTAssertEqual(menu.focused, "play")');p.write_text(s)
edit('GolfArcadeTests/LockerTests.swift','func testHomeContinuesAndHasNoStore()','func testHomePlayInviteEmotesAndFeedbackHaveFocusTargets()')
edit('GolfArcadeTests/LockerTests.swift','XCTAssertEqual(menu.rows(.main).first, ["homeContinue"])','XCTAssertEqual(menu.rows(.main).first, ["play", "homeInvite"])')
edit('GolfArcadeTests/LockerTests.swift','["homeContinue", "play", "character", "settings"]','["play", "homeInvite", "character", "homeEmotes", "settings", "betaFeedback"]')
edit('GolfArcadeTests/NewMenuSnapshotTests.swift','''        XCTAssertEqual(menu.screen,.online(.entry));menu.back();XCTAssertEqual(menu.screen,.party)
        menu.tap("partyOnline");XCTAssertEqual(menu.screen,.online(.entry));menu.back()''','''        XCTAssertEqual(menu.screen,.multiplayer)
        menu.tap("partyOnline");XCTAssertEqual(menu.screen,.onlineChoice)
        menu.tap("onlineQuick");XCTAssertEqual(menu.screen,.online(.entry));menu.back();XCTAssertEqual(menu.screen,.onlineChoice)''')
edit('GolfArcadeUITests/MenuNavigationRegressionTests.swift','        play.tap()\n        let golf = app.buttons["Golf"]','        play.tap()\n        app.buttons["partySolo"].tap()\n        let golf = app.buttons["select-golf"]')
edit('GolfArcadeUITests/MenuNavigationRegressionTests.swift','app.buttons["Golf"].waitForExistence','app.buttons["select-golf"].waitForExistence')
edit('GolfArcadeUITests/MenuNavigationRegressionTests.swift','app.buttons["Tennis"].tap()','app.buttons["select-tennis"].tap()')
p=r/'GolfArcadeTests/LockerMirrorTests.swift';s=p.read_text();s=s.replace('func testLockerTileAndTennisIdlePlayReadyIdleInPlace()', 'func testMenuTilesHoldStillAndExplicitIdlePlaysInPlace()');needle='                XCTAssertEqual(c.motion, .ready, "\\(label) plays ReadyIdle")';s=s.replace(needle,'''                if mode != "tennisIdle" {
                    XCTAssertNil(c.motion); XCTAssertNil(c.rig)
                    XCTAssertFalse(c.character.hasActions)
                    continue
                }
'''+needle);s=s.replace('func testPlayTilePlaysOneServeThenReady()', 'func testExplicitServePlaybackReturnsToReady()');s=s.replace('c.configureClub(.play, animate: true);', 'c.configureClub(.play, animate: true); c.play(.serveOnce);');s=s.replace('d.configureClub(.play, animate: true);', 'd.configureClub(.play, animate: true); d.play(.serveOnce);');a=s.index('    /// The tennis idle on the loading screen');b=s.index('    /// Reduced motion keeps',a);s=s[:a]+'''    /// Loading uses gameplay/map imagery and never runs a character warm-up.
    func testLoadingScreenHasNoCharacterAnimationSurface() async throws {
        let menu = TennisMenu.shared, session = SportsSession.shared
        defer { session.loading.cancel(); menu.debugShow(.title) }
        menu.debugShow(.loading, launch: MenuLaunch(mode: .training)); session.loading.begin(now: Date())
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let host = UIHostingController(rootView: LoadingScreen(menu: menu, compact: false)); host.safeAreaRegions = []
        let window = UIWindow(windowScene: scene); window.frame = CGRect(x: 0, y: 0, width: 1280, height: 720)
        window.rootViewController = host; window.isHidden = false; host.view.frame = window.bounds; host.view.layoutIfNeeded()
        defer { window.isHidden = true }
        try await Task.sleep(for: .milliseconds(300))
        XCTAssertNil(findScene(host.view), "Loading previews the venue, without a warm-up character")
    }

'''+s[b:];p.write_text(s)
# Avoid unrelated onboarding state in the isolated TV snapshot window.
edit('GolfArcadeTests/MenuBetaTests.swift','try await capture(TennisTVRoot(), "home-','try await capture(TennisMenuScreen(compact: false), "home-')
