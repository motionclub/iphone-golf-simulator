using System.Collections;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Hub.Menu;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// ARROW FOCUS (Adnan 10-28): the phone's arrow pad steps the TV's highlight and Select presses what is lit, through the session's own
    /// menuMove / menuSelect commands (the same JSON the phone sends).
    public class MenuArrowFocusTests
    {
        GameObject host; NativeSportsSession bridge; HubWorld hub; MenuHud hud;
        [UnitySetUp] public IEnumerator Boot()
        {
            LogAssert.ignoreFailingMessages = true; AudioListener.volume = 0;
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            bridge = host.AddComponent<NativeSportsSession>();
            Send("start", null, m => { m.sport = "hub"; m.menu = true; m.leader = true; m.playerName = "Adnan"; m.touch = true; });
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            hub = HubWorld.Find(); Assert.IsNotNull(hub?.Hud, "menu mode"); hud = hub.Hud;
            hub.StartArrival(); for (int i = 0; i < 90; i++) yield return null;
        }
        [TearDown] public void Clean() { HubWorld.EditorDriven = false; HubWorld.MenuMode = false; if (host) Object.DestroyImmediate(host); }

        void Send(string action, string mode = null, System.Action<NativeSportsSession.Message> more = null)
        {
            var m = new NativeSportsSession.Message { version = 1, session = "menu-arrows", action = action, mode = mode };
            more?.Invoke(m);
            bridge.Receive(JsonUtility.ToJson(m));
        }
        IEnumerator Settle() { for (int i = 0; i < 40; i++) yield return null; }

        [UnityTest] public IEnumerator ArrowsStepTheHighlightAndSelectPressesIt()
        {
            Assert.AreEqual(MenuHud.Home, hud.Screen);
            Assert.AreEqual("play", hud.Hovered, "Home opens on PLAY (MENU SQUAD 11-13: bottom left, one press to play)");
            Send("menuMove", "up"); yield return null;
            Assert.AreEqual("board-invite", hud.Hovered, "up: a + INVITE on an empty spot in the squad");
            Send("menuMove", "right"); yield return null;
            Assert.AreEqual("board-invite", hud.Hovered, "right: the next empty spot's +");
            Send("menuMove", "down"); yield return null;
            Assert.AreEqual("play", hud.Hovered, "down: back to PLAY");
            Send("menuSelect"); yield return Settle();
            Assert.AreEqual(MenuHud.Sport, hud.Screen, "Select presses the lit item");
            Assert.AreEqual("sport-tennis", hud.Hovered);
            Send("menuMove", "down"); yield return null;
            Assert.AreEqual("sport-golf", hud.Hovered, "down: the next sport");
            Send("menuSelect"); yield return Settle();
            Assert.AreEqual(MenuHud.GolfModes, hud.Screen);
            Assert.AreEqual("bay-golf-round", hud.Hovered);
            Send("menuMove", "down"); yield return null;
            Assert.AreEqual("bay-golf-pass", hud.Hovered);
            Send("menuBack"); yield return Settle();
            Assert.AreEqual(MenuHud.Sport, hud.Screen);
            // up from the list reaches the chrome (the tabs), never nothing
            Send("menuMove", "up"); yield return null;
            Assert.IsNotEmpty(hud.Hovered);
        }

        const string Exhibition = "{\"mode\":\"bay-tennis-exhibition\",\"sport\":\"tennis\",\"title\":\"Exhibition\",\"line2\":\"Pick a court\",\"start\":\"START MATCH\",\"map\":\"resort\"," +
            "\"maps\":[{\"id\":\"resort\",\"title\":\"Tropical Resort\",\"detail\":\"\"},{\"id\":\"volcano\",\"title\":\"Magma Crater\",\"detail\":\"\"}]," +
            "\"rows\":[{\"key\":\"difficulty\",\"label\":\"Difficulty\",\"choices\":[\"Relaxed\",\"Standard\",\"Tough\"],\"value\":1}]}";

        /// MENU SQUAD 11-13 ("it's not simple to start a game"): Select alone goes Home -> Tennis -> Exhibition -> START -> START MATCH.
        [UnityTest] public IEnumerator SelectAloneStartsAMatch()
        {
            var sent = new System.Collections.Generic.List<string>(); hud.Event += (t, m) => sent.Add(t + " " + m);
            Send("menuSelect"); yield return Settle();
            Assert.AreEqual(MenuHud.Sport, hud.Screen);
            Send("menuSelect"); yield return Settle();
            Assert.AreEqual(MenuHud.TennisModes, hud.Screen);
            Assert.AreEqual("bay-tennis-exhibition", hud.Hovered);
            Send("menuSelect"); yield return Settle();
            Assert.AreEqual(MenuHud.Setup, hud.Screen);
            Send("menuSetupState", Exhibition); yield return Settle();
            Assert.AreEqual("setup-start", hud.Hovered, "the setup opens on START (the phone's remembered picks)");
            Send("menuSetupState", Exhibition.Replace("\"value\":1", "\"value\":2")); yield return Settle();
            Assert.AreEqual("setup-start", hud.Hovered, "a refreshed setup keeps the highlight where it is");
            Send("menuSelect"); yield return null;
            Assert.Contains("menuSetupStart bay-tennis-exhibition", sent);
            hud.BeginLoading("tennis", "bay-tennis-exhibition", true); hud.SetLoading(.5f); yield return Settle();
            hud.MatchBuilt(); yield return null;
            Assert.AreEqual("start", hud.Hovered, "START MATCH is lit the moment the match is built");
            Send("menuSelect"); yield return null;
            Assert.Contains("menuStart ", sent);
        }
    }
}
