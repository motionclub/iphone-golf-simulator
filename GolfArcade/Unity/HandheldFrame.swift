import SwiftUI

/// Handheld play (golf and bowling on a phone with no TV of its own): the phone held upright like a Game Boy. The game (Unity, in
/// a window under this see-through one) draws in the top three quarters of the screen; the controls sit on an opaque deck in the
/// bottom quarter (SportsSession.handheldDeck, the same share Unity's NativeSportsSession.HandheldDeck keeps clear).
/// `game` is laid over the game's part of the screen (inside the safe area at the top); `deck` gets a fixed design canvas of
/// `deckDesign` points, scaled to fit the deck above the home indicator.
struct HandheldFrame<Game: View, Deck: View, DeckBackground: View>: View {
    var deckDesign = CGSize(width: 464, height: 220)
    @ViewBuilder var game: () -> Game
    @ViewBuilder var deck: () -> Deck
    @ViewBuilder var deckBackground: () -> DeckBackground

    var body: some View {
        GeometryReader { g in
            let insets = g.safeAreaInsets
            let screen = CGSize(width: g.size.width + insets.leading + insets.trailing, height: g.size.height + insets.top + insets.bottom)
            let deckHeight = screen.height * SportsSession.handheldDeck
            let gameHeight = screen.height - deckHeight
            let room = CGSize(width: screen.width - 16, height: deckHeight - insets.bottom - 6)
            let scale = max(0.1, min(room.width / deckDesign.width, room.height / deckDesign.height))
            VStack(spacing: 0) {
                game()
                    .padding(.top, insets.top).padding(.leading, insets.leading).padding(.trailing, insets.trailing)
                    .frame(width: screen.width, height: gameHeight)
                deck()
                    .frame(width: deckDesign.width, height: deckDesign.height)
                    .scaleEffect(scale)
                    .frame(width: screen.width, height: deckHeight - insets.bottom, alignment: .center)
                    .padding(.bottom, insets.bottom)
                    .frame(width: screen.width, height: deckHeight)
                    .background { deckBackground() }
                    .clipped()
            }
            .frame(width: screen.width, height: screen.height)
            .ignoresSafeArea()
        }
    }

    /// How far above the screen's bottom edge the game's part begins: overlays drawn by the app for the whole screen (the intro's
    /// skip, emote rows, tips) sit above this in handheld play instead of over the deck.
    @MainActor static var deckLift: CGFloat {
        (SportsDisplays.shared.phone?.bounds.height ?? 844) * SportsSession.handheldDeck
    }
}

extension View {
    /// Lift a bottom overlay clear of the handheld deck (`base` points above the deck in handheld play, `base` above the bottom otherwise).
    @MainActor func handheldLift(_ phonePlay: Bool, base: CGFloat) -> some View {
        padding(.bottom, phonePlay ? HandheldFrame<EmptyView, EmptyView, EmptyView>.deckLift + 10 : base)
    }
}
