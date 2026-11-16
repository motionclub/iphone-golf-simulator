import AVKit
import SwiftUI

/// The old tennis front end's colours, matched to the in-game HUD (TennisHud), that the controller and loading screens still use.
enum Arcade {
    static let navyDeep = Color(red: 0.02, green: 0.05, blue: 0.16)
    static let sky = Color(red: 0.25, green: 0.70, blue: 1.0)
    static let skyDeep = Color(red: 0.08, green: 0.34, blue: 0.86)
    static let sun = Color(red: 1.0, green: 0.76, blue: 0.20)
    static let sunDeep = Color(red: 1.0, green: 0.40, blue: 0.12)
    static let sea = Color(red: 0.12, green: 0.85, blue: 0.78)
    static let crimson = Color(red: 0.92, green: 0.14, blue: 0.24)
    static let crimsonDeep = Color(red: 0.36, green: 0.02, blue: 0.08)
    static let lime = Color(red: 0.62, green: 0.93, blue: 0.22)
}

// MARK: - Screens

/// The menu itself. `compact` is the phone held upright with no TV: the same screens,
/// stacked, and touch selects. Otherwise it is laid out for a 16:9 TV and driven by the remote.
/// Set by a host that draws its own top bar (the Plaza's station panel), so the menu does not stack a second one under it.
private struct MenuHostsTopBarKey: EnvironmentKey { static let defaultValue = false }
extension EnvironmentValues {
    var menuHostsTopBar: Bool { get { self[MenuHostsTopBarKey.self] } set { self[MenuHostsTopBarKey.self] = newValue } }
}

struct TennisMenuScreen: View {
    @Bindable var menu = TennisMenu.shared
    var compact: Bool
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.menuHostsTopBar) private var hostsTopBar
    var body: some View {
        ClubCameraHost(route: menu.screen, reducedMotion: true, paused: SportsSession.shared.menuPauseVisible, content: AnyView(screenContent))
            .safeAreaInset(edge: .top) {
                if !hostsTopBar && menu.screen != .title && menu.screen != .main && !SportsSession.shared.menuPauseVisible {
                    HStack {
                        Button { menu.back() } label: { Label("Back", systemImage: "chevron.left") }
                            .accessibilityIdentifier("menu-back")
                        Spacer()
                        Button("Main Menu") { menu.goHome() }.accessibilityIdentifier("menu-home")
                    }
                    .font(IslandUI.font(compact ? 16 : 22, bold: true)).foregroundStyle(IslandUI.ink)
                    .padding(.horizontal, compact ? 22 : 40).frame(minHeight: compact ? 48 : 60)
                    .background(IslandUI.dark)
                }
            }
    }
    private var screenContent: some View {
        Group {
            if SportsSession.shared.menuPauseVisible { IslandPauseScreen(compact: compact) }
            else { switch menu.screen {
            case .title: IslandTitleScreen(menu: menu, compact: compact)
            case .main: IslandHomeScreen(menu: menu, compact: compact)
            case .party, .multiplayer, .localChoice, .localPlayers, .onlineChoice: IslandPartyScreen(menu: menu, compact: compact)
            case .homeEmotes: HomeEmoteScreen(menu: menu, compact: compact)
            case .online(.loading): LoadingScreen(menu: menu, compact: compact)
            case .online(let route): IslandOnlineScreen(menu: menu, route: route, compact: compact)
            case .gameSelect: IslandSportsScreen(menu: menu, compact: compact)
            case .hub(let sport): IslandHubScreen(menu: menu, sport: sport, compact: compact)
            case .campaign: IslandLadderScreen(menu: menu, compact: compact, exhibition: false)
            case .exhibition: IslandLadderScreen(menu: menu, compact: compact, exhibition: true)
            case .training: IslandTrainingScreen(menu: menu, compact: compact)
            case .character: IslandLockerScreen(menu: menu, compact: compact)
            case .settings: IslandSettingsScreen(menu: menu, compact: compact)
            case .howTo: IslandGuideScreen(menu: menu, compact: compact, golf: false)
            case .connect: IslandConnectScreen(menu: menu, compact: compact)
            case .loading: LoadingScreen(menu: menu, compact: compact)
            case .results: IslandResultsScreen(menu: menu, compact: compact)
            case .story: IslandStoryScreen(menu: menu, compact: compact)
            case .map: if menu.mapSport == .golf { GolfCourseScreen(menu: menu, compact: compact) } else { IslandCourtScreen(menu: menu, compact: compact) }
            case .postMatch: IslandResultsScreen(menu: menu, compact: compact, postMatch: true)
            } }
        }.transaction { $0.animation = nil; $0.disablesAnimations = true }
    }
}
