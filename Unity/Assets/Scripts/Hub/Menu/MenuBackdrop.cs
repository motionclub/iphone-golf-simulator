using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Hub.Menu
{
    /// MENU BACKDROP (Adnan 10-28: "a dynamic one where it's them on a random course"; then "they should still stand straight like the
    /// previous menu, but the background changes", centred, feet on the floor). Behind the line-up stands one of ten venue plates, picked at
    /// random each time the menu opens: a still of the real venue rendered from the menu camera's pose (MenuShots.CentreShot) with the hero
    /// hidden and no post, pre-blurred except the floor round the feet (Resources/Menu/Backdrops/<venue>.jpg, baked by MenuVenueStand +
    /// work/menu-backdrop/bake_plates.py). It is drawn on a camera-locked quad; the venue's own sun and ambient (<venue>_light.json, the sun
    /// camera-relative) light the live heroes, and a shadow catcher puts their shadows on the plate's floor. Loading a venue scene behind the
    /// menu was rejected: the plaza plus a map is what the phone's memory kill (10-26) was made of; a plate is one texture. (The plaza the
    /// plates first covered left the game on 2026-11-15: if no plate loads, the heroes stand on a plain brand colour.)
    [DefaultExecutionOrder(10010)]   // after DreamEnvironment (10000) and MajesticVenue (10002), which set the sun and ambient every frame
    public sealed class MenuBackdrop : MonoBehaviour
    {
        public static readonly string[] Venues =
        {
            "tennis-resort", "tennis-skyscraper", "tennis-volcano", "golf-cliffside", "golf-wildisles", "golf-magma",
            "bowling-club", "bowling-neon", "bowling-tiki", "bowling-magma",
        };
        /// The camera's clear colour when no plate could be loaded (brand navy).
        public static readonly Color FallbackColour = MotionSports.Brand.BrandColors.NavyDeep;
        /// Proof captures: the venue to show instead of a random one.
        public static string Pin;
        const string LastKey = "menu.backdrop.last";
        /// Inside the hub depth of field's 55 m start: the plate carries its own blur, sharp at the heroes' feet.
        const float PlateDistance = 30f;

        [Serializable] class Preset
        {
            public string venue; public Color sunColor = Color.white; public float sunIntensity = 1.4f, shadowStrength = .8f;
            public Vector3 sunDirCam = new Vector3(.3f, -.6f, .7f);
            public int ambientMode = (int)AmbientMode.Trilight; public Color ambientSky, ambientEquator, ambientGround; public float ambientIntensity = 1;
        }

        /// The venue on show ("golf-cliffside").
        public string Venue { get; private set; }
        Camera cam; Transform plate, floor; Material plateMat, catcherMat; Preset light; MenuStage stage;
        readonly Vector4[] feet = new Vector4[4];
        static readonly int FeetId = Shader.PropertyToID("_Feet");

        /// Picks a venue (MENU_BACKDROP=<venue> pins one for captures) and stands the line-up on its plate. The squad and its one centred
        /// shot hold either way; null when no plate could be loaded: every other venue is tried first, then the heroes stand on a plain
        /// brand colour (and an error is logged).
        public static MenuBackdrop Attach(HubWorld world, MenuStage stage)
        {
            if (!world || !world.Camera) return null;
            MenuShots.Centred = true;
            if (stage) stage.GoTo(MenuShots.Low, snap: true);
            var plateShader = Shader.Find("GolfArcade/MenuBackdrop"); var catcherShader = Shader.Find("GolfArcade/MenuShadowCatcher");
            string venue = Pick(); Texture2D tex = null; TextAsset json = null;
            if (plateShader && catcherShader)
                for (int i = -1; i < Venues.Length; i++)
                {
                    // the picked venue first, then the others in order
                    string v = i < 0 ? venue : Venues[i]; if (i >= 0 && v == venue) continue;
                    tex = Resources.Load<Texture2D>("Menu/Backdrops/" + v);
                    json = Resources.Load<TextAsset>("Menu/Backdrops/" + v + "_light");
                    if (tex && json) { venue = v; break; }
                    Debug.LogWarning("[Menu] backdrop " + v + " missing: trying another venue");
                    tex = null; json = null;
                }
            if (!tex || !json)
            {
                world.Camera.clearFlags = CameraClearFlags.SolidColor; world.Camera.backgroundColor = FallbackColour;
                Debug.LogError("[Menu] no backdrop plate could be loaded" + (plateShader && catcherShader ? "" : " (the backdrop shaders are missing)") + ": the menu shows a plain colour behind the heroes");
                return null;
            }
            var b = world.gameObject.AddComponent<MenuBackdrop>();
            b.Venue = venue; b.stage = stage; b.cam = world.Camera;
            b.light = JsonUtility.FromJson<Preset>(json.text);
            b.Build(tex, plateShader, catcherShader);
            b.hideUntil = Time.unscaledTime + 10; b.HideScenery();
            foreach (var root in world.gameObject.scene.GetRootGameObjects()) if (root.name == "Majestic dressing") root.SetActive(false);
            b.ApplyLight();
            Lighten();
            return b;
        }

        static string Pick()
        {
            var pinned = !string.IsNullOrEmpty(Pin) ? Pin : Environment.GetEnvironmentVariable("MENU_BACKDROP");
            if (!string.IsNullOrEmpty(pinned) && Array.IndexOf(Venues, pinned) >= 0) return pinned;
            // a different course from last time
            string last = PlayerPrefs.GetString(LastKey, "");
            int pick = UnityEngine.Random.Range(0, Venues.Length);
            if (Venues[pick] == last) pick = (pick + 1 + UnityEngine.Random.Range(0, Venues.Length - 1)) % Venues.Length;
            PlayerPrefs.SetString(LastKey, Venues[pick]);
            return Venues[pick];
        }

        void Build(Texture2D tex, Shader plateShader, Shader catcherShader)
        {
            var quad = Resources.GetBuiltinResource<Mesh>("Quad.fbx");
            plate = new GameObject("Menu backdrop").transform; plate.SetParent(cam.transform, false); plate.gameObject.layer = HubWorld.Layer;
            plate.gameObject.AddComponent<MeshFilter>().sharedMesh = quad;
            var pr = plate.gameObject.AddComponent<MeshRenderer>(); pr.shadowCastingMode = ShadowCastingMode.Off; pr.receiveShadows = false;
            tex.wrapMode = TextureWrapMode.Clamp;   // no bleed from the opposite edge at the frame border
            plateMat = new Material(plateShader) { name = "Menu backdrop " + Venue }; plateMat.SetTexture("_BaseMap", tex); pr.sharedMaterial = plateMat;
            // the floor under the line-up: shadows and a contact darkening, nothing else
            floor = new GameObject("Menu backdrop floor").transform; floor.SetParent(transform, false); floor.gameObject.layer = HubWorld.Layer;
            floor.position = MenuShots.Slots[0] + Vector3.up * .003f; floor.rotation = Quaternion.Euler(90, 0, 0); floor.localScale = new Vector3(9, 9, 1);
            floor.gameObject.AddComponent<MeshFilter>().sharedMesh = quad;
            var fr = floor.gameObject.AddComponent<MeshRenderer>(); fr.shadowCastingMode = ShadowCastingMode.Off;
            catcherMat = new Material(catcherShader) { name = "Menu backdrop floor" }; catcherMat.SetFloat("_Strength", Mathf.Clamp01(light.shadowStrength * .85f)); fr.sharedMaterial = catcherMat;
        }

        /// MENU SPEED (Adnan 10-28: "make the menu faster, it moves at like 30 frames"): the frame is the line-up, the plate
        /// and the UI, so what only the old plaza needed goes: depth of field (the plate carries its own blur), bloom's bicubic upsampling, and
        /// sun shadows reaching 60 m when only the heroes at ~5 m cast any (one cascade over 14 m: cheaper and sharper).
        static void Lighten()
        {
            foreach (var v in UnityEngine.Object.FindObjectsByType<Volume>(FindObjectsSortMode.None))
            {
                var profile = v.HasInstantiatedProfile() ? v.profile : v.sharedProfile; if (!profile) continue;
                if (profile.TryGet(out UnityEngine.Rendering.Universal.DepthOfField dof)) dof.active = false;
                if (profile.TryGet(out UnityEngine.Rendering.Universal.Bloom bloom)) bloom.highQualityFiltering.Override(false);
            }
            // the camera's post keeper re-asserts its depth of field every frame: ask it instead
            foreach (var p in UnityEngine.Object.FindObjectsByType<GolfArcade.Tennis.SportsPostProcessing>(FindObjectsSortMode.None)) p.RequestDepthOfField(false);
            var urp = GolfArcade.Tennis.TennisQuality.Pipeline;
            if (urp) { urp.shadowDistance = 14; urp.shadowCascadeCount = 1; QualitySettings.shadowDistance = 14; }
        }

        void ApplyLight()
        {
            var sun = RenderSettings.sun; if (!sun) return;
            if (Midday)
            {
                // MIDDAY (Adnan 11-13 picked "Bright midday" of six looks, work/menu-lineup-1113): one high, near-white sun from the camera's
                // left on every venue, the venue's own sky and ground kept but never so dark that a shadow side goes black (a fill floor
                // on the equator: the light that reaches the heroes from the camera's side)
                sun.color = MiddaySun; sun.intensity = Env("MENU_MIDDAY_SUN", 2.2f); sun.shadowStrength = Mathf.Min(light.shadowStrength, .7f);
                RenderSettings.ambientMode = AmbientMode.Trilight;
                var sky = AtLeast(light.ambientSky * 1.15f, .45f, new Color(.76f, .82f, .92f));
                var eq = AtLeast(light.ambientEquator, Env("MENU_MIDDAY_FILL", .70f), new Color(.86f, .85f, .82f));
                RenderSettings.ambientSkyColor = sky; RenderSettings.ambientEquatorColor = eq; RenderSettings.ambientGroundColor = AtLeast(light.ambientGround, .3f, new Color(.5f, .48f, .42f));
                RenderSettings.ambientLight = sky; RenderSettings.ambientIntensity = 1;
                HeroFill();
            }
            else
            {
                sun.color = light.sunColor; sun.intensity = light.sunIntensity; sun.shadowStrength = light.shadowStrength;
                RenderSettings.ambientMode = (AmbientMode)light.ambientMode;
                RenderSettings.ambientSkyColor = light.ambientSky; RenderSettings.ambientEquatorColor = light.ambientEquator; RenderSettings.ambientGroundColor = light.ambientGround;
                RenderSettings.ambientLight = light.ambientSky;   // Flat ambient reads ambientLight
                RenderSettings.ambientIntensity = light.ambientIntensity;
            }
            RenderSettings.fog = false;
            if (HeroLookOn) MenuGrade();
        }
        static readonly bool Midday = Environment.GetEnvironmentVariable("MENU_MIDDAY") != "0";
        // the heroes' own front fill (HeroLighting.hlsl: _HeroFillColor x _HeroPresentationFill, 0.5 in play) and skin light, raised for the
        // menu only: the hero shaders roll bright light off, so a stronger sun barely lifts them, the fill from the camera does
        static readonly int FillId = Shader.PropertyToID("_HeroPresentationFill"), FillColourId = Shader.PropertyToID("_HeroFillColor"), SkinId = Shader.PropertyToID("_HeroSkinLightExposure");
        float savedFill = -1, savedSkin, setFill, setSkin; Vector4 savedFillColour, setFillColour;
        void HeroFill()
        {
            if (savedFill < 0) { savedFill = Shader.GetGlobalFloat(FillId); savedSkin = Shader.GetGlobalFloat(SkinId); savedFillColour = Shader.GetGlobalVector(FillColourId); }
            setFill = Env("MENU_HERO_FILL", 1.1f); setSkin = Env("MENU_HERO_SKIN", 1.15f);
            var c = new Color(1f, .97f, .94f).linear; setFillColour = new Vector4(c.r, c.g, c.b, 1);
            Shader.SetGlobalFloat(FillId, setFill); Shader.SetGlobalFloat(SkinId, setSkin); Shader.SetGlobalVector(FillColourId, setFillColour);
        }
        /// Leaving the menu: the play values back, unless a sport's own profile has already set its own.
        void RestoreHeroFill()
        {
            if (savedFill < 0) return;
            if (Mathf.Approximately(Shader.GetGlobalFloat(FillId), setFill)) Shader.SetGlobalFloat(FillId, savedFill);
            if (Mathf.Approximately(Shader.GetGlobalFloat(SkinId), setSkin)) Shader.SetGlobalFloat(SkinId, savedSkin);
            if (Shader.GetGlobalVector(FillColourId) == setFillColour) Shader.SetGlobalVector(FillColourId, savedFillColour);
        }
        static readonly Color MiddaySun = new Color(1f, .96f, .9f);
        /// From the camera's left (35 degrees round) and high (55 degrees up), in camera space: the way the light travels.
        static readonly Vector3 MiddaySunCam = new Vector3(.329f, -.819f, .470f);
        /// `c`, blended toward `toward` until its brightness (luma) is at least `min`.
        static Color AtLeast(Color c, float min, Color toward)
        {
            float l = .2126f * c.r + .7152f * c.g + .0722f * c.b, lt = .2126f * toward.r + .7152f * toward.g + .0722f * toward.b;
            if (l >= min || lt <= l) return c;
            return Color.Lerp(c, toward, Mathf.Clamp01((min - l) / (lt - l)));
        }

        // HERO LOOK (work/hero-look-1111, clone only): the menu keeps the plaza's golden-hour grade (contrast 22, saturation 26, temperature 6,
        // warm highlights), which turns skin yellow on every venue plate. A calmer menu grade: the venue's light does the mood, not the grade.
        bool gazeDone;
        static readonly bool HeroLookOn = Environment.GetEnvironmentVariable("HERO_LOOK") != "0";
        static float Env(string k, float d) => float.TryParse(Environment.GetEnvironmentVariable(k), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : d;
        static void MenuGrade()
        {
            foreach (var v in UnityEngine.Object.FindObjectsByType<Volume>(FindObjectsSortMode.None))
            {
                var profile = v.HasInstantiatedProfile() ? v.profile : v.sharedProfile; if (!profile) continue;
                // midday: a little less colour and a softer contrast than the plaza's grade (the picked look: saturation 1.08, contrast 1.0); four strengths filmed 11-13, work/menu-squad-1113
                if (profile.TryGet(out UnityEngine.Rendering.Universal.ColorAdjustments ca)) { ca.saturation.Override(Env("HERO_LOOK_SAT", Midday ? 8 : 14)); ca.contrast.Override(Env("HERO_LOOK_CONTRAST", Midday ? 4 : 20)); ca.colorFilter.Override(Color.white); }
                if (profile.TryGet(out UnityEngine.Rendering.Universal.WhiteBalance wb)) { wb.temperature.Override(Env("HERO_LOOK_TEMP", 1)); wb.tint.Override(0); }
                if (profile.TryGet(out UnityEngine.Rendering.Universal.ShadowsMidtonesHighlights smh)) { smh.midtones.Override(new Vector4(1, 1, 1, 0)); smh.highlights.Override(new Vector4(1.01f, 1f, .99f, 0)); }
            }
        }

        /// Everything the hub draws except the heroes and the backdrop: layers that attach to the hub itself arrive later, so the first
        /// seconds sweep again; the Majestic dressing is a scene root of its own (empty for the menu), kept off as long as the menu shows.
        float hideUntil;
        void HideScenery()
        {
            foreach (var r in GetComponentsInChildren<Renderer>())
            {
                if (r.forceRenderingOff || (plate && r.transform.IsChildOf(plate)) || (floor && r.transform.IsChildOf(floor))) continue;
                if (r.GetComponentInParent<GolfArcade.Tennis.MatchHeroLook>(true)) continue;   // heroes (their LOD owns forceRenderingOff)
                r.forceRenderingOff = true;
            }
        }

        void LateUpdate()
        {
            if (!cam || !plate) return;
            if (Time.unscaledTime < hideUntil && Time.frameCount % 20 == 0) { HideScenery(); Lighten(); }   // late volumes (the Majestic grade) too
            if (Time.frameCount % 30 == 0)
                foreach (var root in gameObject.scene.GetRootGameObjects()) if (root.activeSelf && root.name == "Majestic dressing") root.SetActive(false);
            // the plate fills the frustum exactly at PlateDistance (the camera's fov and aspect can change: phone-only band, shots)
            float h = 2 * PlateDistance * Mathf.Tan(cam.fieldOfView * .5f * Mathf.Deg2Rad);
            // (an upright phone's lens shift, MenuStage.Frame, moves the view up or down: the plate follows it so it still fills the view)
            plate.localPosition = new Vector3(0, cam.projectionMatrix[1, 2] * h * .5f, PlateDistance); plate.localRotation = Quaternion.identity; plate.localScale = new Vector3(h * cam.aspect, h, 1);
            // the picture keeps its own shape: a wider view (a phone held sideways; MenuStage narrows the lens to the plate's width) shows
            // its middle band, a narrower one (upright) its middle strip
            var tex = plateMat.GetTexture("_BaseMap"); float plateAspect = tex && tex.height > 0 ? (float)tex.width / tex.height : 16f / 9f, a = cam.aspect;
            var crop = a >= plateAspect ? new Vector2(1, plateAspect / a) : new Vector2(a / plateAspect, 1);
            if (plateMat.GetTextureScale("_BaseMap") != crop) { plateMat.SetTextureScale("_BaseMap", crop); plateMat.SetTextureOffset("_BaseMap", (Vector2.one - crop) * .5f); }
            // the venue's light, every frame: the Majestic layer (MajesticVenue) drives the same sun and ambient in its own update
            ApplyLight();
            if (!gazeDone) { var hw = GetComponent<HubWorld>(); if (hw && hw.Player) { MenuHeroGaze.Attach(hw.Player, cam); gazeDone = true; } }
            // the sun keeps the venue's angle to the camera (the plate was lit from there)
            var dir = Midday ? MiddaySunCam : light.sunDirCam;
            var sun = RenderSettings.sun; if (sun && dir.sqrMagnitude > 1e-4f) sun.transform.rotation = cam.transform.rotation * Quaternion.LookRotation(dir.normalized);
            // contact darkening under whoever stands in the line-up
            int heroes = stage ? (stage.FriendsShown ? stage.Heroes : 1) : 1;
            for (int i = 0; i < feet.Length; i++)
            {
                var s = MenuShots.Slots[Mathf.Min(i, MenuShots.Slots.Length - 1)];
                feet[i] = new Vector4(s.x, s.z, 0, i < heroes ? 1 : 0);
            }
            catcherMat.SetVectorArray(FeetId, feet);
        }

        void OnDestroy()
        {
            RestoreHeroFill();
            GolfArcade.Tennis.TennisQuality.SetGolfShadows(false);   // the tier's own shadows back
            if (plate) Destroy(plate.gameObject); if (floor) Destroy(floor.gameObject);
            if (plateMat) Destroy(plateMat); if (catcherMat) Destroy(catcherMat);
        }
    }
}
