using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub.Menu
{
    /// FEEDBACK, its own tab (Adnan 11-19): who we are and why we ask, then one button. The button first warns that it takes the player out of the
    /// app (it opens Messages with a text to the team: BetaFeedback.open on the phone), and only then goes.
    public sealed partial class MenuHud
    {
        RectTransform feedbackMain, feedbackConfirm;

        void BuildFeedback(RectTransform r)
        {
            Heading(r, "Feedback", 760);
            // 1. the ask
            feedbackMain = BrandUi.Box(r, "Ask", 0, 0, 1920, 1080);
            BrandUi.Word(BrandUi.Box(feedbackMain, "Title", Left, ListTop, 760, 70), "Text", "We're a small team.", BrandUi.ExtraBoldItalic, 60, BrandColors.White);
            FeedbackBody(feedbackMain, ListTop + 86, "We're trying to hear from as many players as we can. Tell us what's fun, what's broken and what you wish was in the game. We read every message.");
            BrandUi.Word(BrandUi.Box(feedbackMain, "Hope", Left + 4, ListTop + 336, 760, 40), "Text", "The best ideas might end up in the game.", BrandUi.BoldItalic, 30, BrandColors.Gold);
            var send = BrandUi.Box(feedbackMain, "Send", Left, ListTop + 420, 400, 86);
            var (sendFace, _) = BrandUi.GoButton(send, "SEND US WHAT YOU THINK");
            var sendItem = Item(send, sendFace, "feedback-send", "Send us what you think", () => { if (Leader) { feedbackMain.gameObject.SetActive(false); feedbackConfirm.gameObject.SetActive(true); FocusAfterShow(); } }, 0);
            sendItem.glow = k => sendFace.anchoredPosition = new Vector2(Nudge * .6f * k, 0);
            // 2. the warning, before it leaves the app
            feedbackConfirm = BrandUi.Box(r, "Warning", 0, 0, 1920, 1080);
            BrandUi.Word(BrandUi.Box(feedbackConfirm, "Title", Left, ListTop, 760, 70), "Text", "Heads up", BrandUi.ExtraBoldItalic, 60, BrandColors.White);
            FeedbackBody(feedbackConfirm, ListTop + 86, "This opens Messages so you can text us, and takes you out of the app. Your game stays right where you left it: just come back when you're done.");
            var go = BrandUi.Box(feedbackConfirm, "Open", Left, ListTop + 300, 400, 86);
            var (goFace, _) = BrandUi.GoButton(go, "OPEN MESSAGES");
            var goItem = Item(go, goFace, "feedback-open", "Open Messages", () => { if (!Leader) return; Send("menuOpen", "mailbox-feedback"); ResetFeedback(); }, 0);
            goItem.glow = k => goFace.anchoredPosition = new Vector2(Nudge * .6f * k, 0);
            var group = new System.Collections.Generic.List<MenuItem>();
            WordItem(feedbackConfirm, "feedback-stay", "STAY HERE", "Stay here", null, Left, ListTop + 420, RailSize, ResetFeedbackAndFocus, group);
            feedbackConfirm.gameObject.SetActive(false);
        }
        void FeedbackBody(RectTransform parent, float y, string text)
        {
            var body = BrandUi.Label(BrandUi.Box(parent, "Body", Left + 4, y, 700, 230), "Text", text, BrandUi.Medium, 32, new Color(.902f, .925f, .973f), TextAnchor.UpperLeft);
            body.horizontalOverflow = HorizontalWrapMode.Wrap; body.verticalOverflow = VerticalWrapMode.Overflow;
        }
        /// The tab opens on the ask, never on the warning.
        void ResetFeedback()
        {
            if (!feedbackMain) return;
            feedbackMain.gameObject.SetActive(true); feedbackConfirm.gameObject.SetActive(false);
        }
        void ResetFeedbackAndFocus() { ResetFeedback(); FocusAfterShow(); }
    }
}
