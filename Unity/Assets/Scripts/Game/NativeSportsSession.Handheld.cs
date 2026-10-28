using UnityEngine;

namespace GolfArcade.Game {
    /// Handheld play (golf and bowling on a phone with no TV of its own, PLAN_PhonePlay_Handheld.md): the phone held upright like a
    /// Game Boy. The game draws in the top three quarters of the screen; the app's control deck covers the bottom quarter, so the
    /// gameplay camera, the HUDs on it and the legacy golf overlay all keep clear of it.
    public sealed partial class NativeSportsSession {
        public partial class Message { public bool phonePlay; }
        /// The share of the screen's height the app's control deck takes, at the bottom (SportsSession.handheldDeck on the phone).
        public const float HandheldDeck = .25f;
        bool handheld;
        static Rect HandheldRect => new Rect(0, HandheldDeck, 1, 1 - HandheldDeck);

        /// From the launch message: on for golf and bowling started for phone play (the app sends `phonePlay` only with no TV).
        void ConfigureHandheld(Message m) {
            handheld = m.phonePlay && !m.external && (m.sport == "golf" || m.sport == "bowling");
            GolfArcade.UI.Hud.ReservedBottom = handheld ? HandheldDeck : 0;
            GolfArcade.UI.GolfShotHud.Handheld = handheld;
            // the expanded map fills the phone: a sharper picture than the controller card's
            GolfGame.NativeMapWidth = handheld ? 512 : 256;
        }
        void EndHandheld() {
            handheld = false;
            GolfArcade.UI.Hud.ReservedBottom = 0; GolfArcade.UI.GolfShotHud.Handheld = false; GolfGame.NativeMapWidth = 256;
        }
        /// The gameplay camera's viewport on the phone's own screen: the top of it in handheld play, all of it otherwise.
        Rect PhoneViewport => handheld ? HandheldRect : new Rect(0, 0, 1, 1);
    }
}
