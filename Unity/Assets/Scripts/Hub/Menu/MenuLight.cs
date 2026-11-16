using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UI;

namespace GolfArcade.Hub
{
    /// The menu's light and post (moved here unchanged from the retired Plaza's HubArt / HubKit, 2026-11-15; the approved menu look
    /// was tuned under exactly these values): a low warm sun, a blue-sky / warm-horizon trilight ambient, a sky reflection cubemap
    /// painted from SkyColor, then the "Hub golden hour" volume (neutral tonemapping, gentle warm grade, bloom, vignette, far blur).
    /// MenuBackdrop then sets the venue plate's own sun and ambient over this every frame and calms the grade. Also the world-space
    /// name tag the party's chat bubbles are built from, and its font.
    public static class MenuLight
    {
        /// The sun as seen in the sky (the reflection cubemap's glow), and the direction the light comes from (behind the camera).
        public static readonly Vector3 SunSkyDir = Dir(21, 7.5f), SunLightDir = Dir(176, 25);
        static Color C(string hex) { ColorUtility.TryParseHtmlString("#" + hex, out var c); return c; }
        static Vector3 Dir(float azimuth, float elevation)
        {
            float a = azimuth * Mathf.Deg2Rad, e = elevation * Mathf.Deg2Rad;
            return new Vector3(Mathf.Sin(a) * Mathf.Cos(e), Mathf.Sin(e), Mathf.Cos(a) * Mathf.Cos(e));
        }

        /// The golden-hour sky's colour in a direction (the reflection cubemap): warm gold at the horizon under the sun, peach and soft
        /// lilac above, clear blue overhead, a few lit cloud banks.
        public static Color SkyColor(Vector3 d)
        {
            d.Normalize(); float e = d.y;
            Color c;
            if (e < 0) c = Color.Lerp(C("F5D2A6"), C("C9B8A8"), Mathf.Clamp01(-e * 5));
            else
            {
                var stops = new[] { (0f, C("FFCF8E")), (.035f, C("FBC08E")), (.09f, C("F1BC9E")), (.16f, C("D6C0C8")), (.25f, C("AEC0DF")), (.4f, C("8BABDC")), (.68f, C("6E96D5")), (1f, C("5A84CC")) };
                c = stops[0].Item2;
                for (int k = 1; k < stops.Length; k++) if (e >= stops[k - 1].Item1) c = Color.Lerp(stops[k - 1].Item2, stops[k].Item2, Mathf.InverseLerp(stops[k - 1].Item1, stops[k].Item1, e));
            }
            float sun = Mathf.Max(0, Vector3.Dot(d, SunSkyDir));
            c += C("FFD08A") * (Mathf.Pow(sun, 5) * .32f + Mathf.Pow(sun, 40) * .5f + Mathf.Pow(sun, 500) * .9f);
            c += C("FFDDAE") * Mathf.Exp(-Mathf.Abs(e) * 16) * .16f;
            float flat = Mathf.Max(0, Vector3.Dot(new Vector3(d.x, 0, d.z).normalized, new Vector3(SunSkyDir.x, 0, SunSkyDir.z).normalized));
            c += C("FFB86E") * Mathf.Pow(flat, 6) * Mathf.Exp(-Mathf.Abs(e) * 6) * .3f;
            // cloud banks: soft lumps low in the sky, lit warm on the sun side
            if (e > .02f && e < .42f)
            {
                float az = Mathf.Atan2(d.x, d.z);
                float band = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.03f, .09f, e)) * Mathf.SmoothStep(1, 0, Mathf.InverseLerp(.2f, .42f, e));
                float n = Mathf.PerlinNoise(az * 2.2f + 10, e * 9) * .65f + Mathf.PerlinNoise(az * 6.1f + 3, e * 22) * .35f;
                float cloud = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.5f, .72f, n)) * band;
                var lit = Color.Lerp(C("FFE7CF"), C("FFD3A8"), Mathf.Pow(flat, 3));
                var shade = Color.Lerp(C("E4B9B3"), C("C8B2C8"), Mathf.InverseLerp(.05f, .35f, e));
                c = Color.Lerp(c, Color.Lerp(shade, lit, Mathf.InverseLerp(.5f, .8f, n)), cloud * .85f);
            }
            c.a = 1; return c;
        }

        public static void Lighting(Transform parent, Camera camera)
        {
            // the menu's own shadows, whatever ran before it: golf leaves its 180-320 m, 2-4 cascade sun shadows on the session's
            // pipeline (TennisQuality.SetGolfShadows), which spread the small menu stage over coarse, shimmering cascades on the phone.
            // Off = the tier's own (High: 60 m, one 4096 cascade, MSAA 4x), the setting the editor captures render with.
            GolfArcade.Tennis.TennisQuality.SetGolfShadows(false);
            var sun = new GameObject("Golden-hour sun").AddComponent<Light>(); sun.transform.SetParent(parent, false);
            sun.type = LightType.Directional; sun.color = C("FFD39C"); sun.intensity = 1.42f; sun.shadows = LightShadows.Soft; sun.shadowStrength = .82f;
            sun.shadowBias = .04f; sun.shadowNormalBias = .3f;
            sun.transform.rotation = Quaternion.LookRotation(-SunLightDir, Vector3.up);
            RenderSettings.sun = sun;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = C("A9C1E6") * .74f; RenderSettings.ambientEquatorColor = C("EBCCA6") * .66f; RenderSettings.ambientGroundColor = C("66734A") * .58f;
            RenderSettings.fog = false; RenderSettings.skybox = null;
            // sky reflections on every smooth surface (the slate, the gold, the glass)
            const int size = 64;
            var cube = new Cubemap(size, TextureFormat.RGBA32, false) { name = "Hub sky reflection" };
            for (int f = 0; f < 6; f++)
            {
                var face = (CubemapFace)f; var px = new Color[size * size];
                for (int y = 0; y < size; y++) for (int x = 0; x < size; x++)
                {
                    float u = (x + .5f) / size * 2 - 1, v = (y + .5f) / size * 2 - 1;
                    Vector3 d = face switch
                    {
                        CubemapFace.PositiveX => new Vector3(1, -v, -u), CubemapFace.NegativeX => new Vector3(-1, -v, u),
                        CubemapFace.PositiveY => new Vector3(u, 1, v), CubemapFace.NegativeY => new Vector3(u, -1, -v),
                        CubemapFace.PositiveZ => new Vector3(u, -v, 1), _ => new Vector3(-u, -v, -1)
                    };
                    var c = SkyColor(d.normalized); if (d.y < 0) c = Color.Lerp(c, C("8C9A6A"), Mathf.Clamp01(-d.normalized.y * 3));
                    px[y * size + x] = c;
                }
                cube.SetPixels(px, face);
            }
            cube.Apply(false, true);
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom; RenderSettings.customReflectionTexture = cube; RenderSettings.reflectionIntensity = .8f;
            // camera + post
            camera.allowHDR = true; camera.fieldOfView = 42; camera.nearClipPlane = .3f;
            var data = camera.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = true; data.renderShadows = true; data.antialiasing = AntialiasingMode.None;
            var vol = new GameObject("Hub post-processing"); vol.transform.SetParent(camera.transform, false);
            data.volumeLayerMask = 1 << vol.layer;
            var volume = vol.AddComponent<Volume>(); volume.isGlobal = true; volume.priority = 20;
            var profile = ScriptableObject.CreateInstance<VolumeProfile>(); profile.name = "Hub golden hour";
            var tm = profile.Add<Tonemapping>(true); tm.mode.Override(TonemappingMode.Neutral);
            var ca = profile.Add<ColorAdjustments>(true); ca.postExposure.Override(-.06f); ca.contrast.Override(26); ca.saturation.Override(18); ca.colorFilter.Override(Color.white);
            var wb = profile.Add<WhiteBalance>(true); wb.temperature.Override(4); wb.tint.Override(2);
            var smh = profile.Add<ShadowsMidtonesHighlights>(true);
            smh.shadows.Override(new Vector4(.95f, .97f, 1.08f, -.03f)); smh.midtones.Override(new Vector4(1.01f, 1f, .98f, 0)); smh.highlights.Override(new Vector4(1.03f, 1.0f, .95f, -.02f));
            var bloom = profile.Add<Bloom>(true); bloom.threshold.Override(1.05f); bloom.intensity.Override(.7f); bloom.scatter.Override(.62f); bloom.tint.Override(C("FFE2B8")); bloom.maxIterations.Override(5);
            bloom.highQualityFiltering.Override(true);   // bicubic upsampling: a lantern's or a gold edge's sub-pixel glint no longer pulses its halo
            var vig = profile.Add<Vignette>(true); vig.intensity.Override(.2f); vig.smoothness.Override(.45f); vig.color.Override(C("2A2236"));
            var dof = profile.Add<DepthOfField>(true); dof.mode.Override(DepthOfFieldMode.Gaussian); dof.gaussianStart.Override(55); dof.gaussianEnd.Override(220); dof.gaussianMaxRadius.Override(1.1f); dof.highQualitySampling.Override(true);
            volume.sharedProfile = profile;
            GolfArcade.EnvironmentArt.EnvironmentLook.Hub(RenderSettings.sun);
            camera.gameObject.AddComponent<GolfArcade.Tennis.SportsPostProcessing>().Initialize(volume);
        }

        // ------------------------------------------------------------------ name tag (the chat bubble)
        static Font font;
        public static Font Font => font ??= Resources.Load<Font>("Tennis/UI/Fonts/Rubik-Bold") ?? Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        public static Transform NameTag(Transform parent, string text, Color color)
        {
            var go = new GameObject("Name tag " + text); go.transform.SetParent(parent, false);
            var canvas = go.AddComponent<Canvas>(); canvas.renderMode = RenderMode.WorldSpace;
            var rt = (RectTransform)go.transform; rt.sizeDelta = new Vector2(100, 40); rt.localScale = Vector3.one * .0062f;
            var plate = new GameObject("Plate").AddComponent<Image>(); plate.transform.SetParent(go.transform, false); plate.color = color; plate.raycastTarget = false;
            var prt = plate.rectTransform; prt.anchorMin = Vector2.zero; prt.anchorMax = Vector2.one; prt.offsetMin = prt.offsetMax = Vector2.zero;
            var label = new GameObject("Text").AddComponent<Text>(); label.transform.SetParent(go.transform, false);
            label.font = Font; label.text = text; label.fontSize = 26; label.color = Color.white; label.alignment = TextAnchor.MiddleCenter; label.raycastTarget = false;
            var lrt = label.rectTransform; lrt.anchorMin = Vector2.zero; lrt.anchorMax = Vector2.one; lrt.offsetMin = lrt.offsetMax = Vector2.zero;
            return go.transform;
        }
    }
}
