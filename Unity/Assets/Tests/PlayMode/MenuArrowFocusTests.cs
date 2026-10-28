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
            Assert.AreEqual("play", hud.Hovered, "a screen opens with its first item lit");
            Send("menuMove", "down"); yield return null;
            Assert.AreEqual("board-invite", hud.Hovered, "down: the next row");
            Send("menuMove", "up"); yield return null;
            Assert.AreEqual("play", hud.Hovered, "up: back to PLAY");
            Send("menuSelect"); yield return Settle();
            Assert.AreEqual(MenuHud.Sport, hud.Screen, "Select presses the lit item");
            Assert.AreEqual("sport-tennis", hud.Hovered);
            Send("menuMove", "right"); yield return null;
            Assert.AreEqual("sport-golf", hud.Hovered, "right: the next lane");
            Send("menuSelect"); yield return Settle();
            Assert.AreEqual(MenuHud.GolfModes, hud.Screen);
            Assert.AreEqual("bay-golf-round", hud.Hovered);
            Send("menuMove", "down"); yield return null;
            Assert.AreEqual("bay-golf-pass", hud.Hovered);
            Send("menuBack"); yield return Settle();
            Assert.AreEqual(MenuHud.Sport, hud.Screen);
            // up from the lanes reaches the chrome (the tabs), never nothing
            Send("menuMove", "up"); yield return null;
            Assert.IsNotEmpty(hud.Hovered);
        }
    }
}
