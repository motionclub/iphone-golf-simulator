using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using GolfArcade.Hub;
using GolfArcade.Hub.Menu;
using GolfArcade.Tennis;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace GolfArcade.Game
{
    /// The `hub` session kind (PLAN_MenuHub_WalkableWorld §5 step 1): with a TV connected the menus are the walkable Plaza
    /// (Hub.unity) instead of the native TV menu. Same bridge as a match: the phone sends `start` with sport "hub", then the
    /// stick on the binary sample channel (target = x, aim = y, power = deflection, at the phone's 30–60 Hz) and buttons as
    /// commands. Unity reports where the player is.
    ///
    ///   phone -> Unity   start{sport:"hub", phoneOnly (no TV: the plaza above the phone's own controls, PLAY shut)}  hubMeet{mode:friend id} (joined their party: go to them)  hubArrive (the loading screen is off the TV: fly in)  hubToast{mode:text} (a message in the corner: an invite, a friend joining)  hubA  hubB  hubEmote{mode:id}  hubGo{mode:place|spot}  hubUse{mode:spot} (go there and use it)  hubLook{female,skin,skinHex,shirt,shorts,accent,racket}  end
    ///   Unity -> phone   loadProgress(0..1 scene)  buildProgress(0..1 plaza build)  ready  hubPlace(place)  hubZone(kind|id|label|detail)  hubAction(spot id)  hubState(place|zone|speed|inputAge ms p50|p95)
    public sealed partial class NativeSportsSession
    {
        /// A match start from a bay: load it behind the plaza (additive, hidden) and hand off with a dive into the bay screen.
        public partial class Message { public bool seamless; public string bay; public string remote; public bool phoneOnly; }
        /// The pointer menu (PLAN_PointerMenu.md): `menu` boots the plaza as the menu's backdrop; `leader` = this phone drives it (no
        /// party, or the party's leader); `soloLocked` = friends are here (solo modes lock); `screen` = the screen to open on (back from a
        /// match); `colour` = your party colour. A match start from the menu: `hold` = wait for START on the TV once it is built
        /// (solo / local), `menuLabel` = the mode's name for the loader.
        ///   phone -> Unity  menuBack  menuRecenter  menuGo{mode:screen}  menuPhone{mode:on|off, reason:title}  menuParty{leader, soloLocked}
        ///                   menuMirror{mode:screen|hover|x|y|shown} (a guest's TV)  menuRows{mode:"name|STATE;…"}  menuTag{remote:id, mode:tag}
        ///                   + the pointer on the binary sample channel (flags & 8: target/aim = x/y -1..1, power = shown, swing = Select held,
        ///                   swingStart = Select presses; flags & 16 = a finger, no TV)
        ///   Unity -> phone  menuScreen(id)  menuHover(id|label)  menuOpen(route id)  menuLook(slot|hex)  menuStart  menuCancel
        ///                   menuState(screen|hover|x|y|shown, the leader's, ≤15 Hz)
        public partial class Message { public bool menu, hold, soloLocked; public bool leader = true; public string screen, menuLabel; public int colour; }
        bool hubMode; HubWorld hub; float nextHubBeat, nextHubPose;
        /// The menu's own session and token: a match loading behind the menu takes over `session` / `token`, but the menu (and its
        /// pointer) keeps working until the hand-off.
        string menuSession; int menuToken; double lastMenuSample = -1; string menuReturn;
        readonly float[] hubAges = new float[64]; int hubAgeCount, hubAgeNext;
        /// True while the phone is driving the Plaza.
        public static bool HubActive { get; private set; }
        public HubWorld Hub => hub;

        void StartHub(Message m)
        {
            if (Active && hubMode && m.session == session) return;
            // a bay load was cancelled (standing up): the plaza never left, so take it over instead of reloading it
            var existing = adoptable; adoptable = null;
            if (existing && existing.Initialized && existing.gameObject.activeInHierarchy) { StopAllCoroutines(); loading = false; StartCoroutine(AdoptHub(m, existing)); return; }
            // a newer plaza start while an older one is still loading (the phone moved the plaza to a TV that just connected):
            // the newer one wins. Dropping it left that boot waiting until the player tapped Try again.
            if (loading && hubMode) { StopAllCoroutines(); loading = false; }
            if (loading) return;
            StartCoroutine(LoadHub(m));
        }
        /// A match start leaves the plaza (the match scene replaces Hub.unity; PLAN §5 makes this seamless later).
        void LeaveHub() { hubMode = false; HubActive = false; hub = null; }

        IEnumerator LoadHub(Message m)
        {
            loading = true; Ready = false; Active = true; hubMode = true; HubActive = true; multiplayerSession = false;
            session = m.session; token = m.token; lastSample = -1; target = 0; tennis = null; golf = null; hub = null;
            Left = m.left; Touch = true; touch = true;
            AudioListener.volume = MuteWhenAutomated.Volume(m.sound); Haptics.Enabled = m.haptics; Haptics.Warm();
            Time.timeScale = 1;
            InputRate.Stop();
            Application.targetFrameRate = m.external ? 60 : FrameRate.Target(m.fps, Screen.currentResolution.refreshRateRatio.value);
            QualitySettings.vSyncCount = 0;
            // What the plaza used to inherit from GolfGame.Awake while Golf was the build's first scene (Boot.unity is now): the screen
            // never sleeps in the menu, and Unity keeps running behind the phone's own screens. (Its shadows are HubArt.Lighting's.)
            Screen.sleepTimeout = SleepTimeout.NeverSleep; Application.runInBackground = true;
            // the phone stays upright either way: with a TV it is the controller, alone it shows the plaza above its controls
            Screen.orientation = ScreenOrientation.Portrait;
            HubWorld.StartFemale = m.female; HubWorld.DeferBuild = true; HubWorld.PhoneOnly = m.phoneOnly; HubWorld.MenuMode = m.menu;
            menuSession = m.session; menuToken = m.token; lastMenuSample = -1;
            var op = SceneManager.LoadSceneAsync("Hub");
            float nextProgress = 0;
            while (op != null && !op.isDone)
            {
                if (Time.realtimeSinceStartup >= nextProgress)
                {
                    nextProgress = Time.realtimeSinceStartup + .1f;
                    Emit("loadProgress", Mathf.Clamp01(op.progress / .9f).ToString("0.00", CultureInfo.InvariantCulture));
                }
                yield return null;
            }
            Emit("loadProgress", "1"); Emit("sceneReady", "Plaza loaded");
            hub = HubWorld.Find();
            HubWorld.DeferBuild = false;
            // the build a step a frame: the TV's loading bar (the phone's) moves with it
            if (hub && !hub.Initialized)
                for (var steps = hub.BuildSteps(m.female); steps.MoveNext();)
                { Emit("buildProgress", steps.Current.ToString("0.00", CultureInfo.InvariantCulture)); yield return null; }
            if (!hub || !hub.Initialized || !hub.Camera) { loading = false; Emit("error", "The plaza did not load."); yield break; }
            hub.PlaceChanged += p => { if (hubMode) Emit("hubPlace", p); };
            hub.ZoneChanged += _ => { if (hubMode) Emit("hubZone", ZoneMessage()); };
            hub.Interacted += id => { if (hubMode) Emit("hubAction", id); };
            hub.ApplyLook(m.female, m.skinHex, m.skin, m.shirt, m.shorts, m.accent, m.racket, m.back);
            WireMenu(hub, m);
            if (hub.Hud) { if (!string.IsNullOrEmpty(m.screen)) hub.Hud.Go(m.screen); else hub.PrepareArrival(); }   // back from a match: straight onto the menu
            else if (!string.IsNullOrEmpty(m.bay) && !m.phoneOnly) hub.SitAt(m.bay);   // back from a match: on the same bench (RETURN)
            else hub.PrepareArrival();   // a fresh boot: the first frame is the arrival's opening shot, held until the phone says go
            gameplayCamera = hub.Camera;
            paused = true;   // the point recorder stays off; the plaza itself never pauses (timeScale stays 1)
            yield return Present(m.external, "ready");
            loading = false;
            if (!Ready) yield break;
            hub.ArriveBy(Time.unscaledTime + 1.5f);   // (hubArrive normally comes first, once the loading screen has faded off the TV)
            Emit("hubPlace", hub.Place); Emit("hubZone", ZoneMessage());
            if (hub.Hud) Emit("menuScreen", hub.Hud.Screen);
        }

        /// The menu's events go to the phone; its first look comes from the start message.
        void WireMenu(HubWorld world, Message m)
        {
            var hud = world ? world.Hud : null; if (!hud) return;
            hud.Event -= MenuEvent; hud.Event += MenuEvent;
            hud.SetLook(m.shirt, m.shorts, m.accent, m.racket);
            hud.SetIdentity(m.playerName, m.colour, m.leader && m.soloLocked ? "HOST" : "");
            hud.SetParty(m.leader, m.soloLocked);
        }
        void MenuEvent(string type, string message) { if (hubMode || behindPlaza) Emit(type, message); }

        /// Menu commands that still come under the menu's session while a match loads behind it (the hold): the party, the rows,
        /// a guest's mirror, Back. False: not the menu's (or nothing is loading behind it).
        bool MenuDuringLoad(Message m)
        {
            if (!loading || !behindPlaza || !hub || !hub.Hud || m.session != menuSession || m.session == session) return false;
            if (MenuCommand(m)) return true;
            switch (m.action)
            {
                case "hubRemote": if (!string.IsNullOrEmpty(m.remote)) HubRemotes.For(hub).Receive(JsonUtility.FromJson<RemoteState>(m.remote)); return true;
                case "hubRoster": HubRemotes.For(hub).Roster((m.mode ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries)); return true;
            }
            return false;
        }
        bool MenuCommand(Message m)
        {
            var hud = hub ? hub.Hud : null; if (!hud) return false;
            switch (m.action)
            {
                case "menuBack": hud.Back(); return true;
                // ARROW FOCUS: the phone's arrow pad and Select (no cursor)
                case "menuMove": hud.Move(m.mode == "left" ? -1 : m.mode == "right" ? 1 : 0, m.mode == "up" ? 1 : m.mode == "down" ? -1 : 0); return true;
                case "menuSelect": hud.SelectFocused(); return true;
                case "menuRecenter": return true;
                case "menuGo": if (!string.IsNullOrEmpty(m.mode)) hud.Go(m.mode); return true;
                case "menuPhone": hud.SetPhonePanel(m.mode == "on", m.reason); return true;
                case "menuParty": hud.SetParty(m.leader, m.soloLocked); return true;
                case "menuRows": hud.SetRows(m.mode); return true;
                case "menuSetupState": hud.SetSetup(m.mode); return true;   // the TV's match setup, described by the phone (MenuSetup.swift)
                case "menuTag": hud.SetFriendTag(m.remote ?? "", m.mode); return true;
                case "menuMirror":
                {
                    var f = (m.mode ?? "").Split('|');
                    if (f.Length >= 5 && float.TryParse(f[2], NumberStyles.Float, CultureInfo.InvariantCulture, out var x) && float.TryParse(f[3], NumberStyles.Float, CultureInfo.InvariantCulture, out var y))
                        hud.Mirror(f[0], f[1], x, y, f[4] == "1");
                    return true;
                }
            }
            return false;
        }

        /// While a match loads behind the menu the session's Update stands down: the pointer still moves the menu (START, Back).
        void MenuLoadingUpdate()
        {
            if (!behindPlaza || !hub || !hub.Hud) return;
            Sample latest = default; bool have = false; double now = SportsClock();
            for (int i = 0; i < 64; i++)
            {
                if (SportsPollSample(out var sample) == 0) break;
                if (!sample.menuPointer || !AcceptSample(sample, menuToken, lastMenuSample, now)) continue;
                lastMenuSample = sample.time; latest = sample; have = true;
            }
            if (have) hub.Hud.Pointer(latest.target, latest.aim, latest.power > 0, latest.swing != 0, latest.swingStart, latest.touch);
        }

        /// The plaza is still loaded (a bay load was cancelled): take it over again without reloading it.
        IEnumerator AdoptHub(Message m, HubWorld world)
        {
            loading = true; Ready = false; Active = true; hubMode = true; HubActive = true; multiplayerSession = false;
            session = m.session; token = m.token; lastSample = -1; tennis = null; golf = null; hub = world; Time.timeScale = 1;
            if (world.gameObject.scene.IsValid()) SceneManager.SetActiveScene(world.gameObject.scene);
            menuSession = m.session; menuToken = m.token; lastMenuSample = -1;
            if (world.Hud) world.MatchLoading(-1);
            else { if (!string.IsNullOrEmpty(m.bay)) world.SitAt(m.bay); else world.LeaveStation(); world.BayLoading(-1); }
            world.ApplyLook(m.female, m.skinHex, m.skin, m.shirt, m.shorts, m.accent, m.racket, m.back);
            WireMenu(world, m);
            // a cancelled load: back on the list it was started from
            if (world.Hud) world.Hud.Go(!string.IsNullOrEmpty(m.screen) ? m.screen : menuReturn ?? MenuHud.Home);
            gameplayCamera = world.Camera; paused = true;
            yield return Present(m.external, "ready");
            loading = false;
            Emit("hubPlace", world.Place); Emit("hubZone", ZoneMessage());
            if (world.Hud) Emit("menuScreen", world.Hud.Screen);
        }

        // ================================================================== a match loading behind the plaza (PLAN §5)
        bool behindPlaza; AsyncOperation behindOp; HiddenMatch hidden; bool cancelBehind; HubWorld adoptable;
        readonly List<ResourceRequest> preloads = new List<ResourceRequest>();
        /// Proof: the plaza's frame times while the match loaded behind it (ms), and the memory peak.
        public static readonly List<float> BehindFrameMs = new List<float>();
        public static long BehindPeakBytes;
        public static readonly List<string> BehindSlowFrames = new List<string>();

        /// Load's scene request: the normal single-scene load, or, from a bay with the plaza up, an additive load held behind it.
        AsyncOperation BeginSceneLoad(Message m)
        {
            string scene = SceneFor(m.sport);
            var world = HubWorld.Find();
            behindPlaza = m.seamless && world && world.Initialized && world.gameObject.activeInHierarchy;
            if (!behindPlaza) return SceneManager.LoadSceneAsync(scene);
            hub = world; cancelBehind = false; BehindFrameMs.Clear(); BehindPeakBytes = 0; BehindSlowFrames.Clear();
            TennisGame.SliceInit = true;
            Application.backgroundLoadingPriority = ThreadPriority.Low;   // asset integration stays a few ms per frame
            // the big assets the match's build asks for synchronously: fetch them now, off the main thread
            preloads.Clear();
            foreach (var path in m.sport == "tennis"
                ? new[] { "Tennis/TropicalV3/TropicalTennisResort", "Tennis/Island/TennisIsland", "Tennis/Customization/PlayerMale", "Tennis/Customization/PlayerFemale", "Tennis/Rendering/TennisPost" }
                : new string[0])
                preloads.Add(Resources.LoadAsync(path));
            hidden = gameObject.AddComponent<HiddenMatch>(); hidden.Begin(scene, world);
            var op = SceneManager.LoadSceneAsync(scene, LoadSceneMode.Additive);
            op.allowSceneActivation = false; behindOp = op;
            if (world.Hud) { menuReturn = world.Hud.Screen == MenuHud.Loading ? menuReturn : world.Hud.Screen; world.Hud.BeginLoading(m.sport, m.menuLabel, m.hold); }
            world.MatchLoading(0);
            return op;
        }
        void SceneLoadTick(AsyncOperation op)
        {
            if (!behindPlaza || op != behindOp) return;
            float assets = 0; foreach (var r in preloads) assets += r.isDone ? 1 : r.progress; assets = preloads.Count > 0 ? assets / preloads.Count : 1;
            if (hub) hub.MatchLoading(.6f * Mathf.Min(Mathf.Clamp01(op.progress / .9f), assets));
            // activate once the scene's data and the preloads are in (the build itself is sliced across frames)
            if (op.progress >= .9f && assets >= 1 && !cancelBehind) op.allowSceneActivation = true;
        }

        /// The match is built and hidden: (solo) go now — the camera dives into the bay screen, the match takes the TV, the plaza unloads.
        IEnumerator HandOff(Message m)
        {
            Emit("matchReady", m.bay ?? "");
            if (hub && hub.Hud)
            {
                // the menu: START lights up once the match is built (solo / local: the player starts it; online starts itself), READY! pops,
                // the screen fades to the match
                hub.MatchLoading(1); hub.Hud.ResetStart(); hub.Hud.MatchBuilt();
                if (m.hold) while (!hub.Hud.StartPressed) yield return null;
                hub.Hud.ShowReady();
                for (float t = 0; t < .65f; t += Time.unscaledDeltaTime) yield return null;
                yield return hub.FadeOut(.3f);
            }
            else if (hub) { hub.BayLoading(1); yield return hub.Dive(.55f); }
            TennisGame.SliceInit = false; Application.backgroundLoadingPriority = ThreadPriority.Normal;
            var plaza = hub ? hub.gameObject.scene : default;
            if (hub) hub.gameObject.SetActive(false);
            if (hidden) hidden.Reveal();
            preloads.Clear();
            yield return Present(m.external, "ready");
            behindPlaza = false; hub = null; HubActive = false;
            // the plaza's scene goes, and with it its assets (an additive unload leaves them in memory until asked)
            if (plaza.IsValid() && plaza.isLoaded) { var unload = SceneManager.UnloadSceneAsync(plaza); if (unload != null) yield return unload; Resources.UnloadUnusedAssets(); }
        }

        /// Hub commands, and "end" for a match that is still loading behind the plaza (standing up from the bench: CANCEL).
        bool HubIntercept(Message m)
        {
            if (hubMode && HubCommand(m)) return true;
            if (behindPlaza && loading && m.action == "end") { CancelBehind(); return true; }
            return false;
        }
        void CancelBehind()
        {
            StopAllCoroutines(); loading = false; Ready = false; Active = false; Left = false; Time.timeScale = 1;
            cancelBehind = true; StartCoroutine(UnloadBehind());
        }
        IEnumerator UnloadBehind()
        {
            var op = behindOp; if (op != null) { op.allowSceneActivation = true; while (!op.isDone) yield return null; }
            var plaza = HubWorld.Find(); adoptable = plaza;
            if (plaza && plaza.gameObject.scene.IsValid()) SceneManager.SetActiveScene(plaza.gameObject.scene);
            for (int i = 0; i < SceneManager.sceneCount; i++)
            {
                var s = SceneManager.GetSceneAt(i);
                if (s.isLoaded && (!plaza || s != plaza.gameObject.scene) && (s.name == "Tennis" || s.name == "Golf" || s.name == "Bowling")) SceneManager.UnloadSceneAsync(s);
            }
            if (hidden) hidden.Abandon();
            TennisGame.SliceInit = false; Application.backgroundLoadingPriority = ThreadPriority.Normal;
            preloads.Clear(); behindOp = null; behindPlaza = false; tennis = null; golf = null; bowling = null;
            if (plaza) plaza.MatchLoading(-1);
        }

        string ZoneMessage()
        {
            if (!hub) return "";
            if (hub.ZoneSpot != null) { var s = hub.ZoneSpot; return $"{(s.kind == HubLayout.Kind.Bay ? "bay" : "station")}|{s.id}|{s.label}|{s.detail}"; }
            if (hub.ZoneDoor != null) { var d = hub.ZoneDoor; return $"door|{d.id}|{d.label}|{(d.locked ? "Coming soon" : HubWorld.DoorClosed(d) ? "TV needed" : "Walk in")}"; }
            return "";
        }

        /// Hub commands; false lets the shared handler take it (sound, haptics, display).
        bool HubCommand(Message m)
        {
            if (MenuCommand(m)) return true;
            switch (m.action)
            {
                case "end":
                    if (hub && hub.Player) hub.Player.SetStick(0, 0, 0);
                    StopAllCoroutines(); loading = false; Ready = false; LeaveHub(); Active = false; Left = false;
                    return true;
                case "pause": case "resume": return true;   // the plaza has no pause
                case "hubA": if (hub) hub.Interact(); return true;
                case "hubB": if (hub) hub.LeaveStation(); return true;
                case "hubArrive": if (hub) hub.StartArrival(); return true;
                case "hubToast": if (hub && !string.IsNullOrEmpty(m.mode)) hub.ShowToast(m.mode); return true;
                case "hubUse": if (hub && !string.IsNullOrEmpty(m.mode)) hub.GoTo(m.mode, true); return true;
                case "hubGo": if (hub && !string.IsNullOrEmpty(m.mode)) hub.GoTo(m.mode); return true;
                case "hubEmote":
                    if (hub && hub.Player && TennisEmotes.TryClip(m.mode, out var clip))
                        Emit("emoteResult", hub.Player.PlayEmote(clip.ToString()) ? TennisEmotes.Name(m.mode) : "Stand still to emote");
                    return true;
                case "hubLook":
                    if (hub) hub.ApplyLook(m.female, m.skinHex, m.skin, m.shirt, m.shorts, m.accent, m.racket, m.back);
                    if (hub && hub.Hud) hub.Hud.SetLook(m.shirt, m.shorts, m.accent, m.racket);
                    return true;
                // party (PLAN §4): a friend's state, the member list, Call party
                case "hubRemote": if (hub && !string.IsNullOrEmpty(m.remote)) HubRemotes.For(hub).Receive(JsonUtility.FromJson<RemoteState>(m.remote)); return true;
                case "hubRoster": if (hub) HubRemotes.For(hub).Roster((m.mode ?? "").Split(new[] { ',' }, System.StringSplitOptions.RemoveEmptyEntries)); return true;
                case "hubCall": if (hub) HubRemotes.For(hub).Call(m.mode); return true;
                case "hubGather": if (hub) hub.GatherParty(m.mode); return true;
                case "hubChat": if (hub) HubRemotes.For(hub).Chat(m.remote, m.mode); return true;
                case "hubMeet": if (hub && HubRemotes.For(hub).TryGetLast(m.mode ?? "", out var meetPlace, out var meetAt)) hub.Meet(meetPlace, meetAt); return true;
            }
            return false;
        }

        void HubUpdate()
        {
            if (!hub || !hub.Player) return;
            Sample latest = default; bool have = false; double now = SportsClock();
            for (int i = 0; i < 64; i++)
            {
                if (SportsPollSample(out var sample) == 0) break;
                if (!AcceptSample(sample, token, lastSample, now)) continue;
                lastSample = sample.time; latest = sample; have = true;
            }
            if (have)
            {
                // the pointer menu: the phone's pointer moves the TV's cursor; the walkable plaza: the stick walks the hero
                if (hub.Hud) { if (latest.menuPointer) hub.Hud.Pointer(latest.target, latest.aim, latest.power > 0, latest.swing != 0, latest.swingStart, latest.touch); }
                else hub.Player.SetStick(latest.target, latest.aim, latest.power, latest.time);
                hubAges[hubAgeNext] = (float)(now - latest.time); hubAgeNext = (hubAgeNext + 1) % hubAges.Length; hubAgeCount = Mathf.Min(hubAgeCount + 1, hubAges.Length);
            }
            // a phone that stops talking (backgrounded, out of range) must not leave the hero running
            else if (lastSample > 0 && now - lastSample > .4 && hub.Player.StickMagnitude > 0) hub.Player.SetStick(0, 0, 0);
            // my pose for the party (the phone relays it to friends at ~10 Hz; the menu's line-up only needs it now and then for the
            // emotes): place|x|y|z|yaw|speed|seated bay|emote
            if (Time.unscaledTime >= nextHubPose)
            {
                nextHubPose = Time.unscaledTime + (hub.Hud ? 1f : .1f);
                var pp = hub.Player.transform.position;
                string seat = hub.SeatedInBay ? hub.Station.id : "";
                string emote = hub.Player.hero && hub.Player.hero.Playing != null ? hub.Player.hero.Playing : "";
                Emit("hubPose", string.Format(CultureInfo.InvariantCulture, "{0}|{1:0.000}|{2:0.000}|{3:0.000}|{4:0.0}|{5:0.00}|{6}|{7}", hub.Place, pp.x, pp.y, pp.z, hub.Player.Yaw, hub.Player.Speed, seat, emote));
            }
            if (Time.unscaledTime >= nextHubBeat)
            {
                nextHubBeat = Time.unscaledTime + .25f;
                Emit("hubState", string.Format(CultureInfo.InvariantCulture, "{0}|{1}|{2:0.00}|{3:0}|{4:0}", hub.Place, hub.ZoneId, hub.Player.Speed, AgePercentile(.5f) * 1000, AgePercentile(.95f) * 1000));
            }
        }

        readonly float[] ageScratch = new float[64];
        float AgePercentile(float p)
        {
            if (hubAgeCount == 0) return 0;
            System.Array.Copy(hubAges, ageScratch, hubAgeCount); System.Array.Sort(ageScratch, 0, hubAgeCount);
            return ageScratch[Mathf.Clamp(Mathf.RoundToInt(p * (hubAgeCount - 1)), 0, hubAgeCount - 1)];
        }
    }
}

namespace GolfArcade.Game
{
    /// Keeps a match scene invisible and silent while it loads and builds behind the plaza: its cameras, lights, canvases,
    /// post-processing volumes and audio listeners are held off (state recorded), the plaza's lighting settings stay in force (the
    /// match's own are remembered for the hand-off), and the plaza's frame times and memory are recorded for the gates.
    sealed class HiddenMatch : MonoBehaviour
    {
        string sceneName; Scene scene; bool loaded; HubWorld plaza;
        Snapshot hubLight, matchLight; bool sawMatchLight;
        readonly List<(Behaviour b, bool was)> held = new List<(Behaviour, bool)>();
        readonly HashSet<Behaviour> seen = new HashSet<Behaviour>();

        public void Begin(string name, HubWorld world)
        {
            sceneName = name; plaza = world; hubLight = Snapshot.Take();
            AudioListener.pause = true;
            SceneManager.sceneLoaded += Loaded;
        }
        void OnDestroy() { SceneManager.sceneLoaded -= Loaded; }
        void Loaded(Scene s, LoadSceneMode mode)
        {
            if (s.name != sceneName || mode != LoadSceneMode.Additive) return;
            scene = s; loaded = true;
            // objects the match creates in Start must land in its own scene, not the plaza's (which unloads later)
            SceneManager.SetActiveScene(s);
            Hold();
        }
        void LateUpdate()
        {
            if (plaza && plaza.gameObject.activeInHierarchy)
            {
                NativeSportsSession.BehindFrameMs.Add(Time.unscaledDeltaTime * 1000);
                if (Time.unscaledDeltaTime > .05f)
                {
                    var g = FindFirstObjectByType<GolfArcade.Tennis.TennisGame>();
                    NativeSportsSession.BehindSlowFrames.Add($"{Time.unscaledDeltaTime * 1000:0}ms loaded={loaded} initProgress={(g ? g.InitProgress : -1):0.00} initialized={(g && g.Initialized)} frame={Time.frameCount}");
                }
                NativeSportsSession.BehindPeakBytes = System.Math.Max(NativeSportsSession.BehindPeakBytes, UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong());
            }
            if (!loaded) return;
            Hold();
            // the match sets its sky / ambient / reflections in its build: remember them, keep the plaza's on screen
            var now = Snapshot.Take();
            if (!now.Same(hubLight)) { matchLight = now; sawMatchLight = true; hubLight.Apply(); }
            var game = FindFirstObjectByType<GolfArcade.Tennis.TennisGame>();
            if (plaza && game && !game.Initialized) plaza.MatchLoading(.6f + .4f * game.InitProgress);
        }
        void Hold()
        {
            if (!scene.IsValid()) return;
            foreach (var root in scene.GetRootGameObjects())
            {
                foreach (var c in root.GetComponentsInChildren<Camera>(true)) Keep(c);
                foreach (var c in root.GetComponentsInChildren<Light>(true)) Keep(c);
                foreach (var c in root.GetComponentsInChildren<Canvas>(true)) Keep(c);
                foreach (var c in root.GetComponentsInChildren<Volume>(true)) Keep(c);
                foreach (var c in root.GetComponentsInChildren<AudioListener>(true)) Keep(c);
            }
        }
        void Keep(Behaviour b)
        {
            if (!b || !seen.Add(b)) { if (b && b.enabled && held.Exists(h => h.b == b)) b.enabled = false; return; }
            held.Add((b, b.enabled)); b.enabled = false;
        }
        /// Hand-off: the match's components and lighting come back exactly as it set them.
        public void Reveal()
        {
            foreach (var (b, was) in held) if (b) b.enabled = was;
            if (sawMatchLight) matchLight.Apply();
            AudioListener.pause = false; Destroy(this);
        }
        /// Cancelled: the match scene is being unloaded; the plaza keeps its own settings.
        public void Abandon() { hubLight.Apply(); AudioListener.pause = false; Destroy(this); }

        struct Snapshot
        {
            AmbientMode mode; Color sky, equator, ground, flat; float ambientIntensity; SphericalHarmonicsL2 probe; Material skybox; Light sun;
            bool fog; Color fogColor; FogMode fogMode; float fogDensity, fogStart, fogEnd;
            DefaultReflectionMode reflectionMode; Texture reflection; float reflectionIntensity; int bounces; Color subtractive;
            public static Snapshot Take() => new Snapshot
            {
                mode = RenderSettings.ambientMode, sky = RenderSettings.ambientSkyColor, equator = RenderSettings.ambientEquatorColor, ground = RenderSettings.ambientGroundColor,
                flat = RenderSettings.ambientLight, ambientIntensity = RenderSettings.ambientIntensity, probe = RenderSettings.ambientProbe, skybox = RenderSettings.skybox, sun = RenderSettings.sun,
                fog = RenderSettings.fog, fogColor = RenderSettings.fogColor, fogMode = RenderSettings.fogMode, fogDensity = RenderSettings.fogDensity,
                fogStart = RenderSettings.fogStartDistance, fogEnd = RenderSettings.fogEndDistance, reflectionMode = RenderSettings.defaultReflectionMode,
                reflection = RenderSettings.customReflectionTexture, reflectionIntensity = RenderSettings.reflectionIntensity, bounces = RenderSettings.reflectionBounces,
                subtractive = RenderSettings.subtractiveShadowColor,
            };
            public bool Same(Snapshot o) => mode == o.mode && sky == o.sky && equator == o.equator && ground == o.ground && flat == o.flat && skybox == o.skybox && sun == o.sun
                && fog == o.fog && fogColor == o.fogColor && reflectionMode == o.reflectionMode && reflection == o.reflection && Mathf.Approximately(ambientIntensity, o.ambientIntensity)
                && Mathf.Approximately(reflectionIntensity, o.reflectionIntensity);
            public void Apply()
            {
                RenderSettings.ambientMode = mode; RenderSettings.ambientSkyColor = sky; RenderSettings.ambientEquatorColor = equator; RenderSettings.ambientGroundColor = ground;
                RenderSettings.ambientLight = flat; RenderSettings.ambientIntensity = ambientIntensity; RenderSettings.ambientProbe = probe; RenderSettings.skybox = skybox; RenderSettings.sun = sun;
                RenderSettings.fog = fog; RenderSettings.fogColor = fogColor; RenderSettings.fogMode = fogMode; RenderSettings.fogDensity = fogDensity;
                RenderSettings.fogStartDistance = fogStart; RenderSettings.fogEndDistance = fogEnd; RenderSettings.defaultReflectionMode = reflectionMode;
                RenderSettings.customReflectionTexture = reflection; RenderSettings.reflectionIntensity = reflectionIntensity; RenderSettings.reflectionBounces = bounces;
                RenderSettings.subtractiveShadowColor = subtractive;
            }
        }
    }
}
