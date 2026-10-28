import SwiftUI

// Shared pieces of the Island menu system (IslandUI tokens live in ClubDesign.swift). Every focusable thing uses the same
// focus look — a lime fill with a navy ring — so it reads from the couch on a TV and on a phone alike.

extension IslandUI {
    static let ring = lime
    static let dark = MotionBrand.navyInk
    static let coral = MotionBrand.error
    /// Row / chip surface: a Deep Navy panel with a white edge, as the brand's panels.
    static let card = MotionBrand.navyDeep
}

/// The focus look: Lift fill + gold ring (+ a lift). Unfocused: the base fill (a Deep Navy panel) with a thin white edge.
struct IslandFocusStyle: ViewModifier {
    let focused: Bool
    var radius: CGFloat = 16
    var base: Color = IslandUI.card
    var ringWidth: CGFloat = 3.5
    func body(content: Content) -> some View {
        content
            .background(focused ? IslandUI.selected : base, in: RoundedRectangle(cornerRadius: radius, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: radius, style: .continuous)
                .strokeBorder(focused ? IslandUI.ring : IslandUI.ink.opacity(base == .clear ? 0 : 0.28), lineWidth: focused ? ringWidth : 1.5))
            .shadow(color: IslandUI.shadow.opacity(focused ? 0.5 : 0.25), radius: focused ? 10 : 4, y: focused ? 6 : 3)
            .accessibilityAddTraits(focused ? .isSelected : [])
    }
}
extension View {
    func islandFocus(_ focused: Bool, radius: CGFloat = 16, base: Color = IslandUI.card, ringWidth: CGFloat = 3.5) -> some View {
        modifier(IslandFocusStyle(focused: focused, radius: radius, base: base, ringWidth: ringWidth))
    }
}

/// The remote's legend along the bottom of the TV.
struct IslandHintBar: View {
    let items: [(key: String, label: String)]
    var compact = false
    static let move: [(key: String, label: String)] = [("▲ ▼ ◀ ▶", "Move"), ("A", "Select"), ("B", "Back")]
    var body: some View {
        HStack(spacing: compact ? 14 : 26) {
            ForEach(Array(items.enumerated()), id: \.offset) { _, item in
                HStack(spacing: 7) { Text(item.key).foregroundStyle(IslandUI.lime); Text(item.label) }
            }
        }
        .font(IslandUI.font(compact ? 13 : 16, bold: true)).foregroundStyle(.white)
        .padding(.horizontal, compact ? 16 : 26).padding(.vertical, compact ? 7 : 9)
        .background(IslandUI.dark.opacity(0.88), in: Capsule())
        .accessibilityHidden(true)
    }
}

/// One colour dot: ringed when picked, bigger ring when the row has focus.
struct IslandSwatch: View {
    let colour: Color
    var selected = false
    var size: CGFloat = 32
    var body: some View {
        Circle().fill(colour).frame(width: size, height: size)
            .overlay(Circle().strokeBorder(selected ? IslandUI.lime : IslandUI.ink.opacity(0.35), lineWidth: selected ? 3 : 2))
            .overlay(Circle().strokeBorder(IslandUI.dark, lineWidth: selected ? 2 : 0).padding(selected ? 3 : 0))
    }
}

/// A line of swatches that can be tapped; `kit` adds the "Kit" chip (the kit's own colour) at the front.
struct IslandSwatchRow: View {
    let colours: [Color]
    let selected: Int          // -1 = kit colour, -2 = custom, else index
    var kit = false
    var size: CGFloat = 32
    let pick: (Int) -> Void
    var body: some View {
        HStack(spacing: 0) {
            if kit {
                Button { pick(-1) } label: {
                    Text("Kit").font(IslandUI.font(size * 0.34, bold: true)).foregroundStyle(IslandUI.ink)
                        .frame(width: size, height: size)
                        .background(IslandUI.card, in: Circle())
                        .overlay(Circle().strokeBorder(selected == -1 ? IslandUI.lime : IslandUI.ink.opacity(0.35), lineWidth: selected == -1 ? 3 : 2))
                }.buttonStyle(.plain).accessibilityLabel("Kit colour")
                Spacer(minLength: 2)
            }
            ForEach(colours.indices, id: \.self) { i in
                Button { pick(i) } label: { IslandSwatch(colour: colours[i], selected: selected == i, size: size) }
                    .buttonStyle(.plain)
                if i < colours.count - 1 { Spacer(minLength: 2) }
            }
        }
    }
}

/// A two- or three-way choice drawn as a segmented pill (display + touch).
struct IslandSegments: View {
    let titles: [String]
    let selected: Int
    var compact = false
    var focused: Int? = nil
    let pick: (Int) -> Void
    var body: some View {
        HStack(spacing: 4) {
            ForEach(titles.indices, id: \.self) { i in
                Button { pick(i) } label: {
                    Text(titles[i]).font(IslandUI.font(compact ? 14 : 18, bold: true)).foregroundStyle(selected == i && focused != i ? IslandUI.navy : IslandUI.ink)
                        .lineLimit(1).minimumScaleFactor(0.7)
                        .frame(maxWidth: .infinity).padding(.vertical, compact ? 9 : 12)
                        .islandFocus(focused == i, radius: 11, base: selected == i ? IslandUI.lime : .clear)
                }.buttonStyle(.plain)
            }
        }
        .padding(4).background(IslandUI.dark.opacity(0.75), in: RoundedRectangle(cornerRadius: 15, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 15, style: .continuous).strokeBorder(IslandUI.ink.opacity(0.28), lineWidth: 1.5))
    }
}

/// A switch drawn like the rest of Island (the system Toggle is blue and tiny on a TV).
struct IslandSwitch: View {
    let on: Bool
    var compact = false
    var body: some View {
        let w: CGFloat = compact ? 56 : 80, h: CGFloat = compact ? 32 : 44
        ZStack(alignment: on ? .trailing : .leading) {
            Capsule().fill(on ? IslandUI.lime : IslandUI.dark).frame(width: w, height: h)
                .overlay(Capsule().strokeBorder(on ? MotionBrand.goldDeep : IslandUI.ink.opacity(0.45), lineWidth: 2.5))
            Circle().fill(.white).frame(width: h - 8, height: h - 8).padding(4).shadow(color: .black.opacity(0.25), radius: 1.5, y: 1)
        }
        .animation(.easeOut(duration: 0.15), value: on)
        .accessibilityHidden(true)
    }
}

/// A short message that fades on its own: refusals, "Equipped", "Coaching tips will show again".
struct IslandNotice: View {
    let text: String
    var compact = false
    var body: some View {
        if !text.isEmpty {
            Text(text).font(IslandUI.font(compact ? 14 : 18, bold: true)).foregroundStyle(IslandUI.navy)
                .padding(.horizontal, 18).padding(.vertical, compact ? 9 : 12)
                .background(IslandUI.lime, in: Capsule())
                .transition(.opacity.combined(with: .move(edge: .bottom)))
                .accessibilityAddTraits(.updatesFrequently)
        }
    }
}

/// The menu's current notice, shown as a pill that clears itself after a few seconds.
struct IslandMenuNotice: View {
    let menu: TennisMenu
    var compact = false
    var body: some View {
        IslandNotice(text: menu.notice, compact: compact)
            .task(id: menu.notice) {
                let shown = menu.notice
                guard !shown.isEmpty else { return }
                try? await Task.sleep(for: .seconds(3.5))
                menu.clearNotice(shown)
            }
    }
}

/// Typography for Island screens. Kept beside the shared palette and focus treatment.
extension View {
    func islandType(_ size: CGFloat, bold: Bool = false) -> some View { font(IslandUI.font(size, bold: bold)) }
}

/// A lobby action / discovery row. Uses the hub row's spacing, radius and common focus treatment.
struct IslandLobbyRow: View {
    let title: String
    var subtitle = ""
    var icon = "chevron.right"
    let id: String
    let menu: TennisMenu
    var compact = false
    var enabled = true
    var ready: Bool? = nil
    /// A big choice tile that stretches to share the screen's height (the phone's choice screens fill the screen).
    var tall = false
    var body: some View {
        if tall { tile } else { row }
    }
    private var tile: some View {
        let focused = menu.isFocused(id)
        return Button { menu.tap(id) } label: {
            HStack(spacing: 16) {
                Image(systemName: icon).font(.system(size: 26, weight: .bold)).foregroundStyle(focused ? IslandUI.navy : IslandUI.lime)
                    .frame(width: 60, height: 60).background(focused ? IslandUI.lime : IslandUI.dark.opacity(0.6), in: Circle())
                VStack(alignment: .leading, spacing: 4) {
                    Text(title).font(MotionBrand.font(.extraBoldItalic, 27)).lineLimit(1).minimumScaleFactor(0.6)
                    if !subtitle.isEmpty { Text(subtitle).islandType(15).foregroundStyle(focused ? IslandUI.ink.opacity(0.85) : IslandUI.muted).fixedSize(horizontal: false, vertical: true) }
                }
                Spacer(minLength: 0)
                Image(systemName: "chevron.right").font(.system(size: 18, weight: .heavy)).opacity(0.7)
            }
            .foregroundStyle(IslandUI.ink).padding(.horizontal, 20).padding(.vertical, 14)
            .frame(maxWidth: .infinity, minHeight: 92, maxHeight: .infinity, alignment: .leading)
            .background(alignment: .trailing) {
                // the choice's icon, large and faint, so a tall tile does not read as an empty box
                Image(systemName: icon).font(.system(size: 120, weight: .bold)).foregroundStyle(IslandUI.ink.opacity(0.06))
                    .offset(x: 18).clipped().accessibilityHidden(true)
            }
            .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
            .islandFocus(focused, radius: 24)
            .opacity(enabled ? 1 : 0.65)
        }.buttonStyle(.plain).disabled(!enabled).accessibilityIdentifier(id)
    }
    private var row: some View {
        Button { menu.tap(id) } label: {
            HStack(spacing: 12) {
                Image(systemName: icon).islandType(compact ? 20 : 24, bold: true).frame(width: 30)
                VStack(alignment: .leading, spacing: 3) {
                    Text(title).islandType(compact ? 18 : 24, bold: true).lineLimit(1).minimumScaleFactor(0.75)
                    if !subtitle.isEmpty { Text(subtitle).islandType(compact ? 12 : 15).foregroundStyle(IslandUI.muted).fixedSize(horizontal: false, vertical: true) }
                }
                Spacer(minLength: 0)
                if let ready { IslandSwitch(on: ready, compact: compact) }
            }.foregroundStyle(IslandUI.ink).padding(.horizontal, 16).padding(.vertical, compact ? 12 : 15)
                .frame(maxWidth: .infinity, minHeight: compact ? 54 : 66, alignment: .leading)
                .islandFocus(menu.isFocused(id), radius: 20, base: IslandUI.card)
                .opacity(enabled ? 1 : 0.65)
        }.buttonStyle(.plain).disabled(!enabled).accessibilityIdentifier(id)
    }
}

/// A participant's small paper card under the shared stage.
struct IslandLobbyPlayerCard: View {
    let participant: MultiplayerParticipant
    var host = false
    var local = false
    var loading = false
    var compact = false
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack(spacing: 5) {
                Circle().fill(participant.connected ? IslandUI.lime : IslandUI.coral).frame(width: 7, height: 7)
                Text(participant.name).islandType(compact ? 13 : 18, bold: true).lineLimit(1).minimumScaleFactor(0.65)
                if host { Image(systemName: "crown.fill").islandType(compact ? 11 : 15) }
                Spacer(minLength: 0)
            }
            HStack(spacing: 4) {
                Text(participant.seat < 0 ? "Watching" : "P\(participant.seat + 1)").islandType(compact ? 11 : 14, bold: true).lineLimit(1).minimumScaleFactor(0.6)
                if local { Text("· You").islandType(compact ? 10 : 13) }
                Spacer(minLength: 0)
                if participant.ready { Image(systemName: "checkmark.circle.fill").foregroundStyle(IslandUI.navy).background(IslandUI.lime, in: Circle()) }
            }
            if loading {
                Text(participant.loaded ? "Loaded 1/1" : "Loading 0/1").islandType(compact ? 10 : 13)
                Capsule().fill(IslandUI.ink.opacity(0.18)).frame(height: 5)
                    .overlay(alignment: .leading) { if participant.loaded { Capsule().fill(IslandUI.lime) } }
            } else if !participant.connected { Text("Reconnecting").islandType(compact ? 10 : 13).foregroundStyle(IslandUI.coral) }
        }.foregroundStyle(IslandUI.ink).padding(compact ? 10 : 14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(IslandUI.paper.opacity(0.96), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(IslandUI.ink.opacity(0.28), lineWidth: 1.5))
            .accessibilityElement(children: .combine)
    }
}

/// Emote shelf tiles share the locker's tile dimensions and radius, with the single Island focus look.
struct IslandEmoteTile: View {
    let id: String
    let title: String
    let image: UIImage?
    let menu: TennisMenu
    var cooldown: Double = 0
    var scale: CGFloat = 1
    var body: some View {
        Button { menu.tap("net-emote-\(id)") } label: {
            VStack(spacing: 0) {
                ZStack {
                    IslandUI.paper
                    if let image { Image(uiImage: image).resizable().scaledToFit() }
                    if cooldown > 0 { Text(String(format: "%.1f s", cooldown)).islandType(14 * scale, bold: true).padding(8).background(IslandUI.paper, in: Capsule()) }
                }.frame(height: 98 * scale).clipped()
                Text(title).islandType(14 * scale, bold: true).frame(maxWidth: .infinity, minHeight: 36 * scale)
            }.foregroundStyle(IslandUI.ink).frame(width: 112 * scale, height: 134 * scale)
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                .islandFocus(menu.isFocused("net-emote-\(id)"), radius: 18)
        }.buttonStyle(.plain).disabled(cooldown > 0).accessibilityIdentifier("net-emote-\(id)")
    }
}
