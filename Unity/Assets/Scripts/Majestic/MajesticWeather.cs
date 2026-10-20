using System;
using System.Collections.Generic;
using System.Reflection;
using GolfArcade.Course;
using GolfArcade.EnvironmentArt;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace GolfArcade.Majestic
{
    /// The Majestic weather layer (chat W, 10-17, work/majestic-weather; PLAN.md §3 M3-M4, §4.4).
    /// One state (weather + biome family + phase + level) drives:
    /// - weather inside the world materials (Resources/Majestic/MajesticWeather.hlsl via EnvironmentSurface.hlsl):
    ///   wetness, puddles + ripples, snow / ash cover, frost, grass waves, cloud shadows, whitecaps, height fog
    ///   toward the rendered sky's colour (ball, flag and players capped at 15 % fog);
    /// - one camera-attached fall layer + at most 400 near drops outside the ball corridor (MajesticWeatherFx);
    /// - sky events: storm wall, lightning light, eruption flash + lava bombs, rain clearing to sunbeams + rainbow;
    /// - one global wind (_WindDir/_WindStrength/_Gust, and it strengthens _GolfWind for grass, trees, flags, bunting, sails);
    /// - the light under the weather (sun, ambient, sky cover), and the ambience beds (+ AudioCue hooks for chat 8's bus).
    /// While on, the game's WeatherView keeps its state, timing, thunder and rules, but its three full-screen volumes and
    /// its particles are switched off (by name, no edit to WeatherView). Self-attaching (Tennis / Golf scenes), off with
    /// MAJESTIC=0 or MAJESTIC_WEATHER=0, and dormant until the shader hook is installed (Majestic/MajesticWeatherHook).
    /// Tennis: weather wraps around play (Adnan, 10-17): arrival, between games, after the match; never during a rally.
    [DefaultExecutionOrder(10003)]
    public sealed class MajesticWeather : MonoBehaviour
    {
        public static bool Enabled { get; private set; } = Environment.GetEnvironmentVariable("MAJESTIC") != "0" && Environment.GetEnvironmentVariable("MAJESTIC_WEATHER") != "0";
        public static MajesticWeather Current { get; private set; }
        static int hookChecked = -1;
        /// The world shaders carry the weather terms (EnvironmentSurface.hlsl includes MajesticWeather.hlsl): the
        /// hook's installer drops this marker next to it. Without it the layer stays dormant and WeatherView draws as before.
        public static bool ShadersReady
        {
            get { if (hookChecked < 0) hookChecked = Resources.Load<TextAsset>("Majestic/MajesticWeatherHook") ? 1 : 0; return hookChecked == 1; }
        }

        // ---- state (read by the tests and the proof harness) ----
        public Weather Weather { get; private set; }
        public Sky Family { get; private set; }
        public WeatherPhase Phase { get; private set; }
        public bool Tennis => tennis;
        public bool Active { get; private set; }
        /// The look drawn this frame (blended, after the tennis play window).
        public WeatherLook Now;
        public float Rainbow { get; private set; }
        public float Beams { get; private set; }
        public float Flash { get; private set; }
        public float PlayShare { get; private set; } = 1;     // tennis: 1 weather shows, 0 a rally is on
        public float GustNow { get; private set; }
        /// The game's wind speed as a share of its strongest (0..1), for the wind wisps.
        public float Wind01 { get; private set; }
        public Vector2 WindDir { get; private set; } = Vector2.up;
        public Vector3 CorridorA { get; private set; }
        public Vector3 CorridorB { get; private set; }
        public Camera Cam => cam;
        /// Proof harness / tools: the WeatherView to follow (null: the game's own).
        public static WeatherView Source;
        /// Proof harness: treat the next frame as a new place (the weather snaps in as at a hole's start).
        public void Restart() { started = false; }
        public MajesticWeatherFx Fx => fx;

        // ---- audio hooks (chat 8's Ambience bus subscribes; until then the game's EventSounds beds play them) ----
        public struct AudioBeds { public float Rain, Wind, Gust, Snow, Embers; }
        public static AudioBeds Beds;
        /// ("thunder", distance 0..1, delay s) · ("rumble", strength, 0) · ("gust", strength, 0)
        public static event Action<string, float, float> AudioCue;

        GolfGame golf; TennisGame tennis; CameraRig rig; Camera cam;
        WeatherView view; EventSounds sounds;
        readonly List<Renderer> hidden = new();
        readonly List<(ParticleSystem ps, float speed)> muted = new();
        readonly List<Renderer> bolts = new();
        WeatherView takenOver;
        MajesticWeatherFx fx;
        MajesticWeatherGlow glow;

        WeatherLook from, to; float easeStart, easeTime = 1;
        float wet, puddles, cover, dryEdge;
        object placeKey; Weather lastWeather; Sky lastFamily; bool started;
        int lastStrikes; float flashStart = -10; bool flashEruption;
        float clearingUntil, rainbowTo, beamsTo;
        int gamesAtLastRally = -1;
        float fogBase; float waterY; bool hasWater;
        float playTo = 1;
        bool hooked;
        int seed;

        static readonly FieldInfo NextStrikeField = typeof(WeatherView).GetField("nextStrike", BindingFlags.Instance | BindingFlags.NonPublic);
        static readonly string[] VolumeNames = { "Cloud dome", "Ground fog", "Wet ground" };
        static readonly string[] SystemNames = { "Rain", "Snow", "Ash", "Embers", "Splashes" };
        static readonly string[] BoltNames = { "Lightning", "Lightning branch" };

        // ------------------------------------------------------------------ attach
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            SceneManager.sceneLoaded -= OnScene; SceneManager.sceneLoaded += OnScene;
            OnScene(SceneManager.GetActiveScene(), LoadSceneMode.Single);
        }

        static void OnScene(Scene scene, LoadSceneMode mode)
        {
            if (Environment.GetEnvironmentVariable("MAJESTIC") == "0" || Environment.GetEnvironmentVariable("MAJESTIC_WEATHER") == "0") return;
            if (scene.name != "Tennis" && scene.name != "Golf") return;
            var runner = new GameObject("Majestic weather boot").AddComponent<MajesticWeatherBoot>();
            runner.SceneName = scene.name;
            SceneManager.MoveGameObjectToScene(runner.gameObject, scene);
        }

        internal static void Attach(MonoBehaviour game)
        {
            if (!game || game.GetComponent<MajesticWeather>()) return;
            var w = game.gameObject.AddComponent<MajesticWeather>();
            w.golf = game as GolfGame; w.tennis = game as TennisGame;
            Current = w;
        }

        /// Runtime switch (the proof harness, a settings toggle). Off puts everything back on the next frame.
        public static void SetEnabled(bool on)
        {
            Enabled = on;
            if (Current && !on) Current.Off();
        }

        void OnDestroy() { Off(); Hook(false); fx?.Destroy(); glow?.Destroy(); if (Current == this) Current = null; }

        // ------------------------------------------------------------------ frame
        void LateUpdate()
        {
            if (!Enabled || !ShadersReady) { if (Active) Off(); return; }
            Resolve();
            if (!view || !cam) { if (Active) Off(); return; }
            fx ??= new MajesticWeatherFx(transform);
            TakeOver(view, true);
            if (!hooked || !LastInvoked()) hooked = Hook(true);

            float now = Time.time, dt = Time.deltaTime;
            var family = tennis ? MajesticWeatherRules.FamilyForTennis((int)TennisVenue.Current) : Weathers.SkyOf(golf.CurrentHole);
            object place = tennis ? (object)tennis : golf.CurrentHole;
            var w = view.Weather;
            if (!started || !ReferenceEquals(place, placeKey) || family != lastFamily) NewPlace(place, w, family, now);
            else if (w != lastWeather) Turn(w, now);
            lastWeather = w; lastFamily = family; Weather = w; Family = family;

            // the look: eased from the last to the target, then the slow ground channels
            float e = easeTime <= 0 ? 1 : Mathf.Clamp01((now - easeStart) / easeTime);
            e = e * e * (3 - 2 * e);
            Now = WeatherLook.Lerp(from, to, e);
            wet = Mathf.MoveTowards(wet, to.Wet, dt / (to.Wet > wet ? 6f : 45f));
            puddles = Mathf.MoveTowards(puddles, to.Puddles, dt / (to.Puddles > puddles ? 9f : 60f));
            cover = Mathf.MoveTowards(cover, to.Cover, dt / (to.Cover > cover ? 10f : 40f));
            dryEdge = Mathf.MoveTowards(dryEdge, to.Wet < wet - .01f ? 1 : 0, dt / (to.Wet < wet ? 6f : 2f));
            Now.Wet = wet; Now.Puddles = puddles; Now.Cover = cover;
            if (Phase == WeatherPhase.Arriving && e >= 1) Phase = WeatherPhase.Full;
            if (Phase == WeatherPhase.Clearing && now > clearingUntil) { Phase = WeatherPhase.Calm; rainbowTo = beamsTo = 0; }

            // tennis: nothing falls or flashes while a point is played
            PlayWindow(now);
            PlayShare = Mathf.MoveTowards(PlayShare, playTo, dt / 1.2f);
            float play = PlayShare;
            Now.Precip *= play; Now.Lightning *= play; Now.Eruption *= play;
            Now.FogDensity *= Mathf.Lerp(.35f, 1, play); Now.Gust *= Mathf.Lerp(.3f, 1, play); Now.Embers *= Mathf.Lerp(.4f, 1, play);
            if (tennis && playTo < .5f && w != Weather.Clear) Phase = WeatherPhase.Held;
            else if (Phase == WeatherPhase.Held) Phase = WeatherPhase.Full;

            Rainbow = Mathf.MoveTowards(Rainbow, rainbowTo * play, dt / 4f);
            Beams = Mathf.MoveTowards(Beams, Mathf.Max(beamsTo, Now.Shafts) * play, dt / 3f);
            Events(now, play);

            bool calm = Now.Precip < .002f && Now.Cloud < .1f && wet < .002f && cover < .002f && Now.FogDensity < 1e-5f && Rainbow < .002f && Beams < .002f
                        && Now.Wind < .01f && Flash < .002f && Now.Embers < .002f;
            Active = !calm;

            WindNow(now);
            Publish(now);
            fx.Update(this, cam, now, dt);
            (glow ??= new MajesticWeatherGlow()).Update(this);
            FogAndAerial();
            Audio();
        }

        void Resolve()
        {
            if (Source) { view = Source; }
            if (golf)
            {
                if (!rig) rig = FindFirstObjectByType<CameraRig>();
                cam = rig ? rig.Camera : Camera.main;
                if (!Source) view = golf.WeatherShown;
                if (!view) { var v = golf.GetComponentInChildren<WeatherView>(); if (v) view = v; }
            }
            else if (tennis)
            {
                cam = tennis.GameplayCamera ? tennis.GameplayCamera : Camera.main;
                if (!view) view = tennis.GetComponentInChildren<WeatherView>();
            }
            if (view && !sounds) sounds = (golf ? (Component)golf : tennis).GetComponentInChildren<EventSounds>();
        }

        // ------------------------------------------------------------------ phases
        void NewPlace(object place, Weather w, Sky family, float now)
        {
            placeKey = place; started = true;
            var target = MajesticWeatherRules.For(w, family, tennis);
            // golf: a hole's weather rolls in over the opening (the intro flyover); tennis: a game's weather eases in
            bool heavy = w == Weather.Rain || w == Weather.Storm;
            from = tennis && Phase != WeatherPhase.Calm ? Now : MajesticWeatherRules.For(Weather.Clear, family, tennis);
            if (!tennis) { from.Cloud = Mathf.Lerp(from.Cloud, target.Cloud, .55f); from.FogDensity = target.FogDensity * .5f; from.Wet = target.Wet; }
            to = target; easeStart = now; easeTime = heavy ? 6f : 3f;
            if (!tennis) { wet = target.Wet * .9f; puddles = target.Puddles * .8f; cover = target.Cover; }
            Phase = w == Weather.Clear ? WeatherPhase.Calm : WeatherPhase.Arriving;
            rainbowTo = beamsTo = 0; Rainbow = Beams = 0; clearingUntil = 0;
            lastStrikes = view ? view.Strikes : 0;
            gamesAtLastRally = -1;
            seed = DreamEnvironment.Session?.seed ?? 0;
            Ground();
        }

        void Turn(Weather w, float now)
        {
            var was = lastWeather;
            from = Now; to = MajesticWeatherRules.For(w, Family, tennis); easeStart = now; easeTime = 5f;
            if (w == Weather.Clear && was.IsWet() && Family == Sky.Rain)
            {
                // the clearing: sunbeams through the last of the cloud, a rainbow beyond the pin, the ground drying edges-first
                Phase = WeatherPhase.Clearing; clearingUntil = now + 40f; rainbowTo = 1; beamsTo = 1; easeTime = 8f;
                to.Cloud = .32f; to.Precip = 0;
            }
            else { Phase = w == Weather.Clear ? WeatherPhase.Calm : WeatherPhase.Arriving; rainbowTo = beamsTo = 0; }
        }

        /// Snap to the target at once (proof harness, cost A/B): no easing, ground already soaked / covered.
        public void Snap()
        {
            from = to; easeTime = 0; wet = to.Wet; puddles = to.Puddles; cover = to.Cover; dryEdge = 0;
            PlayShare = playTo; if (Phase == WeatherPhase.Arriving) Phase = WeatherPhase.Full;
            Rainbow = rainbowTo; Beams = beamsTo;
        }

        /// Proof harness: the rain-clearing event now (as GolfGame.SkiesCleared does when rain turns clear).
        public void ClearingNow(float hold = 40f) { Phase = WeatherPhase.Clearing; clearingUntil = Time.time + hold; rainbowTo = beamsTo = 1; }

        void PlayWindow(float now)
        {
            if (!tennis) { playTo = 1; return; }
            int games = TennisConditions.Epoch(tennis.Match);
            bool rally = tennis.Flow == TennisGame.Phase.Rally;
            if (rally && gamesAtLastRally != games) gamesAtLastRally = games;
            bool shows = MajesticWeatherRules.TennisWeatherShows(rally, tennis.Flow == TennisGame.Phase.MatchOver, tennis.IntroPlaying, games, gamesAtLastRally);
            playTo = shows ? 1 : 0;
            // WeatherView keeps its own strike clock: hold it while a point is played (no bolt, no thunder mid-rally)
            if (NextStrikeField != null && view && to.Lightning + to.Eruption > 0)
            {
                float next = (float)NextStrikeField.GetValue(view);
                if (!shows && next < float.MaxValue) NextStrikeField.SetValue(view, now + 2f);
            }
        }

        // ------------------------------------------------------------------ events
        void Events(float now, float play)
        {
            int strikes = view.Strikes;
            if (strikes != lastStrikes)
            {
                lastStrikes = strikes;
                if (play > .5f)
                {
                    flashStart = now; flashEruption = Family == Sky.Ash;
                    if (flashEruption) { fx.Erupt(this, cam); AudioCue?.Invoke("rumble", 1, 0); }
                    else AudioCue?.Invoke("thunder", .5f, .6f);
                }
            }
            float a = now - flashStart;
            if (flashEruption) Flash = a < 0 ? 0 : Mathf.Exp(-a * 1.6f) * Mathf.Clamp01(a * 12);
            else
            {
                // a strike flickers: three pulses in 0.3 s (never more than 3 flashes a second), exposure-clamped
                float f = 0;
                if (a >= 0 && a < .5f) f = Mathf.Max(Pulse(a, 0, .07f), Mathf.Max(.55f * Pulse(a, .11f, .06f), .8f * Pulse(a, .24f, .12f)));
                Flash = f;
            }
            foreach (var r in bolts) if (r) r.forceRenderingOff = play < .5f;
        }

        static float Pulse(float t, float at, float len) => t < at || t > at + len ? 0 : 1 - (t - at) / len;

        // ------------------------------------------------------------------ wind
        static readonly int GolfWindId = Shader.PropertyToID("_GolfWind"), WindDirId = Shader.PropertyToID("_WindDir"),
            WindStrengthId = Shader.PropertyToID("_WindStrength"), GustId = Shader.PropertyToID("_Gust");

        void WindNow(float now)
        {
            double deg = golf ? golf.Wind.DirectionDegrees : 45;
            float mph = golf ? (float)golf.Wind.SpeedMPH : (Weather == Weather.Storm ? 10 : Weather == Weather.Gusty ? 7 : 2);
            WindDir = MajesticWeatherRules.Direction(deg);
            Wind01 = Mathf.Clamp01(mph / (float)Wind.MaxMPH);
            GustNow = MajesticWeatherRules.Gust(seed, DreamEnvironment.Utc, Now.Gust);
            float strength = Mathf.Clamp01(Mathf.Max(Now.Wind, mph / (float)Wind.MaxMPH));
            Shader.SetGlobalVector(WindDirId, new Vector4(WindDir.x, 0, WindDir.y, 0));
            Shader.SetGlobalFloat(WindStrengthId, Active ? strength : 0);
            Shader.SetGlobalFloat(GustId, Active ? GustNow : 0);
            if (!Active) return;
            // the shared sway global (_GolfWind: grass, palms, trees, flags, bunting, sails): stronger and gusting
            var g = Shader.GetGlobalVector(GolfWindId);
            float boost = 1 + 1.6f * Now.Wind + 1.8f * GustNow;
            if (new Vector2(g.x, g.z).sqrMagnitude < 1e-6f && Now.Wind > 0) { g.x = WindDir.x * .05f; g.z = WindDir.y * .05f; g.w = now; }
            g.x *= boost; g.z *= boost;
            Shader.SetGlobalVector(GolfWindId, g);
        }

        // ------------------------------------------------------------------ material globals
        static readonly int OnId = Shader.PropertyToID("_MajWeatherOn"), UnitId = Shader.PropertyToID("_MajUnit"), WetId = Shader.PropertyToID("_MajWet"),
            CoverId = Shader.PropertyToID("_MajCover"), CoverFxId = Shader.PropertyToID("_MajCoverFx"), CorridorId = Shader.PropertyToID("_MajCorridor"),
            ClearId = Shader.PropertyToID("_MajClear"), FogColorId = Shader.PropertyToID("_MajFogColor"), FogId = Shader.PropertyToID("_MajFog"),
            FogGlowId = Shader.PropertyToID("_MajFogGlow"), ObserverId = Shader.PropertyToID("_MajObserver"), SkyReflId = Shader.PropertyToID("_MajSkyRefl"),
            SunDirId = Shader.PropertyToID("_MajSunDir"), SunColId = Shader.PropertyToID("_MajSunCol"), MajWindId = Shader.PropertyToID("_MajWind"),
            TimeId = Shader.PropertyToID("_MajTime"), FlashId = Shader.PropertyToID("_MajFlash"), WaterId = Shader.PropertyToID("_MajWater"),
            PoolsId = Shader.PropertyToID("_MajPools"), SkyMapId = Shader.PropertyToID("_MajSkyMap");

        public Color FogColour { get; private set; }

        /// The world shaders' weather variant (MAJESTIC_WEATHER_ON, fragment): on only while weather is active, so
        /// clear weather and the layer switched off render the original shader code exactly.
        static GlobalKeyword keyword; static bool keywordMade;
        static void SetKeyword(bool on)
        {
            if (!keywordMade) { keyword = GlobalKeyword.Create("MAJESTIC_WEATHER_ON"); keywordMade = true; }
            if (Shader.IsKeywordEnabled(keyword) != on) Shader.SetKeyword(keyword, on);
        }

        void Publish(float now)
        {
            Shader.SetGlobalFloat(OnId, Active ? 1 : 0);
            SetKeyword(Active);
            if (!Active) return;
            float unit = tennis ? 1f : .9144f;
            Shader.SetGlobalFloat(UnitId, unit);
            Shader.SetGlobalVector(WetId, new Vector4(wet, puddles, Now.Precip * (Now.Fall == WeatherFall.Rain ? 1 : 0), dryEdge));
            Shader.SetGlobalVector(CoverId, new Vector4(Now.CoverColor.r, Now.CoverColor.g, Now.CoverColor.b, cover));
            // the line of play stays clear of ash; snow may dust it (as the refs show), lightly
            Shader.SetGlobalVector(CoverFxId, new Vector4(Now.Frost, tennis ? 0 : Family == Sky.Snow ? .7f : 1, Now.Embers, Family == Sky.Ash ? .03f : .65f));
            Corridor();
            Shader.SetGlobalVector(CorridorId, new Vector4(CorridorA.x, CorridorA.z, CorridorB.x, CorridorB.z));
            if (golf && golf.CurrentHole != null) { var pin = HoleView.ToWorld(golf.CurrentHole.Pin); Shader.SetGlobalVector(ClearId, new Vector4(pin.x, pin.y, pin.z, 16)); }
            else Shader.SetGlobalVector(ClearId, new Vector4(0, 0, 0, 21));

            // fog colour: the rendered horizon (RenderedSky drives RenderSettings.fogColor), tinted toward the weather's own
            var horizon = RenderedSky.Current ? RenderedSky.Current.HorizonColour : RenderSettings.fogColor;
            if (horizon.maxColorComponent < .01f) horizon = RenderSettings.fogColor;
            float lum = Mathf.Clamp(horizon.r * .3f + horizon.g * .55f + horizon.b * .15f, .05f, 1.2f);
            var tint = Now.FogTint * Mathf.Clamp(lum / .62f, .3f, 1f);
            FogColour = Color.Lerp(horizon, tint, Now.FogTintShare) * Mathf.Lerp(1, Now.SkyExposure, Family == Sky.Ash ? 1f : .55f);
            Shader.SetGlobalVector(FogColorId, new Vector4(FogColour.r, FogColour.g, FogColour.b, Now.FogMax));
            Shader.SetGlobalVector(FogId, new Vector4(Now.FogDensity, Now.FogFalloff, fogBase, tennis ? 24 : 16));
            var sun = RenderSettings.sun;
            Vector3 toSun = sun ? -sun.transform.forward : new Vector3(.3f, .6f, .7f).normalized;
            Color sunCol = sun ? sun.color * sun.intensity : Color.white;
            var glow = Color.Lerp(Now.FogGlow * sunCol.maxColorComponent, Now.FogGlow, Family == Sky.Ash ? .7f : 0);
            Shader.SetGlobalVector(FogGlowId, new Vector4(glow.r, glow.g, glow.b, Now.FogGlowStrength));
            bool observer = golf && Weather == Weather.Fog && DreamVisibility.Fog;
            var o = DreamVisibility.Observer;
            Shader.SetGlobalVector(ObserverId, new Vector4(o.x, o.y, o.z, observer ? 1 : 0));
            // what wet ground mirrors: the sky as darkened by this weather (not the pale horizon), a little sun
            var refl = Color.Lerp(RenderSettings.ambientSkyColor, FogColour, .5f) * Mathf.Lerp(.7f, 1f, Now.SkyExposure) * Now.SkyExposure + sunCol * .04f * (1 - Now.Cloud);
            Shader.SetGlobalVector(SkyReflId, new Vector4(refl.r, refl.g, refl.b, 1));
            float glints = Mathf.Lerp(1.6f, .5f, Now.Cloud) * (Phase == WeatherPhase.Clearing ? 2.2f : 1);
            Shader.SetGlobalVector(SunDirId, new Vector4(toSun.x, toSun.y, toSun.z, glints));
            Shader.SetGlobalVector(SunColId, sunCol);
            Shader.SetGlobalVector(MajWindId, new Vector4(WindDir.x, WindDir.y, Mathf.Clamp01(Now.Wind), GustNow));
            Shader.SetGlobalVector(TimeId, new Vector4(now % 3600f, Now.GrassWaves * (.55f + .45f * GustNow), Now.CloudShadows, Now.Whitecaps * (.6f + .4f * GustNow)));
            var flash = (flashEruption ? new Color(1f, .45f, .18f) * .45f : new Color(.75f, .8f, 1f) * .8f) * Flash;
            Shader.SetGlobalVector(FlashId, new Vector4(flash.r, flash.g, flash.b, 0));
            Shader.SetGlobalVector(WaterId, new Vector4(waterY, hasWater ? 1 : 0, 0, 0));
            // puddles mirror the real rendered sky (chat 2's equirect reflection), darkened as this weather darkens it
            var skyMap = RenderedSky.Current ? RenderedSky.Current.Reflection : null;
            if (skyMap) Shader.SetGlobalTexture(SkyMapId, skyMap);
            Shader.SetGlobalVector(PoolsId, new Vector4(Now.LavaPools, Now.IcePools, Now.SkyExposure, skyMap ? 1 : 0));
        }

        void Corridor()
        {
            if (golf && golf.CurrentHole != null)
            {
                var hole = golf.CurrentHole;
                var ball = HoleView.ToWorld(golf.BallAt, .1);
                var pin = HoleView.ToWorld(hole.Pin);
                float reach = Mathf.Clamp(Vector3.Distance(ball, pin), 30, 290);
                var d = MajesticWeatherRules.Direction(golf.AimHeading);
                CorridorA = ball; CorridorB = ball + new Vector3(d.x, 0, d.y) * reach;
                CorridorB = new Vector3(CorridorB.x, Mathf.Max(ball.y, pin.y), CorridorB.z);
            }
            else { CorridorA = new Vector3(0, 1, -12.5f); CorridorB = new Vector3(0, 1, 12.5f); }
        }

        void Ground()
        {
            hasWater = false; fogBase = 0;
            if (golf && golf.CurrentHole != null)
            {
                var hole = golf.CurrentHole;
                double G(CoursePoint p) => hole.Ground != null ? hole.Ground(p) : HoleView.GroundHeight(p);
                fogBase = (float)Math.Min(G(hole.Tee), Math.Min(G(hole.Pin), G(hole.RecommendedTarget(hole.Tee)))) - 2f;
                foreach (var r in FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                {
                    var m = r.sharedMaterial;
                    if (!m || !m.shader || m.shader.name.IndexOf("Ocean", StringComparison.OrdinalIgnoreCase) < 0) continue;
                    var b = r.bounds; if (b.size.x < 50) continue;
                    waterY = b.max.y; hasWater = true; break;
                }
            }
            else fogBase = -2f;
        }

        // ------------------------------------------------------------------ light (after DreamEnvironment + MajesticVenue)
        void OnDreamApplied(DreamEnvironment env)
        {
            if (!Active || !Enabled) return;
            var sky = RenderSettings.skybox;
            if (sky && sky.HasProperty("_Cloud")) sky.SetFloat("_Cloud", Mathf.Max(sky.GetFloat("_Cloud"), Now.Cloud));
            var sun = RenderSettings.sun;
            float f = Flash;
            if (sun)
            {
                sun.intensity *= 1 - Now.SunDim;
                sun.color = Color.Lerp(sun.color, sun.color * Now.SunTint, .85f);
                sun.shadowStrength *= 1 - .6f * Mathf.Clamp01((Now.Cloud - .25f) / .6f);
                if (f > 0)
                {
                    var fc = flashEruption ? new Color(1f, .55f, .25f) : new Color(.86f, .88f, 1f);
                    sun.color = Color.Lerp(sun.color, fc, f * (flashEruption ? .3f : .6f)); sun.intensity += f * (flashEruption ? .3f : 1.1f);
                }
            }
            Color A(Color c) { var x = c * (1 - Now.AmbientDim); x = new Color(x.r * Now.AmbientTint.r, x.g * Now.AmbientTint.g, x.b * Now.AmbientTint.b, c.a); return x; }
            RenderSettings.ambientSkyColor = A(RenderSettings.ambientSkyColor);
            RenderSettings.ambientEquatorColor = A(RenderSettings.ambientEquatorColor);
            RenderSettings.ambientGroundColor = A(RenderSettings.ambientGroundColor);
            if (f > 0)
            {
                var add = (flashEruption ? new Color(.5f, .22f, .08f) : new Color(.32f, .34f, .45f)) * f;
                RenderSettings.ambientSkyColor += add; RenderSettings.ambientEquatorColor += add * .7f;
                if (flashEruption) RenderSettings.ambientGroundColor += add * .8f;   // lit from below by the crater
            }
        }

        static readonly int AmbUpId = Shader.PropertyToID("_RSkyAmbientUp"), AmbHorId = Shader.PropertyToID("_RSkyAmbientHorizon");
        static readonly int AerialId = Shader.PropertyToID("_RSkyAerial"), SkyParamsId = Shader.PropertyToID("_RSkyParams"), HorizonTintId = Shader.PropertyToID("_RSkyHorizonTint");
        /// Ball, flag and players: the URP fog (all they get) capped at 15 %; distant scenery hazes with the weather.
        void FogAndAerial()
        {
            if (!Active) return;
            float d = 45;
            if (golf && golf.CurrentHole != null)
            {
                var c = cam.transform.position;
                d = Mathf.Max(Vector3.Distance(c, HoleView.ToWorld(golf.CurrentHole.Pin)), Vector3.Distance(c, HoleView.ToWorld(golf.BallAt))) * 1.25f;
                d = Mathf.Max(d, 80);
            }
            if (RenderSettings.fog)
            {
                float s = RenderSettings.fogStartDistance, e = RenderSettings.fogEndDistance;
                if (RenderSettings.fogMode == FogMode.Linear) RenderSettings.fogEndDistance = MajesticWeatherRules.FogEndForCap(s, e, d, .15f);
                RenderSettings.fogColor = Color.Lerp(RenderSettings.fogColor, FogColour, .6f);
            }
            // (RenderedSky rewrites _RSkyAerial every frame; without it there is nothing to scale)
            var aerial = Shader.GetGlobalVector(AerialId);
            if (RenderedSky.Current && aerial.x > 0)
            {
                aerial.x *= Mathf.Max(.02f, Now.Aerial); aerial.z += (1 - Now.Aerial) * (Family == Sky.Ash ? 0 : .15f); Shader.SetGlobalVector(AerialId, aerial);
                // the sky itself darkens under the weather's cloud (and warms over the volcano); RenderedSky rewrites both every frame
                var sp = Shader.GetGlobalVector(SkyParamsId); sp.x *= Now.SkyExposure + .9f * Flash * (1 - Now.SkyExposure); Shader.SetGlobalVector(SkyParamsId, sp);
                // the overcast deck's grey is lit by the rendered ambient: darken it too, or a storm sky stays pale
                float deck = Now.SkyExposure + .9f * Flash * (1 - Now.SkyExposure);
                Shader.SetGlobalVector(AmbUpId, Shader.GetGlobalVector(AmbUpId) * deck);
                Shader.SetGlobalVector(AmbHorId, Shader.GetGlobalVector(AmbHorId) * deck);
                var ht = Shader.GetGlobalVector(HorizonTintId); ht.x *= Now.SkyTint.r; ht.y *= Now.SkyTint.g; ht.z *= Now.SkyTint.b; Shader.SetGlobalVector(HorizonTintId, ht);
            }
        }

        // ------------------------------------------------------------------ audio
        void Audio()
        {
            float rain = Now.Fall == WeatherFall.Rain ? Now.Precip : Now.Fall == WeatherFall.Ash ? Now.Precip * .3f : 0;
            float windBed = Mathf.Clamp01(Now.Wind * .7f + GustNow * .5f + (Now.Fall == WeatherFall.Snow ? Now.Precip * .4f : 0));
            Beds = new AudioBeds { Rain = rain, Wind = windBed, Gust = GustNow, Snow = Now.Fall == WeatherFall.Snow ? Now.Precip : 0, Embers = Now.Embers };
            if (sounds && Active) sounds.SetAmbience(rain, windBed);
        }

        // ------------------------------------------------------------------ WeatherView takeover
        void TakeOver(WeatherView v, bool on)
        {
            if (on && takenOver == v) return;
            if (takenOver && takenOver != v) TakeOver(takenOver, false);
            if (!on)
            {
                foreach (var r in hidden) if (r) r.forceRenderingOff = false;
                foreach (var r in bolts) if (r) r.forceRenderingOff = false;
                foreach (var (ps, speed) in muted) if (ps) { var m = ps.main; m.simulationSpeed = speed; }
                hidden.Clear(); muted.Clear(); bolts.Clear(); takenOver = null;
                return;
            }
            takenOver = v;
            int found = 0;
            foreach (var name in VolumeNames)
            {
                var t = v.transform.Find(name); if (!t) continue;
                var r = t.GetComponent<Renderer>(); if (!r) continue;
                r.forceRenderingOff = true; hidden.Add(r); found++;
            }
            foreach (var name in SystemNames)
            {
                var t = v.transform.Find(name); if (!t) continue;
                var ps = t.GetComponent<ParticleSystem>(); if (!ps) continue;
                // paused, not cleared: no simulation cost, and switching the layer off gives back exactly what was there
                var m = ps.main; muted.Add((ps, m.simulationSpeed)); m.simulationSpeed = 0;
                var r = t.GetComponent<Renderer>(); if (r) { r.forceRenderingOff = true; hidden.Add(r); }
                found++;
            }
            foreach (var name in BoltNames) { var t = v.transform.Find(name); if (t && t.GetComponent<Renderer>() is Renderer r) bolts.Add(r); }
            if (found < VolumeNames.Length + SystemNames.Length) Debug.LogWarning($"[MajesticWeather] WeatherView takeover found {found}/8 pieces: its children were renamed?");
        }

        void Off()
        {
            Active = false;
            TakeOver(null, false);
            Shader.SetGlobalFloat(OnId, 0);
            SetKeyword(false);
            Shader.SetGlobalFloat(WindStrengthId, 0); Shader.SetGlobalFloat(GustId, 0);
            Beds = default;
            fx?.Hide();
            glow?.Hide();
        }

        // ------------------------------------------------------------------ DreamEnvironment.AfterApply (reflection, as MajesticVenue)
        static readonly FieldInfo AfterApplyField = typeof(DreamEnvironment).GetField("AfterApply", BindingFlags.Public | BindingFlags.Static);
        Action<DreamEnvironment> handler;
        bool LastInvoked()
        {
            if (AfterApplyField == null) return true;
            var cur = AfterApplyField.GetValue(null) as Delegate;
            return cur != null && ReferenceEquals(cur.Target, this);   // a multicast delegate's Target is its LAST entry
        }
        bool Hook(bool add)
        {
            if (AfterApplyField == null || AfterApplyField.FieldType != typeof(Action<DreamEnvironment>)) return false;
            handler ??= OnDreamApplied;
            var cur = (Action<DreamEnvironment>)AfterApplyField.GetValue(null);
            cur = (Action<DreamEnvironment>)Delegate.Remove(cur, handler);
            if (add) cur = (Action<DreamEnvironment>)Delegate.Combine(cur, handler);   // last: after MajesticVenue's signature light
            AfterApplyField.SetValue(null, cur);
            return add;
        }
    }

    /// Waits for the scene's game to finish initialising, then attaches the weather layer.
    sealed class MajesticWeatherBoot : MonoBehaviour
    {
        public string SceneName;
        float giveUp;
        void Start() => giveUp = Time.realtimeSinceStartup + 90;
        void Update()
        {
            if (SceneName == "Tennis") { var t = FindFirstObjectByType<TennisGame>(); if (t && t.Initialized) { MajesticWeather.Attach(t); Destroy(gameObject); return; } }
            else { var g = FindFirstObjectByType<GolfGame>(); if (g && HoleView.Current && g.CurrentHole != null) { MajesticWeather.Attach(g); Destroy(gameObject); return; } }
            if (Time.realtimeSinceStartup > giveUp) Destroy(gameObject);
        }
    }
}
