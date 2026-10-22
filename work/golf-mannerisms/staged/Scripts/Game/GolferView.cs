using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;
using GolfArcade.Course;
using GolfArcade.Shot;

namespace GolfArcade.Game
{
    /// The golfer on screen: Adnan's standard character (Resources/Golfer/golfer_m|f, out of
    /// his sports animation studio via blender/scripts/adnan_golfer_export.py) with a swing
    /// clip per club — Drive, IronSwing, HalfSwing, Chip, Putt — and the club in hand. The phone
    /// drives the clip: the backswing is scrubbed by the detector's load, so the figure winds
    /// up exactly as far as the player does, and on impact the downswing runs through to the
    /// finish at real speed. Without the model a Mii-simple figure of primitives stands in.
    /// Off the course it can also Perform the studio's moves (the intro's wave, the gallery's
    /// idle and cheering), and a spectator is the same figure in a look of its own.
    public sealed class GolferView : MonoBehaviour
    {
        /// Who a figure looks like: the player's comes from GolferStyle; a spectator has its own.
        public struct Look
        {
            public string ModelPath, HairMesh;
            public Color Skin, Hair;
            /// The polo and the trousers, where they differ from the studio's golf kit (teal and
            /// sand); null keeps the kit.
            public Color? Shirt, Trousers;
            /// Adnan's modular Hero, when the build has it and this figure is a player: the look to assemble.
            public HeroLook? Hero;
            public static Look Player => new()
            {
                ModelPath = GolferStyle.ModelPath, HairMesh = GolferStyle.HairMesh,
                Skin = GolferStyle.SkinColor, Hair = GolferStyle.HairColor,
                Shirt = GolferStyle.ShirtColor, Trousers = GolferStyle.TrousersColor,
                Hero = GolferStyle.UseHero ? GolferStyle.Hero : null,
            };
        }
        Look? own;
        Look CurrentLook => own ?? Look.Player;
        /// A spectator: its own look, never holds a club, and isn't animated while off screen.
        bool spectator;

        const float MetresToYards = 1.0936f;

        /// One clip's landmarks, from golfer_<m|f>_clips.json (frames found in Blender from the
        /// club head's path: farthest from address is the top, its closest return is impact).
#pragma warning disable 649 // filled by JsonUtility
        [System.Serializable]
        public class ClipInfo { public string name, club; public int frames, fps, top, impact; }
        [System.Serializable]
        class ClipSet { public string gender; public ClipInfo[] clips; }
#pragma warning restore 649

        // rigged model
        PlayableGraph graph;
        AnimationPlayableOutput output;
        AnimationClipPlayable clip;
        AnimationClip clipAsset;
        // crossfades: the pose being left stays behind, frozen, on the mixer's second input and
        // fades out under the new one, so no change of clip or pose ever pops
        AnimationMixerPlayable mixer;
        AnimationClipPlayable ghost;
        float fade, fadeSeconds;
        readonly Dictionary<string, AnimationClip> clips = new();
        readonly Dictionary<string, ClipInfo> landmarks = new();
        readonly Dictionary<string, GameObject> clubMeshes = new();
        /// The clubs' own materials, before a finish went on them.
        readonly Dictionary<Renderer, Material[]> clubOriginal = new();
        Color? clubFinish;

        /// A finish on every club (Gear.ClubFinish, one of the rewards): the head and the shaft
        /// take its colour, the dark grip stays. Null is the steel as modelled.
        public Color? ClubFinish { get => clubFinish; set { clubFinish = value; DressClubs(); } }

        void DressClubs()
        {
            foreach (var club in clubMeshes.Values)
                foreach (var r in club.GetComponentsInChildren<Renderer>(true))
                {
                    if (!clubOriginal.TryGetValue(r, out var original)) clubOriginal[r] = original = r.sharedMaterials;
                    if (clubFinish is not Color finish) { r.sharedMaterials = original; continue; }
                    var mats = (Material[])original.Clone();
                    for (int i = 0; i < mats.Length; i++)
                    {
                        if (!mats[i]) continue;
                        var c = mats[i].color;
                        if (0.3f * c.r + 0.59f * c.g + 0.11f * c.b < 0.3f) continue;   // the grip
                        mats[i] = FinishedClub(original[i], Color.Lerp(c, finish, 0.85f));
                    }
                    r.sharedMaterials = mats;
                }
        }
        string clipName;
        float TopTime, ImpactTime, EndTime;
        bool hasModel;
        float time;            // clip time being shown
        float loadTarget;      // where the backswing should be, from the phone
        float loadVelocity;    // SmoothDamp's, following it
        /// 0 posing with the load, 2 the downswing, 5 the follow-through, 3 holding the finish, 4 performing a move
        int phase;
        // The swing's tempo, per clip (SetClub). The studio's clips come down from the top in
        // 0.6 s at an even pace; a real downswing takes about a third of a second and speeds up all the way to
        // the ball, and the follow-through leaves the ball at that speed and eases into the
        // finish. So the downswing is played over Downswing seconds with clip time running as
        // u^Accel, and the follow-through as 1-(1-v)^EaseOut over however long matches the club's
        // speed at impact.
        float Downswing = 0.38f, Accel = 1.4f, EaseOut = 2.6f;
        float swingU, swingRate, throughV, throughSeconds, finishTime;
        // A phone swing paces its own downswing (PaceDownswing): the club is as far along its path from the top to the ball as
        // the phone is through the player's turn, so it meets the ball on the sample the phone does, which is the shot's impact (the
        // clock above only runs the swings nothing paces: touch, replays, other players). downArc is the clip time at even
        // shares of the club's path; strikeAt / strikeClip time the paced downswing for the follow-through's pace.
        float pace = -1, paceAt, paceStartShare, strikeAt, strikeClip;
        // the phone's last two downswing samples (its own clock) and the least lag seen between its clock and this frame's
        double paceT0, paceT1, paceLag; float paceP0;
        // the paced downswing's own clip pace (clip seconds a second) over its last frames, which the follow-through carries on
        float paceRate, paceShownAt;
        float[] downArc;
        readonly Dictionary<string, float[]> downArcs = new();

        // primitive fallback
        Transform pivot, club, body;
        float shownLoad;
        float swingThrough = -1;
        const float rest = 20f;

        /// Blender material name → flat game colour, matching the character sheet.
        static readonly Dictionary<string, Color> Palette = new()
        {
            ["MAT_SKIN"] = Rgb(226, 160, 110), ["MAT_SHIRT"] = Rgb(38, 84, 176), ["MAT_TROUSERS"] = Rgb(214, 196, 160),
            ["MAT_BELT"] = Rgb(34, 40, 62), ["MAT_EYE"] = Rgb(28, 24, 22), ["MAT_LOGO"] = Rgb(38, 84, 176),
            ["MAT_CAP"] = Rgb(245, 245, 245), ["MAT_GLOVE"] = Rgb(240, 240, 240), ["MAT_SHOE"] = Rgb(240, 240, 240),
            ["MAT_SHOE_SOLE"] = Rgb(40, 40, 44), ["MAT_SHAFT"] = Rgb(190, 192, 198), ["MAT_CLUBHEAD"] = Rgb(40, 42, 48),
            ["MAT_GRIP"] = Rgb(30, 30, 34), ["MAT_HAIR"] = Rgb(70, 48, 30), ["MAT_LIPS"] = Rgb(196, 84, 90), ["MAT_SHIRT_DARK"] = Rgb(28, 62, 136),
        };
        static Color Rgb(int r, int g, int b) => new(r / 255f, g / 255f, b / 255f);

        /// The kit's cloth, which carries the knit of Adnan's tee and joggers.
        static readonly HashSet<string> Cloth = new()
        {
            "V4 teal", "V4 sand", "V4 navy", "V4 joined hip panel", "V4 golf belt", "MAT_SHIRT", "MAT_TROUSERS", "MAT_SHIRT_DARK",
        };

        static bool IsShirtTrim(string part) =>
            part.StartsWith("Collar") || part.StartsWith("Sleeve piping") || part.StartsWith("Armhole binding")
            || part.StartsWith("V4 shirt button") || part.EndsWith("Golf 1 top");

        static readonly Dictionary<(Color, bool, Texture), Material> clayMaterials = new();
        static Texture2D matCap, knit;

        /// A GolferClay material (Shaders/GolferClay.shader): the soft matte look of Adnan's
        /// studio renders, from a Higgsfield MatCap of his lighting; cloth adds the knit. Falls
        /// back to the course's flat lit material if the shader isn't in the build.
        static Material Clay(Color color, bool cloth, Texture map = null)
        {
            if (clayMaterials.TryGetValue((color, cloth, map), out var m) && m) return m;
            var shader = Shader.Find("GolfArcade/GolferClay");
            if (!shader) return HoleView.Mat(color);
            if (!matCap) matCap = Resources.Load<Texture2D>("Golfer/Look/clay_matcap");
            if (!knit) knit = Resources.Load<Texture2D>("Golfer/Look/knit_detail");
            m = new Material(shader) { color = color };
            if (matCap) m.SetTexture("_MatCap", matCap);
            if (knit) m.SetTexture("_Knit", knit);
            m.SetFloat("_MatCapStrength", .12f);
            m.SetFloat("_Wrap", cloth ? .34f : .32f);
            m.SetFloat("_Fabric", cloth ? .18f : 0f);
            m.SetFloat("_SurfaceSmoothness", cloth ? .12f : .28f);
            m.SetFloat("_SurfaceSpecular", cloth ? .25f : .8f);
            m.SetFloat("_SurfaceSheen", cloth ? .45f : 0f);
            m.SetColor("_SurfaceWarmth", cloth ? Color.black : new Color(.12f, .035f, .02f));
            if (map) { m.SetTexture("_MainTex", map); m.SetFloat("_MatCapStrength", .08f); }   // (the map carries its own shading)
            clayMaterials[(color, cloth, map)] = m;
            return m;
        }

        /// The clubs' finishes (blender/scripts/golf_clubs.py FINISHES): colour, metallic, smoothness.
        static readonly Dictionary<string, (Color color, float metal, float smooth)> ClubFinishes = new()
        {
            ["CLUB chrome"] = (new Color(0.86f, 0.87f, 0.89f), 1f, 0.88f),
            ["CLUB satin"] = (new Color(0.72f, 0.73f, 0.75f), 1f, 0.62f),
            ["CLUB gunmetal"] = (new Color(0.30f, 0.31f, 0.33f), 1f, 0.68f),
            ["CLUB carbon"] = (new Color(0.05f, 0.052f, 0.058f), 0f, 0.70f),
            ["CLUB black"] = (new Color(0.035f, 0.035f, 0.04f), 0f, 0.45f),
            ["CLUB grip"] = (new Color(0.05f, 0.05f, 0.055f), 0f, 0.15f),
            ["CLUB accent"] = (new Color(0.05f, 0.62f, 0.62f), 0f, 0.55f),
            ["CLUB white"] = (new Color(0.92f, 0.92f, 0.90f), 0f, 0.5f),
            ["CLUB groove"] = (new Color(0.10f, 0.10f, 0.11f), 1f, 0.5f),
        };
        static readonly Dictionary<string, Material> clubMaterials = new();

        static readonly Dictionary<(Material, Color), Material> finishedClubMaterials = new();
        static Material FinishedClub(Material source, Color tint)
        {
            if (finishedClubMaterials.TryGetValue((source, tint), out var cached) && cached) return cached;
            // A reward changes the finish colour, retaining the authored metal/carbon roughness.
            // The former clay replacement erased both sky reflections and the material identity.
            var m = new Material(source) { name = source.name + " (finish)" };
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", tint);
            if (m.HasProperty("_Color")) m.SetColor("_Color", tint);
            finishedClubMaterials[(source, tint)] = m;
            return m;
        }



        /// Real metal for the clubs: Standard, so chrome and satin catch the sky.
        static Material ClubMaterial(string name)
        {
            if (clubMaterials.TryGetValue(name, out var m) && m) return m;
            var f = ClubFinishes.TryGetValue(name, out var known) ? known : (color: Color.grey, metal: 0f, smooth: 0.3f);
            var shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            if (!shader) return HoleView.Mat(f.color);
            m = new Material(shader) { name = name, color = f.color };
            m.SetFloat("_Metallic", f.metal);
            m.SetFloat("_Glossiness", f.smooth);
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", f.color);
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", f.smooth);
            clubMaterials[name] = m;
            return m;
        }

        GameObject modelGo;
        Material kitMaterial;
        /// The Hero, when this figure is one (its parts, materials and skeleton); null for the older V4 figure.
        HeroGolfer heroFigure;
        /// Aim footwork: the shoes stay planted and shuffle round the ball as the aim turns (GolferFootwork).
        GolferFootwork footwork;
        public GolferFootwork Footwork => footwork;
        GolfSwingClearance swingClearance;
        GolfArcade.Tennis.HeroPoseSafety poseSafety;
        GolfArcade.Tennis.HeroPoseTransition poseTransition;
        float performanceRate = 1;
        Vector3 leadToeAnchor;
        bool leadToeAnchored;
        /// How the model is turned at rest so the golf clips face the ball (the Hero's export is not yawed as V4's was).
        Quaternion baseRot = Quaternion.identity;

        /// The chosen kit colours on the golfer as they stand, without rebuilding the model.
        /// The older V4 figure's kit: the shorts' and the shirt's colours over its colour map (alpha 0 keeps the map's own).
        static void DressKit(Material m)
        {
            if (!m) return;
            var look = GolferStyle.Current;
            var shorts = GolferStyle.ColorOf(look.Shorts); var shirt = GolferStyle.ColorOf(look.Shirt);
            m.SetFloat("_KitOn", shorts.HasValue ? 1 : 0); m.SetColor("_KitColor", shorts ?? Color.white);
            m.SetFloat("_ShirtOn", shirt.HasValue ? 1 : 0); m.SetColor("_ShirtColor", shirt ?? Color.white);
        }

        public void Redress()
        {
            if (heroFigure != null && CurrentLook.Hero is HeroLook h) heroFigure.Dress(h);
            else DressKit(kitMaterial);
        }

        // ----- The face: Adnan's expression atlas (Resources/Golfer/Look/FaceAtlas, 4 × 2 cells in
        // this order, as his TennisActor uses it) on the Higgsfield golfer's face decal.

        public enum Expression { Neutral, Blink, Happy, Focus, Effort, Sad, Surprised, Cheer }
        Material faceMaterial;
        Expression face = (Expression)(-1);
        float nextBlink = 2f, blinkFor;
        static Texture2D faceAtlas;

        /// How far up the face the features are drawn, in cells: the decal fills the bare skin
        /// between the brim and the chin, and the atlas has its eyes mid-cell, which put them in
        /// the lower face with the mouth on the chin. (The cells' margins are empty, so the shift
        /// samples nothing of the next row.)
        const float FaceRaise = 0.1f;

        Material FaceMaterial()
        {
            if (!faceAtlas) faceAtlas = Resources.Load<Texture2D>("Golfer/Look/FaceAtlas");
            var shader = Shader.Find("Unlit/Transparent");
            var m = new Material(shader ? shader : Shader.Find("Standard")) { mainTexture = faceAtlas, mainTextureScale = new Vector2(0.25f, 0.5f) };
            face = (Expression)(-1);
            return m;
        }

        void ShowFace(Expression e)
        {
            if (!faceMaterial || e == face) return;
            face = e;
            int cell = (int)e;
            faceMaterial.mainTextureOffset = new Vector2((cell % 4) * 0.25f, (cell < 4 ? 0.5f : 0f) - FaceRaise * 0.5f);
        }

        /// What the face says: effort through the downswing, focus as the backswing loads, a big
        /// smile for a cheer or a fist pump, happy while waving; a blink every few seconds.
        void UpdateFace(float dt)
        {
            if (!faceMaterial) return;
            Expression want = phase switch
            {
                2 => Expression.Effort,
                0 when loadTarget > 0.3f => Expression.Focus,
                4 when clipName is "Cheer" or "FistPump" => Expression.Cheer,
                4 when clipName == "Wave" => Expression.Happy,
                _ => Expression.Neutral,
            };
            nextBlink -= dt;
            if (nextBlink <= 0) { blinkFor = 0.13f; nextBlink = Random.Range(2.2f, 4.5f); }
            if (blinkFor > 0) { blinkFor -= dt; if (want is Expression.Neutral or Expression.Focus) want = Expression.Blink; }
            ShowFace(want);
        }

        public static GolferView Create(Transform parent)
        {
            var go = new GameObject("Golfer");
            go.transform.SetParent(parent, false);
            var v = go.AddComponent<GolferView>();
            v.ApplyStyle();
            return v;
        }

        public static GolferView CreatePlayer(Transform parent, Look look)
        {
            var go = new GameObject("Party golfer"); go.transform.SetParent(parent, false);
            var v = go.AddComponent<GolferView>(); v.own = look; v.ApplyStyle(); return v;
        }

        public static GolferView CreateSpectator(Transform parent, Look look)
        {
            var go = new GameObject("Spectator");
            go.transform.SetParent(parent, false);
            var v = go.AddComponent<GolferView>();
            v.own = look; v.spectator = true;
            v.ApplyStyle();
            v.Perform("Idle", startAt: Mathf.Repeat(go.GetInstanceID() * .137f, 1f));
            return v;
        }

        /// (Re)build the figure from GolferStyle: body model and skin tone. Comes up at address.
        public void ApplyStyle()
        {
            if (graph.IsValid()) graph.Destroy();
            heroFigure?.Dispose(); heroFigure = null; footwork = null;
            swingClearance = null; poseSafety = null; poseTransition = null; leadToeAnchored = false;
            heroLook = null; headFaceKnown = false; EndWatch(true); waggleClock = 0; waggleWeight = 0;
            baseRot = Quaternion.identity;   // (the Hero sets its own; a rebuilt V4 figure must not keep the last Hero's quarter turn)
            if (modelGo) Destroy(modelGo);
            faceMaterial = null;
            if (body) Destroy(body.gameObject);
            hasModel = false; body = null; modelGo = null; Head = null;
            phase = 0; loadTarget = 0; time = 0; swingThrough = -1; shownLoad = 0;
            var look = CurrentLook;
            if (look.Hero.HasValue && BuildHero(look)) { /* the Hero */ }
            else
            {
                if (look.Hero.HasValue) Debug.LogError($"The Hero golfer ({HeroAssets.Golf(look.Hero.Value.Female)}) failed to build: falling back to the OLDER golfer {look.ModelPath}");
                var model = Resources.Load<GameObject>(look.ModelPath);
                if (model && !BuildModel(model, look)) Debug.LogWarning($"{look.ModelPath} has no swing clips; using the primitive golfer");
            }
            if (!hasModel) BuildFigure();
            SetClub(shownClub, shownShort);
        }

        // ----- The Hero (Adnan's modular character; see HeroGolfer) -----

        /// The Hero's swing clips and clubs, the parts on one skeleton. False if it isn't in the build.
        bool BuildHero(Look look)
        {
            clips.Clear(); landmarks.Clear(); clubMeshes.Clear(); clubOriginal.Clear();
            string path = HeroGolfer.PathFor(look.Hero.Value.Female);
            foreach (var c in Resources.LoadAll<AnimationClip>(path))
                if (!c.name.StartsWith("__preview__")) clips[c.name] = c;
            if (clips.Count == 0) { Debug.LogWarning($"{path} has no swing clips"); return false; }
            // EMOTE STANDARD: the empty-handed emotion set and the standard Walk / Run (they replace the borrowed tennis ones)
            foreach (var c in Resources.LoadAll<AnimationClip>("HeroMoves/" + (look.Hero.Value.Female ? "Female" : "Male")))
                if (!c.name.StartsWith("__preview__")) clips[c.name] = c;
            var json = Resources.Load<TextAsset>(path + "_clips");
            if (json)
                foreach (var info in JsonUtility.FromJson<ClipSet>(json.text).clips) landmarks[info.name] = info;
            heroFigure = HeroGolfer.Build(transform, look.Hero.Value);
            if (heroFigure == null) { Debug.LogWarning($"{path} is not in the build"); return false; }
            var model = modelGo = heroFigure.Root;
            model.transform.localPosition = Vector3.zero;
            baseRot = Quaternion.Euler(0, HeroYaw, 0);
            model.transform.localRotation = baseRot;
            model.transform.localScale = Vector3.one * MetresToYards;
            foreach (var r in model.GetComponentsInChildren<Renderer>(true))
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (!mats[i]) continue;
                    string name = mats[i].name.Replace(" (Instance)", "");
                    if (name.StartsWith("CLUB ")) mats[i] = ClubMaterial(name);
                }
                r.sharedMaterials = mats;
                if (r is SkinnedMeshRenderer smr) { smr.updateWhenOffscreen = !spectator; if (!body0 && !r.name.StartsWith("CLUB_")) body0 = smr; }
                if (spectator) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
            foreach (var t in model.GetComponentsInChildren<Transform>(true))
                if (t.name.StartsWith("CLUB_")) clubMeshes[t.name.Substring(5)] = t.gameObject;
            if (spectator) foreach (var club in clubMeshes.Values) club.SetActive(false);
            else DressClubs();
            feetFix.Clear();
            Head = heroFigure.Bones.TryGetValue("Head", out var head) ? head : null;
            footwork = spectator ? null : GolferFootwork.Build(model.transform, heroFigure.Bones);
            swingClearance = new GolfSwingClearance(heroFigure);
            poseSafety = new GolfArcade.Tennis.HeroPoseSafety(heroFigure.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>());
            heroLook = heroFigure.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>();
            poseTransition = new GolfArcade.Tennis.HeroPoseTransition(model.transform);
            StartGraph(model);
            return true;
        }

        /// The Y rotation that turns the Hero's rig (facing where its clips take it) to face the ball on +Z.
        const float HeroYaw = -90f;

        void StartGraph(GameObject model)
        {
            var animator = model.GetComponent<Animator>() ?? model.AddComponent<Animator>();
            animator.applyRootMotion = false;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            graph = PlayableGraph.Create("Golfer swing");
            graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
            output = AnimationPlayableOutput.Create(graph, "Swing", animator);
            mixer = AnimationMixerPlayable.Create(graph, 2);
            output.SetSourcePlayable(mixer);
            fade = 0;
            graph.Play();
            poseSafety?.UseGraph(graph);   // hand clearance, bake-first: the baked corrections of the clips this graph plays
            hasModel = true;
            clipName = null;
        }

        // ----- Rigged model -----

        bool BuildModel(GameObject prefab, Look look)
        {
            string path = look.ModelPath;
            clips.Clear(); landmarks.Clear(); clubMeshes.Clear(); clubOriginal.Clear();
            foreach (var c in Resources.LoadAll<AnimationClip>(path)) clips[c.name] = c;
            if (clips.Count == 0) return false;
            var json = Resources.Load<TextAsset>(path + "_clips");
            if (json)
                foreach (var info in JsonUtility.FromJson<ClipSet>(json.text).clips) landmarks[info.name] = info;

            var model = Instantiate(prefab, transform);
            modelGo = model;
            model.name = "Golfer model";
            model.transform.localPosition = Vector3.zero;
            model.transform.localRotation = Quaternion.identity;
            model.transform.localScale = Vector3.one * MetresToYards; // the FBX is in metres, the course in yards
            foreach (var r in model.GetComponentsInChildren<Renderer>(true))
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (!mats[i]) continue;
                    string name = mats[i].name.Replace(" (Instance)", "");
                    if (name.StartsWith("CLUB ")) { mats[i] = ClubMaterial(name); continue; }
                    // The Higgsfield golfer (blender/scripts/fit_golf_characters.py): its colour map
                    // beside the FBX, and a face painted from Adnan's expression atlas.
                    if (name.StartsWith("V4 Higgs body"))
                    {
                        mats[i] = kitMaterial = Clay(Color.white, false, Resources.Load<Texture2D>($"{System.IO.Path.GetDirectoryName(path)}/higgs_{(path.EndsWith("_f") ? "f" : "m")}_color"));
                        DressKit(kitMaterial);
                        continue;
                    }
                    if (name.StartsWith("V4 face decal"))
                    {
                        mats[i] = faceMaterial = FaceMaterial();
                        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;   // a thin shell on the head
                        continue;
                    }
                    Color color = mats[i].color;
                    if (name == "MAT_SKIN") color = look.Skin;
                    else if (name == "MAT_HAIR") color = look.Hair;
                    else if (name == "V4 teal" && look.Shirt is Color shirt) color = shirt;
                    else if (name == "V4 sand" && look.Trousers is Color legs) color = legs;
                    // Adnan's plain tee and joggers have none of the kit's ivory trim (collar,
                    // hem, piping, the stripe down the leg) or navy buttons; the shoes stay white.
                    else if ((name == "V4 ivory" || name == "V4 navy") && look.Shirt is Color tee && IsShirtTrim(r.name)) color = tee;
                    else if (name == "V4 ivory" && look.Trousers is Color joggers && r.name.Contains("bottom leg")) color = joggers;
                    else if (Palette.TryGetValue(name, out var known)) color = known;
                    mats[i] = Clay(color, Cloth.Contains(name));
                }
                r.sharedMaterials = mats;
                if (r is SkinnedMeshRenderer smr) { smr.updateWhenOffscreen = !spectator; if (!body0) body0 = smr; }
                if (spectator) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
            foreach (var t in model.GetComponentsInChildren<Transform>(true))
            {
                if (t.name.StartsWith("CLUB_")) clubMeshes[t.name.Substring(5)] = t.gameObject;
                if (t.name.StartsWith("HAIR_")) t.gameObject.SetActive(t.name == look.HairMesh);
            }
            if (spectator) foreach (var club in clubMeshes.Values) club.SetActive(false);
            else DressClubs();
            MeasureFeet(model);
            // the Head bone (not a mesh that happens to share the name)
            foreach (var smr in model.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                if ((Head = System.Array.Find(smr.bones, b => b && b.name == "Head")) != null) break;
            StartGraph(model);
            return true;
        }

        /// The feet as the shoes were bound to them. In the golfer FBXs the foot and toe bones'
        /// bind pose is turned 150-180 degrees about their own X from where every clip turns
        /// them (the rest of the skeleton agrees to a few degrees), so each clip folded the
        /// shoes flat. Measured once against the standing clip, which the studio keyed with the
        /// feet at rest, the difference is put back after every pose: each bone's turn (and the
        /// toes' place on the turned foot).
        readonly List<(Transform bone, Quaternion fix, Vector3? at)> feetFix = new();

        void MeasureFeet(GameObject model)
        {
            feetFix.Clear();
            if (!clips.TryGetValue("Idle", out var idle)) return;
            SkinnedMeshRenderer skin = null;
            foreach (var smr in model.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                if (!skin || smr.sharedMesh.vertexCount > skin.sharedMesh.vertexCount) skin = smr;
            if (!skin) return;
            idle.SampleAnimation(model, 0f);
            var bones = skin.bones; var binds = skin.sharedMesh.bindposes;
            float worst = 0;
            foreach (var name in new[] { "Foot.L", "Toes.L", "Foot.R", "Toes.R" })
            {
                int i = System.Array.FindIndex(bones, b => b && b.name == name);
                int p = i < 0 ? -1 : System.Array.IndexOf(bones, bones[i].parent);
                if (p < 0) continue;
                var bound = binds[p] * binds[i].inverse;   // in its parent's frame, as the skin was bound
                var fix = Quaternion.Inverse(bones[i].localRotation) * bound.rotation;
                worst = Mathf.Max(worst, Quaternion.Angle(Quaternion.identity, fix));
                bool onFixed = feetFix.Exists(f => f.bone == bones[i].parent);
                feetFix.Add((bones[i], fix, onFixed ? bound.GetColumn(3) : null));
            }
            if (worst < 20f) feetFix.Clear();   // bound as the clips pose them: nothing to put back
        }

        /// The clip's pose, with the feet put back as the shoes were bound.
        void Evaluate()
        {
            graph.Evaluate();
            poseTransition?.Apply();
            if (phase == 4 && (clipName == "Wave" || clipName == "Intro_Wave")) poseSafety?.RelaxWaveWrist();
            if (phase != 4)
            {
                if (clipName == "Drive" && clip.IsValid())
                {
                    // The driver's wrap belongs to the pose on screen: while a crossfade leaves the finish behind (Settle, the next backswing) it fades
                    // out with that pose, instead of vanishing on the crossfade's first frame (the club jumped ~1.2 m back to the raw clip's finish).
                    if (fade > 0 && ghost.IsValid() && ghost.GetTime() >= 2.5) swingClearance?.ApplyDriveFollowThrough((float)ghost.GetTime(), fade);
                    else swingClearance?.ApplyDriveFollowThrough((float)clip.GetTime());
                }
                swingClearance?.Apply();
                Mannerisms();
            }
            foreach (var (bone, fix, at) in feetFix)
            {
                bone.localRotation *= fix;
                if (at is Vector3 p) bone.localPosition = p;
            }
            // Complete the closed golf grip synchronously after the source clip
            // and shaft-clearance solve; scrubbing/export does not rely on LateUpdate.
            if (heroFigure != null)
                GolfArcade.Tennis.HeroGripPolish.ApplyGrip(heroFigure.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>());
            if (phase != 4) swingClearance?.SeparateHands();
            poseSafety?.Apply(phase != 4);
            if (phase == 4) FitMoveToClothes();
            PlantSwingLeadFoot();
        }

        void PlantSwingLeadFoot()
        {
            if (heroFigure == null || !modelGo) return;
            if (phase == 4) { leadToeAnchored = false; return; }
            var bones = heroFigure.Bones;
            if (!bones.TryGetValue("LeftToes", out var toe) || !bones.TryGetValue("LeftFoot", out var foot)) return;
            if (phase == 0 && time < .03f)
            { leadToeAnchor = modelGo.transform.InverseTransformPoint(toe.position); leadToeAnchored = true; }
            if (!leadToeAnchored || clipName == "Putt" || phase != 2 && phase != 5 && phase != 3) return;
            // Pivot on the lead forefoot while the heel and foot orientation follow
            // the authored downswing. Do not pin the whole shoe flat to the ground.
            var delta = modelGo.transform.TransformPoint(leadToeAnchor) - toe.position;
            float blend = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(TopTime, ImpactTime, time));
            var rotation = foot.rotation;
            GolfArcade.Tennis.HeroPoseSafety.Solve(bones["LeftUpperLeg"], bones["LeftLowerLeg"], foot, foot.position + delta * blend);
            foot.rotation = rotation;
        }

        GolfClub shownClub = GolfClub.Driver;
        bool shownShort;
        SkinnedMeshRenderer body0;

        // ----- Mannerisms (chat B, 2026-10-19; work/golf-mannerisms) -----
        // Cosmetic layers on the clip pose, applied in Evaluate after the club clearance and before the grip polish and the hand
        // clearance (so both see them). After a full shot (WatchShot, from GolfGame.PostShotWatch at contact) the finish is held,
        // the head and chest follow the ball, then the arms and club drop together in front of the chest (T_jKUimVpuk 46.4-48.6).
        // At address the club head hinges back and to the ball twice with a look down the line between, then the hands settle on
        // the grip (jkeRIJrv8g0 23.5-26.8). Nothing here touches `time`, the phase or a swing's timing: any backswing load lets
        // the address routine go within WaggleRelease seconds.
        GolfArcade.Tennis.MatchHeroLook heroLook;
        System.Func<Vector3?> watchBall;
        float watchClock = -1, finishClock = -1, watchFade;   // seconds since contact (-1: not watching); since then to the finish; weight
        bool watchEnding;
        float waggleClock, waggleWeight;
        Vector3 standBall, standAim = Vector3.forward; bool hasStand;
        /// The face's direction in the Head bone's frame, measured on the clean address pose (the clip has the eyes on the ball).
        Vector3 headFace; bool headFaceKnown;
        /// Off: the clips alone (before/after films).
        public static bool MannerismsOff;
        /// The finish is held this long before the club comes down, which takes DropTime; the hands end this far below the shoulders.
        const float HoldFinish = .3f, DropTime = .65f, DropBelow = 40f, MaxLook = 55f;
        /// The address routine starts this long after the golfer is settled and repeats every WaggleEvery seconds while they wait.
        const float WaggleDelay = .45f, WaggleEvery = 7f, WaggleRelease = .08f;

        /// The golfer has hit a full shot: hold the finish, watch `ball` (world position, null when gone), then drop the club.
        public void WatchShot(System.Func<Vector3?> ball) { watchBall = ball; watchClock = 0; finishClock = -1; watchEnding = false; watchFade = 1; }
        /// True while the post-shot watch is on the golfer (from contact until the next address).
        public bool Watching => watchClock >= 0;
        /// The address routine's share on the pose now (0 = the clip alone), for the tests and films.
        public float WaggleShare => waggleClock > WaggleDelay ? waggleWeight : 0;
        void EndWatch(bool now = false)
        {
            if (watchClock < 0) return;
            if (now) { watchClock = -1; finishClock = -1; watchBall = null; watchFade = 0; } else watchEnding = true;
        }

        /// Seen from behind, turned `degrees` to the golfer's left of a square back view (the lead side to the camera), on the
        /// gameplay camera as it is over the next frames (a chip-in's camera cuts back to the shot's view after this call).
        public void TurnFromCamera(float degrees) { turnFromCamera = degrees; turnFrames = 3; ApplyTurnFromCamera(); }
        float turnFromCamera; int turnFrames;
        void ApplyTurnFromCamera()
        {
            var cam = Camera.main; if (!cam || turnFrames <= 0) return;
            turnFrames--;
            var away = transform.position - cam.transform.position; away.y = 0;
            if (away.sqrMagnitude > .01f) transform.rotation = Quaternion.LookRotation(Quaternion.AngleAxis(-turnFromCamera, Vector3.up) * away.normalized, Vector3.up);
        }

        void TickMannerisms(float dt)
        {
            if (watchClock >= 0)
            {
                watchClock += dt;
                if (finishClock < 0 && phase == 3) finishClock = watchClock;
                if (watchEnding && (watchFade -= dt / .3f) <= 0) EndWatch(true);
            }
            bool atRest = phase == 0 && loadTarget < .001f && time < .02f && clipName != "Putt" && !spectator && hasStand && watchClock < 0;
            if (atRest) { waggleClock += dt; waggleWeight = 1; }
            else { waggleWeight = Mathf.Max(0, waggleWeight - dt / WaggleRelease); if (waggleWeight <= 0) waggleClock = 0; }
        }

        static float Ease(float x) { x = Mathf.Clamp01(x); return x * x * (3 - 2 * x); }
        /// 0 outside [a, b], rising smoothly to 1 at the middle and back.
        static float Bump(float u, float a, float b) => u <= a || u >= b ? 0 : .5f - .5f * Mathf.Cos((u - a) / (b - a) * 2 * Mathf.PI);

        void Mannerisms()
        {
            if (MannerismsOff || heroFigure == null || !heroLook) return;
            var head = heroLook.Bone(HumanBodyBones.Head);
            if (phase == 0 && time < .02f && hasStand && head && fade <= 0 && waggleClock <= WaggleDelay)
            { headFace = Quaternion.Inverse(head.rotation) * (standBall - head.position).normalized; headFaceKnown = true; }
            if (watchClock >= 0 && watchFade > 0) PostShot(head);
            else if (waggleWeight > 0 && waggleClock > WaggleDelay) Waggle(head);
        }

        Transform ClubBone => heroFigure.Bones.TryGetValue("Club", out var c) ? c : null;
        Transform Bone(HumanBodyBones b) => heroLook.Bone(b);

        /// Turns `bone` (and the club, when the hands hang from it) about its joint by `r`.
        static void Turn(Transform bone, Quaternion r, Transform club = null)
        {
            if (!bone) return;
            if (club) { club.position = bone.position + r * (club.position - bone.position); club.rotation = r * club.rotation; }
            bone.rotation = r * bone.rotation;
        }

        /// Puts a hand where the rigid motion (about `pivot` by `r`, then by `shift`) takes it, the arm following it (two-bone IK).
        static void Carry(Transform upper, Transform lower, Transform hand, Vector3 pivot, Quaternion r, Vector3 shift)
        {
            if (!upper || !lower || !hand) return;
            var to = pivot + r * (hand.position - pivot) + shift; var rot = r * hand.rotation;
            GolfArcade.Tennis.HeroPoseSafety.Solve(upper, lower, hand, to);
            hand.rotation = rot;
        }

        void PostShot(Transform head)
        {
            float t = watchClock, w = watchFade;
            var club = ClubBone;
            // 1. the club comes down: the arms and club turn together about the shoulder line (both shoulders are on it, so the
            //    grip stays in the hands), from over the lead shoulder to the hands in front of the chest and the shaft upright
            float drop = finishClock < 0 ? 0 : w * Ease((t - finishClock - HoldFinish) / DropTime);
            Transform lu = Bone(HumanBodyBones.LeftUpperArm), ru = Bone(HumanBodyBones.RightUpperArm), lh = Bone(HumanBodyBones.LeftHand), rh = Bone(HumanBodyBones.RightHand);
            if (drop > 0 && lu && ru && lh && rh && hasStand)
            {
                var axis = (ru.position - lu.position).normalized; var pivot = (lu.position + ru.position) * .5f;
                var want = Vector3.ProjectOnPlane(standAim * Mathf.Cos(DropBelow * Mathf.Deg2Rad) - Vector3.up * Mathf.Sin(DropBelow * Mathf.Deg2Rad), axis);
                var hands = Vector3.ProjectOnPlane((lh.position + rh.position) * .5f - pivot, axis);
                if (want.sqrMagnitude > 1e-4f && hands.sqrMagnitude > 1e-4f)
                {
                    var r = Quaternion.AngleAxis(Mathf.Clamp(Vector3.SignedAngle(hands, want, axis), -150, 150) * drop, axis);
                    if (club) { club.position = pivot + r * (club.position - pivot); club.rotation = r * club.rotation; }
                    lu.rotation = r * lu.rotation; ru.rotation = r * ru.rotation;
                }
            }
            // 2. the head and chest follow the ball (the chest carries the arms and the club with it)
            float look = w * Ease((t - .3f) / .5f);
            var ball = watchBall?.Invoke();
            if (look > 0 && ball.HasValue && head && headFaceKnown)
            {
                var chest = Bone(HumanBodyBones.UpperChest) ?? Bone(HumanBodyBones.Chest);
                foreach (var (bone, share) in new[] { (chest, .25f), (Bone(HumanBodyBones.Neck), .35f), (head, .8f) })
                {
                    if (!bone) continue;
                    var q = Quaternion.FromToRotation(head.rotation * headFace, (ball.Value - head.position).normalized);
                    q = Quaternion.RotateTowards(Quaternion.identity, q, MaxLook);
                    Turn(bone, Quaternion.Slerp(Quaternion.identity, q, share * look), bone == chest ? club : null);
                }
            }
        }

        void Waggle(Transform head)
        {
            float u = Mathf.Repeat(waggleClock - WaggleDelay, WaggleEvery), w = waggleWeight;
            float hinge = (Bump(u, 0f, 1.0f) * 24f + Bump(u, 2.0f, 2.8f) * 16f) * w;
            float lookDown = Bump(u, 1.0f, 2.0f) * w;
            float twist = Bump(u, 2.8f, 3.3f) * 7f * w;
            Transform lu = Bone(HumanBodyBones.LeftUpperArm), ll = Bone(HumanBodyBones.LeftLowerArm), lh = Bone(HumanBodyBones.LeftHand);
            Transform ru = Bone(HumanBodyBones.RightUpperArm), rl = Bone(HumanBodyBones.RightLowerArm), rh = Bone(HumanBodyBones.RightHand);
            var club = ClubBone;
            if (!lh || !rh || !club) return;
            var grip = (lh.position + rh.position) * .5f;
            var shaft = (standBall - grip).normalized;   // at address the club head sits at the ball
            if (hinge > .01f)
            {
                // the wrists hinge the club head back off the ball about the lead hand; the hands drift back a little with it
                var n = Vector3.Cross(shaft, standAim).normalized;
                var r = Quaternion.AngleAxis(hinge, n);
                if (Vector3.Dot(r * shaft - shaft, standAim) > 0) r = Quaternion.AngleAxis(-hinge, n);
                var pivot = lh.position; var shift = -standAim * (.025f * hinge / 24f);
                club.position = pivot + r * (club.position - pivot) + shift; club.rotation = r * club.rotation;
                Carry(ru, rl, rh, pivot, r, shift);
                Carry(lu, ll, lh, pivot, r, shift);
            }
            if (twist > .01f)
            {
                // the regrip: both hands turn a little on the grip and settle back
                var r = Quaternion.AngleAxis(twist, shaft);
                Carry(lu, ll, lh, grip, r, Vector3.zero);
                Carry(ru, rl, rh, grip, r, Vector3.zero);
            }
            if (lookDown > .01f && head && headFaceKnown)
            {
                // a look down the line at the target and back, turning about the neck
                var neck = Bone(HumanBodyBones.Neck);
                if (neck)
                {
                    var axis = (head.position - neck.position).normalized;
                    float a = Mathf.Clamp(Vector3.SignedAngle(Vector3.ProjectOnPlane(head.rotation * headFace, axis), Vector3.ProjectOnPlane(standAim, axis), axis), -75, 75) * .85f * lookDown;
                    Turn(neck, Quaternion.AngleAxis(a * .35f, axis)); Turn(head, Quaternion.AngleAxis(a * .65f, axis));
                }
            }
        }

        // ----- The hole-out reactions fitted to the clothes (chat B, 2026-10-19) -----
        // Seen from behind (chat A's hole-out camera) the empty-handed reactions pressed the hands flat into the trousers at the thigh
        // and hip (Stomp, Slump), kept the fist-pump elbow tight to the shirt and folded the wrists. The moves are fitted to the
        // clothes, not the clothes to the moves: after the hand clearance each hand and forearm is kept a visible gap clear of the
        // body + garments proxy (the fist-pump elbow stays off the body, BJ0623X5GQw 26.6-27.4; a frustrated arm hangs away from
        // the hips, yRbtwqYXWVg 28.8-33.2) and each wrist is kept within WristLimit of the forearm line.
        const float HandGap = .05f, ForearmGap = .03f, WristLimit = 45f, MaxFit = .12f;
        /// At the hips and thighs the hands keep this much more: the trousers' and (more) the pleated skirt's flare stands off the proxy.
        const float HipAllowance = .015f, SkirtAllowance = .04f;
        readonly Vector3[] fitShift = new Vector3[2];
        /// Diagnostics: the larger hand shift applied last frame (m), and the larger raw shortfall measured (m).
        public float FitShown => Mathf.Max(fitShift[0].magnitude, fitShift[1].magnitude);
        public float FitWanted { get; private set; }
        public int FitCapsules => poseSafety?.clearance?.proxy != null ? poseSafety.clearance.proxy.capsules.Count : -1;
        static bool FitsClothes(string move) => move != null && (move.StartsWith("Emote_") || move is "Idle" or "Cheer" or "FistPump");

        void FitMoveToClothes()
        {
            if (MannerismsOff || !heroLook || poseSafety?.clearance == null || poseSafety.VolumeCount == 0 || !FitsClothes(clipName))
            { fitShift[0] = fitShift[1] = Vector3.zero; return; }
            var proxy = poseSafety.clearance.proxy; proxy.Refresh(); FitWanted = 0;
            float k = 1 - Mathf.Exp(-Time.deltaTime / .07f);   // a short follow, so a contact that comes and goes never pops
            for (int side = 0; side < 2; side++)
            {
                var upper = Bone(side == 0 ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm);
                var lower = Bone(side == 0 ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm);
                var hand = Bone(side == 0 ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand);
                var middle = Bone(side == 0 ? HumanBodyBones.LeftMiddleProximal : HumanBodyBones.RightMiddleProximal);
                if (!upper || !lower || !hand) continue;
                if (middle) StraightenWrist(lower, hand, middle);
                var palm = middle ? (hand.position + middle.position) * .5f : hand.position;
                float hips = heroLook.female ? SkirtAllowance : HipAllowance;
                var want = Gap(proxy, palm, HandGap, hips);
                var fore = Gap(proxy, (lower.position + hand.position) * .5f, ForearmGap, hips) * 2;   // the hand moves twice as far as the forearm's middle
                if (fore.sqrMagnitude > 1e-8f) { var n = fore.normalized; float have = Vector3.Dot(want, n), need = fore.magnitude; if (need > have) want += n * (need - have); }
                want = Vector3.ClampMagnitude(want, MaxFit); FitWanted = Mathf.Max(FitWanted, want.magnitude);
                fitShift[side] = Vector3.Lerp(fitShift[side], want, k);
                if (fitShift[side].sqrMagnitude < 1e-8f) continue;
                var rot = hand.rotation;
                GolfArcade.Tennis.HeroPoseSafety.Solve(upper, lower, hand, hand.position + fitShift[side]);
                hand.rotation = rot;
            }
        }

        /// How far (and which way) `point` must move to be `gap` clear of the body and its clothes (arms excluded): the deepest
        /// shortfall over the proxy's capsules, measured along each capsule's own surface ray.
        static Vector3 Gap(GolfArcade.Tennis.HeroClearanceProxy proxy, Vector3 point, float gap, float hips)
        {
            Vector3 best = Vector3.zero; float bestNeed = 0;
            foreach (var c in proxy.capsules)
            {
                if (c == null || c.part is GolfArcade.Tennis.HeroClearanceProxy.Part.UpperArm or GolfArcade.Tennis.HeroClearanceProxy.Part.Forearm
                    or GolfArcade.Tennis.HeroClearanceProxy.Part.Hand or GolfArcade.Tennis.HeroClearanceProxy.Part.Finger) continue;
                float g = gap + (c.part is GolfArcade.Tennis.HeroClearanceProxy.Part.Pelvis or GolfArcade.Tennis.HeroClearanceProxy.Part.Thigh ? hips : 0);
                var core = c.aW + Vector3.Project(point - c.aW, c.bW - c.aW);
                if ((point - core).sqrMagnitude > Mathf.Pow(c.maxR * c.scale + g, 2) * 1.2f) continue;
                var surface = GolfArcade.Tennis.HeroClearanceProxy.Surface(c, point, true);
                var ray = point - core; if (ray.sqrMagnitude < 1e-10f) continue;
                var n = ray.normalized;
                float clear = Vector3.Dot(point - surface, n), need = g - clear;
                if (need > bestNeed) { bestNeed = need; best = n * need; }
            }
            return best;
        }

        /// A wrist bent past WristLimit (a fist folded back, a hand cocked against the hip) is brought back towards the forearm line.
        static void StraightenWrist(Transform lower, Transform hand, Transform middle)
        {
            var palm = middle.position - hand.position; var forearm = hand.position - lower.position;
            float angle = Vector3.Angle(palm, forearm);
            if (angle > WristLimit) hand.rotation = Quaternion.Slerp(Quaternion.identity, Quaternion.FromToRotation(palm, forearm), (angle - WristLimit) / angle) * hand.rotation;
        }

        // ----- Moves off the course -----

        /// The studio's shared moves were made facing a quarter turn from its golf clips; this
        /// turns them back so every clip faces where the golfer stands.
        Quaternion BaseRot(Quaternion clipYaw) => baseRot * clipYaw;
        static float ClipYaw(string move) => move is "Idle" or "Wave" or "Cheer" or "Walk" || move.StartsWith("Intro_") || move.StartsWith("Emote_") ? 90f : 0f;   // (Walk and the pick-up face the cup: the golfer's own stance is side-on to it)
        float performTime, performLength;
        bool loopPerformance;
        public float PerformanceDuration => performLength;

        /// Plays a move off the course — "Wave", "Cheer", "FistPump", "Idle" — at real speed,
        /// looping, empty-handed, from `startAt` seconds in. Settle() (or SetClub) brings the
        /// swing back. False when the model has no such clip.
        /// The model has a clip of this name.
        public bool HasMove(string move) => hasModel && clips.ContainsKey(move);
        /// How long that move runs once through (seconds), 0 when there is no such clip.
        public float MoveLength(string move) => hasModel && clips.TryGetValue(move, out var c) ? GolfArcade.Tennis.TennisEmotes.PlaybackDuration(move, c.length) : 0f;

        public bool Perform(string move, float startAt = 0f, bool loop = true)
        {
            if (!hasModel || !clips.TryGetValue(move, out var c)) return false;
            if (pickStage != 0 && !pickInternal) CancelPickUp();
            EndWatch(true);
            var yaw = Quaternion.Euler(0, ClipYaw(move), 0); yaw = BaseRot(yaw);
            bool turn = Quaternion.Angle(modelGo.transform.localRotation, yaw) > .1f;
            if (turn) poseTransition?.Capture(.28f);
            Play(c, turn ? 0f : .25f);
            clipName = move; SetMood(move);
            foreach (var kv in clubMeshes) kv.Value.SetActive(false);
            modelGo.transform.localRotation = yaw;
            loopPerformance = loop;
            performLength = Mathf.Max(.1f, GolfArcade.Tennis.TennisEmotes.PlaybackDuration(move, c.length));
            performanceRate = c.length / performLength;
            performTime = Mathf.Repeat(startAt, performLength);
            phase = 4;
            clip.SetTime(GolfArcade.Tennis.TennisEmotes.SourceTime(clipName, performTime * performanceRate, performLength * performanceRate));
            Evaluate();
            return true;
        }


        // ----- Hole-out pick-up: walk to the cup, bend, take the ball out with the right hand, pocket it -----
        // Emote_PickUp (work/emote-standard/scripts/clip_pickup.py, empty-handed like every hole-out move: the club is put away).
        // The right wrist is at the cup at GrabFrame; the ball rides the hand from there and goes into the pocket at PocketFrame.
        const float PickUpFps = 30f, PickUpGrabFrame = 36f, PickUpPocketFrame = 70f, PickUpWalkMetresPerSecond = 1.2f;
        int pickStage;            // 0 none, 1 walking to the stand point, 2 playing the pick-up
        bool pickInternal, pickCarrying;
        Transform pickBall;
        Vector3 pickFrom, pickStand, pickCup;
        float pickClock, pickWalkSeconds, pickMetresPerSecond;
        /// Walk + pick-up, seconds (set by PickUpBall).
        public float PickUpSeconds { get; private set; }
        public bool PickingUp => pickStage != 0;
        /// The right wrist at the grab frame, metres to the golfer's right / forward of the model origin, measured on the clip (hero by hero).
        Vector2 PickUpReach => CurrentLook.Hero.HasValue && CurrentLook.Hero.Value.Female ? new Vector2(.112f, .223f) : new Vector2(.129f, .219f);
        public bool CanPickUp => HasMove("Walk") && HasMove("Emote_PickUp");

        /// The golfer walks from where they stand (never farther than `maxWalk` yards: they start that far from the cup) to the cup at the Walk
        /// clip's pace (faster, at the clip's own foot speed, when the cup is far), bends, and takes `ball` out into the pocket.
        public bool PickUpBall(Vector3 cup, Transform ball, float maxWalk = 7f)
        {
            if (!CanPickUp) return false;
            var here = transform.position;
            var to = cup - here; to.y = 0;
            var fwd = to.sqrMagnitude > .0001f ? to.normalized : transform.forward;
            var right = Vector3.Cross(Vector3.up, fwd);
            var reach = PickUpReach * MetresToYards;
            var wrist = cup;   // (the fingers hang straight down into the cup from the wrist)
            pickStand = wrist - fwd * reach.y - right * reach.x; pickStand.y = cup.y;
            pickFrom = here; pickFrom.y = cup.y;
            if (Vector3.Distance(pickFrom, pickStand) > maxWalk) pickFrom = pickStand - fwd * maxWalk;
            float dist = Vector3.Distance(pickFrom, pickStand);
            pickCup = cup; pickBall = ball; pickCarrying = false; pickClock = 0;
            pickMetresPerSecond = Mathf.Clamp(dist / MetresToYards / 4f, PickUpWalkMetresPerSecond, 1.9f);
            pickWalkSeconds = dist / (pickMetresPerSecond * MetresToYards);
            PickUpSeconds = (dist > .25f ? pickWalkSeconds : 0f) + MoveLength("Emote_PickUp");
            transform.rotation = Quaternion.LookRotation(fwd, Vector3.up);
            transform.position = pickFrom;
            if (dist > .25f) { pickStage = 1; PerformInternal("Walk", true); float len = clips["Walk"].length, rate = pickMetresPerSecond / PickUpWalkMetresPerSecond; performanceRate = rate; performLength = len / rate; }
            else { pickStage = 2; PerformInternal("Emote_PickUp", false); ShowCupBall(); }
            return true;
        }

        void PerformInternal(string move, bool loop) { pickInternal = true; Perform(move, 0f, loop); pickInternal = false; }

        void ShowCupBall()
        {
            if (!pickBall) return;
            pickBall.position = pickCup + Vector3.down * (.02f * MetresToYards);
            pickBall.gameObject.SetActive(true);
        }

        void TickPickUp(float dt)
        {
            pickClock += dt;
            if (pickStage == 1)
            {
                float u = Mathf.Clamp01(pickClock / Mathf.Max(.01f, pickWalkSeconds));
                transform.position = Vector3.Lerp(pickFrom, pickStand, u);
                if (u < 1) return;
                pickStage = 2; pickClock = 0;
                PerformInternal("Emote_PickUp", false);
                ShowCupBall();
                return;
            }
            if (phase != 4 || clipName != "Emote_PickUp") { CancelPickUp(); return; }
            if (!pickCarrying && pickClock >= PickUpGrabFrame / PickUpFps) pickCarrying = true;
            if (pickCarrying && pickBall && heroFigure != null)
            {
                if (pickClock >= PickUpPocketFrame / PickUpFps) { pickBall.gameObject.SetActive(false); pickBall = null; pickStage = 0; return; }
                var b = heroFigure.Bones;
                if (b.TryGetValue("RightHand", out var hand))
                {
                    var p = hand.position;
                    if (b.TryGetValue("RightMiddleIntermediate", out var mid)) p = Vector3.Lerp(p, mid.position, .5f);
                    pickBall.position = p;
                }
            }
        }

        /// The pick-up is over or interrupted: the ball stays in the cup (holed balls stay hidden until the next hole puts one down).
        void CancelPickUp()
        {
            if (pickStage == 0 && !pickBall) return;
            if (pickBall) pickBall.gameObject.SetActive(false);
            pickBall = null; pickStage = 0; pickCarrying = false;
        }

        /// True when the figure is Adnan's Hero (else the older V4 golfer or the primitive stand-in).
        public bool IsHero => heroFigure != null;
        /// The Hero's parts (for the tests), or null.
        public HeroGolfer Hero => heroFigure;
        /// ACCESSORIES: the golf bag is on the golfer's back between shots only (the round calls this as its state changes); swings and intros never carry it.
        public void SetBagCarried(bool carried)
        {
            var look = heroFigure != null && heroFigure.Root ? heroFigure.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>() : null;
            if (look) GolfArcade.Tennis.HeroAccessories.For(look).SetCarry(carried);
        }

        /// The clubhead in world space (the point of the held club farthest from its grip), for the tests.
        public Vector3? ClubHeadWorld()
        {
            if (!modelGo) return null;
            foreach (var kv in clubMeshes)
            {
                if (!kv.Value.activeSelf) continue;
                var smr = kv.Value.GetComponentInChildren<SkinnedMeshRenderer>();
                if (!smr) continue;
                var grip = System.Array.Find(modelGo.GetComponentsInChildren<Transform>(true), t => t.name == "Club");
                var baked = new Mesh();
                smr.BakeMesh(baked, false);
                var origin = grip ? smr.transform.InverseTransformPoint(grip.position) : Vector3.zero;
                Vector3 far = Vector3.zero; float best = -1;
                foreach (var v in baked.vertices) { float d = (v - origin).sqrMagnitude; if (d > best) { best = d; far = v; } }
                Destroy(baked);
                return smr.transform.TransformPoint(far);
            }
            return null;
        }

        /// The move playing now, or null while it's the swing.
        public string Performing => phase == 4 ? clipName : null;
        /// Read-only cosmetic gate: never add idle motion during load, contact or an emote.
        public bool AliveAtRest => hasModel && (phase == 0 && loadTarget < .001f && time < .02f || phase == 4 && clipName == "Idle");

        /// The head (the rig's Head bone, or the stand-in's sphere), for a camera on the face.
        public Transform Head { get; private set; }

        /// The clip and the club in hand for `club`: the driver's swing, the iron's, a half
        /// swing or a chip for the wedge depending on how far there is to go, the putt.
        public void SetClub(GolfClub club, bool shortShot)
        {
            shownClub = club; shownShort = shortShot;
            if (!hasModel) return;
            string wanted = club.Family() switch
            {
                ClubFamily.Wood => "Drive",
                ClubFamily.Iron => "IronSwing",
                ClubFamily.Wedge => shortShot ? "Chip" : "HalfSwing",
                _ => "Putt",
            };
            if (!clips.ContainsKey(wanted)) wanted = clips.ContainsKey("Drive") ? "Drive" : new List<string>(clips.Keys)[0];
            if (wanted == clipName) { SquareTheModel(); return; }
            clipName = wanted; SetMood(wanted);
            var c = clips[wanted];
            if (landmarks.TryGetValue(wanted, out var info) && info.fps > 0)
            {
                TopTime = (float)info.top / info.fps; ImpactTime = (float)info.impact / info.fps; EndTime = (float)(info.frames - 1) / info.fps;
            }
            else { TopTime = c.length * 0.55f; ImpactTime = c.length * 0.75f; EndTime = c.length; }
            string clubMesh = info != null ? info.club.ToUpperInvariant() : club.ToString().ToUpperInvariant();
            foreach (var kv in clubMeshes) kv.Value.SetActive(!spectator && kv.Key == clubMesh);
            (Downswing, Accel, EaseOut) = wanted switch
            {
                "Putt" => (0.42f, 1.1f, 1.6f),     // a pendulum: hardly any acceleration
                "Chip" => (0.42f, 1.25f, 2.0f),
                // The full and part swings are authored from scratch (blender/scripts/golf_swing.py) and carry the whole speed profile themselves (Swing.retime(): the club
                // head's speed rises to its peak at the ball and eases into the finish), so both the downswing and the follow-through play at an even rate here: easing either
                // again made the club hang at the top and then snap, or stop short of the finish. Tour players come down from the top in 0.19-0.23 s (measured on Adnan's reference
                // swings, work/swing-compare); 0.25 s is that pace with a frame to spare at 60 fps (it was 0.38 s, and the swing read as floaty). A pitch comes down a touch slower.
                "HalfSwing" => (0.26f, 1.0f, 1.0f),
                _ => (0.25f, 1.0f, 1.0f),
            };
            bool turn = Quaternion.Angle(modelGo.transform.localRotation, baseRot) > .1f;
            if (turn) poseTransition?.Capture(.28f);
            Play(c, turn ? 0f : .2f);
            modelGo.transform.localRotation = baseRot;
            downArc = DownArc(wanted, c);
            pace = -1;
            if (phase == 4) { phase = 0; time = 0; }
            Show(Mathf.Min(time, TopTime));
        }

        void Show(float t)
        {
            time = Mathf.Clamp(t, 0, EndTime);
            clip.SetTime(time);
            Evaluate();
        }

        /// Puts `c` on the mixer; with a crossfade, the pose on screen now stays behind, frozen,
        /// and fades out over that many seconds.
        void Play(AnimationClip c, float crossfade)
        {
            if (ghost.IsValid()) { graph.Disconnect(mixer, 1); ghost.Destroy(); }
            if (clip.IsValid())
            {
                graph.Disconnect(mixer, 0);
                if (crossfade > 0) { ghost = clip; graph.Connect(ghost, 0, mixer, 1); fade = 1; fadeSeconds = crossfade; }
                else clip.Destroy();
            }
            if (!ghost.IsValid()) fade = 0;   // nothing on screen yet to fade from
            clip = AnimationClipPlayable.Create(graph, c);
            clip.SetApplyFootIK(false);
            clip.SetApplyPlayableIK(false);
            graph.Connect(clip, 0, mixer, 0);
            clipAsset = c;
            Weigh();
        }

        /// Leaves the pose on screen for another point in the same clip, smoothly.
        void Crossfade(float seconds) { if (clipAsset) { float t = time; Play(clipAsset, seconds); clip.SetTime(t); } }

        void Weigh()
        {
            mixer.SetInputWeight(0, 1 - fade);
            mixer.SetInputWeight(1, ghost.IsValid() ? fade : 0);
        }

        void TickFade(float dt)
        {
            if (fade <= 0) return;
            fade = Mathf.Max(0, fade - dt / fadeSeconds);
            if (fade == 0 && ghost.IsValid()) { graph.Disconnect(mixer, 1); ghost.Destroy(); }
            Weigh();
        }

        void ShowThrough()
        {
            if (throughV >= 1) { phase = 3; Show(finishTime); return; }
            Show(ImpactTime + (finishTime - ImpactTime) * (1 - Mathf.Pow(1 - throughV, EaseOut)));
        }

        float DownswingTime(float u) => TopTime + (ImpactTime - TopTime) * Mathf.Pow(Mathf.Clamp01(u), Accel);

        const int ArcSteps = 32;

        /// The clip's downswing as clip time at even shares of the club's travel from the top to the ball (ArcSteps + 1 entries):
        /// the club head's path in the golfer's own frame, measured once per clip. (Its path, not the shaft's turn: a putter hardly
        /// turns, it rocks.) Null without a club to measure.
        float[] DownArc(string name, AnimationClip c)
        {
            if (downArcs.TryGetValue(name, out var arc)) return arc;
            downArcs[name] = null;
            if (spectator || !modelGo || ImpactTime - TopTime < .05f) return null;
            var grip = System.Array.Find(modelGo.GetComponentsInChildren<Transform>(true), t => t.name == "Club");
            if (!grip || !(ClubHeadWorld() is Vector3 head)) return null;
            var tip = grip.InverseTransformPoint(head);
            if (tip.sqrMagnitude < 1e-6f) return null;
            var root = modelGo.transform; var pos = root.localPosition; var rot = root.localRotation;
            var times = new float[ArcSteps + 1]; var turned = new float[ArcSteps + 1]; Vector3 last = default;
            for (int i = 0; i <= ArcSteps; i++)
            {
                times[i] = Mathf.Lerp(TopTime, ImpactTime, i / (float)ArcSteps);
                c.SampleAnimation(modelGo, times[i]);
                var at = root.InverseTransformPoint(grip.TransformPoint(tip));
                turned[i] = i == 0 ? 0 : turned[i - 1] + (at - last).magnitude;
                last = at;
            }
            root.localPosition = pos; root.localRotation = rot;
            if (turned[ArcSteps] < .02f) return null;   // hardly moves: nothing to follow
            arc = new float[ArcSteps + 1];
            for (int i = 0, j = 0; i <= ArcSteps; i++)
            {
                float want = turned[ArcSteps] * i / ArcSteps;
                while (j < ArcSteps - 1 && turned[j + 1] < want) j++;
                float span = turned[j + 1] - turned[j];
                arc[i] = Mathf.Lerp(times[j], times[j + 1], span > 1e-6f ? Mathf.Clamp01((want - turned[j]) / span) : 0);
            }
            return downArcs[name] = arc;
        }

        /// Clip time at `share` of the club's path from the top (0) to the ball (1).
        float ArcTime(float share)
        {
            float x = Mathf.Clamp01(share) * ArcSteps; int i = Mathf.Min(ArcSteps - 1, (int)x);
            return Mathf.Lerp(downArc[i], downArc[i + 1], x - i);
        }

        /// The share of the club's path from the top that clip time `t` has reached (ArcTime's inverse).
        float ArcShare(float t)
        {
            if (t <= downArc[0]) return 0;
            for (int i = 0; i < ArcSteps; i++)
                if (t <= downArc[i + 1]) return (i + Mathf.InverseLerp(downArc[i], downArc[i + 1], t)) / ArcSteps;
            return 1;
        }

        /// The phone's own downswing, 0 at its top to 1 at the ball (MotionSwingDetector.DownswingProgress), every sample while it
        /// comes down: the club follows it turn for turn instead of its own clock, so it meets the ball on the sample the phone
        /// does. (It never runs back, and samples that stop for a moment hand the swing back to the clock.)
        public void PaceDownswing(float progress, double sampleTime)
        {
            if (!hasModel || downArc == null || phase == 4) return;
            double lag = Time.timeAsDouble - sampleTime;
            if (pace < 0) { paceLag = lag; paceT1 = sampleTime - .01; paceP0 = progress; }
            else { paceLag = System.Math.Min(paceLag, lag); paceP0 = pace; }
            paceT0 = paceT1; paceT1 = sampleTime;
            pace = Mathf.Max(pace, progress); paceAt = Time.time;
        }

        /// The phone's progress at this frame's moment: the samples come at 100 Hz and a frame takes whatever arrived since the
        /// last (one or two, 0-10 ms old), so the newest is carried on along the last two's pace to the frame's time on the phone's
        /// clock (this frame's time less the least lag seen); otherwise the club would step unevenly frame to frame.
        float PaceNow()
        {
            double ahead = System.Math.Min(.02, System.Math.Max(0, Time.timeAsDouble - paceLag - paceT1));
            double span = paceT1 - paceT0;
            float rate = span > 1e-4 ? (float)((pace - paceP0) / span) : 0;
            return pace + Mathf.Max(0, rate) * (float)ahead;
        }

        void OnDestroy() { if (graph.IsValid()) graph.Destroy(); }

        // ----- Shared API -----

        /// Stand beside the ball, facing across the aim line (a right-hander stands to the
        /// ball's left as seen from behind).
        public void Stand(Vector3 ball, Vector3 aimDirection)
        {
            var side = Vector3.Cross(Vector3.up, aimDirection).normalized; // right of the line
            transform.position = ball - side * 0.75f;
            transform.rotation = Quaternion.LookRotation(side, Vector3.up);
            standBall = ball; standAim = Vector3.ProjectOnPlane(aimDirection, Vector3.up).normalized; hasStand = standAim.sqrMagnitude > .5f;
        }

        public void SetVisible(bool on) => gameObject.SetActive(on);

        /// The backswing follows the phone: 0 is address, 1 the top.
        public void ShowLoad(float load)
        {
            shownLoad = load;
            if (phase == 4 && hasModel && load > .001f) Settle();   // (a backswing never starts out of a move: Idle, an emote, a reaction)
            if (phase == 0) pace = -1;
            if (phase == 3 && hasModel) { EndWatch(); Crossfade(0.3f); phase = 0; loadVelocity = 0; Show(0); }
            if (phase == 3) phase = 0;
            if (phase == 0) loadTarget = clipName == "Putt" ? Mathf.Sqrt(Mathf.Clamp01(load)) : Mathf.Clamp01(load);
        }

        /// Swing through from wherever the backswing got to. Returns the seconds until the club
        /// reaches the ball, so the ball can leave exactly then.
        public float Strike(bool atImpact = false)
        {
            swingThrough = 0;
            if (!hasModel) return atImpact ? 0 : 0.12f;
            if (phase == 4) Settle();   // (nor a downswing: it is the swing clip, square to the stance, or nothing)
            // How far back it got. A full swing comes down from the top; a shorter one joins the
            // downswing where the club is about as far back, a little slower (a shorter swing
            // is a gentler one), and its follow-through stops short of the full finish.
            // (the backswing asked for, not only the pose shown, while the pose is following it: it trails the phone a little, and
            // a full turn is a full swing. A backswing the pose never followed, a touch tap's, stays the tap it was.)
            float f = Mathf.Clamp01(time / Mathf.Max(0.01f, TopTime));
            if (phase == 0 && f >= .75f * loadTarget) f = Mathf.Max(f, Mathf.Clamp01(loadTarget));
            bool full = f >= 0.9f;
            swingU = full ? 0 : Mathf.Min(0.95f, Mathf.Pow(1 - f, 1 / Accel));   // (even a tap swings through a little)
            float seconds = Downswing * (full ? 1 : Mathf.Lerp(0.7f, 1f, f));
            swingRate = (1 - swingU) / seconds;
            // the club's clip-speed at impact, which the follow-through picks up
            float impactSpeed = (ImpactTime - TopTime) * Accel * swingRate;
            // (a putt's follow-through mirrors its stroke: a short one is short through the ball too)
            finishTime = full ? EndTime : ImpactTime + (EndTime - ImpactTime) * Mathf.Max(clipName == "Putt" ? 0.3f : 0.55f, f);
            throughSeconds = Mathf.Clamp((finishTime - ImpactTime) * EaseOut / Mathf.Max(0.01f, impactSpeed), 0.35f, 1.6f);
            if (atImpact) {
                // The real club has reached the ball. Never schedule a second downswing.
                pace = -1;
                if (phase == 5) return 0;   // the club got there first and is on its way through: carry on, never back to the ball
                if (phase == 2)
                {
                    // the follow-through leaves the ball at the pace the club actually came down (a phone swing's own), and
                    // finishes as far as the downswing's backswing earned
                    finishTime = swingFinish;
                    float down = Time.time - strikeAt;
                    // (a paced downswing's own last pace, so the club leaves the ball as fast as it came to it; else its average)
                    float rate = paceRate > 0 ? paceRate / Accel : down > .02f ? (ImpactTime - strikeClip) / down : swingRate * (ImpactTime - TopTime);
                    rate = Mathf.Clamp(rate, (ImpactTime - TopTime) / .5f, (ImpactTime - TopTime) / .16f);
                    throughSeconds = Mathf.Clamp((finishTime - ImpactTime) * EaseOut / Mathf.Max(0.01f, rate * Accel), 0.35f, 1.6f);
                    if (time > ImpactTime && finishTime > ImpactTime)
                    {
                        // (already a touch past the ball: the follow-through goes on from there)
                        float x = Mathf.Clamp01((time - ImpactTime) / (finishTime - ImpactTime));
                        fade = 0; Weigh(); throughV = 1 - Mathf.Pow(1 - x, 1 / EaseOut); phase = 5;
                        ShowThrough();
                        return 0;
                    }
                }
                fade = 0; Weigh(); throughV = 0; phase = 5;
                Show(ImpactTime);
                return 0;
            }
            Crossfade(full ? 0.07f : 0.12f);   // from the backswing pose into the downswing's
            phase = 2;
            swingFinish = finishTime; strikeAt = Time.time; strikeClip = DownswingTime(swingU);
            paceRate = 0; paceShownAt = Time.time;
            if (downArc != null) paceStartShare = ArcShare(strikeClip);
            Show(DownswingTime(swingU));
            if (pace >= 0) ShowPaced();
            return seconds;
        }

        float swingFinish;

        /// The downswing where the phone's turn has it: as far along the club's path as the phone is through its own turn (from where
        /// this downswing started), never back, and waiting at the ball for the phone's impact.
        void ShowPaced()
        {
            float share = paceStartShare + (1 - paceStartShare) * PaceNow();
            // (a phone a moment ahead of its impact sample carries the club a little on through the ball at the downswing's last
            // pace rather than holding it there: the impact then takes the follow-through on from where the club is)
            float t = share <= 1 ? ArcTime(share) : ImpactTime + Mathf.Min(share - 1, .1f) * (ImpactTime - ArcTime(.9f)) * 10;
            t = Mathf.Max(time, t);
            float dt = Time.time - paceShownAt;
            if (dt > 1e-4f) { float r = (t - time) / dt; paceRate = paceRate > 0 ? Mathf.Lerp(paceRate, r, .5f) : r; paceShownAt = Time.time; }
            swingU = Mathf.Pow(Mathf.Clamp01((t - TopTime) / Mathf.Max(1e-4f, ImpactTime - TopTime)), 1 / Accel);
            Show(t);
        }

        /// The model back square to the stance. The studio's idle and emote moves turn it a quarter (ClipYaw: they face the camera),
        /// and a golfer left in that turn at address stood facing the TV; whatever got them to address, the swing clips are square.
        void SquareTheModel()
        {
            if (!hasModel || !modelGo || phase == 4 || Quaternion.Angle(modelGo.transform.localRotation, baseRot) <= .1f) return;
            modelGo.transform.localRotation = baseRot;
        }

        public void Settle()
        {
            pace = -1; EndWatch(); CancelPickUp();
            if (phase == 4) { clipName = null; SetClub(shownClub, shownShort); }
            SquareTheModel();
            swingThrough = -1; shownLoad = 0;
            // back to address from wherever it is (the finish, a half-made backswing) without a pop
            if (hasModel && phase != 4 && time > 0.001f) Crossfade(0.3f);
            phase = 0; loadTarget = 0; loadVelocity = 0;
            if (hasModel) Show(0);
        }

        void Update()
        {
            if (hasModel) UpdateModel(); else UpdateFigure();
        }

        /// After every Update (GolfGame turns the stance round the ball in its own): the shoes, at address only.
        void LateUpdate()
        {
            if (turnFrames > 0) ApplyTurnFromCamera();
            SquareTheModel();   // (whatever turned the model, a swing is never played with it facing the TV)
            if (hasModel && phase == 2 && pace >= 0) ShowPaced();   // (the phone's downswing, with this frame's samples in)
            if (footwork != null && hasModel) footwork.Tick(phase == 0 && time <= Mathf.Max(.02f, TopTime * .04f), Time.deltaTime);
        }

        /// The face that goes with a move (the golfer has no tennis driver to read it from).
        static GolfArcade.Tennis.MatchHeroFacePerformance.Mood MoodOf(string move) => move switch
        {
            "Emote_JumpJoy" or "Emote_FistPump" or "Emote_Victory" or "Cheer" or "FistPump" => GolfArcade.Tennis.MatchHeroFacePerformance.Mood.Happy,
            "Emote_Slump" or "Emote_Defeat" => GolfArcade.Tennis.MatchHeroFacePerformance.Mood.Sad,
            "Emote_Stomp" => GolfArcade.Tennis.MatchHeroFacePerformance.Mood.Angry,
            "Emote_Shock" => GolfArcade.Tennis.MatchHeroFacePerformance.Mood.Shock,
            _ => GolfArcade.Tennis.MatchHeroFacePerformance.Mood.None,
        };
        void SetMood(string move)
        {
            var face = heroFigure != null ? heroFigure.Root.GetComponentInChildren<GolfArcade.Tennis.MatchHeroFacePerformance>() : null;
            if (face) face.ForcedMood = MoodOf(move);
        }

        void UpdateModel()
        {
            float dt = Time.deltaTime;
            TickFade(dt);
            poseTransition?.Tick(dt);
            UpdateFace(dt);
            TickMannerisms(dt);
            if (pickStage != 0) TickPickUp(dt);
            switch (phase)
            {
                case 0:
                    // follow the phone's load with a critically damped spring: live, but it eases
                    // in and out of every move instead of travelling at a constant rate
                    Show(Mathf.SmoothDamp(time, loadTarget * TopTime, ref loadVelocity, clipName == "Putt" ? .11f : .07f, TopTime * 10f, dt));
                    break;
                case 2:
                    if (pace >= 0 && Time.time - paceAt > .2f) pace = -1;   // the phone went quiet: the clock carries the swing on
                    if (pace >= 0) break;   // paced in LateUpdate, once every Update has taken this frame's samples
                    swingU += swingRate * dt;
                    if (swingU < 1) { Show(DownswingTime(swingU)); break; }
                    // through the ball: the time left over this frame goes into the follow-through
                    throughV = swingRate > 0 ? (swingU - 1) / swingRate / throughSeconds : 0;
                    phase = 5;
                    ShowThrough();
                    break;
                case 5:
                    throughV += dt / throughSeconds;
                    ShowThrough();
                    break;
                case 3:
                    if (fade > 0 || watchClock >= 0) Evaluate();
                    break;
                case 4:
                    if (!loopPerformance && performTime + dt >= performLength)
                    {
                        Perform("Idle");
                        break;
                    }
                    performTime = Mathf.Repeat(performTime + dt, performLength);
                    // a spectator nobody can see isn't worth posing
                    if (spectator && body0 && !body0.isVisible) break;
                    clip.SetTime(GolfArcade.Tennis.TennisEmotes.SourceTime(clipName, performTime * performanceRate, performLength * performanceRate));
                    Evaluate();
                    break;
            }
        }

        // ----- Primitive fallback -----

        void BuildFigure()
        {
            var skin = GolferStyle.SkinColor;
            var shirt = new Color(0.2f, 0.45f, 0.85f);
            var trousers = new Color(0.25f, 0.25f, 0.3f);

            body = new GameObject("Body").transform;
            body.SetParent(transform, false);
            var legs = HoleView.Primitive(PrimitiveType.Capsule, "Legs", trousers, body);
            legs.transform.localPosition = new Vector3(0, 0.45f, 0);
            legs.transform.localScale = new Vector3(0.35f, 0.45f, 0.3f);
            var torso = HoleView.Primitive(PrimitiveType.Capsule, "Torso", shirt, body);
            torso.transform.localPosition = new Vector3(0, 1.05f, 0);
            torso.transform.localScale = new Vector3(0.45f, 0.35f, 0.32f);
            var head = HoleView.Primitive(PrimitiveType.Sphere, "Head", skin, body);
            Head = head.transform;
            head.transform.localPosition = new Vector3(0, 1.62f, 0);
            head.transform.localScale = Vector3.one * 0.34f;
            var cap = HoleView.Primitive(PrimitiveType.Cylinder, "Cap", Color.white, body);
            cap.transform.localPosition = new Vector3(0, 1.78f, 0.02f);
            cap.transform.localScale = new Vector3(0.36f, 0.04f, 0.36f);

            pivot = new GameObject("Shoulders").transform;
            pivot.SetParent(body, false);
            pivot.localPosition = new Vector3(0, 1.3f, 0);

            var arms = HoleView.Primitive(PrimitiveType.Capsule, "Arms", skin, pivot);
            arms.transform.localPosition = new Vector3(0, -0.35f, 0.15f);
            arms.transform.localScale = new Vector3(0.12f, 0.35f, 0.12f);

            club = new GameObject("Club").transform;
            club.SetParent(pivot, false);
            var shaft = HoleView.Primitive(PrimitiveType.Cylinder, "Shaft", new Color(0.75f, 0.75f, 0.78f), club);
            shaft.transform.localPosition = new Vector3(0, -0.85f, 0.2f);
            shaft.transform.localScale = new Vector3(0.03f, 0.55f, 0.03f);
            var headGo = HoleView.Primitive(PrimitiveType.Cube, "Clubhead", new Color(0.3f, 0.3f, 0.32f), club);
            headGo.transform.localPosition = new Vector3(0.06f, -1.38f, 0.2f);
            headGo.transform.localScale = new Vector3(0.16f, 0.07f, 0.09f);
        }

        void UpdateFigure()
        {
            float angle;
            if (swingThrough >= 0)
            {
                swingThrough += Time.deltaTime;
                float t = Mathf.Clamp01(swingThrough / 0.35f);
                float eased = 1 - Mathf.Pow(1 - t, 3);
                angle = Mathf.Lerp(-(rest + shownLoad * 150f), 170f, eased);
                if (t >= 1 && swingThrough > 1.2f) { swingThrough = -1; shownLoad = 0; }
            }
            else
            {
                angle = -(rest + shownLoad * 150f);
            }
            pivot.localRotation = Quaternion.AngleAxis(-angle + rest, Vector3.forward) * Quaternion.AngleAxis(25f, Vector3.right);
            float turn = swingThrough >= 0 ? Mathf.Lerp(-shownLoad * 30f, 40f, Mathf.Clamp01(swingThrough / 0.35f)) : -shownLoad * 30f;
            body.localRotation = Quaternion.AngleAxis(turn, Vector3.up);
        }
    }
}
