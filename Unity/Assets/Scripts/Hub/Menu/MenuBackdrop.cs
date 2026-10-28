using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Hub.Menu
{
    /// MENU BACKDROP (Adnan 10-28: "a dynamic one where it's them on a random course"; then "they should still stand straight like the
    /// previous menu, but the background changes", centred, feet on the floor). The plaza is swapped for one of ten venue plates, picked at
    /// random each time the menu opens: a still of the real venue rendered from the menu camera's pose (MenuShots.CentreShot) with the hero
    /// hidden and no post, pre-blurred except the floor round the feet (Resources/Menu/Backdrops/<venue>.jpg, baked by MenuVenueStand +
    /// work/menu-backdrop/bake_plates.py). It is drawn on a camera-locked quad; the venue's own sun and ambient (<venue>_light.json, the sun
    /// camera-relative) light the live heroes, and a shadow catcher puts their shadows on the plate's floor. Loading a venue scene behind the
    /// menu was rejected: the plaza plus a map is what the phone's memory kill (10-26) was made of; a plate is one texture.
    [DefaultExecutionOrder(10010)]   // after DreamEnvironment (10000) and MajesticVenue (10002), which set the sun and ambient every frame
    public sealed class MenuBackdrop : MonoBehaviour
    {
        public static readonly string[] Venues =
        {
            "tennis-resort", "tennis-skyscraper", "tennis-volcano", "golf-cliffside", "golf-wildisles", "golf-magma",
            "bowling-club", "bowling-neon", "bowling-tiki", "bowling-magma",
        };
        /// Off: the plaza as before. Read when the menu builds.
        public static bool On = true;
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

        /// The venue on show ("golf-cliffside"), null when no plate loaded (the plaza stays).
        public string Venue { get; private set; }
        Camera cam; Transform plate, floor; Material plateMat, catcherMat; Preset light; MenuStage stage;
        readonly Vector4[] feet = new Vector4[4];
        static readonly int FeetId = Shader.PropertyToID("_Feet");

        /// Picks a venue (MENU_BACKDROP=<venue> pins one for captures), hides the plaza under `scenery` and stands the line-up on the plate.
        public static MenuBackdrop Attach(HubWorld world, MenuStage stage, Transform scenery)
        {
            if (!On || !world || !world.Camera) return null;
            string venue = Pick();
            var tex = Resources.Load<Texture2D>("Menu/Backdrops/" + venue);
            var json = Resources.Load<TextAsset>("Menu/Backdrops/" + venue + "_light");
            var plateShader = Shader.Find("GolfArcade/MenuBackdrop"); var catcherShader = Shader.Find("GolfArcade/MenuShadowCatcher");
            if (!tex || !json || !plateShader || !catcherShader) { Debug.LogWarning("[Menu] backdrop " + venue + " missing: the plaza stays"); return null; }
            var b = world.gameObject.AddComponent<MenuBackdrop>();
            b.Venue = venue; b.stage = stage; b.cam = world.Camera;
            b.light = JsonUtility.FromJson<Preset>(json.text);
            if (scenery) scenery.gameObject.SetActive(false);
            b.Build(tex, plateShader, catcherShader);
            b.hideUntil = Time.unscaledTime + 10; b.HideScenery();
            foreach (var root in world.gameObject.scene.GetRootGameObjects()) if (root.name == "Majestic dressing") root.SetActive(false);
            b.ApplyLight();
            Lighten();
            MenuShots.Centred = true;
            if (stage) stage.GoTo(MenuShots.Low, snap: true);
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

        /// MENU SPEED (Adnan 10-28: "make the menu faster, it moves at like 30 frames"): with the plaza gone the frame is the line-up, the plate
        /// and the UI, so what only the plaza needed goes too: depth of field (the plate carries its own blur), bloom's bicubic upsampling, and
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
            sun.color = light.sunColor; sun.intensity = light.sunIntensity; sun.shadowStrength = light.shadowStrength;
            RenderSettings.ambientMode = (AmbientMode)light.ambientMode;
            RenderSettings.ambientSkyColor = light.ambientSky; RenderSettings.ambientEquatorColor = light.ambientEquator; RenderSettings.ambientGroundColor = light.ambientGround;
            RenderSettings.ambientLight = light.ambientSky;   // Flat ambient reads ambientLight
            RenderSettings.ambientIntensity = light.ambientIntensity;
            RenderSettings.fog = false;
        }

        /// Everything the hub draws except the heroes and the backdrop: the plaza root is off, but kits that attach to the hub itself arrive
        /// later, so the first seconds sweep again; the Majestic plaza dressing (bunting, flower pots) is a scene root of its own that the
        /// kit may rebuild, so that one is checked for as long as the menu shows.
        float hideUntil;
        void HideScenery()
        {
            foreach (var r in GetComponentsInChildren<Renderer>())   // active only: the plaza root is off, its thousands need no visit
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
            plate.localPosition = new Vector3(0, 0, PlateDistance); plate.localRotation = Quaternion.identity; plate.localScale = new Vector3(h * cam.aspect, h, 1);
            // the venue's light, every frame: the plaza's sky and weather layers drive the same sun and ambient in their own updates
            ApplyLight();
            // the sun keeps the venue's angle to the camera (the plate was lit from there)
            var sun = RenderSettings.sun; if (sun && light.sunDirCam.sqrMagnitude > 1e-4f) sun.transform.rotation = cam.transform.rotation * Quaternion.LookRotation(light.sunDirCam.normalized);
            // contact darkening under whoever stands in the line-up
            int heroes = stage ? (stage.Solo ? 1 : stage.Heroes) : 1;
            for (int i = 0; i < feet.Length; i++)
            {
                var s = MenuShots.Slots[Mathf.Min(i, MenuShots.Slots.Length - 1)];
                feet[i] = new Vector4(s.x, s.z, 0, i < heroes ? 1 : 0);
            }
            catcherMat.SetVectorArray(FeetId, feet);
        }

        void OnDestroy()
        {
            MenuShots.Centred = false;
            GolfArcade.Tennis.TennisQuality.SetGolfShadows(false);   // the tier's own shadows back
            if (plate) Destroy(plate.gameObject); if (floor) Destroy(floor.gameObject);
            if (plateMat) Destroy(plateMat); if (catcherMat) Destroy(catcherMat);
        }
    }
}
