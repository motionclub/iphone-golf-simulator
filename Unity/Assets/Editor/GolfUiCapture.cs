#if UNITY_EDITOR
using System;
using System.Collections;
using System.IO;
using System.Reflection;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Shot;
using GolfArcade.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Batch capture of the golf aim HUD at the tee, from the normal gameplay camera: the mock-up's moment
    /// (hole 1, address) at 1920x1080, then the power meter part-filled. Run with
    /// -executeMethod GolfArcade.EditorTools.GolfUiCapture.Run and GOLF_UI_OUT=<dir>, GOLF_UI_TAG=before|after.
    [InitializeOnLoad]
    public static class GolfUiCapture
    {
        const string Key = "GolfUiCapture";
        static IEnumerator script; static int last = -1; static string output, tag;
        static GolfGame game; static Camera cam; static CameraRig rig;
        static readonly BindingFlags P = BindingFlags.Instance | BindingFlags.NonPublic;

        static GolfUiCapture() { EditorApplication.update += Tick; EditorApplication.update += TickTennis; }

        /// Loads Tennis once and logs the theme it ends up with (GOLF_UI_OUT for the marker file).
        public static void RunTennis()
        {
            output = Environment.GetEnvironmentVariable("GOLF_UI_OUT"); Directory.CreateDirectory(output);
            SessionState.SetString(Key + "out", output); SessionState.SetBool(Key + "tennis", true);
            EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");
            EditorApplication.isPlaying = true;
        }

        static int tennisFrames;
        static void TickTennis()
        {
            if (!SessionState.GetBool(Key + "tennis", false) || !EditorApplication.isPlaying || last == Time.frameCount) return;
            last = Time.frameCount;
            if (++tennisFrames < 90) return;
            Debug.Log($"[GolfUiCapture] tennis scene theme {ThemeService.Current.name} (sport {ThemeService.Sport})");
            File.WriteAllText(Path.Combine(SessionState.GetString(Key + "out", "."), "tennis_theme.txt"), ThemeService.Current.name);
            SessionState.SetBool(Key + "tennis", false); Finish(0);
        }

        /// Clean golf frames with no HUD (clear sky, calm), for laying UI mock-ups over: hole 1 and hole 7 at the tee.
        public static void RunPlates()
        {
            output = Environment.GetEnvironmentVariable("GOLF_UI_OUT"); tag = "plate";
            Directory.CreateDirectory(output);
            SessionState.SetString(Key + "out", output); SessionState.SetString(Key + "tag", tag);
            SessionState.SetBool(Key + "plates", true); SessionState.SetBool(Key + "results", false); SessionState.SetBool(Key, true);
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            EditorApplication.isPlaying = true;
        }

        /// The golf result screens as the game builds them (strike words, landings, shot result, hole-out, round card, events).
        public static void RunResults()
        {
            output = Environment.GetEnvironmentVariable("GOLF_UI_OUT"); tag = "res";
            Directory.CreateDirectory(output);
            SessionState.SetString(Key + "out", output); SessionState.SetString(Key + "tag", tag);
            SessionState.SetBool(Key + "plates", false); SessionState.SetBool(Key + "results", true); SessionState.SetBool(Key, true);
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            EditorApplication.isPlaying = true;
        }

        static IEnumerator Results()
        {
            Time.captureFramerate = 30; game.InstantReplays = false;
            game.PrepareNativeAddress();
            for (int i = 0; i < 40; i++) yield return null;
            typeof(GolfGame).GetMethod("ChangeWeather", P).Invoke(game, new object[] { Weather.Clear });
            game.SetWind(Wind.Calm); var hud = game.TutorialHud; hud.SetConditions(null);
            for (int i = 0; i < 20; i++) yield return null;
            var broadcast = Object.FindFirstObjectByType<GolfShotHud>(); broadcast.gameObject.SetActive(false);
            cam.aspect = 16f / 9f; Frame();
            // the HUD's own canvas is an overlay; draw it through the camera so the capture sees it
            var hudCanvas = hud.GetComponent<Canvas>();
            hudCanvas.renderMode = RenderMode.ScreenSpaceCamera; hudCanvas.worldCamera = cam; hudCanvas.planeDistance = 1f;
            for (int i = 0; i < 4; i++) yield return null;

            var strikeField = typeof(Hud).GetField("strikePopup", P); var calloutField = typeof(Hud).GetField("callout", P);
            void ClearWords() { ((StrikePopup)strikeField.GetValue(hud))?.Hide(); var c = (Callout)calloutField.GetValue(hud); if (c) c.gameObject.SetActive(false); hud.HideLanding(); }
            foreach (var (word, color, shape) in new[] { ("PERFECT!", UiKit.ArcadeYellow, "DRAW"), ("GREAT!", UiKit.Hex("5CD66B"), "FADE"), ("GOOD", Color.white, "STRAIGHT"), ("THIN", UiKit.Hex("FF9A4A"), "SLICE") })
            {
                ClearWords(); hud.ShowStrike(word, color, shape); for (int i = 0; i < 12; i++) yield return null; Capture("strike_" + word.TrimEnd('!')); ClearWords();
            }
            hud.ShowCallout("Bounty! +50", GolfShotHud.Gold); for (int i = 0; i < 12; i++) yield return null; Capture("callout"); ClearWords();
            foreach (var (kind, word, detail, stats) in new[] {
                (LandingBadge.Kind.Fairway, "Fairway", "121 yd to pin", "Carry 224 yd · Total 248 yd"), (LandingBadge.Kind.Green, "Green", "14 ft to pin", "Carry 238 yd · Total 261 yd"),
                (LandingBadge.Kind.Rough, "Rough", "168 yd to pin", "Carry 201 yd · Total 207 yd"), (LandingBadge.Kind.Bunker, "Bunker", "34 yd to pin", "Carry 169 yd"),
                (LandingBadge.Kind.Water, "Water", "+1 penalty", "Carry 232 yd"), (LandingBadge.Kind.OutOfBounds, "Out of bounds", "+1 penalty", "Carry 251 yd") })
            {
                hud.ShowLanding(kind, word, detail, stats, 3f); for (int i = 0; i < 16; i++) yield return null; Capture("landing_" + kind);
            }
            hud.HideLanding();
            hud.ShowEvent("Gust!", "Wind now 12 mph · left to right", UiKit.Hex("3FA9F5"), "wind", 3f); for (int i = 0; i < 16; i++) yield return null; Capture("event");
            hud.HideLanding();

            var shot = Object.FindFirstObjectByType<ShotResultPanel>(FindObjectsInactive.Include) ?? ShotResultPanel.Create(game.transform, cam);
            shot.ShowGolf("Adnan", "Fairway", 224, 24, 41, 121, false, false);
            for (int i = 0; i < 40; i++) yield return null; Capture("shot_result");
            shot.gameObject.SetActive(false);

            var holeOut = Object.FindFirstObjectByType<HoleOutCard>(FindObjectsInactive.Include) ?? HoleOutCard.Create(game.transform, cam);
            var tiles = new HoleOutCard.Tile[5]; int[] pars = { 4, 4, 5, 3, 3 };
            for (int i = 0; i < 5; i++) tiles[i] = new HoleOutCard.Tile { Ordinal = i + 1, Par = pars[i], Strokes = i == 0 ? 4 : i == 1 ? 5 : null, Current = i == 1 };
            tiles[0].Current = false;
            holeOut.Show(new HoleOutCard.Data { Score = "BOGEY", Eyebrow = "HOLE 2 OF 5  ·  NEEDLE", Detail = "PAR 4", Strokes = 5, Par = 4, HoleToPar = 1, ToPar = 1, Thru = 2, Tiles = tiles, NextLabel = "NEXT HOLE", NextDetail = "3 · THE STEPS · PAR 5 · 512 YD", Emotes = new[] { "Wave", "Scuba", "Spike" } }, () => { }, _ => true);
            for (int i = 0; i < 50; i++) yield return null; Capture("holeout_bogey");
            tiles[1].Strokes = 3;
            holeOut.Show(new HoleOutCard.Data { Score = "BIRDIE", Eyebrow = "HOLE 2 OF 5  ·  NEEDLE", Detail = "PAR 4", Strokes = 3, Par = 4, HoleToPar = -1, ToPar = -1, Thru = 2, Tiles = tiles, NextLabel = "NEXT HOLE", NextDetail = "3 · THE STEPS · PAR 5 · 512 YD", Emotes = new[] { "Wave", "Scuba", "Spike" } }, () => { }, _ => true);
            for (int i = 0; i < 50; i++) yield return null; Capture("holeout_birdie");
            holeOut.Hide();

            var card = new RoundCard(hud.IntroLayer, "Round complete", null, new[] { 1, 2, 3, 4, 5 }, pars, new int?[] { 4, 3, 5, 3, 2 }, 17, -2,
                new[] { new RoundCard.Highlight { Icon = "star", Title = "Perfect strikes", Value = "3" }, new RoundCard.Highlight { Icon = "flag", Title = "Longest drive", Value = "268 yd" }, new RoundCard.Highlight { Icon = "trophy", Title = "Fairways hit", Value = "4 / 5" } }, false);
            for (int i = 0; i < 30; i++) yield return null; Capture("roundcard");
            card.Destroy();

            // the phone steering the round card's buttons: lit ring on the way on, the stick down, then right, then a tap
            int pressed = -1;
            var nav = new RoundCard(hud.IntroLayer, "Round complete", null, new[] { 1, 2, 3, 4, 5 }, pars, new int?[] { 4, 3, 5, 3, 2 }, 17, -2,
                new[] { new RoundCard.Highlight { Icon = "star", Title = "Perfect strikes", Value = "3" } }, true);
            nav.NextHole.Pressed = () => pressed = 0; nav.PlayAgain.Pressed = () => pressed = 1; nav.Menu.Pressed = () => pressed = 2;
            for (int i = 0; i < 30; i++) yield return null; Capture("nav_0_default");
            MenuFocus.Move(.1f, -1f); for (int i = 0; i < 8; i++) yield return null; Capture("nav_1_stick_down");
            MenuFocus.Move(0, 0); MenuFocus.Move(1f, 0f); for (int i = 0; i < 8; i++) yield return null; Capture("nav_2_stick_right");
            Debug.Log($"[MENUFOCUS] wants={MenuFocus.Wants}");
            foreach (var fi in Object.FindObjectsByType<FocusItem>(FindObjectsSortMode.None)) Debug.Log($"[MENUFOCUS] item {fi.name} default={fi.Default} pos={fi.transform.position}");
            Debug.Log("[MENUFOCUS] focus=" + typeof(MenuFocus).GetField("focus", P).GetValue(Object.FindFirstObjectByType<MenuFocus>()));
            MenuFocus.Select(); yield return null;
            Debug.Log($"[MENUFOCUS] tapped -> button {pressed} (2 = main menu)");
            nav.Destroy();
        }

        static IEnumerator Plates()
        {
            Time.captureFramerate = 30; game.InstantReplays = false;
            game.PrepareNativeAddress();
            for (int i = 0; i < 40; i++) yield return null;
            typeof(GolfGame).GetMethod("ChangeWeather", P).Invoke(game, new object[] { Weather.Clear });
            game.SetWind(Wind.Calm); game.TutorialHud.SetConditions(null);
            for (int i = 0; i < 20; i++) yield return null;
            var broadcast = Object.FindFirstObjectByType<GolfShotHud>(); broadcast.gameObject.SetActive(false);
            cam.aspect = 16f / 9f; Frame(); for (int i = 0; i < 4; i++) yield return null;
            Capture("hole1");
            game.JumpToHole(7); game.DropBall(game.CurrentHole.Tee); for (int i = 0; i < 12; i++) yield return null;
            broadcast.gameObject.SetActive(false); cam.aspect = 16f / 9f; Frame(); for (int i = 0; i < 4; i++) yield return null;
            Capture("hole7");
        }

        public static void Run()
        {
            SessionState.SetBool(Key + "plates", false); SessionState.SetBool(Key + "results", false);
            output = Environment.GetEnvironmentVariable("GOLF_UI_OUT");
            tag = Environment.GetEnvironmentVariable("GOLF_UI_TAG") ?? "shot";
            Directory.CreateDirectory(output);
            SessionState.SetString(Key + "out", output); SessionState.SetString(Key + "tag", tag); SessionState.SetBool(Key, true);
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Key, false) || !EditorApplication.isPlaying || last == Time.frameCount) return;
            last = Time.frameCount;
            try
            {
                if (script == null)
                {
                    game = Object.FindFirstObjectByType<GolfGame>();
                    if (!game || game.Swing == null) return;
                    output = SessionState.GetString(Key + "out", ""); tag = SessionState.GetString(Key + "tag", "shot");
                    cam = game.GameplayCamera; rig = cam.GetComponent<CameraRig>();
                    script = SessionState.GetBool(Key + "results", false) ? Results() : SessionState.GetBool(Key + "plates", false) ? Plates() : Shoot();
                }
                if (!script.MoveNext()) Finish(0);
            }
            catch (Exception e) { Debug.LogException(e); File.WriteAllText(Path.Combine(output, "error.txt"), e.ToString()); Finish(1); }
        }

        static void Finish(int code) { SessionState.SetBool(Key, false); Time.captureFramerate = 0; EditorApplication.Exit(code); }

        static void Capture(string name, int width = 1920, int height = 1080)
        {
            var old = cam.targetTexture; float aspect = cam.aspect; var active = RenderTexture.active;
            var rt = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default, 4);
            var tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            try
            {
                cam.targetTexture = rt; cam.aspect = (float)width / height;
                foreach (var hud in Object.FindObjectsByType<GolfShotHud>(FindObjectsSortMode.None)) hud.RefreshLayout();
                OffscreenSize.Override = new Vector2Int(width, height);
                foreach (var c in Object.FindObjectsByType<HoleOutCard>(FindObjectsSortMode.None)) c.RefreshLayout();
                foreach (var c in Object.FindObjectsByType<ShotResultPanel>(FindObjectsSortMode.None)) c.SendMessage("LateUpdate", SendMessageOptions.DontRequireReceiver);
                Canvas.ForceUpdateCanvases(); cam.Render();
                RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, width, height), 0, 0); tex.Apply();
                File.WriteAllBytes(Path.Combine(output, $"{tag}_{name}.png"), tex.EncodeToPNG());
            }
            finally { OffscreenSize.Override = null; cam.targetTexture = old; cam.aspect = aspect; RenderTexture.active = active; Object.DestroyImmediate(tex); RenderTexture.ReleaseTemporary(rt); }
        }

        static void Frame() { typeof(GolfGame).GetMethod("FrameAim", P).Invoke(game, null); rig.SnapNext(); rig.ApplyFrame(); }

        // The game's own per-frame pin call hides the marker while the capture is idle; draw it for the frame (the map's world is in yards).
        static void Pin(Hud hud)
        {
            var ball = hud.Map.Ball; var pin = hud.Map.Pin; ball.y = pin.y = 0;
            hud.SetPinMarker(cam, hud.Map.Pin + Vector3.up * 3.2f, "PIN  " + (pin - ball).magnitude.ToString("F0") + " YD");
            Canvas.ForceUpdateCanvases();
        }

        static IEnumerator Shoot()
        {
            Time.captureFramerate = 30; game.InstantReplays = false;
            game.PrepareNativeAddress();
            for (int i = 0; i < 40; i++) yield return null;
            cam.aspect = 16f / 9f; Frame(); for (int i = 0; i < 4; i++) yield return null;
            Debug.Log($"[GolfUiCapture] theme {ThemeService.Current.name}");
            // the round's conditions as drawn on the first screenshot, then the mock-up's moment: clear sky, calm wind
            var hud = game.TutorialHud;
            Pin(hud); Capture("tee_conditions");
            typeof(GolfGame).GetMethod("ChangeWeather", P).Invoke(game, new object[] { Weather.Clear });
            game.SetWind(Wind.Calm); hud.SetConditions(null);
            for (int i = 0; i < 20; i++) yield return null;
            Pin(hud); Capture("tee");
            foreach (var (mph, deg) in new[] { (14.0, 135.0), (6.0, 20.0) })
            {
                game.SetWind(new Wind(mph, deg)); for (int i = 0; i < 12; i++) yield return null;
                Pin(hud); Capture($"tee_wind_{mph}");
            }
            game.SetWind(Wind.Calm); for (int i = 0; i < 6; i++) yield return null;
            // the meter filling with a real backswing's load and yards
            // the yardage the meter shows must not move with the wind (or the lie, or where the ball is)
            var showWind = typeof(GolfGame).GetMethod("ShowWindUp", P);
            var yardsText = typeof(GolfShotHud).GetField("liveYards", P);
            var broadcast = Object.FindFirstObjectByType<GolfShotHud>();
            typeof(GolfGame).GetMethod("SelectClub", P).Invoke(game, new object[] { GolfClub.Driver }); yield return null;
            foreach (var wind in new[] { Wind.Calm, new Wind(25, 180), new Wind(25, 0), new Wind(15, 90) })
            {
                game.SetWind(wind); yield return null;
                foreach (double load in new[] { 1.0, .8 })
                {
                    showWind.Invoke(game, new object[] { load });
                    Debug.Log($"[YARDAGE] driver load {load} wind {wind.SpeedMPH}@{wind.DirectionDegrees}: meter says '{((UnityEngine.UI.Text)yardsText.GetValue(broadcast)).text}'");
                }
            }
            game.SetWind(Wind.Calm); yield return null;
            // the meter's flames per club: from 2.5 bars (driver), 3 (irons), 3.5 (wedges); never on a putt
            var plan = new (GolfClub club, float[] loads)[]
            {
                (GolfClub.Driver, new[] { .55f, .7f, .85f, 1f }), (GolfClub.Iron, new[] { .7f, .85f, 1f }),
                (GolfClub.PitchingWedge, new[] { .8f, .95f, 1f }), (GolfClub.Putter, new[] { 1f }),
            };
            foreach (var (club, loads) in plan)
            {
                // (the game owns the club in hand: pick it the way a player does, and let its HUD follow)
                typeof(GolfGame).GetMethod("SelectClub", P).Invoke(game, new object[] { club });
                for (int i = 0; i < 6; i++) yield return null;
                foreach (var load in loads)
                {
                    for (int i = 0; i < 28; i++) { hud.SetMeter(load, null, $"{Mathf.RoundToInt(load * 240)} yd"); yield return null; }
                    Capture($"meter_{club}_{Mathf.RoundToInt(load * 100)}");
                }
            }
            // the flames moving: four frames, three apart
            typeof(GolfGame).GetMethod("SelectClub", P).Invoke(game, new object[] { GolfClub.Driver }); yield return null;
            for (int k = 0; k < 4; k++)
            {
                for (int i = 0; i < 3; i++) { hud.SetMeter(1f, null, "240 yd"); yield return null; }
                Capture("anim_" + k);
            }
            hud.SetMeter(0f); yield return null;
        }
    }
}
#endif
