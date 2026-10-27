using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Bowling
{
    /// Magma Lanes (PLAN_BowlingVenues.md §3.4): lanes carved into a volcano at night.
    ///   * the gutters run with lava (a gutter ball rolls through magma), lava rivers down both sides,
    ///     two lavafalls pouring beside the pins, embers drifting up;
    ///   * obsidian cappings that mirror the lava, basalt masking with glowing cracks and a gold crest;
    ///   * a faceted basalt cavern, open to the dusk sky above the pins, the moon over the crater rim;
    ///   * cool moonlight as the key from above, lava bounce from below (ambient ground), a hot white
    ///     pin spot, an orange/teal grade with strong bloom.
    public static class BowlingMagmaLanes
    {
        static readonly Color Lava = new Color(1f, .22f, .02f), LavaHot = new Color(1f, .45f, .08f);
        static readonly Color Basalt = new Color(.075f, .066f, .068f);
        const int LanesEachSide = 2;

        /// Basalt with a web of glowing cracks and the gold swing-arc crest (the masking boards).
        static Texture2D MaskingRock()
        {
            const int w = 512, h = 256;
            var tex = BowlingClubLanes.ArcTexture(w, h, Color.clear, 210, 330, .04f, false);
            var px = tex.GetPixels();
            var rng = new System.Random(77);
            var crack = new float[w * h];
            for (int k = 0; k < 16; k++)
            {
                float x = rng.Next(w), y = rng.Next(h), a = (float)(rng.NextDouble() * Mathf.PI * 2);
                int len = 60 + rng.Next(160);
                for (int s = 0; s < len; s++)
                {
                    int ix = Mathf.RoundToInt(x), iy = Mathf.RoundToInt(y);
                    for (int dy = -2; dy <= 2; dy++) for (int dx = -2; dx <= 2; dx++)
                        {
                            int X = ix + dx, Y = iy + dy; if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
                            crack[Y * w + X] = Mathf.Max(crack[Y * w + X], 1 - (dx * dx + dy * dy) / 8f);
                        }
                    a += ((float)rng.NextDouble() - .5f) * .9f; x += Mathf.Cos(a); y += Mathf.Sin(a);
                }
            }
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float u = x / (float)w, v = y / (float)h;
                    float n = BowlingVenue.Noise(u * 9, v * 5, 3) * .6f + BowlingVenue.Noise(u * 30, v * 15, 4) * .4f;
                    var rock = Basalt * Mathf.Lerp(.5f, 1.4f, n);
                    float c = crack[y * w + x];
                    var col = Color.Lerp(rock, Color.Lerp(Lava, LavaHot, c) * 1.6f, c);
                    var a = px[y * w + x];
                    // the arc in gold (the texture's arc is white with a warm fringe)
                    var gold = Color.Lerp(BrandColors.Gold, Color.white, Mathf.Pow(a.a, 6)) * a.a;
                    px[y * w + x] = col * (1 - a.a) + gold * 1.3f;
                }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        /// Basalt flooring and approach: dark stone with faint glowing seams.
        static Texture2D BasaltTiles()
        {
            const int n = 256;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Repeat, name = "MagmaBasalt" };
            var px = new Color[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float k = .75f + .5f * BowlingVenue.Noise(x / 18f, y / 18f, 11) + .15f * BowlingVenue.Noise(x / 3f, y / 3f, 12);
                    px[y * n + x] = new Color(k, k * .95f, k * .97f);
                }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        /// Basalt with the lava showing through its cracks (lava_cracks as the emission map).
        static Material Seamed(Material m, float intensity)
        {
            m.SetTexture("_EmissionMap", Resources.Load<Texture2D>("Course/Lava/lava_cracks"));
            m.SetColor("_EmissionColor", Lava * intensity);
            m.EnableKeyword("_EMISSION");
            m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
            return m;
        }

        static Material LavaFlow(float intensity, Vector2 tiling)
        {
            var m = BowlingClubLanes.Glow(Lava, intensity, Resources.Load<Texture2D>("Course/Look/Lava_E"));
            m.SetColor("_BaseColor", new Color(.25f, .05f, .01f));
            m.SetFloat("_Smoothness", .7f);
            m.SetTextureScale("_BaseMap", tiling);
            return m;
        }

        /// Embers: small glowing sparks rising off the lava, drifting and fading.
        static void Embers(Transform root, Vector3 centre, Vector3 size, float rate)
        {
            var go = new GameObject("Embers");
            go.transform.SetParent(root, false); go.transform.localPosition = centre;
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.duration = 10; main.loop = true; main.prewarm = true;
            main.startLifetime = new ParticleSystem.MinMaxCurve(4, 8);
            main.startSpeed = new ParticleSystem.MinMaxCurve(.15f, .5f);
            main.startSize = new ParticleSystem.MinMaxCurve(.025f, .07f);
            main.startColor = new ParticleSystem.MinMaxGradient(LavaHot * 3, Lava * 2.2f);
            main.gravityModifier = -.03f;
            main.maxParticles = 400;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            var emission = ps.emission; emission.rateOverTime = rate;
            var shape = ps.shape; shape.shapeType = ParticleSystemShapeType.Box; shape.scale = size;
            shape.rotation = new Vector3(-90, 0, 0);   // emit upward
            var noise = ps.noise; noise.enabled = true; noise.strength = .35f; noise.frequency = .4f; noise.scrollSpeed = .3f;
            var col = ps.colorOverLifetime; col.enabled = true;
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(new Color(1, .4f, .2f), 1) },
                      new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(1, .1f), new GradientAlphaKey(.8f, .6f), new GradientAlphaKey(0, 1) });
            col.color = g;
            var r = go.GetComponent<ParticleSystemRenderer>();
            // the particles shader (URP Unlit ignores the particle colours), additive
            var mat = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
            mat.SetTexture("_BaseMap", BowlingVenue.Dot()); mat.SetColor("_BaseColor", Color.white);
            mat.SetFloat("_Surface", 1); mat.SetFloat("_Blend", 2);
            mat.SetOverrideTag("RenderType", "Transparent");
            mat.SetInt("_SrcBlend", (int)BlendMode.One); mat.SetInt("_DstBlend", (int)BlendMode.One); mat.SetInt("_ZWrite", 0);
            mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            mat.renderQueue = (int)RenderQueue.Transparent;
            r.sharedMaterial = mat; r.renderMode = ParticleSystemRenderMode.Billboard;
            r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
            ps.Play();
        }

        public static BowlingClubLanes.Venue Build(Transform parent, Camera camera)
        {
            var root = new GameObject("MagmaLanes").transform;
            root.SetParent(parent, false);
            var venue = new BowlingClubLanes.Venue { Root = root };
            var fx = venue.Fx = root.gameObject.AddComponent<BowlingVenueFx>();

            // The alley: the shared kit in volcano dress (obsidian gutters with a lava seam, carved basalt
            // returns and seats, iron consoles and monitors) on smoked-amber maple (PLAN_BowlingLook.md).
            var rock = BowlingAlleyKit.Pbr("CaveRock", new Color(1.9f, 1.6f, 1.45f), .9f, Vector2.one, 1.2f);
            var iron = BowlingAlleyKit.Plain(new Color(.11f, .1f, .1f), .55f, .9f);
            var obsidian = BowlingAlleyKit.Plain(new Color(.025f, .02f, .025f), .95f, .2f);
            var gold = BowlingAlleyKit.Plain(BrandColors.Gold * .9f, .82f, 1);
            var black = BowlingAlleyKit.Plain(new Color(.006f, .004f, .004f), .1f);
            var lavaSeam = BowlingAlleyKit.Emissive(Lava, 2.4f);
            var masking = BowlingAlleyKit.Emissive(Color.white, 2.4f, BowlingAlleyKit.Tex("MaskingMagma_Emission"));
            var smoked = new Color(.80f, .66f, .58f);
            var slots = new Dictionary<string, Material>
            {
                ["LaneMaple"] = BowlingAlleyKit.Lane("LaneMaple", smoked, .97f),
                ["LanePine"] = BowlingAlleyKit.Lane("LanePine", smoked, .97f),
                ["Approach"] = BowlingAlleyKit.Lane("Basalt", new Color(1.2f, 1.1f, 1.05f), 1, 1.3f, .4f, new Vector2(.35f, .35f)),   // polished basalt approach (3 m tile = 0.35 per lane width)
                ["Ink"] = BowlingAlleyKit.Plain(new Color(.06f, .03f, .02f), .7f),
                ["Gutter"] = obsidian, ["Capping"] = obsidian, ["CappingTrim"] = lavaSeam, ["Kickback"] = rock, ["Pit"] = black,
                ["PinLight"] = BowlingAlleyKit.Emissive(new Color(1, .93f, .82f), 4),
                ["MaskingFrame"] = rock, ["MaskingPanel"] = masking,
                ["Numbers"] = BowlingAlleyKit.Emissive(new Color(1, .55f, .18f), 2.6f), ["Step"] = iron,
                ["ReturnBody"] = rock, ["ReturnTrim"] = iron, ["ReturnDark"] = black, ["ReturnAccent"] = lavaSeam,
                ["ConsoleBody"] = iron, ["ConsoleTrim"] = gold,
                ["Screen"] = BowlingAlleyKit.Emissive(Color.white, 1.1f, BowlingAlleyKit.Tex("ScoreScreenMagma_Emission")),
                ["MonitorFrame"] = iron, ["MonitorMount"] = iron,
                ["Upholstery"] = BowlingAlleyKit.Pbr("CaveRock", new Color(1.3f, 1.1f, 1.0f), .7f, new Vector2(1.5f, 1.5f), 1.4f),   // carved stone seats
                ["SofaBase"] = iron,
                ["TableTop"] = BowlingAlleyKit.Pbr("Basalt", Color.white, 1, new Vector2(.5f, .5f)), ["TableBase"] = iron,
            };
            var balls = new[]
            {
                BowlingAlleyKit.Plain(new Color(.55f, .06f, .02f), .93f), BowlingAlleyKit.Plain(new Color(.9f, .35f, .05f), .93f),
                BowlingAlleyKit.Plain(new Color(.03f, .025f, .03f), .96f), BowlingAlleyKit.Plain(BrandColors.Gold * .8f, .93f),
            };
            BowlingAlleyKit.Place(root, slots, balls);
            var theme = new BowlingClubLanes.LaneTheme { Kit = true, PinSpot = new Color(1f, .95f, .88f), PinSpotIntensity = 5.4f, PinFace = 1.6f };
            BowlingClubLanes.Lanes(root, theme);
            fx.AddPulse(lavaSeam, 1.3f, .18f);
            fx.AddFlash(masking);

            // The volcano dress: the cavern, lava trenches under iron grates, the arch and crest, pillars.
            var lava = BowlingAlleyKit.Emissive(LavaHot, 3.2f, BowlingAlleyKit.Tex("Lava_Emission"));
            BowlingAlleyKit.Place(root, new Dictionary<string, Material>
            {
                ["CaveRock"] = BowlingAlleyKit.Pbr("CaveRock", new Color(2.6f, 2.0f, 1.8f), .9f, Vector2.one, 1.4f), ["TrenchRock"] = BowlingAlleyKit.Pbr("CaveRock", new Color(.6f, .45f, .4f), .6f, Vector2.one), ["Iron"] = iron,
                ["Gold"] = gold, ["Lava"] = lava,
            }, null, "MagmaKit");
            fx.AddScroll(lava, new Vector2(.02f, -.06f));
            fx.AddScroll(lava, new Vector2(.02f, -.06f), "_EmissionMap");
            fx.AddPulse(lava, .7f, .12f);

            float end = BowlingLane.LaneEnd, deckFrom = BowlingLane.FoulToHeadPin - .6f;
            const float floorY = BowlingAlleyKit.SetteeFloor, back = -15.8f, crossZ = -9.45f, chW = .72f, wall = 14.6f;
            float sideL = BowlingAlleyKit.BankLeft - 1.1f, sideR = BowlingAlleyKit.BankRight + 1.1f;
            // polished basalt flagstones everywhere off the lanes, cut round the trenches (3 m tile)
            var basalt = BowlingAlleyKit.Pbr("Basalt", new Color(1.15f, 1.05f, 1.0f), 1, Vector2.one, 1.3f);
            void Slab(string name, float x0, float x1, float z0, float z1) =>
                BowlingAlleyKit.Floor(root, name, new Vector3((x0 + x1) / 2, floorY, (z0 + z1) / 2), new Vector2(x1 - x0, z1 - z0), basalt, 3);
            // behind the trench across the lounge, between it and the settee step, and the aisles either side
            Slab("FloorLounge", -wall, wall, back, crossZ - chW / 2);
            Slab("FloorSettee", sideL + chW / 2, sideR - chW / 2, crossZ + chW / 2, BowlingAlleyKit.ApproachBack);
            Slab("FloorAisleInL", sideL + chW / 2, BowlingAlleyKit.BankLeft, BowlingAlleyKit.ApproachBack, end + 1.2f);
            Slab("FloorAisleInR", BowlingAlleyKit.BankRight, sideR - chW / 2, BowlingAlleyKit.ApproachBack, end + 1.2f);
            Slab("FloorAisleOutL", -wall, sideL - chW / 2, crossZ - chW / 2, end + 3);
            Slab("FloorAisleOutR", sideR + chW / 2, wall, crossZ - chW / 2, end + 3);
            // a basalt footbridge over the trench where the players walk between their bench and the lane (BowlingGame.AisleX)
            BowlingClubLanes.Box(root, "TrenchBridge", new Vector3(BowlingGame.AisleX, floorY - .045f, crossZ), new Vector3(1.1f, .12f, chW + .5f), rock);   // top 1.5 cm proud of the flagstones it overlaps (never coplanar: no z-fight)
            // the approach's side walls down to the aisle floor (the bank stands one step up)
            foreach (float x in new[] { BowlingAlleyKit.BankLeft, BowlingAlleyKit.BankRight })
                BowlingClubLanes.Box(root, "BankSide", new Vector3(x, -.09f, (BowlingAlleyKit.ApproachBack + end) / 2), new Vector3(.03f, .18f, end - BowlingAlleyKit.ApproachBack), rock);

            // Lavafalls either side of the pins, pouring down the cavern wall into the trenches.
            foreach (float x in new[] { sideL, sideR })
            {
                var fall = BowlingAlleyKit.Emissive(Color.white, 2.2f, BowlingAlleyKit.Tex("Lavafall_Emission"));
                fall.SetTextureScale("_BaseMap", new Vector2(1, 2)); fall.SetTextureScale("_EmissionMap", new Vector2(1, 2));
                var q = BowlingClubLanes.Quad(root, "Lavafall", new Vector3(x + Mathf.Sign(x) * 1.4f, 4.4f, end + 2.2f), new Vector3(1.6f, 9f, 1), fall);
                q.transform.localRotation = Quaternion.Euler(0, Mathf.Sign(x) * 30, 0);
                fx.AddScroll(fall, new Vector2(0, .35f)); fx.AddScroll(fall, new Vector2(0, .35f), "_EmissionMap");
            }
            BowlingClubLanes.Box(root, "DeckWallBelow", new Vector3(-.8f, 1.3f, end + 1.6f), new Vector3(BowlingAlleyKit.BankRight - BowlingAlleyKit.BankLeft, 2.6f, .2f), black);

            // The sky through the crater: dusk over the rim, and the moon (the key's source).
            BowlingClubLanes.SkyDome(root, "Course/Resort/SkyVolcanic", -46, 42, .7f);
            var moon = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            if (moon.TryGetComponent<Collider>(out var mc)) Object.Destroy(mc);
            moon.name = "Moon"; moon.transform.SetParent(root, false);
            moon.transform.localPosition = new Vector3(-9, 26, 60); moon.transform.localScale = Vector3.one * 4.5f;
            moon.GetComponent<MeshRenderer>().sharedMaterial = BowlingClubLanes.Glow(new Color(.85f, .92f, 1f), 2.4f);

            // Behind the settees: carved stone terraces for the house, braziers either side of the players' bench.
            BowlingVenue.Settee(root, obsidian, lavaSeam, iron);
            BowlingClubLanes.Gallery(root, new Vector3(-6.5f, floorY, -11.6f), new Vector3(0, 0, -1), 21, 3, 0, rock, lavaSeam, venue, alongX: true);
            foreach (float x in new[] { -2.4f, 2.4f })
            {
                BowlingClubLanes.Box(root, "Brazier", new Vector3(x, .27f, BowlingClubLanes.LoungeZ + .2f), new Vector3(.4f, .9f, .4f), iron);
                var coal = LavaFlow(3, Vector2.one);
                BowlingClubLanes.Box(root, "BrazierCoals", new Vector3(x, .74f, BowlingClubLanes.LoungeZ + .2f), new Vector3(.34f, .06f, .34f), coal);
                fx.AddPulse(coal, 2.3f, .25f, x);
            }
            BowlingClubLanes.Light(root, "LoungeEmber", LightType.Point, new Vector3(0, 1.6f, BowlingClubLanes.LoungeZ + .4f), Vector3.zero, new Color(1f, .5f, .2f), 2.2f, 4.5f);
            BowlingAlleyKit.SetteeSeats(venue.Seats);
            float outer = wall - 2;

            // the lava's light on the cave walls and the fans' backs: point lights down the rivers, kept
            // well away from the pins and the bowler so they never take those objects' two light slots
            foreach (float x in new[] { sideL, sideR })
                foreach (float z in new[] { -6f, 8f })
                    BowlingClubLanes.Light(root, "LavaGlow", LightType.Point, new Vector3(x, .3f, z), Vector3.zero, new Color(1f, .38f, .08f), 4, 6.5f);
            BowlingClubLanes.Light(root, "LavaGlowBack", LightType.Point, new Vector3(0, .3f, crossZ), Vector3.zero, new Color(1f, .38f, .08f), 3.5f, 6.5f);
            Embers(root, new Vector3(0, .2f, 6), new Vector3(2 * outer + 3, 30, .2f), 26);
            foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true)) r.shadowCastingMode = ShadowCastingMode.Off;

            // Light: moonlight from the crater as the key, lava from below (the ambient ground colour),
            // a cold sky above; the pins keep their hot white spot.
            BowlingVenue.Ambient(new Color(.32f, .34f, .52f), new Color(.62f, .32f, .18f), new Color(.95f, .40f, .14f));
            BowlingVenue.Fog(new Color(.22f, .06f, .02f), 22, 150);
            BowlingClubLanes.Key(root, new Color(.70f, .80f, 1f), 1.7f, new Vector3(46, 14, 0), .7f);
            BowlingClubLanes.BowlerLights(root, new Color(1f, .86f, .74f), 5.5f, 8.5f);

            BowlingClubLanes.Probes(root, venue, 2 * wall, new Color(.06f, .02f, .01f), 1.2f);
            venue.Post = BowlingClubLanes.Post(root, camera, new BowlingClubLanes.PostLook
            {
                BloomThreshold = .9f, BloomIntensity = 1.25f, BloomScatter = .72f, BloomTint = new Color(1f, .8f, .65f),
                Exposure = .7f, Contrast = 20, Saturation = 6, Temperature = 7, Filter = new Color(1f, .9f, .78f),   // the whole cave runs warm off the lava
                Shadows = new Color(.40f, .52f, .58f), Highlights = new Color(.62f, .50f, .40f),
                Vignette = .34f, VignetteColor = new Color(.07f, .01f, 0),
            });
            venue.Crowd = Majestic.MajesticCrowd.Build(root, venue.Seats, lod: true);
            return venue;
        }
    }
}
