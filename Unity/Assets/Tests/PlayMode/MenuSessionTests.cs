using System;
using System.Collections;
using System.Linq;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Hub.Menu;
using GolfArcade.Multiplayer;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// The menu as a session (the `hub` session kind): it boots from the phone's start message with `menu: true`, with and without a
    /// TV; a match start leaves it and the next hub start brings it back; the TV toast; chat bubbles and emotes in the squad; an
    /// online match wears the lobby looks. Every match start here is the plain scene swap the phone asks for (never `seamless`).
    /// (Ported from HubPlazaTests / HubPartyTests when the walk-around Plaza was removed, 2026-11-15.)
    public class MenuSessionTests
    {
        const string Session = "menu-s";
        GameObject host; NativeSportsSession bridge;

        void Send(string session, string action, Action<NativeSportsSession.Message> more = null)
        {
            var m = new NativeSportsSession.Message { version = 1, session = session, action = action, touch = true };
            more?.Invoke(m); bridge.Receive(JsonUtility.ToJson(m));
        }
        IEnumerator BootMenu(string session = Session, bool phoneOnly = false, string screen = null)
        {
            AudioListener.volume = 0; LogAssert.ignoreFailingMessages = true;
            HubWorld.EditorDriven = true;
            if (!host) { host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host); bridge = host.AddComponent<NativeSportsSession>(); }
            Send(session, "start", m =>
            {
                m.sport = "hub"; m.menu = true; m.leader = true; m.playerName = "Adnan"; m.phoneOnly = phoneOnly; m.screen = screen;
                m.shirt = "E8505B"; m.shorts = "24345E"; m.accent = "FFFFFF"; m.back = "racket_back";
            });
            for (int i = 0; i < 1500 && !(bridge.Ready && NativeSportsSession.HubActive && HubWorld.Find()); i++) yield return null;
        }
        [TearDown] public void Clean()
        {
            HubWorld.EditorDriven = false; HubWorld.PhoneOnly = false;
            if (host) Object.DestroyImmediate(host);
            Time.timeScale = 1;
        }
        static IEnumerator Wait(float seconds) { for (float t = 0; t < seconds; t += Time.unscaledDeltaTime) yield return null; }

        /// BOOT: the phone's start message builds the menu a step a frame and the first frame is the line-up on its venue plate.
        [UnityTest, Timeout(300000)] public IEnumerator MenuBootsFromTheNativeStartAndRendersTheLineUp()
        {
            yield return BootMenu();
            Assert.IsTrue(bridge.Ready, "the menu camera must render a frame before ready");
            var hub = HubWorld.Find(); Assert.IsNotNull(hub); Assert.IsTrue(hub.Initialized);
            Assert.IsTrue(NativeSportsSession.Active); Assert.IsTrue(NativeSportsSession.HubActive);
            Assert.AreEqual(hub.Camera, bridge.GameplayCamera);
            Assert.AreEqual(1, Time.timeScale, "the menu never pauses");
            Assert.IsNotNull(hub.Menu, "the stage"); Assert.IsNotNull(hub.Hud, "the HUD"); Assert.AreEqual(MenuHud.Home, hub.Hud.Screen);
            Assert.IsNotNull(hub.Backdrop, "a venue plate stands behind the line-up"); Assert.IsTrue(MenuShots.Centred);
            Assert.IsNull(hub.transform.Find("Hub world"), "no plaza is built behind the menu");
            Assert.IsNotNull(hub.Player.hero, "the menu hero is the match hero with the menu animator");
            Assert.IsNotNull(hub.Player.look);
            Assert.IsFalse(hub.Player.look.female);
            Assert.IsTrue(hub.Player.locked, "nobody walks");
            Assert.IsTrue(hub.Player.look.TryGetKitColour("Kit_Shirt", out var shirt));
            Assert.Greater(shirt.r, shirt.b, "the launch's shirt colour reaches the menu hero");
            Assert.IsNotEmpty(hub.Player.hero.Emotes.ToList(), "emote clips resolved from the hero prefab");
        }

        /// BOOT, no TV: the same start with `phoneOnly` boots the same menu on the phone's own screen.
        [UnityTest, Timeout(300000)] public IEnumerator MenuBootsOnAPhoneWithNoTv()
        {
            yield return BootMenu(phoneOnly: true);
            Assert.IsTrue(bridge.Ready);
            var hub = HubWorld.Find(); Assert.IsNotNull(hub); Assert.IsTrue(hub.Initialized);
            Assert.IsTrue(HubWorld.PhoneOnly);
            Assert.IsNotNull(hub.Hud); Assert.AreEqual(MenuHud.Home, hub.Hud.Screen);
            Assert.IsNotNull(hub.Backdrop);
            yield return null; yield return null;
            var want = MenuHud.PhoneCameraRect(); var got = hub.Camera.rect;
            Assert.Less(Mathf.Abs(got.y - want.y) + Mathf.Abs(got.height - want.height), 1e-3f, "the camera keeps to the part of the phone above the menu's panel");
        }

        /// NO PLATE: there is no plaza behind the plates any more, so when a plate cannot be loaded the next venue's is used, and when
        /// none can the menu still boots: the squad in its one centred shot on a plain brand colour, with an error in the log.
        [UnityTest, Timeout(300000)] public IEnumerator TheMenuStillStandsWhenAPlateIsMissing()
        {
            var keep = (string[])MenuBackdrop.Venues.Clone(); string pin = MenuBackdrop.Pin;
            try
            {
                // one venue's plate missing: another venue stands in
                MenuBackdrop.Venues[0] = "missing-venue"; MenuBackdrop.Pin = "missing-venue";
                yield return BootMenu("menu-plate-1");
                var hub = HubWorld.Find(); Assert.IsNotNull(hub); Assert.IsTrue(bridge.Ready);
                Assert.IsNotNull(hub.Backdrop, "another venue's plate"); Assert.AreEqual(keep[1], hub.Backdrop.Venue);
                Send("menu-plate-1", "end");
                // no plate at all
                for (int i = 0; i < MenuBackdrop.Venues.Length; i++) MenuBackdrop.Venues[i] = "missing-venue-" + i;
                MenuBackdrop.Pin = null;
                LogAssert.Expect(LogType.Error, new System.Text.RegularExpressions.Regex("no backdrop plate could be loaded"));
                yield return BootMenu("menu-plate-2");
                hub = HubWorld.Find(); Assert.IsNotNull(hub); Assert.IsTrue(bridge.Ready, "the menu still boots");
                Assert.IsNull(hub.Backdrop); Assert.IsTrue(MenuShots.Centred, "the squad keeps its one shot");
                Assert.AreEqual(CameraClearFlags.SolidColor, hub.Camera.clearFlags);
                Assert.Less(Vector4.Distance(hub.Camera.backgroundColor, MenuBackdrop.FallbackColour), 1e-4f, "a plain brand colour behind the heroes");
                hub.StartArrival(); yield return Wait(.5f);
                Assert.Less(Vector3.Distance(hub.Camera.transform.position, MenuShots.CentreShot.position), .1f, "the centred shot");
                Assert.Less(Vector3.Distance(hub.Player.transform.position, MenuShots.Slots[0]), .05f);
                Assert.IsNotNull(hub.Hud); Assert.AreEqual(MenuHud.Home, hub.Hud.Screen);
                Assert.IsTrue(hub.Hud.TryCentre("play", out _), "the menu is usable");
            }
            finally { for (int i = 0; i < keep.Length; i++) MenuBackdrop.Venues[i] = keep[i]; MenuBackdrop.Pin = pin; }
        }

        /// TOAST: the phone's `hubToast` shows a message in the TV corner (an invite arrived, a friend is joining) for a few seconds; a
        /// newer one replaces it; it never blocks the menu (the pointer still clicks under it).
        [UnityTest, Timeout(300000)] public IEnumerator AToastShowsOnTheTvAndGoesAway()
        {
            yield return BootMenu();
            var hub = HubWorld.Find(); Assert.IsNotNull(hub); var hud = hub.Hud; Assert.IsNotNull(hud);
            hub.StartArrival(); yield return Wait(1f);
            Assert.AreEqual("", hub.ToastShown);
            Send(Session, "hubToast", m => m.mode = "Sam invited you · Tennis · accept on your phone");
            yield return null;
            Assert.AreEqual("Sam invited you · Tennis · accept on your phone", hub.ToastShown);
            hub.ShowToast("Joining Sam…", .4f); Assert.AreEqual("Joining Sam…", hub.ToastShown, "the newer message replaces it");
            Assert.IsTrue(hud.TryCentre("play", out var at));
            hud.PointAt(at, false, 0); yield return null;
            hud.PointAt(at, true, 1); yield return null;
            hud.PointAt(at, false, 1); yield return Wait(.3f);
            Assert.AreEqual(MenuHud.Sport, hud.Screen, "the menu works under a toast");
            yield return new WaitForSecondsRealtime(.5f);
            Assert.AreEqual("", hub.ToastShown, "it goes away by itself");
            Send(Session, "hubToast", m => m.mode = "");
            yield return null; Assert.AreEqual("", hub.ToastShown, "an empty message shows nothing");
        }

        /// LEAVE + RETURN: a match start from the menu replaces Hub.unity (a plain scene swap under the phone's cover); when the match
        /// ends the next hub start, carrying the screen to open on, brings the menu back.
        [UnityTest, Timeout(600000)] public IEnumerator MatchStartLeavesTheMenuAndTheMenuComesBack()
        {
            yield return BootMenu("menu-1");
            Assert.IsTrue(bridge.Ready); Assert.IsNotNull(HubWorld.Find());
            Send("match-1", "start", m => m.sport = "tennis");
            for (int i = 0; i < 2400 && !(bridge.Ready && Object.FindFirstObjectByType<TennisGame>()); i++) yield return null;
            Assert.IsTrue(bridge.Ready, "the match is up");
            Assert.IsFalse(NativeSportsSession.HubActive, "a match start leaves the menu");
            Assert.IsNull(HubWorld.Find(), "the match scene replaced Hub.unity");
            Send("match-1", "end");
            yield return BootMenu("menu-2", screen: MenuHud.Home);
            Assert.IsTrue(bridge.Ready); Assert.IsTrue(NativeSportsSession.HubActive);
            var hub = HubWorld.Find(); Assert.IsNotNull(hub); Assert.IsNotNull(hub.Hud);
            Assert.AreEqual(MenuHud.Home, hub.Hud.Screen, "back from a match: straight onto the menu");
            Assert.IsNull(Object.FindFirstObjectByType<TennisGame>(), "the match scene is gone");
            Assert.AreEqual(1, Time.timeScale);
        }

        /// PARTY: a friend's chat shows as a bubble over their hero and yours over you (literal text, bounded on screen), their emote
        /// plays on their hero, and both go when the friend leaves the party or after a few seconds.
        [UnityTest, Timeout(300000)] public IEnumerator FriendsChatAndEmoteInTheSquad()
        {
            yield return BootMenu();
            var hub = HubWorld.Find(); Assert.IsNotNull(hub);
            hub.StartArrival(); yield return Wait(.6f);
            var remotes = HubRemotes.For(hub);
            var friend = new RemoteState { id = "mia", name = "Mia", place = "plaza", female = true, shirt = "4E88D4", shorts = "24345E", skinHex = "C47A4C", colour = 1, x = 0, z = -7 };
            Send(Session, "hubRemote", m => m.remote = JsonUtility.ToJson(friend));
            yield return Wait(.6f);
            Assert.AreEqual(2, hub.Menu.Heroes, "the friend joins the squad");
            Assert.IsTrue(remotes.TryGetShown("mia", out var shown)); Assert.Less(Vector3.Distance(shown, MenuShots.Slots[1]), .05f, "on slot 1");
            friend.emote = HeroTennisDriver.Clip.IntroWave.ToString();
            Send(Session, "hubRemote", m => m.remote = JsonUtility.ToJson(friend));
            yield return Wait(.2f);
            var friendHero = remotes.HeroOf("mia"); Assert.IsNotNull(friendHero);
            Assert.IsNotEmpty(friendHero.Playing ?? "", "the friend's emote plays on their hero");
            Send(Session, "hubChat", m => { m.remote = "mia"; m.mode = "Meet at the bench!"; });
            Send(Session, "hubChat", m => { m.remote = ""; m.mode = "Ready! Let's play <b>now</b>"; });
            Send(Session, "hubChat", m => { m.remote = "stranger"; m.mode = "not in the party"; });
            Assert.IsTrue(remotes.HasSpeech("mia")); Assert.IsTrue(remotes.HasSpeech(""));
            Assert.IsFalse(remotes.HasSpeech("stranger"), "only party members speak");
            Assert.IsFalse(hub.GetComponentsInChildren<UnityEngine.UI.Text>().First(t => t.text == "Meet at the bench!").supportRichText, "chat is literal text");
            yield return Wait(.3f);
            foreach (var canvas in hub.GetComponentsInChildren<Canvas>().Where(c => c.name.StartsWith("Party speech")))
            {
                var rect = (RectTransform)canvas.transform; var corners = new Vector3[4]; rect.GetWorldCorners(corners);
                float width = Mathf.Abs(hub.Camera.WorldToViewportPoint(corners[3]).x - hub.Camera.WorldToViewportPoint(corners[0]).x);
                Assert.LessOrEqual(width, .225f, "chat bubbles stay bounded on the menu's close camera");
                var centre = hub.Camera.WorldToViewportPoint(rect.position);
                Debug.Log($"[MenuSessionTests] {canvas.name}: viewport ({centre.x:0.00}, {centre.y:0.00}), width {width:0.000}");
            }
            Send(Session, "hubRoster", m => m.mode = "");
            Assert.AreEqual(0, remotes.Count, "a friend who left the party is removed");
            yield return null; yield return null;
            Assert.IsFalse(remotes.HasSpeech("mia"), "their bubble goes with them");
            Assert.AreEqual(1, hub.Menu.Heroes);
            yield return new WaitForSecondsRealtime(8.1f);
            Assert.IsFalse(remotes.HasSpeech(""), "a bubble lasts 8 s");
        }

        /// OLD PHONES: the walk-around Plaza's commands (an older build of the app still sends them) are swallowed by the menu: nothing
        /// moves, nothing fades, and they never reach a match handler. `hubB` is still sent by today's menu flows. An emote still plays.
        [UnityTest, Timeout(300000)] public IEnumerator OldPlazaCommandsAreSwallowedAndAnEmoteStillPlays()
        {
            yield return BootMenu();
            var hub = HubWorld.Find(); Assert.IsNotNull(hub);
            hub.StartArrival(); yield return Wait(.6f);
            var friend = new RemoteState { id = "sam", name = "Sam", place = "locker", bay = "bay-tennis-online", x = 30, z = 40, speed = 3, colour = 2 };
            Send(Session, "hubRemote", m => m.remote = JsonUtility.ToJson(friend));
            yield return Wait(.3f);
            var at = hub.Player.transform.position; float yaw = hub.Player.Yaw; var cam = hub.Camera.transform.position;
            foreach (var action in new[] { "hubA", "hubB", "hubGo", "hubUse", "hubCall", "hubGather", "hubMeet", "hubSomethingNewer" })
                foreach (var mode in new[] { "bay-tennis-online", "locker", "sam", "" })
                    Send(Session, action, m => m.mode = mode);
            float fade = 0;
            for (float t = 0; t < .6f; t += Time.unscaledDeltaTime) { fade = Mathf.Max(fade, hub.FadeAlpha); yield return null; }
            Assert.AreEqual(0, fade, "no fade to black (hubMeet used to run the plaza's quick travel)");
            Assert.Less(Vector3.Distance(at, hub.Player.transform.position), 1e-3f, "your hero stays on the line-up");
            Assert.Less(Mathf.Abs(Mathf.DeltaAngle(yaw, hub.Player.Yaw)), .01f);
            Assert.Less(Vector3.Distance(cam, hub.Camera.transform.position), .1f, "the camera holds its shot");
            Assert.IsTrue(hub.Player.locked);
            Assert.IsTrue(NativeSportsSession.Active); Assert.IsTrue(NativeSportsSession.HubActive); Assert.IsTrue(bridge.Ready);
            Assert.AreEqual(MenuHud.Home, hub.Hud.Screen);
            Assert.IsTrue(HubRemotes.For(hub).TryGetShown("sam", out var shown));
            Assert.Less(Vector3.Distance(shown, MenuShots.Slots[1]), .05f, "a friend stands in the squad wherever an old phone says they are");
            Send(Session, "hubEmote", m => m.mode = "wave"); yield return Wait(.3f);
            Assert.IsNotEmpty(hub.Player.hero.Playing ?? "", "the wave plays on the menu hero");
            Send(Session, "end");
            Assert.IsFalse(NativeSportsSession.Active); Assert.IsFalse(NativeSportsSession.HubActive);
        }

        /// WIRE: hubPose keeps the eight fields every build of the phone parses (the place is always "plaza", nobody walks or sits).
        [Test] public void HubPoseKeepsItsWireFormat()
        {
            Assert.AreEqual("plaza|-0.100|0.000|-7.600|173.4|0.00||IntroWave", NativeSportsSession.HubPose(new Vector3(-.1f, 0, -7.6f), 173.42f, "IntroWave"));
            Assert.AreEqual("plaza|1.500|0.250|2.000|-90.0|0.00||", NativeSportsSession.HubPose(new Vector3(1.5f, .25f, 2), -90, null));
            Assert.AreEqual(8, NativeSportsSession.HubPose(Vector3.zero, 0, "").Split('|').Length);
        }

        /// LOOK: an online tennis match started from the menu wears the lobby's colours (the same ones the squad shows).
        [UnityTest, Timeout(600000)] public IEnumerator OnlineTennisWearsTheLobbyLooks()
        {
            yield return BootMenu();
            Assert.IsTrue(bridge.Ready); Assert.IsNotNull(HubWorld.Find());
            NetworkParticipant P(string id, int seat, bool female, string shirt, string skin) => new NetworkParticipant { id = id, name = id, seat = seat, ready = true, loaded = true, connected = true, female = female,
                loadout = new NetworkEmoteLoadout { emotes = new[] { "wave", "scuba", "spike" }, skinHex = skin, shirtHex = shirt, shortsHex = "24345E" } };
            var c = new NetworkConfiguration { lobbyID = "L", matchID = "M", hostID = "a", localID = "a", sport = "tennis", venue = "resort", sets = 1, games = 1, seed = 5,
                participants = new[] { P("a", 0, false, "E8505B", "EEBB8F"), P("b", 1, true, "3F62CC", "965835") } };
            Send("net-look", "start", m => { m.sport = "tennis"; m.network = JsonUtility.ToJson(c); });
            for (int i = 0; i < 2400 && !(bridge.Ready && Object.FindFirstObjectByType<TennisGame>()); i++) yield return null;
            Assert.IsTrue(bridge.Ready);
            Assert.IsNull(HubWorld.Find(), "the match scene replaced the menu (no load behind it)");
            var game = Object.FindFirstObjectByType<TennisGame>(); Assert.IsNotNull(game);
            HeroTennisDriver Hero(TennisActor a) => a.GetComponentsInChildren<HeroTennisDriver>(true).Single();
            var near = Hero(game.Player); var far = Hero(game.Opponent);
            Assert.IsFalse(near.matchLook.female); Assert.IsTrue(far.matchLook.female, "the far hero follows the participant's body");
            Assert.IsTrue(near.matchLook.TryGetKitColour(MatchHeroLook.RoleShirt, out var nearShirt)); Assert.IsTrue(far.matchLook.TryGetKitColour(MatchHeroLook.RoleShirt, out var farShirt));
            Color Want(string hex) { ColorUtility.TryParseHtmlString("#" + hex, out var c0); var k = MatchHeroLook.KitTint(c0); return k; }
            Assert.That(Vector4.Distance(nearShirt, Want("E8505B")), Is.LessThan(.02f), "your shirt colour");
            Assert.That(Vector4.Distance(farShirt, Want("3F62CC")), Is.LessThan(.02f), "your friend's shirt colour");
            Assert.That(Vector4.Distance(far.matchLook.skinTone, HeroKit.Hex("965835")), Is.LessThan(.02f), "your friend's skin");
            Send("net-look", "end");
        }
    }
}
