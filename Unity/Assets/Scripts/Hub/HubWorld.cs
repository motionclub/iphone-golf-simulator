using System.Collections;
using System.Collections.Generic;
using GolfArcade.Tennis;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub
{
    /// The menu's host (PLAN_PointerMenu.md): Hub.unity's only authored object. It builds the menu's camera, light and post
    /// (MenuLight), spawns the player's match hero on the line-up, and attaches the stage (MenuStage: the camera's shots and the squad),
    /// the HUD (MenuHud) and the venue plate behind the heroes (MenuBackdrop). Also the TV toast and the fade.
    /// (Until 2026-11-15 this also built the walk-around Plaza the menu replaced: its buildings, rooms, doors, benches and follow
    /// camera. The class, the scene and the `hub` wire names keep their names; the scene references this script by guid.)
    [DefaultExecutionOrder(-100)]
    public sealed class HubWorld : MonoBehaviour
    {
        public static HubWorld Instance { get; private set; }
        /// The menu draws only this layer, so a match scene loading at the same place (both sit at the origin) stays out of its shots.
        public const int Layer = 29;
        public static void SetLayer(Transform t) { foreach (var c in t.GetComponentsInChildren<Transform>(true)) c.gameObject.layer = Layer; }

        public Camera Camera { get; private set; }
        public HubPlayer Player { get; private set; }
        public bool Initialized { get; private set; }

        Image fade; Canvas overlay; bool building;

        public static HubWorld Find() => Instance ? Instance : FindFirstObjectByType<HubWorld>();

        /// Set by the session before the scene loads, so the right hero is built the first time.
        public static bool StartFemale;
        /// Set by the session before the scene loads: Awake leaves the build to BuildSteps, which the session runs a step a frame
        /// and reports as the TV's loading bar, instead of building everything in one multi-second frame.
        public static bool DeferBuild;
        /// Phone only (no TV connected): the menu fills the phone's own screen (MenuHud.Phone). Set by the session before the scene loads.
        public static bool PhoneOnly;
        /// The menu's venue plate (null: none could be loaded, the heroes stand on a plain colour).
        public global::GolfArcade.Hub.Menu.MenuBackdrop Backdrop { get; private set; }
        public Menu.MenuStage Menu { get; private set; }
        public Menu.MenuHud Hud { get; private set; }

        void Awake()
        {
            Instance = this;
            if (!GetComponent<GolfArcade.Game.PlazaMusic>()) gameObject.AddComponent<GolfArcade.Game.PlazaMusic>();
            if (!DeferBuild) Build(StartFemale);
            DeferBuild = false;   // one menu only: a later load (a test's, a retry's) builds itself again
        }
        void OnDestroy() { if (Instance == this) Instance = null; }

        /// Builds everything. `female` picks the hero; the look is applied afterwards (ApplyLook) by the session.
        public void Build(bool female) { var steps = BuildSteps(female); while (steps.MoveNext()) { } }

        /// The build one step at a time; Current is the share of it done (0..1, roughly by time) after each step.
        public IEnumerator<float> BuildSteps(bool female)
        {
            if (Initialized || building) yield break;
            building = true;
            BuildCamera();
            MenuLight.Lighting(transform, Camera);
            BuildOverlay();
            var slot0 = global::GolfArcade.Hub.Menu.MenuShots.Slots[0];
            Player = HubPlayer.Spawn(transform, female, slot0, global::GolfArcade.Hub.Menu.MenuShots.FacingYaw(slot0));
            SetLayer(transform);
            Menu = global::GolfArcade.Hub.Menu.MenuStage.Attach(this);
            Hud = global::GolfArcade.Hub.Menu.MenuHud.Attach(this, Menu);
            Backdrop = global::GolfArcade.Hub.Menu.MenuBackdrop.Attach(this, Menu);   // a random course behind the line-up
            yield return .5f;
            Prewarm();
            yield return .62f;
            PrewarmHero(female);
            yield return .72f;
            // (the four baked tailored polos were preloaded here, the last 28 % of this bar, and held for the session; no hero has worn
            // them since the V2 kits, and they left the game on 2026-11-15)
            Initialized = true;
        }

        // ------------------------------------------------------------------ arrival
        /// When to let the stage go at the latest (unscaled time; 0: not set).
        float arrivalAutoStart;
        /// The camera on the opening shot, the hero waiting (before the first frame the TV shows).
        public void PrepareArrival()
        {
            if (!Player || !Camera || !Menu) return;
            Menu.PrepareArrival(); arrivalAutoStart = 0;
        }
        /// The phone's loading screen faded off the TV.
        public void StartArrival() { if (Menu) Menu.Arrive(); }
        /// Arrive at `time` (unscaled) even if the phone never says so.
        public void ArriveBy(float time) { if (Menu && Menu.Arriving) arrivalAutoStart = time; }

        // ------------------------------------------------------------------ look and body
        /// The locker's look on the menu hero (changes show live). Hex strings without '#', "" = the kit's own colour.
        public void ApplyLook(bool female, string skinHex, int skinIndex, string shirt, string shorts, string shoes, string racket, string back = null, string accessorySkin = null)
        {
            if (!Player) return;
            Player.SetHero(female);
            Player.SetBackCarry(back);   // MENU HERO: golf bag or racket on the back (the locker's pick)
            var look = Player.look; if (!look) return;
            var skin = !string.IsNullOrEmpty(skinHex) ? HeroKit.Hex(skinHex) : HeroKit.Hex(HeroKit.SkinHex[Mathf.Clamp(skinIndex, 0, 5)]);
            look.SetSkin(skin);
            look.SetKit(shirt, shorts, shoes);
            look.SetRacketColour(!string.IsNullOrEmpty(racket) ? HeroKit.Hex(racket) : new Color(0, 0, 0, 0));
            HeroAccessories.For(look).SetFinish(accessorySkin);
        }

        // ------------------------------------------------------------------ per frame
        void LateUpdate()
        {
            if (!Initialized || !Menu) return;
            // nobody walks; the stage holds the camera on the line-up (and the menu fills the phone with no TV)
            if (arrivalAutoStart > 0 && Time.unscaledTime >= arrivalAutoStart) { arrivalAutoStart = 0; Menu.Arrive(); }
            Menu.Tick(Time.unscaledDeltaTime);
            if (overlay && Camera) overlay.targetDisplay = Camera.targetDisplay;
            if (Camera && PhoneOnly && Screen.height > 0)
            {
                // no TV: the menu fills the phone, sideways or upright (upright, the camera keeps to the part above the menu's panel)
                var view = global::GolfArcade.Hub.Menu.MenuHud.PhoneCameraRect();
                if (Camera.rect != view) { Camera.rect = view; Camera.ResetAspect(); }
            }
        }

        /// A match always has both bodies on court (you and your rival): their one-time mesh preparation (seconds for a body the
        /// first time) and their clips are done here, while the menu boots behind the loading screen, not when the match starts.
        static readonly List<UnityEngine.Object> keepAlive = new List<UnityEngine.Object>();
        void PrewarmHero(bool female)
        {
            var prefab = TennisCustomization.HeroBase(!female); if (!prefab) return;
            var tmp = Instantiate(prefab, new Vector3(0, -5000, 0), Quaternion.identity); tmp.name = "Hero prewarm";
            var driver = tmp.GetComponent<HeroTennisDriver>();
            if (driver) { driver.enabled = false; driver.ResolvePerformanceClips(); foreach (var slot in driver.slots) if (slot.clip && !keepAlive.Contains(slot.clip)) keepAlive.Add(slot.clip); }
            Destroy(tmp);
            // (then TailoredPoloDeformation.LoadAll, held for the session: reading one later froze the plaza ~2 s (seated load) and the hand-off (LOD))
        }

        /// Renders the menu's shot once, off screen, while it boots: the first frame the TV shows must not pay for uploading the heroes'
        /// meshes, textures and pipeline states.
        void Prewarm()
        {
            if (!Camera) return;
            var rt = RenderTexture.GetTemporary(320, 180, 24); var keep = Camera.targetTexture; var pos = Camera.transform.position; var rot = Camera.transform.rotation; float far = Camera.farClipPlane;
            Camera.targetTexture = rt;
            var s = global::GolfArcade.Hub.Menu.MenuShots.For(global::GolfArcade.Hub.Menu.MenuShots.Low);
            Camera.transform.SetPositionAndRotation(s.position, Quaternion.LookRotation(s.look - s.position)); Camera.farClipPlane = 600; Camera.Render();
            Camera.targetTexture = keep; Camera.transform.SetPositionAndRotation(pos, rot); Camera.farClipPlane = far;
            RenderTexture.ReleaseTemporary(rt);
        }

        // ------------------------------------------------------------------ camera
        void BuildCamera()
        {
            var go = new GameObject("Hub camera"); go.transform.SetParent(transform, false);
            Camera = go.AddComponent<Camera>(); Camera.fieldOfView = 48; Camera.nearClipPlane = .2f;
            Camera.clearFlags = CameraClearFlags.SolidColor; Camera.backgroundColor = new Color(.98f, .72f, .58f);
            go.AddComponent<AudioListener>();
            // NOT MainCamera: a match loading behind the menu looks its own camera up with Camera.main
            Camera.cullingMask = 1 << Layer;
        }

        // ------------------------------------------------------------------ toast (an invite arrived, a friend is joining)
        Image toastBox; Text toastText; Coroutine toastRoutine;
        public string ToastShown => toastBox && toastBox.gameObject.activeSelf ? toastText.text : "";
        /// A short message in the top-right corner of the TV, for ~4 s (a newer one replaces it).
        public void ShowToast(string text, float seconds = 4f)
        {
            if (!overlay || string.IsNullOrEmpty(text)) return;
            if (!toastBox)
            {
                toastBox = new GameObject("Toast").AddComponent<Image>(); toastBox.transform.SetParent(overlay.transform, false);
                toastBox.color = new Color(.063f, .141f, .239f, .94f); toastBox.raycastTarget = false;
                var rt = toastBox.rectTransform; rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(1, 1);
                rt.anchoredPosition = new Vector2(-40, -40); rt.sizeDelta = new Vector2(620, 92);
                var bar = new GameObject("Accent").AddComponent<Image>(); bar.transform.SetParent(toastBox.transform, false); bar.color = new Color(.843f, .941f, .267f); bar.raycastTarget = false;
                var br = bar.rectTransform; br.anchorMin = Vector2.zero; br.anchorMax = new Vector2(0, 1); br.pivot = new Vector2(0, .5f); br.sizeDelta = new Vector2(10, 0); br.anchoredPosition = Vector2.zero;
                toastText = new GameObject("Text").AddComponent<Text>(); toastText.transform.SetParent(toastBox.transform, false);
                toastText.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf"); toastText.fontSize = 30; toastText.fontStyle = FontStyle.Bold;
                toastText.color = new Color(1, .976f, .933f); toastText.alignment = TextAnchor.MiddleLeft; toastText.raycastTarget = false;
                toastText.horizontalOverflow = HorizontalWrapMode.Wrap; toastText.verticalOverflow = VerticalWrapMode.Truncate;
                var tr = toastText.rectTransform; tr.anchorMin = Vector2.zero; tr.anchorMax = Vector2.one; tr.offsetMin = new Vector2(30, 6); tr.offsetMax = new Vector2(-18, -6);
            }
            toastText.text = text; toastBox.gameObject.SetActive(true);
            if (toastRoutine != null) StopCoroutine(toastRoutine);
            toastRoutine = StartCoroutine(HideToast(seconds));
        }
        IEnumerator HideToast(float seconds) { yield return new WaitForSecondsRealtime(seconds); if (toastBox) toastBox.gameObject.SetActive(false); toastRoutine = null; }

        // ------------------------------------------------------------------ overlay: the fade (and the toast's canvas)
        void BuildOverlay()
        {
            var go = new GameObject("Hub overlay"); go.transform.SetParent(transform, false);
            overlay = go.AddComponent<Canvas>(); overlay.renderMode = RenderMode.ScreenSpaceOverlay; overlay.sortingOrder = 30000;
            fade = new GameObject("Fade").AddComponent<Image>(); fade.transform.SetParent(go.transform, false);
            fade.color = new Color(0, 0, 0, 0); fade.raycastTarget = false;
            var rt = fade.rectTransform; rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
        }
        void SetFade(float a) { if (fade) fade.color = new Color(.02f, .02f, .05f, Mathf.Clamp01(a)); }
        /// A match loading behind the menu (0..1, -1 = none): the menu's loader.
        public void MatchLoading(float progress) { if (Hud) Hud.SetLoading(progress); }
        /// The fade to the match (the hand-off of a match that loaded behind the menu).
        public IEnumerator FadeOut(float seconds)
        {
            for (float t = 0; t < seconds; t += Time.unscaledDeltaTime) { SetFade(t / seconds * .85f); yield return null; }
            SetFade(.85f);
        }
        public float FadeAlpha => fade ? fade.color.a : 0;

        /// Tests and proof tools drive the menu themselves; the editor keyboard stays out of their way (MenuHud).
        public static bool EditorDriven;
    }
}
