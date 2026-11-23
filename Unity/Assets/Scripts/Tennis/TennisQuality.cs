using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using ShadowQuality = UnityEngine.ShadowQuality;
using ShadowResolution = UnityEngine.ShadowResolution;

namespace GolfArcade.Tennis
{
    /// Rendering settings chosen per phone.
    ///
    /// The project's iPhone default was the "Medium" level: no anti-aliasing and hard,
    /// lowest-resolution shadows. In motion, unsmoothed edges crawl from frame to frame,
    /// which reads as flicker -- a smoothness problem as much as a looks one. Every phone in
    /// the target range (iPhone 15 to 18) has an A16 or newer GPU, and MSAA on Apple's tiled
    /// GPUs resolves on-chip, so it is cheap there.
    ///
    /// Tiers come from the hardware model identifier, which is stable and cannot be spoofed
    /// by a setting: iPhone15,x is A16 (iPhone 14 Pro / 15), iPhone16,x A17 Pro (15 Pro),
    /// iPhone17,x A18 (16 family), iPhone18,x A19 (17 family).
    public static class TennisQuality
    {
        public enum Tier { Low, Standard, High }
        public static Tier Current { get; private set; } = Tier.High;
        /// Set when the frame governor has had to step quality down this session.
        public static int Reductions { get; private set; }

        public static Tier ForModel(string model)
        {
            if (string.IsNullOrEmpty(model) || !model.StartsWith("iPhone")) return Tier.High;
            int comma = model.IndexOf(',');
            if (comma < 0 || !int.TryParse(model.Substring(6, comma - 6), out int generation)) return Tier.Standard;
            if (generation >= 16) return Tier.High;
            if (generation == 15) return Tier.Standard;
            return Tier.Low;
        }

        public struct Settings
        {
            public int Msaa, PixelLights;
            public ShadowQuality Shadows;
            public ShadowResolution ShadowResolution;
            public float ShadowDistance;
            public int ShadowCascades;
        }

        public static Settings For(Tier tier) => tier switch
        {
            Tier.High => new Settings { Msaa = 4, PixelLights = 2, Shadows = ShadowQuality.All, ShadowResolution = ShadowResolution.VeryHigh, ShadowDistance = 60, ShadowCascades = 1 },
            Tier.Standard => new Settings { Msaa = 4, PixelLights = 1, Shadows = ShadowQuality.All, ShadowResolution = ShadowResolution.High, ShadowDistance = 38, ShadowCascades = 1 },
            _ => new Settings { Msaa = 2, PixelLights = 1, Shadows = ShadowQuality.HardOnly, ShadowResolution = ShadowResolution.Medium, ShadowDistance = 32, ShadowCascades = 1 },
        };

        public static void Apply() => Apply(ForModel(SystemInfo.deviceModel));

        // ---- What this phone held the last time (2026-11-15, "consistently smooth 60 fps for everyone") ----
        // Every launch used to start again from the tier's full settings, so a phone that cannot hold them spent the first minute
        // or more of every match below 60 while the governor found its level one step at a time (4 s to settle, then 2–6 s of late
        // frames, per step; golf's shadow reach alone is eight steps). The steps a phone needed in a sport are remembered and
        // taken at once at its next launch, under the loading screen. After three sessions that held their level for a minute
        // without a further step, one step back up is tried, so a phone that was only hot that day gets its picture back.
        public const int CalmSessionsToStepUp = 3;
        const string Memory = "quality.v1.";
        static string memory; static bool replaying;
        /// The steps taken from memory at this launch.
        public static int Remembered { get; private set; }

        /// Settings → Picture: Sharp (11-22). The tier's full effects and, on the phone's own screen, the panel's own resolution; nothing is
        /// stepped down for time (a ProMotion phone at 120 may still drop to 60). Smooth (the default) holds the frame rate first.
        public static bool Sharp;

        /// The phone's tier for `sport` ("tennis", "golf", "bowling"), then the steps down it needed there before, remembered apart for a TV
        /// and the phone's own screen (11-22: a phone that needed steps for one should not start the other below its level).
        public static void Apply(string sport, bool external = false)
        {
            Apply();
            memory = string.IsNullOrEmpty(sport) || Sharp ? null : Memory + sport + (external ? ".tv" : ".phone");
            Remembered = 0;
            if (memory == null || Application.isEditor) return;
            int level = PlayerPrefs.GetInt(memory, 0), calm = PlayerPrefs.GetInt(memory + ".calm", 0);
            if (level > 0 && PlayerPrefs.GetInt(memory + ".held", 0) == 1 && PlayerPrefs.GetInt(memory + ".stepped", 0) == 0 && ++calm >= CalmSessionsToStepUp) { level--; calm = 0; }
            PlayerPrefs.SetInt(memory, level); PlayerPrefs.SetInt(memory + ".calm", calm);
            PlayerPrefs.SetInt(memory + ".held", 0); PlayerPrefs.SetInt(memory + ".stepped", 0);
            replaying = true;
            try { while (Remembered < level && StepDown(Pipeline)) Remembered++; } finally { replaying = false; }
            if (Remembered > 0) Debug.Log($"[TennisQuality] {sport}: {Remembered} step(s) down from the start, as this phone needed last time");
        }

        /// A governor's word that this session has run a minute at its level without late frames.
        public static void MarkHeld() { if (memory != null && !Application.isEditor && PlayerPrefs.GetInt(memory + ".held", 0) == 0) PlayerPrefs.SetInt(memory + ".held", 1); }

        /// The game drawn on the phone's own screen (no TV): its 3D is drawn 1080 lines across the short side, not the panel's
        /// 1179 to 1320, and scaled up under the interface (which stays at the panel's own sharpness). That is 16 to 33 % fewer
        /// pixels to shade, and still Adnan's floor of 1080p. A TV is drawn at its own size, as before.
        public const int PhoneLines = 1080;
        public static bool PhoneScreenCap = true;
        public static void FitScreen(bool external)
        {
            var urp = Pipeline; if (!urp) return;
            int lines = Mathf.Min(Screen.width, Screen.height);
            urp.renderScale = !PhoneScreenCap || Sharp || external || lines <= PhoneLines ? 1f : Mathf.Max(.75f, PhoneLines / (float)lines);
        }
        // what the steps have done to the shadows so far: golf sets its own long shadows when its scene wakes, after Apply
        static bool cascadesCut; static float shadowScale = 1;

        static UniversalRenderPipelineAsset live;

        /// Under URP the pipeline asset owns MSAA, shadows and render scale. Each session
        /// works on its own copy so tier changes and governor step-downs never edit the asset
        /// on disk.
        public static UniversalRenderPipelineAsset Pipeline
        {
            get
            {
                if (live) return live;
                // In the editor, reassigning the pipeline writes into the project's settings;
                // the editor always runs the asset as authored (the High tier) instead.
                if (Application.isEditor) return null;
                var shared = GraphicsSettings.defaultRenderPipeline as UniversalRenderPipelineAsset;
                if (!shared) return null;
                live = Object.Instantiate(shared); live.name = shared.name + " (session)";
                GraphicsSettings.defaultRenderPipeline = live;
                QualitySettings.renderPipeline = live;
                return live;
            }
        }

        public static void Apply(Tier tier)
        {
            Current = tier; Reductions = 0; cascadesCut = false; shadowScale = 1; GolfArcade.Bowling.BowlingLaneMirror.Divisor = 2;
            var s = For(tier);
            QualitySettings.antiAliasing = s.Msaa;
            QualitySettings.pixelLightCount = s.PixelLights;
            QualitySettings.shadows = s.Shadows;
            QualitySettings.shadowResolution = s.ShadowResolution;
            QualitySettings.shadowDistance = s.ShadowDistance;
            QualitySettings.shadowCascades = s.ShadowCascades;
            QualitySettings.anisotropicFiltering = AnisotropicFiltering.Enable;
            QualitySettings.lodBias = tier == Tier.Low ? .8f : 1.2f;
            QualitySettings.skinWeights = SkinWeights.FourBones;
            QualitySettings.globalTextureMipmapLimit = 0;
            var urp = Pipeline;
            if (urp)
            {
                urp.msaaSampleCount = s.Msaa;
                urp.shadowDistance = s.ShadowDistance;
                urp.shadowCascadeCount = s.ShadowCascades;
                urp.mainLightShadowmapResolution = s.ShadowResolution switch
                { ShadowResolution.VeryHigh => 4096, ShadowResolution.High => 2048, ShadowResolution.Medium => 1024, _ => 512 };
                urp.supportsHDR = true; // Tone mapping stays active; Low drops bloom and AO.
                urp.renderScale = 1f;
            }
            SetAmbientOcclusion(tier == Tier.High);
        }

        /// Golf's camera flies the length of a hole: sun shadows cover all of it, so no shadow edge fades
        /// in ahead of the camera as it travels; cascades keep the tee and the ball sharp. Off puts
        /// the tier's own shadows back (the plaza and tennis). In the editor the pipeline asset is the
        /// project's own, so it is only touched for review captures (GOLF_EDITOR_LONG_SHADOWS=1).
        public static void SetGolfShadows(bool on)
        {
            var urp = Pipeline;
            if (!urp && Application.isEditor && System.Environment.GetEnvironmentVariable("GOLF_EDITOR_LONG_SHADOWS") == "1")
                urp = GraphicsSettings.defaultRenderPipeline as UniversalRenderPipelineAsset;
            if (!urp) return;
            var s = For(Current);
            if (!on) { urp.shadowDistance = s.ShadowDistance; urp.shadowCascadeCount = s.ShadowCascades; return; }
            // (less the steps down already taken: the ones remembered from this phone's last round are taken before the course wakes)
            urp.shadowDistance = Mathf.Max(MinShadowDistance, GolfShadowDistance * shadowScale);
            // (four cascades keep the address shadow sharpest; two cost half the shadow passes and read the same in flight)
            urp.shadowCascadeCount = cascadesCut ? 1 : Current == Tier.High ? 4 : 2;
            urp.cascade2Split = .18f;
            urp.cascade4Split = new Vector3(.05f, .14f, .38f);
        }
        /// The shortest shadow reach a step-down leaves: the players and the ball still cast shadows.
        public const float MinShadowDistance = 25f;
        public static float GolfShadowDistance => Current == Tier.High ? 320 : Current == Tier.Standard ? 260 : 180;

        /// Screen-space AO is the most expensive effect; only the High tier keeps it.
        static void SetAmbientOcclusion(bool on)
        {
            var data = Resources.Load<UniversalRendererData>("Tennis/Rendering/TennisURP_Renderer");
            if (!data) return;
            foreach (var feature in data.rendererFeatures)
                if (feature is ScreenSpaceAmbientOcclusion && feature.isActive != on && !Application.isEditor) feature.SetActive(on);
        }

        /// Called by the frame governor when frames are consistently late. Each step trades
        /// a little image quality for time; smoothness wins over sharpness.
        /// FRAME_RATE_60B: never the resolution. Adnan's floor is 60 fps at 1080p or more, and a render scale of .85 drew a
        /// 1080p TV at 918 lines (and the phone below 1080), so the steps are effects only: MSAA, AO, cascades, shadow reach
        /// and level of detail. The render scale stays at 1 (TennisQuality.Apply sets it).
        public static bool StepDown()
        {
            if (Sharp || !StepDown(Pipeline)) return false;
            // remembered for this phone's next launch of the sport (Apply(sport))
            if (memory != null && !replaying && !Application.isEditor)
            {
                PlayerPrefs.SetInt(memory, PlayerPrefs.GetInt(memory, 0) + 1); PlayerPrefs.SetInt(memory + ".stepped", 1); PlayerPrefs.SetInt(memory + ".calm", 0);
            }
            return true;
        }

        /// One step down on `urp` (the session's pipeline copy; tests pass their own).
        public static bool StepDown(UniversalRenderPipelineAsset urp)
        {
            if (!urp) return false;
            if (urp.msaaSampleCount > 2) urp.msaaSampleCount = 2;
            else if (Current == Tier.High && !Application.isEditor) { SetAmbientOcclusion(false); Current = Tier.Standard; }
            else if (GolfArcade.Bowling.BowlingLaneMirror.Running && GolfArcade.Bowling.BowlingLaneMirror.Divisor < 4) GolfArcade.Bowling.BowlingLaneMirror.Divisor = 4;   // (the lanes' mirror at a quarter)
            else if (urp.shadowCascadeCount > 1) { urp.shadowCascadeCount = 1; cascadesCut = true; }
            else if (urp.shadowDistance > MinShadowDistance + 1) { urp.shadowDistance = Mathf.Max(MinShadowDistance, urp.shadowDistance * .7f); QualitySettings.shadowDistance = urp.shadowDistance; shadowScale *= .7f; }
            else if (QualitySettings.lodBias > .75f) QualitySettings.lodBias = .7f;
            else if (urp.msaaSampleCount > 1) urp.msaaSampleCount = 1;
            else return false;
            Reductions++;
            return true;
        }
    }
}
