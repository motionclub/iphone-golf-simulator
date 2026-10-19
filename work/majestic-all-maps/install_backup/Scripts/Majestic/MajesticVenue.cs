using System;
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
    /// The "majestic" layer over a place (chat 9, 10-17): each tennis venue, golf course and the plaza keeps
    /// one signature hour of light, its own colour grade, and dressing (life, flags, flowers, boats, birds)
    /// built on top of the existing scene. Nothing here edits another system's files: it attaches itself when
    /// a Tennis / Golf / Hub scene loads, applies its light right after DreamEnvironment (through
    /// DreamEnvironment.AfterApply when that hook exists, else after it in the frame), and can be switched off
    /// at runtime (SetEnabled) or for a whole run with MAJESTIC=0. Weather still dims the light.
    /// Signature hour: the light is the venue's fixed best hour rather than the real clock (MAJESTIC_CLOCK=real
    /// keeps DreamEnvironment's clock-driven sun and only adds grade + dressing).
    [DefaultExecutionOrder(10002)]
    public sealed class MajesticVenue : MonoBehaviour
    {
        public static bool Enabled { get; private set; } = Environment.GetEnvironmentVariable("MAJESTIC") != "0";
        /// true = keep DreamEnvironment's real-clock sun (only grade + dressing); false = each place's signature hour.
        public static bool UseRealClock { get; set; } = Environment.GetEnvironmentVariable("MAJESTIC_CLOCK") == "real";
        public static MajesticVenue Current { get; private set; }

        /// What a place adds: dressing built under a root, material restyle (idempotent; undone with on=false),
        /// and per-frame animation.
        internal sealed class Kit
        {
            public Action<Transform, MajesticLook> Build = (_, _) => { };
            public Action<bool, MajesticLook> Restyle = (_, _) => { };
            public Action<MajesticLook, float> Animate = (_, _) => { };
        }

        MajesticLook look; Kit kit;
        float viewYaw;                       // the place's "forward" (tennis +Z, golf tee->pin, hub arrival view)
        Volume volume;
        GameObject dressing;
        bool hooked;
        Light sun;
        float nextRestyle, attachedAt;
        GolfGame golf; Hole lastHole;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            SceneManager.sceneLoaded -= OnScene; SceneManager.sceneLoaded += OnScene;
            OnScene(SceneManager.GetActiveScene(), LoadSceneMode.Single);
        }

        static void OnScene(Scene scene, LoadSceneMode mode)
        {
            if (Environment.GetEnvironmentVariable("MAJESTIC") == "0") return;
            if (scene.name != "Tennis" && scene.name != "Golf" && scene.name != "Hub") return;
            var runner = new GameObject("Majestic boot").AddComponent<MajesticBoot>();
            runner.SceneName = scene.name;
            SceneManager.MoveGameObjectToScene(runner.gameObject, scene);
        }

        public static void SetEnabled(bool on)
        {
            Enabled = on;
            if (Current) Current.Toggle(on);
        }

        static MajesticVenue Add(Component host, MajesticLook look, Kit kit, float viewYaw)
        {
            var v = host.gameObject.AddComponent<MajesticVenue>();
            v.look = look; v.kit = kit; v.viewYaw = viewYaw;
            Current = v; v.attachedAt = Time.unscaledTime;
            v.Build(); v.Toggle(Enabled);
            return v;
        }

        internal static void Attach(TennisGame game)
        {
            if (!game || game.GetComponent<MajesticVenue>()) return;
            var kit = TennisVenue.Current switch
            {
                TennisVenueKind.Volcano => new Kit { Build = MajesticVolcano.Build, Restyle = MajesticVolcano.SetMaterials, Animate = MajesticVolcano.Animate },
                TennisVenueKind.Skyscraper => new Kit { Build = MajesticSkyscraper.Build, Restyle = MajesticSkyscraper.SetMaterials, Animate = MajesticSkyscraper.Animate },
                _ => new Kit { Build = MajesticResort.Build, Restyle = MajesticResort.SetMaterials, Animate = MajesticResort.Animate },
            };
            Add(game, MajesticLook.For(TennisVenue.Current), kit, 0);
        }

        internal static void Attach(GolfGame game)
        {
            if (!game || game.GetComponent<MajesticVenue>()) return;
            var v = Add(game, MajesticLook.Golf(0), new Kit { Build = MajesticGolf.Build, Animate = MajesticGolf.Animate }, 0);
            v.golf = game;
        }

        internal static void Attach(GolfArcade.Hub.HubWorld world)
        {
            if (!world || world.GetComponent<MajesticVenue>()) return;
            float yaw = world.Camera ? world.Camera.transform.eulerAngles.y : 0;
            Add(world, MajesticLook.Hub(), new Kit { Build = MajesticHub.Build, Restyle = MajesticHub.SetMaterials, Animate = MajesticHub.Animate }, yaw);
        }

        void Build()
        {
            var go = new GameObject("Majestic grade");
            go.transform.SetParent(transform, false);
            volume = go.AddComponent<Volume>();
            volume.isGlobal = true; volume.priority = 50;
            volume.profile = look.Grade();
            Redress();
            hooked = Hook(true);
        }

        void Redress()
        {
            if (dressing) Destroy(dressing);
            // a scene root at the world origin (venue meshes are authored in world space; some hosts, e.g. the
            // plaza's HubWorld, are not at the origin), on the host's layer so its cameras draw it
            dressing = new GameObject("Majestic dressing") { layer = gameObject.layer };
            SceneManager.MoveGameObjectToScene(dressing, gameObject.scene);
            if (look.Active) kit.Build(dressing.transform, look);
            foreach (var t in dressing.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = gameObject.layer;
            dressing.SetActive(Enabled && look.Active);
        }

        void Toggle(bool on)
        {
            bool active = on && look.Active;
            if (volume) volume.enabled = active;
            if (dressing) dressing.SetActive(active);
            kit.Restyle(active, look);
        }

        void OnDestroy() { Hook(false); if (dressing) Destroy(dressing); if (Current == this) Current = null; }

        /// DreamEnvironment.AfterApply (static Action<DreamEnvironment>) is a one-line hook in a shared file;
        /// bound by reflection so this layer also compiles and runs without it.
        bool Hook(bool add)
        {
            var f = typeof(DreamEnvironment).GetField("AfterApply", BindingFlags.Public | BindingFlags.Static);
            if (f == null || f.FieldType != typeof(Action<DreamEnvironment>)) return false;
            var cur = (Action<DreamEnvironment>)f.GetValue(null);
            Action<DreamEnvironment> me = OnDreamApplied;
            f.SetValue(null, add ? (Action<DreamEnvironment>)Delegate.Combine(cur, me) : (Action<DreamEnvironment>)Delegate.Remove(cur, me));
            return true;
        }

        void OnDreamApplied(DreamEnvironment env) => ApplyLight();

        void LateUpdate()
        {
            if (golf)
            {
                var hole = golf.CurrentHole;
                if (hole != null && hole != lastHole)
                {
                    lastHole = hole;
                    var tee = HoleView.ToWorld(hole.Tee); var pin = HoleView.ToWorld(hole.Pin);
                    var fwd = pin - tee; fwd.y = 0;
                    viewYaw = fwd.sqrMagnitude > 1 ? Quaternion.LookRotation(fwd).eulerAngles.y : 0;
                    look = MajesticLook.Golf(hole.Number);
                    MajesticGolf.Hole = hole; MajesticGolf.Forward = fwd.normalized; MajesticGolf.Tee = tee; MajesticGolf.Pin = pin;
                    volume.profile = look.Grade();
                    Redress(); Toggle(Enabled);
                }
            }
            if (!hooked || DreamEnvironment.Current == null) ApplyLight();
            if (!Enabled || !look.Active) return;
            Shader.SetGlobalVector(WindId, look.Wind(Time.time));
            if (Time.unscaledTime >= nextRestyle)
            {
                kit.Restyle(true, look);
                nextRestyle = Time.unscaledTime + (Time.unscaledTime - attachedAt < 20 ? 1 : 10);
            }
            kit.Animate(look, Time.time);
        }

        static readonly int WindId = Shader.PropertyToID("_GolfWind"), NightId = Shader.PropertyToID("_DreamNight");

        void ApplyLight()
        {
            if (!Enabled || look == null || !look.Active || UseRealClock) return;
            if (!sun) sun = RenderSettings.sun;
            float cloud = 0;
            var sky = RenderSettings.skybox;
            if (sky && sky.HasProperty("_Cloud")) cloud = Mathf.Clamp01((sky.GetFloat("_Cloud") - .08f) / .57f);
            if (sun)
            {
                var toSun = Quaternion.Euler(0, viewYaw, 0) * look.ToSun;
                sun.transform.rotation = Quaternion.LookRotation(-toSun);
                sun.color = Color.Lerp(look.SunColor, new Color(.78f, .8f, .86f), cloud * .7f);
                sun.intensity = look.SunIntensity * (1 - cloud * .55f);
                sun.shadowStrength = look.ShadowStrength * (1 - cloud * .6f);
            }
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = Color.Lerp(look.AmbientSky, look.AmbientSky * .8f, cloud);
            RenderSettings.ambientEquatorColor = look.AmbientEquator;
            RenderSettings.ambientGroundColor = look.AmbientGround;
            if (cloud < .3f && look.FogEnd > 0)
            {
                RenderSettings.fogColor = look.FogColor;
                RenderSettings.fogStartDistance = look.FogStart; RenderSettings.fogEndDistance = look.FogEnd;
            }
            if (sky && look.SkySunset >= 0 && sky.HasProperty("_Sunset")) sky.SetFloat("_Sunset", look.SkySunset);
            if (sky && look.SkyDay >= 0 && sky.HasProperty("_Day")) sky.SetFloat("_Day", look.SkyDay);
            if (look.Night >= 0) Shader.SetGlobalFloat(NightId, look.Night);
            if (sky && look.SkyExposure >= 0 && sky.HasProperty("_Exposure")) sky.SetFloat("_Exposure", look.SkyExposure);
            if (MajesticVolcano.Flash > 0 && TennisVenue.Current == TennisVenueKind.Volcano && !golf)
            {
                // lightning: a brief cool lift of the sky light (ambient only; the ball keeps its contrast)
                RenderSettings.ambientSkyColor += new Color(.35f, .32f, .55f);
                RenderSettings.ambientEquatorColor += new Color(.2f, .18f, .3f);
            }
        }
    }

    /// Waits for the scene's game to finish initialising, then attaches the layer.
    sealed class MajesticBoot : MonoBehaviour
    {
        public string SceneName;
        float giveUp;
        void Start() => giveUp = Time.realtimeSinceStartup + 90;
        void Update()
        {
            switch (SceneName)
            {
                case "Tennis":
                    var tennis = FindFirstObjectByType<TennisGame>();
                    if (tennis && tennis.Initialized) { MajesticVenue.Attach(tennis); Destroy(gameObject); return; }
                    break;
                case "Golf":
                    var golf = FindFirstObjectByType<GolfGame>();
                    if (golf && HoleView.Current && golf.CurrentHole != null) { MajesticVenue.Attach(golf); Destroy(gameObject); return; }
                    break;
                case "Hub":
                    var hub = GolfArcade.Hub.HubWorld.Find();
                    if (hub && hub.Camera) { MajesticVenue.Attach(hub); Destroy(gameObject); return; }
                    break;
            }
            if (Time.realtimeSinceStartup > giveUp) Destroy(gameObject);
        }
    }
}
