using GolfArcade.Course;
using UnityEngine;

namespace GolfArcade.Game
{
    /// How a shot looks in the air and when it comes down. The ball draws a short trail, the way
    /// Wii Sports' does (Adnan 10-28: "shorter, not a straight line", like the strike's effect):
    /// a comet tail over the last third of a second of its path (CometTail) with speed-line
    /// wisps twisting round it, in the colour of the swing's rating — green for a clean one,
    /// yellow for an imperfect one, red for a mishit — gone soon after it lands.
    /// Every bounce throws up a puff of the ground it hit, and a ball in the sea splashes. The
    /// strike itself flashes: a starburst at the ball, a shockwave ring across the ground and the
    /// turf it cut flying forward (Resources/Effects: Higgsfield sprites — flash, ring, grass,
    /// dust, splash). The
    /// rating bands and colours are Resources/Course/swing_trail.json, read off Codex's
    /// Hole_12_Cinematic.blend by blender/scripts/hole12_cinematic_export.py.
    public sealed class ShotEffects : MonoBehaviour
    {
        public enum Quality { Pure, Fair, OffLine }

        [System.Serializable] public class RatingBand { public string quality; public float min, max; }
        [System.Serializable] public class Rgb { public float[] green, yellow, red; }
        [System.Serializable]
        public class Recipe
        {
            public Rgb colors;
            public float headAlpha = 0.42f, tailAlpha = 0.04f, headRadiusBalls = 0.68f, tailRadiusBalls = 0.056f;
            public float lengthSeconds = 0.333f, fadeSeconds = 0.533f;
            public RatingBand[] ratingBands;
        }
        static Recipe recipe;
        public static Recipe TrailRecipe() => Spec();
        static Recipe Spec()
        {
            if (recipe != null) return recipe;
            var text = Resources.Load<TextAsset>("Course/swing_trail");
            recipe = text ? JsonUtility.FromJson<Recipe>(text.text) : new Recipe();
            recipe.colors ??= new Rgb();
            recipe.colors.green ??= new[] { 1f, .82f, .32f };
            recipe.colors.yellow ??= new[] { 1f, .97f, .86f };
            recipe.colors.red ??= new[] { .64f, .76f, .86f };
            if (recipe.ratingBands == null || recipe.ratingBands.Length == 0)
                recipe.ratingBands = new[] { new RatingBand { quality = "red", min = 0, max = 50 }, new RatingBand { quality = "yellow", min = 50, max = 80 }, new RatingBand { quality = "green", min = 80, max = 101 } };
            return recipe;
        }
        static Color Of(float[] c) => new(c[0], c[1], c[2]);
        public static Color PureColor => Of(Spec().colors.green);
        public static Color FairColor => Of(Spec().colors.yellow);
        public static Color OffLineColor => Of(Spec().colors.red);
        public static Color ColorOf(Quality q) => q == Quality.Pure ? PureColor : q == Quality.Fair ? FairColor : OffLineColor;

        /// The band a 0–100 rating falls in, by Codex's thresholds.
        public static Quality QualityOf(float rating)
        {
            foreach (var b in Spec().ratingBands)
                if (rating >= b.min && rating < b.max)
                    return b.quality == "green" ? Quality.Pure : b.quality == "yellow" ? Quality.Fair : Quality.OffLine;
            return rating >= 80 ? Quality.Pure : rating >= 50 ? Quality.Fair : Quality.OffLine;
        }

        static Texture2D soft;
        static Material particleMaterial;

        CometTail comet;
        Transform ball;
        BallLook look;
        ParticleSystem puffs, splash, trail;
        Gear.TrailStyle trailStyle;
        Vector3 trailFrom; bool trailing;

        /// The trail the ball leaves in the air (a reward): none, sparkles, fire or a rainbow.
        public void SetTrail(Gear.TrailStyle style) => trailStyle = style;
        Camera view;

        public static ShotEffects Create(Transform parent, Transform ball, Camera view, BallLook look)
        {
            var go = new GameObject("Shot effects");
            go.transform.SetParent(parent, false);
            var fx = go.AddComponent<ShotEffects>();
            fx.view = view;
            fx.ball = ball;
            fx.look = look;
            fx.comet = CometTail.Create(go.transform, look);
            fx.SetQuality(Quality.Fair);
            fx.puffs = fx.BuildParticles("Puffs", 0.7f, 1.1f, 0.22f, 0.5f, -2.2f);
            fx.splash = fx.BuildParticles("Splash", 0.9f, 1.4f, 0.28f, 0.9f, -3.5f);
            // cartoon dust for the puffs; the splash keeps its soft droplets
            var dust = SpriteMaterial("dust");
            if (dust) fx.puffs.GetComponent<ParticleSystemRenderer>().sharedMaterial = dust;
            fx.clippings = fx.BuildParticles("Clippings", 0.28f, 0.5f, 0.55f, 0.95f, -9f);
            fx.trail = fx.BuildParticles("Trail", 0.3f, 0.5f, 0.5f, 0.9f, 0f);
            var trailMain = fx.trail.main; trailMain.maxParticles = 3000;
            var grass = SpriteMaterial("grass");
            if (grass)
            {
                fx.clippings.GetComponent<ParticleSystemRenderer>().sharedMaterial = grass;
                var sheet = fx.clippings.textureSheetAnimation;
                sheet.enabled = true; sheet.numTilesX = 2; sheet.numTilesY = 2;
                sheet.animation = ParticleSystemAnimationType.WholeSheet;
                sheet.frameOverTime = new ParticleSystem.MinMaxCurve(0f);
                sheet.startFrame = new ParticleSystem.MinMaxCurve(0f, 3.999f / 4f);   // one clump each, at random
                var main = fx.clippings.main;
                main.startRotation = new ParticleSystem.MinMaxCurve(0, Mathf.PI * 2);
                var spin = fx.clippings.rotationOverLifetime; spin.enabled = true;
                spin.z = new ParticleSystem.MinMaxCurve(-6f, 6f);
                var size = fx.clippings.sizeOverLifetime; size.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0, 1, 1, 0.8f));
            }
            fx.flash = fx.Burst("Strike flash", "flash", false);
            fx.flare = fx.Burst("Strike flare", "flash", false);
            fx.ring = fx.Burst("Strike ring", "ring", true);
            fx.shock = fx.Burst("Strike shock", "ring", false);
            // speed lines behind the ball for its first instants: stretched along their own velocity
            fx.streaks = fx.BuildParticles("Launch streaks", 0.12f, 0.2f, 0.12f, 0.2f, 0f);
            var streakDraw = fx.streaks.GetComponent<ParticleSystemRenderer>();
            streakDraw.renderMode = ParticleSystemRenderMode.Stretch; streakDraw.velocityScale = 0.1f; streakDraw.lengthScale = 1f;
            streakDraw.sharedMaterial = new Material(ParticleMaterial()) { mainTexture = Band(), name = "Launch streak" };
            var streakMain = fx.streaks.main; streakMain.maxParticles = 800;   // the flight's wisps (EmitWisps) as well as the launch's
            fx.crown = fx.Burst("Splash crown", "splash", false);
            // droplets and molten globs: stretched along their flight, shrinking as they fall; ripples spreading flat on the surface
            fx.drops = fx.BuildDroplets("Droplets", -10.5f, 0.05f, 1.9f);
            fx.globs = fx.BuildDroplets("Molten globs", -7.5f, 0.02f, 1.25f);
            fx.ripples = new Flare[4];
            for (int i = 0; i < fx.ripples.Length; i++) fx.ripples[i] = fx.Burst("Ripple " + i, "ring", true);
            return fx;
        }

        static Texture2D band;
        /// A strip solid down its middle, fading to nothing at both edges — across a line so it
        /// reads as light rather than a painted stripe.
        public static Texture2D Band()
        {
            if (band) return band;
            const int n = 32;
            band = new Texture2D(4, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[4 * n];
            for (int y = 0; y < n; y++)
            {
                float d = Mathf.Abs((y + 0.5f) / n - 0.5f) * 2f;
                float a = Mathf.Clamp01(1 - d); a = a * a * (3 - 2 * a);
                for (int x = 0; x < 4; x++) px[y * 4 + x] = new Color32(255, 255, 255, (byte)(255 * a));
            }
            band.SetPixels32(px); band.Apply();
            return band;
        }

        /// A disc that fades to nothing at its edge, for particles.
        public static Texture2D Soft()
        {
            if (soft) return soft;
            const int n = 64;
            soft = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float d = Mathf.Sqrt((x + 0.5f - n / 2f) * (x + 0.5f - n / 2f) + (y + 0.5f - n / 2f) * (y + 0.5f - n / 2f)) / (n / 2f);
                    float a = Mathf.Clamp01(1 - d); a = a * a * (3 - 2 * a);
                    px[y * n + x] = new Color32(255, 255, 255, (byte)(255 * a));
                }
            soft.SetPixels32(px); soft.Apply();
            return soft;
        }

        /// A particle material wearing one of the Higgsfield sprites in Resources/Effects.
        static Material SpriteMaterial(string name)
        {
            var tex = Resources.Load<Texture2D>("Effects/" + name);
            if (!tex) return null;
            tex.wrapMode = TextureWrapMode.Clamp;
            return new Material(ParticleMaterial()) { mainTexture = tex, name = "Effect " + name };
        }

        /// A one-shot sprite that grows and fades: a quad facing the camera, or lying flat on the ground.
        sealed class Flare
        {
            public Transform quad; public Material mat; public bool flat; public Vector3 facing;
            public float age = -1, seconds, from, to; public Color tint;
        }
        Flare flash, flare, ring, shock, crown;
        Flare[] ripples;
        ParticleSystem drops, globs;
        /// Parts of an effect that come a moment after the first (the jet after the crown).
        readonly System.Collections.Generic.List<(float at, System.Action act)> later = new();
        void After(float seconds, System.Action act) => later.Add((Time.time + seconds, act));
        ParticleSystem clippings, streaks;
        float streakLeft, streakTier; Vector3 streakFrom; bool streakStarted;

        Flare Burst(string name, string sprite, bool flat)
        {
            var mat = SpriteMaterial(sprite);
            if (!mat) return null;
            var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
            go.name = name;
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(transform, false);
            var r = go.GetComponent<MeshRenderer>();
            r.sharedMaterial = mat; r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
            go.layer = BallLook.OverlayLayer;   // the minimap leaves it out
            go.SetActive(false);
            return new Flare { quad = go.transform, mat = mat, flat = flat };
        }

        void Fire(Flare f, Vector3 at, float seconds, float from, float to, Color tint)
        {
            if (f == null) return;
            f.quad.position = at; f.age = 0; f.seconds = seconds; f.from = from; f.to = to; f.tint = tint;
            f.quad.localRotation = f.flat ? Quaternion.Euler(90, 0, 0) : f.facing != Vector3.zero ? Quaternion.LookRotation(f.facing) : Quaternion.identity;
            f.quad.gameObject.SetActive(true);
            Step(f, 0);
        }

        void Step(Flare f, float dt)
        {
            if (f == null || f.age < 0) return;
            f.age += dt;
            float t = f.age / f.seconds;
            if (t >= 1) { f.age = -1; f.quad.gameObject.SetActive(false); return; }
            float grow = 1 - (1 - t) * (1 - t) * (1 - t);   // out fast, then settle
            f.quad.localScale = Vector3.one * Mathf.Lerp(f.from, f.to, grow);
            var c = f.tint; c.a *= t < 0.25f ? 1 : 1 - (t - 0.25f) / 0.75f; f.mat.color = c;
            if (!f.flat && f.facing == Vector3.zero && view)
            {
                // face the camera, with a quick spin on the starburst
                f.quad.rotation = Quaternion.LookRotation(f.quad.position - view.transform.position, view.transform.up) * Quaternion.Euler(0, 0, f.age * 90f);
            }
        }

        void Update()
        {
            float dt = Time.deltaTime;
            Step(flash, dt); Step(flare, dt); Step(ring, dt); Step(shock, dt); Step(crown, dt);
            if (ripples != null) foreach (var r in ripples) Step(r, dt);
            for (int i = later.Count - 1; i >= 0; i--)
                if (Time.time >= later[i].at) { var act = later[i].act; later.RemoveAt(i); act(); }
        }

        ParticleSystem BuildDroplets(string name, float gravity, float velocityScale, float lengthScale)
        {
            var ps = BuildParticles(name, 1f, 1f, 0.5f, 1f, gravity);
            var main = ps.main; main.maxParticles = 500;
            var draw = ps.GetComponent<ParticleSystemRenderer>();
            draw.renderMode = ParticleSystemRenderMode.Stretch; draw.velocityScale = velocityScale; draw.lengthScale = lengthScale;
            var size = ps.sizeOverLifetime; size.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0, 1, 1, 0.55f));
            var col = ps.colorOverLifetime;
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) },
                      new[] { new GradientAlphaKey(1f, 0), new GradientAlphaKey(0.9f, 0.7f), new GradientAlphaKey(0, 1) });
            col.color = g;
            return ps;
        }

        void Drop(ParticleSystem system, Vector3 at, Vector3 velocity, Color color, float size, float life, int i) =>
            system.Emit(new ParticleSystem.EmitParams { position = at, velocity = velocity, startColor = color, startSize = size, startLifetime = life },
                        GolfArcade.EnvironmentArt.EnvironmentFx.ParticleAt(i));

        void Ripple(int k, Vector3 at, float seconds, float to, Color tint) =>
            Fire(ripples != null && k < ripples.Length ? ripples[k] : null, at + Vector3.up * 0.02f, seconds, 0.25f, to, tint);

        /// How big the contact reads, 0–1, by the strike's grade (the same hook the strike's sound and haptics use):
        /// a thin one is a dull tick, a perfect one the full bundle. Without a grade, the trail's rating stands in.
        public float StrikeTier(GolfArcade.Swing.StrikeGrade? grade) => grade switch
        {
            GolfArcade.Swing.StrikeGrade.Perfect => 1f,
            GolfArcade.Swing.StrikeGrade.Great => .72f,
            GolfArcade.Swing.StrikeGrade.Good => .48f,
            GolfArcade.Swing.StrikeGrade.Thin => .2f,
            _ => quality == Quality.Pure ? .8f : quality == Quality.Fair ? .48f : .2f,
        };

        /// The club meets the ball at `at`, sending it along `forward`, off `lie`, at `power` (0–1), struck
        /// `grade`: layered feedback all inside the first tenth of a second, scaled by the grade (game-feel tiers) —
        /// a white flash with a gold flare and sparks on a great one, a shock ring the ball punches through, a ring
        /// across the ground, what the club cut by lie (turf and a clod of soil off the fairway, long grass out of
        /// the rough, a sand blast from a bunker, chips off ice), and speed lines behind the ball as it leaves.
        /// A putt only rings, softly (gold for a perfect stroke).
        public void Strike(Vector3 at, Vector3 forward, CourseLie lie, float power, bool putt, GolfArcade.Swing.StrikeGrade? grade = null)
        {
            power = Mathf.Clamp01(power);
            float tier = StrikeTier(grade), punch = tier * (0.55f + 0.45f * power);
            var ground = at; ground.y += 0.03f;
            if (putt)
            {
                Fire(ring, ground, 0.4f, 0.2f, 0.8f + 0.3f * tier, grade == GolfArcade.Swing.StrikeGrade.Perfect ? new Color(1f, .9f, .55f, .6f) : new Color(1, 1, 1, 0.5f));
                return;
            }
            forward.y = 0; forward = forward.sqrMagnitude > 1e-4f ? forward.normalized : Vector3.forward;
            var side = Vector3.Cross(Vector3.up, forward);
            var gold = new Color(1f, .86f, .42f);
            // the flash: white, bigger and brighter the cleaner the strike; a slower gold flare behind it on a great one
            Fire(flash, at + Vector3.up * 0.12f, 0.16f + 0.08f * tier, 0.3f, 0.7f + 2.4f * punch, Color.white);
            if (tier >= .7f) Fire(flare, at + Vector3.up * 0.15f, 0.34f, 0.5f, 1.8f + 2.6f * punch, new Color(gold.r, gold.g, gold.b, .8f));
            // the shock: a ring standing across the shot that the ball punches through, and one across the ground
            if (tier >= .45f && shock != null) { shock.facing = forward; Fire(shock, at + forward * 0.5f + Vector3.up * 0.35f, 0.24f, 0.2f, 1.2f + 2.6f * punch, new Color(1, 1, 1, .45f + .4f * tier)); }
            Fire(ring, ground, 0.45f, 0.3f, 1.6f + 4.2f * punch, new Color(1, 1, 1, 0.45f + 0.4f * tier));
            // sparks off a great strike, thrown forward and up
            if (tier >= .7f)
                for (int i = 0; i < Mathf.RoundToInt(10 + 26 * punch); i++)
                    trail.Emit(new ParticleSystem.EmitParams
                    {
                        position = at + Vector3.up * 0.12f,
                        velocity = forward * Random.Range(2f, 9f) + side * Random.Range(-3f, 3f) + Vector3.up * Random.Range(1.5f, 6f),
                        // a perfect one throws confetti in with the gold (Mario Golf: Super Rush's "nice shot", refs/_H7Y7Ijug0w)
                        startColor = tier >= .95f && i % 3 == 0 ? Color.HSVToRGB(Random.value, .7f, 1f) : Color.Lerp(Color.white, gold, Random.value),
                        startSize = Random.Range(0.12f, 0.3f),
                        startLifetime = Random.Range(0.25f, 0.55f),
                    }, 1);
            // speed lines behind the ball for its first instants
            streakLeft = 0.18f + 0.22f * tier; streakTier = tier; streakStarted = false;
            switch (lie)
            {
                case CourseLie.Water: return;
                case CourseLie.Bunker:
                    Touchdown(at, CourseLie.Bunker, 1.2f + power);
                    for (int i = 0; i < Mathf.RoundToInt(18 + 30 * punch); i++)
                        splash.Emit(new ParticleSystem.EmitParams
                        {
                            position = at + Vector3.up * 0.05f,
                            velocity = forward * Random.Range(1f, 5f) + side * Random.Range(-2f, 2f) + Vector3.up * Random.Range(2f, 5f),
                            startColor = Color.Lerp(new Color(.95f, .86f, .64f), new Color(.82f, .7f, .48f), Random.value),
                            startSize = Random.Range(0.2f, 0.5f), startLifetime = Random.Range(0.5f, 0.9f),
                        }, 1);
                    return;
                case CourseLie.Ice:
                    for (int i = 0; i < 3; i++) IceSpray(at, -forward, 1f);
                    return;
            }
            if (!clippings) return;
            bool rough = lie is CourseLie.Rough or CourseLie.OutOfBounds, tee = lie == CourseLie.Tee;
            int count = Mathf.RoundToInt((8 + 26 * punch) * (rough ? 1.8f : tee ? .5f : 1f));
            for (int i = 0; i < count; i++)
            {
                var v = forward * Random.Range(1.5f, 6f) * (0.5f + power) + side * Random.Range(-1.6f, 1.6f) + Vector3.up * Random.Range(1.8f, 4.5f) * (0.6f + 0.6f * power) * (rough ? 1.2f : 1f);
                clippings.Emit(new ParticleSystem.EmitParams
                {
                    position = at + side * Random.Range(-0.08f, 0.08f) + Vector3.up * 0.04f,
                    velocity = v,
                    startColor = rough ? Color.Lerp(new Color(.55f, .78f, .4f), new Color(.75f, .9f, .55f), Random.value) : Color.Lerp(Color.white, new Color(0.8f, 0.95f, 0.7f), Random.value),
                    startSize = Random.Range(0.28f, 0.5f) * (rough ? 1.25f : 1f),
                    startLifetime = Random.Range(0.55f, 0.95f),
                }, 1);
            }
            // the divot: clods of soil thrown forward off fairway grass (not off a tee peg)
            if (!tee && !rough)
                for (int i = 0; i < Mathf.RoundToInt(3 + 8 * punch); i++)
                    clippings.Emit(new ParticleSystem.EmitParams
                    {
                        position = at + forward * 0.1f + Vector3.up * 0.03f,
                        velocity = forward * Random.Range(2f, 5f) + side * Random.Range(-.8f, .8f) + Vector3.up * Random.Range(2f, 3.5f),
                        startColor = Color.Lerp(new Color(.42f, .3f, .18f), new Color(.5f, .62f, .3f), Random.value * .5f),
                        startSize = Random.Range(0.35f, 0.6f), startLifetime = Random.Range(0.6f, 0.9f),
                    }, 1);
            // a puff of dust off the turf it cut
            Touchdown(at, lie, 0.3f + 0.3f * punch);
        }

        /// Speed lines laid behind the ball for its first instants in the air (Strike starts them).
        void EmitStreaks()
        {
            if (streakLeft <= 0 || !ball || !streaks) return;
            streakLeft -= Time.deltaTime;
            var at = ball.position;
            if (!streakStarted) { streakFrom = at; streakStarted = true; return; }
            var step = at - streakFrom; float dt = Mathf.Max(1e-4f, Time.deltaTime);
            if (step.sqrMagnitude < 1e-4f) return;
            var v = step / dt;
            int n = Mathf.RoundToInt(2 + 4 * streakTier);
            for (int i = 0; i < n; i++)
                streaks.Emit(new ParticleSystem.EmitParams
                {
                    position = Vector3.Lerp(streakFrom, at, i / (float)n) + Random.insideUnitSphere * 0.25f,
                    velocity = v * 0.25f,
                    startColor = Color.Lerp(Color.white, new Color(1f, .86f, .42f), streakTier * Random.value),
                    startSize = Random.Range(0.08f, 0.16f) * (0.7f + streakTier),
                    startLifetime = Random.Range(0.12f, 0.2f),
                }, 1);
            streakFrom = at;
        }

        /// The ball meeting something standing on the course: a shower of leaves out of a crown or
        /// a bush, chips and dust off a trunk, a rock or a wall.
        public void Knock(Vector3 at, bool leaves, bool stone)
        {
            if (leaves && clippings)
            {
                for (int i = 0; i < 44; i++)
                {
                    var v = Random.insideUnitSphere * 3.6f + Vector3.up * 1.6f;
                    clippings.Emit(new ParticleSystem.EmitParams
                    {
                        position = at + Random.insideUnitSphere * 0.8f,
                        velocity = v,
                        startColor = Color.Lerp(new Color(0.35f, 0.62f, 0.3f), new Color(0.62f, 0.85f, 0.4f), Random.value),
                        startSize = Random.Range(0.5f, 0.95f),
                        startLifetime = Random.Range(1.0f, 1.7f),
                    }, 1);
                }
                return;
            }
            Color a = stone ? new Color(0.78f, 0.8f, 0.84f) : new Color(0.55f, 0.4f, 0.28f), b = stone ? new Color(0.6f, 0.62f, 0.68f) : new Color(0.72f, 0.6f, 0.45f);
            for (int i = 0; i < 12; i++)
            {
                var dir = Random.insideUnitSphere;
                puffs.Emit(new ParticleSystem.EmitParams
                {
                    position = at + dir * 0.1f,
                    velocity = dir * 2.2f + Vector3.up * 0.6f,
                    startColor = Color.Lerp(a, b, Random.value),
                    startSize = Random.Range(0.25f, 0.5f),
                    startLifetime = Random.Range(0.3f, 0.55f),
                }, 1);
            }
        }

        /// A puff of `count` soft bits flying out of `at`, coloured between `a` and `b`: feathers off a
        /// gull, a pop of air off a balloon, dust off a cart.
        public void Burst(Vector3 at, Color a, Color b, int count, float speed, float size, float life = 0.8f, float lift = 0.6f)
        {
            for (int i = 0; i < count; i++)
            {
                var dir = Random.insideUnitSphere;
                puffs.Emit(new ParticleSystem.EmitParams
                {
                    position = at + dir * 0.15f,
                    velocity = dir * speed + Vector3.up * lift,
                    startColor = Color.Lerp(a, b, Random.value),
                    startSize = Random.Range(size * 0.6f, size),
                    startLifetime = Random.Range(life * 0.6f, life),
                }, 1);
            }
        }

        public static Material ParticleMaterial()
        {
            if (particleMaterial) return particleMaterial;
            var shader = Shader.Find("GolfArcade/ParticleSoft");
            if (!shader) Debug.LogError("GolfArcade/ParticleSoft missing from the build — run Golf Arcade → Set Up Project");
            particleMaterial = new Material(shader ?? Shader.Find("Unlit/Color")) { mainTexture = Soft() };
            return particleMaterial;
        }

        ParticleSystem BuildParticles(string name, float sizeMin, float sizeMax, float lifeMin, float lifeMax, float gravity)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var ps = go.AddComponent<ParticleSystem>();
            var main = ps.main;
            main.loop = false; main.playOnAwake = false;
            main.startLifetime = new ParticleSystem.MinMaxCurve(lifeMin, lifeMax);
            main.startSize = new ParticleSystem.MinMaxCurve(sizeMin, sizeMax);
            main.startSpeed = 0; main.gravityModifier = 0; main.maxParticles = 200;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            var emission = ps.emission; emission.enabled = false;
            var shape = ps.shape; shape.enabled = false;
            var col = ps.colorOverLifetime; col.enabled = true;
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) },
                      new[] { new GradientAlphaKey(0.9f, 0), new GradientAlphaKey(0.6f, 0.5f), new GradientAlphaKey(0, 1) });
            col.color = g;
            var size = ps.sizeOverLifetime; size.enabled = true;
            size.size = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(new Keyframe(0, 0.5f), new Keyframe(0.3f, 1f), new Keyframe(1, 1.3f)));
            var force = ps.forceOverLifetime; force.enabled = true; force.y = gravity;
            var r = ps.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = ParticleMaterial();
            r.renderMode = ParticleSystemRenderMode.Billboard;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
            return ps;
        }

        // ---- in flight

        Quality quality = Quality.Fair;
        public void SetQuality(Quality q) => quality = q;

        /// Which ball the trail follows: the game's, or Codex's during his shot.
        public void Follow(Transform t) => ball = t;

        bool flying;
        /// The ball is away: its short trail starts (the ball POV's too: `pov` no longer draws differently).
        public void BeginFlight(bool pov = false)
        {
            comet.Begin(ColorOf(quality));
            flying = true; wisping = false;
        }
        /// The ball is down: the tail narrows away behind the bouncing ball.
        public void Land()
        {
            comet.Land();
            flying = false;
        }
        /// The shot is over (a ball in the water never Lands): the tail goes the same way.
        public void EndFlight() { flying = false; comet.Land(); }
        /// Setting up the next shot: the trail goes now.
        public void ClearTracer() { flying = false; comet.Clear(); }

        void LateUpdate()
        {
            EmitStreaks();
            if (flying && ball) EmitWisps();
            else wisping = false;
            if (flying && ball && trailStyle != Gear.TrailStyle.None) EmitTrail(ball.position);
            else trailing = false;
        }

        /// The strike's speed lines, carried on for the whole flight: short streaks laid along the
        /// ball's path on a slow twist round it (two strands, a ball's width out), so the trail
        /// reads as a ribbon of light curling after the ball rather than a ruled line. Sized off the
        /// drawn ball, so it reads at any distance.
        void EmitWisps()
        {
            var at = look ? look.Centre : ball.position;
            if (!wisping) { wispFrom = at; wispTwist = 0; wisping = true; return; }
            var step = at - wispFrom; float dt = Mathf.Max(1e-4f, Time.deltaTime);
            float length = step.magnitude;
            if (length < 1e-3f) return;
            var dir = step / length;
            var across = Vector3.Cross(dir, Vector3.up); if (across.sqrMagnitude < 1e-4f) across = Vector3.right;
            across.Normalize();
            var up = Vector3.Cross(across, dir);
            float drawn = look ? look.DrawnDiameter : 0.12f;
            var tint = Color.Lerp(Color.white, ColorOf(quality), .55f);
            int n = Mathf.Clamp(Mathf.CeilToInt(length / Mathf.Max(.05f, drawn * .6f)), 1, 12);
            for (int i = 0; i < n; i++)
            {
                float u = (i + 1f) / n;
                wispTwist += 9f * dt / n;   // radians: about one and a half turns a second
                for (int strand = 0; strand < 2; strand++)
                {
                    float a = wispTwist + strand * Mathf.PI;
                    var round = across * Mathf.Cos(a) + up * Mathf.Sin(a);
                    streaks.Emit(new ParticleSystem.EmitParams
                    {
                        position = Vector3.Lerp(wispFrom, at, u) + round * drawn * .55f,
                        velocity = step / dt * .12f + round * drawn * 2f,
                        startColor = new Color(tint.r, tint.g, tint.b, Random.Range(.55f, .85f)),
                        startSize = drawn * Random.Range(.35f, .55f),
                        startLifetime = Random.Range(.16f, .26f),
                    }, 1);
                }
            }
            wispFrom = at;
        }
        Vector3 wispFrom; float wispTwist; bool wisping;

        /// Puffs laid along the ball's path since the last frame, a third of a yard apart so a
        /// fast ball leaves no gaps: sparkles twinkling white and gold, fire burning out from
        /// yellow to red, or bands of every colour.
        void EmitTrail(Vector3 at)
        {
            if (!trailing) { trailFrom = at; trailing = true; return; }
            float length = (at - trailFrom).magnitude;
            int steps = Mathf.Clamp(Mathf.CeilToInt(length / 0.14f), 1, 80);
            for (int i = 1; i <= steps; i++)
            {
                var p = Vector3.Lerp(trailFrom, at, i / (float)steps);
                var e = new ParticleSystem.EmitParams { position = p };
                switch (trailStyle)
                {
                    case Gear.TrailStyle.Sparkle:
                        e.position = p + Random.insideUnitSphere * 0.25f;
                        e.velocity = Random.insideUnitSphere * 0.4f;
                        e.startColor = Color.Lerp(Color.white, new Color(1f, 0.85f, 0.35f), Random.value);
                        e.startSize = Random.Range(0.15f, 0.4f);
                        e.startLifetime = Random.Range(0.4f, 0.9f);
                        break;
                    case Gear.TrailStyle.Fire:
                        e.velocity = Vector3.up * Random.Range(0.3f, 1.2f) + Random.insideUnitSphere * 0.3f;
                        e.startColor = Color.Lerp(new Color(1f, 0.9f, 0.3f), new Color(1f, 0.25f, 0.05f), Random.value);
                        e.startSize = Random.Range(0.45f, 0.8f);
                        e.startLifetime = Random.Range(0.35f, 0.7f);
                        break;
                    default:
                        float hue = (Time.time * 0.9f + i / (float)steps * 0.05f) % 1f;
                        e.startColor = Color.HSVToRGB(hue, 0.75f, 1f);
                        e.startSize = 0.45f;
                        e.startLifetime = 0.8f;
                        break;
                }
                trail.Emit(e, 1);
            }
            trailFrom = at;
        }

        // ---- coming down

        public void Cup(Vector3 at) => Fire(ring, at + Vector3.up * .03f, .4f, .18f, .8f, PureColor);
        public void WetLanding(Vector3 at) => Fire(ring, at + Vector3.up * .03f, .35f, .15f, .7f, new Color(.65f, .85f, 1f, .65f));

        /// A bounce or the landing: the ground it hit decides the puff.
        public void Touchdown(Vector3 at, CourseLie lie, float strength)
        {
            strength = Mathf.Clamp(strength, 0.3f, 1.5f);
            if (lie == CourseLie.Water) { Splash(at); return; }
            Color a, b;
            switch (lie)
            {
                case CourseLie.Ice: a = new Color(0.94f, 0.98f, 1f); b = new Color(0.7f, 0.88f, 1f); break;
                case CourseLie.Bunker: a = new Color(0.94f, 0.85f, 0.62f); b = new Color(0.86f, 0.74f, 0.5f); break;
                case CourseLie.Green: a = new Color(0.75f, 0.95f, 0.5f); b = new Color(0.55f, 0.85f, 0.4f); break;
                case CourseLie.Rough: case CourseLie.OutOfBounds: a = new Color(0.4f, 0.65f, 0.28f); b = new Color(0.55f, 0.45f, 0.3f); break;
                default: a = new Color(0.62f, 0.9f, 0.4f); b = new Color(0.45f, 0.75f, 0.3f); break;
            }
            GolfArcade.EnvironmentArt.EnvironmentFx.Landing(lie,ref a,ref b);
            int count = Mathf.RoundToInt(10 + 14 * strength);
            for (int i = 0; i < count; i++)
            {
                var dir = Random.insideUnitCircle * 1.6f;
                var p = new ParticleSystem.EmitParams
                {
                    position = at + new Vector3(dir.x * 0.1f, 0.05f, dir.y * 0.1f),
                    velocity = new Vector3(dir.x, Random.Range(1.2f, 3.2f) * strength, dir.y) * strength,
                    startColor = Color.Lerp(a, b, Random.value),
                    startSize = Random.Range(0.35f, 0.75f) * (0.7f + 0.5f * strength),
                    startLifetime = Random.Range(0.3f, 0.6f),
                };
                puffs.Emit(p, GolfArcade.EnvironmentArt.EnvironmentFx.ParticleAt(i));
            }
        }

        /// The ball into lava: a molten heave, not water — a flash, thick globs lobbed up and falling back to a glowing surface,
        /// embers streaking higher, orange rings spreading, and smoke.
        public void LavaBurst(Vector3 at)
        {
            Fire(flash, at + Vector3.up * 0.4f, 0.4f, 0.5f, 3.2f, new Color(1f, 0.6f, 0.2f));
            // the glowing surface heaving: rings of molten orange spreading and cooling
            Ripple(0, at, 1.0f, 3.4f, new Color(1f, 0.55f, 0.1f, 0.9f));
            Ripple(1, at, 1.4f, 5.2f, new Color(1f, 0.3f, 0.05f, 0.7f));
            After(0.22f, () => Ripple(2, at, 1.4f, 4.6f, new Color(1f, 0.75f, 0.2f, 0.6f)));
            // thick globs, lobbed up in a dome and falling heavily
            for (int i = 0; i < 26; i++)
            {
                float a = Random.value * Mathf.PI * 2, outward = Random.Range(0.4f, 2.4f);
                Drop(globs, at + new Vector3(Mathf.Cos(a) * 0.2f, 0.05f, Mathf.Sin(a) * 0.2f),
                     new Vector3(Mathf.Cos(a) * outward, Random.Range(3.2f, 7.5f), Mathf.Sin(a) * outward),
                     Color.Lerp(new Color(1f, 0.85f, 0.25f), new Color(0.95f, 0.22f, 0.04f), Random.value), Random.Range(0.28f, 0.6f), Random.Range(0.8f, 1.5f), i);
            }
            // embers: small, bright and fast
            for (int i = 0; i < 60; i++)
            {
                var dir = Random.insideUnitCircle;
                Drop(drops, at + new Vector3(dir.x * 0.3f, 0.05f, dir.y * 0.3f),
                     new Vector3(dir.x * Random.Range(1f, 3.5f), Random.Range(5f, 11f), dir.y * Random.Range(1f, 3.5f)),
                     Color.Lerp(new Color(1f, 0.95f, 0.5f), new Color(1f, 0.4f, 0.08f), Random.value), Random.Range(0.07f, 0.16f), Random.Range(0.7f, 1.4f), i);
            }
            for (int i = 0; i < 16; i++)
            {
                var dir = Random.insideUnitCircle;
                puffs.Emit(new ParticleSystem.EmitParams
                {
                    position = at + new Vector3(dir.x * 0.4f, 0.3f, dir.y * 0.4f),
                    velocity = new Vector3(dir.x * 0.6f, Random.Range(1.5f, 3.2f), dir.y * 0.6f),
                    startColor = Color.Lerp(new Color(0.32f, 0.3f, 0.3f), new Color(0.55f, 0.52f, 0.5f), Random.value),
                    startSize = Random.Range(1.0f, 1.8f),
                    startLifetime = Random.Range(0.9f, 1.6f),
                }, GolfArcade.EnvironmentArt.EnvironmentFx.ParticleAt(i));
            }
        }

        /// A ball skidding on the ice: chips and powder kicked up off its path, thrown back and
        /// out to the sides.
        public void IceSpray(Vector3 at, Vector3 along, float strength)
        {
            along.y = 0;
            var fwd = along.sqrMagnitude > 1e-4f ? along.normalized : Vector3.forward;
            var side = Vector3.Cross(Vector3.up, fwd);
            int count = Mathf.RoundToInt(3 + 7 * Mathf.Clamp01(strength));
            for (int i = 0; i < count; i++)
            {
                puffs.Emit(new ParticleSystem.EmitParams
                {
                    position = at + Vector3.up * 0.04f,
                    velocity = -fwd * Random.Range(0.2f, 1.2f) + side * Random.Range(-1.4f, 1.4f) + Vector3.up * Random.Range(0.6f, 1.8f),
                    startColor = Color.Lerp(new Color(0.95f, 0.98f, 1f), new Color(0.72f, 0.88f, 1f), Random.value),
                    startSize = Random.Range(0.2f, 0.45f),
                    startLifetime = Random.Range(0.25f, 0.5f),
                }, GolfArcade.EnvironmentArt.EnvironmentFx.ParticleAt(i));
            }
        }

        /// The ball into water: an impact crown and a flash of spray, droplets thrown out in a ring and a jet shooting up behind
        /// them, the falling drops, a little mist, and ripples spreading across the surface.
        public void Splash(Vector3 at)
        {
            at.y = 0.02f;
            var water = new Color(0.82f, 0.94f, 1f);
            var deep = new Color(0.5f, 0.78f, 1f);
            Fire(crown, at + Vector3.up * 0.55f, 0.6f, 0.5f, 2.4f, new Color(1f, 1f, 1f, 0.8f));
            // the crown: a ring of drops thrown out and up
            const int count = 36;
            for (int i = 0; i < count; i++)
            {
                float a = (i + Random.value * 0.6f) / count * Mathf.PI * 2, outward = Random.Range(1.6f, 3.2f);
                Drop(drops, at + new Vector3(Mathf.Cos(a) * 0.25f, 0.03f, Mathf.Sin(a) * 0.25f),
                     new Vector3(Mathf.Cos(a) * outward, Random.Range(3.4f, 5.6f), Mathf.Sin(a) * outward),
                     Color.Lerp(water, deep, Random.value), Random.Range(0.12f, 0.26f), Random.Range(0.6f, 1.0f), i);
            }
            // the jet: straight up from the middle a moment later, higher and narrower
            After(0.07f, () =>
            {
                for (int i = 0; i < 26; i++)
                {
                    var j = Random.insideUnitCircle * 0.5f;
                    Drop(drops, at + new Vector3(j.x * 0.2f, 0.1f, j.y * 0.2f),
                         new Vector3(j.x, Random.Range(6f, 10.5f), j.y),
                         Color.Lerp(Color.white, water, Random.value), Random.Range(0.14f, 0.32f), Random.Range(0.8f, 1.3f), i);
                }
                // mist hanging where it broke
                for (int i = 0; i < 10; i++)
                {
                    var d = Random.insideUnitCircle;
                    puffs.Emit(new ParticleSystem.EmitParams
                    {
                        position = at + new Vector3(d.x * 0.5f, 0.4f, d.y * 0.5f),
                        velocity = new Vector3(d.x * 0.5f, Random.Range(0.6f, 1.6f), d.y * 0.5f),
                        startColor = new Color(0.9f, 0.97f, 1f, 0.55f), startSize = Random.Range(0.8f, 1.5f), startLifetime = Random.Range(0.7f, 1.2f),
                    }, GolfArcade.EnvironmentArt.EnvironmentFx.ParticleAt(i));
                }
            });
            // the jet falls back as rain
            After(0.4f, () =>
            {
                for (int i = 0; i < 18; i++)
                {
                    var d = Random.insideUnitCircle * 0.9f;
                    Drop(drops, at + new Vector3(d.x, Random.Range(1.4f, 2.6f), d.y), new Vector3(d.x * 0.3f, Random.Range(-1f, 0f), d.y * 0.3f),
                         Color.Lerp(water, deep, Random.value), Random.Range(0.08f, 0.18f), Random.Range(0.4f, 0.7f), i);
                }
            });
            // ripples spreading across the surface
            Ripple(0, at, 1.0f, 3.0f, new Color(0.9f, 0.97f, 1f, 0.85f));
            After(0.18f, () => Ripple(1, at, 1.2f, 4.6f, new Color(0.85f, 0.95f, 1f, 0.6f)));
            After(0.38f, () => Ripple(2, at, 1.3f, 6.2f, new Color(0.8f, 0.92f, 1f, 0.4f)));
        }
    }
}
