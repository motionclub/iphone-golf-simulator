using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// Tiki Shores (PLAN_BowlingVenues.md §3.3): open-air lanes on a beach, late afternoon. The only
    /// daylight venue, so it reads apart from the three night ones at a glance:
    ///   * a thatched pavilion over the approach and the lounge, a slatted pergola over the lanes whose
    ///     shadows stripe the wood in the low sun, open sides onto sand, palms and the sea;
    ///   * teak cappings and kickbacks with warm rope lights, painted-sunset masking boards;
    ///   * driftwood bleachers, tiki torches, strings of paper lanterns;
    ///   * the sun as the key (low, warm, from the sea side), a sky/sand trilight, a warm grade.
    public static class BowlingTikiShores
    {
        static readonly Color Teak = new Color(.46f, .28f, .15f), Bamboo = new Color(.80f, .66f, .40f), Sand = new Color(.90f, .79f, .60f);
        static readonly Color Ember = new Color(1f, .58f, .22f);
        const int LanesEachSide = 2;

        /// The masking boards: a painted sunset over the sea with palm silhouettes.
        static Texture2D SunsetPainting()
        {
            const int w = 512, h = 256;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Clamp, name = "TikiSunset" };
            var px = new Color[w * h];
            const float horizon = .34f;
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float u = x / (float)w, v = y / (float)h;
                    Color c;
                    float dx = (u - .5f) * 2, dy = v - horizon;
                    if (v > horizon)
                    {
                        float k = (v - horizon) / (1 - horizon);
                        c = Color.Lerp(new Color(1f, .62f, .30f), new Color(.98f, .38f, .42f), Mathf.Clamp01(k * 1.6f));
                        c = Color.Lerp(c, new Color(.36f, .22f, .52f), Mathf.Clamp01((k - .5f) * 2));
                        float r = Mathf.Sqrt(dx * dx * 4 + dy * dy * 16);
                        if (r < .55f) c = Color.Lerp(new Color(1f, .93f, .62f), c, Mathf.SmoothStep(.4f, .55f, r));
                        // painted cloud streaks
                        float cl = BowlingVenue.Noise(u * 5, v * 30, 2);
                        if (cl > .62f && k > .15f) c = Color.Lerp(c, new Color(1f, .55f, .55f), (cl - .62f) * 2);
                    }
                    else
                    {
                        float k = (horizon - v) / horizon;
                        c = Color.Lerp(new Color(.42f, .30f, .45f), new Color(.10f, .22f, .36f), k);
                        // the sun's glitter path on the water
                        float glint = Mathf.Abs(dx) < .12f * (1 - k * .4f) + .02f ? BowlingVenue.Noise(u * 80, v * 200, 4) : 0;
                        if (glint > .55f) c = Color.Lerp(c, new Color(1f, .85f, .55f), (glint - .55f) * 2.5f);
                    }
                    // palm silhouettes at both edges: a leaning trunk and a crown of fronds
                    foreach (float side in new[] { -1f, 1f })
                    {
                        float baseU = side < 0 ? .08f : .92f;
                        float tu = baseU + side * -.1f * v;                      // leans in toward the middle
                        if (v < .78f && Mathf.Abs(u - tu) < .012f * (1.4f - v)) c = new Color(.10f, .05f, .08f);
                        float cx = baseU + side * -.078f, cy = .8f;
                        for (int f = 0; f < 7; f++)
                        {
                            float a = f / 7f * Mathf.PI * 2 + .3f;
                            float fx = cx + Mathf.Cos(a) * .09f, fy = cy + Mathf.Sin(a) * .12f - .04f * Mathf.Abs(Mathf.Cos(a));
                            float t = Mathf.Clamp01(((u - cx) * (fx - cx) + (v - cy) * (fy - cy)) / ((fx - cx) * (fx - cx) + (fy - cy) * (fy - cy)));
                            float px2 = cx + (fx - cx) * t - u, py2 = cy + (fy - cy) * t - v;
                            if (px2 * px2 + py2 * py2 < Mathf.Pow(.012f * (1 - t * .7f), 2)) c = new Color(.10f, .05f, .08f);
                        }
                    }
                    px[y * w + x] = c;
                }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        /// Sand with soft ripples and a little grain.
        static Texture2D SandTexture()
        {
            const int n = 256;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Repeat, name = "TikiSand" };
            var px = new Color[n * n];
            var rng = new System.Random(5);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float rip = .5f + .5f * Mathf.Sin((x / (float)n * 6 + BowlingVenue.Noise(x / 40f, y / 40f, 1) * 2.5f) * Mathf.PI * 2);
                    float k = .9f + .07f * rip + .06f * ((float)rng.NextDouble() - .5f);
                    px[y * n + x] = new Color(k, k * .97f, k * .93f);
                }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        /// Thatch: dense straw streaks.
        static Texture2D ThatchTexture()
        {
            const int n = 128;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Repeat, name = "TikiThatch" };
            var px = new Color[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float s = BowlingVenue.Noise(x / 2.5f, y / 22f, 8) * .6f + BowlingVenue.Noise(x / 9f, y / 40f, 9) * .4f;
                    float k = Mathf.Lerp(.55f, 1.1f, s) * (Mathf.Repeat(y / 16f, 1) < .1f ? .7f : 1);   // tied courses
                    px[y * n + x] = new Color(k, k * .86f, k * .62f);
                }
            tex.SetPixels(px); tex.Apply(true);
            return tex;
        }

        public static BowlingClubLanes.Venue Build(Transform parent, Camera camera)
        {
            var root = new GameObject("TikiShores").transform;
            root.SetParent(parent, false);
            var venue = new BowlingClubLanes.Venue { Root = root };
            var fx = venue.Fx = root.gameObject.AddComponent<BowlingVenueFx>();

            // The alley: the shared kit in island dress (carved teak returns with rope trim, rattan seats, a painted
            // sunset across the masking) on honey maple, under a thatched pavilion (PLAN_BowlingLook.md).
            var boards = BowlingAlley.Boards();
            var teak = BowlingAlleyKit.Pbr("Teak", Color.white, .8f, new Vector2(.5f, .5f));
            var teakDark = BowlingAlleyKit.Plain(Teak * .5f, .6f);
            var bamboo = BowlingClubLanes.Surface(Bamboo, .55f);
            var rope = BowlingAlleyKit.Plain(new Color(.70f, .58f, .40f), .2f);
            var ember = BowlingAlleyKit.Emissive(Ember, 2.2f);
            var painting = BowlingAlleyKit.Emissive(Color.white, 1.15f, BowlingAlleyKit.Tex("MaskingTiki_Emission"));
            var rattan = BowlingAlleyKit.Pbr("Rattan", Color.white, .8f, new Vector2(3, 3));
            var honey = new Color(1f, .93f, .82f);
            var slots = new Dictionary<string, Material>
            {
                ["LaneMaple"] = BowlingAlleyKit.Lane("LaneMaple", honey, .96f),
                ["LanePine"] = BowlingAlleyKit.Lane("LanePine", honey, .96f),
                ["Approach"] = BowlingAlleyKit.Lane("Approach", honey, .8f, .5f, .25f),
                ["Ink"] = BowlingAlleyKit.Plain(new Color(.25f, .14f, .08f), .6f),
                ["Gutter"] = BowlingAlleyKit.Plain(new Color(.16f, .1f, .06f), .85f, .2f), ["Capping"] = teak, ["CappingTrim"] = rope,
                ["Kickback"] = teak, ["Pit"] = BowlingAlleyKit.Plain(new Color(.025f, .016f, .01f), .1f),
                ["PinLight"] = BowlingAlleyKit.Emissive(new Color(1f, .91f, .78f), 4),
                ["MaskingFrame"] = teakDark, ["MaskingPanel"] = painting, ["Numbers"] = BowlingAlleyKit.Emissive(new Color(1f, .9f, .7f), 2),
                ["Step"] = teakDark, ["Divider"] = BowlingAlleyKit.Lane("Approach", new Color(.6f, .45f, .32f), .8f, .5f, .25f),
                ["ReturnBody"] = teak, ["ReturnTrim"] = rope, ["ReturnDark"] = teakDark, ["ReturnAccent"] = ember,
                ["ConsoleBody"] = teak, ["ConsoleTrim"] = bamboo,
                ["Screen"] = BowlingAlleyKit.Emissive(Color.white, 1.1f, BowlingAlleyKit.Tex("ScoreScreenTiki_Emission")),
                ["MonitorFrame"] = bamboo, ["MonitorMount"] = bamboo,
                ["Upholstery"] = rattan, ["SofaBase"] = teakDark,
                ["TableTop"] = teak, ["TableBase"] = bamboo,
            };
            var balls = new[]
            {
                BowlingAlleyKit.Plain(new Color(.1f, .6f, .65f), .93f), BowlingAlleyKit.Plain(new Color(.95f, .35f, .5f), .93f),
                BowlingAlleyKit.Plain(new Color(1f, .7f, .2f), .93f), BowlingAlleyKit.Plain(new Color(.3f, .75f, .3f), .93f),
            };
            BowlingAlleyKit.Place(root, slots, balls);
            BowlingClubLanes.Lanes(root, new BowlingClubLanes.LaneTheme { Kit = true, PinSpot = new Color(1f, .91f, .78f), PinSpotIntensity = 4.6f, PinFace = 1.4f });
            fx.AddFlash(painting);

            float end = BowlingLane.LaneEnd, deckFrom = BowlingLane.FoulToHeadPin - .6f;
            const float outer = 13.2f, back = -15.8f;

            // The beach, and a teak deck under the whole centre (the lounge and aisles one step below the approach).
            BowlingClubLanes.Box(root, "Sand", new Vector3(0, -.3f, 5), new Vector3(60, .1f, 70), BowlingClubLanes.Surface(Sand, .18f, SandTexture(), new Vector2(22, 22)));
            BowlingAlleyKit.Floor(root, "Deck", new Vector3(0, BowlingAlleyKit.SetteeFloor, (back + end + 2) / 2), new Vector2(2 * outer + .6f, end + 2 - back), teak, 1);
            BowlingClubLanes.Box(root, "DeckEdge", new Vector3(0, -.24f, (back + end + 2) / 2), new Vector3(2 * outer + .7f, .12f, end + 2.1f - back), teakDark);
            BowlingClubLanes.Box(root, "DeckWallBelow", new Vector3(-.8f, .6f, end + 1.6f), new Vector3(BowlingAlleyKit.BankRight - BowlingAlleyKit.BankLeft + 2, 1.4f, .2f), teakDark);

            // The pavilion: posts down both sides, a thatched roof over the approach and the lounge,
            // a slatted pergola over the lanes (open to the sky; its shadows stripe the lanes).
            var posts = new List<CombineInstance>(); var cyl = BowlingVenue.Primitive(PrimitiveType.Cylinder); var cube = BowlingVenue.Primitive(PrimitiveType.Cube);
            var ropes = new List<CombineInstance>();
            for (float z = -15; z <= 19.5f; z += 3.45f)
                foreach (float s in new[] { -1f, 1f })
                {
                    var at = new Vector3(s * (outer + .25f), 2.2f, z);
                    posts.Add(BowlingVenue.Part(cyl, at, Quaternion.identity, new Vector3(.3f, 2.2f, .3f)));
                    for (int k = 0; k < 3; k++) ropes.Add(BowlingVenue.Part(cyl, at + Vector3.up * (-.9f + k * .22f), Quaternion.identity, new Vector3(.34f, .05f, .34f)));
                }
            foreach (float s in new[] { -1f, 1f })
                posts.Add(BowlingVenue.Part(cube, new Vector3(s * (outer + .25f), 4.45f, 2.5f), Quaternion.identity, new Vector3(.26f, .26f, 35.5f)));
            for (float z = 0.4f; z <= 17.5f; z += 1.15f)
                posts.Add(BowlingVenue.Part(cube, new Vector3(0, 4.62f, z), Quaternion.identity, new Vector3(2 * outer + .9f, .1f, .3f)));
            // bamboo rafters under the thatch, every 1.2 m
            for (float z = -15.4f; z <= 0.2f; z += 1.2f)
                foreach (float s in new[] { -1f, 1f })
                {
                    float half = outer + 1.4f, rise = 1.5f, ang = Mathf.Atan2(rise, half) * Mathf.Rad2Deg;
                    posts.Add(BowlingVenue.Part(cyl, new Vector3(s * half / 2, 4.42f + rise / 2, z), Quaternion.Euler(0, 0, 90 - s * ang), new Vector3(.12f, Mathf.Sqrt(half * half + rise * rise) / 2, .12f)));
                }
            BowlingVenue.Combine(root, "PavilionTimber", posts, teakDark);
            BowlingVenue.Combine(root, "PostRopes", ropes, rope, false);

            var thatch = BowlingClubLanes.Surface(Color.white * .9f, .05f, ThatchTexture(), new Vector2(3, 6));
            foreach (float s in new[] { -1f, 1f })
            {
                float half = outer + 1.4f, rise = 1.5f;
                float ang = Mathf.Atan2(rise, half) * Mathf.Rad2Deg;
                BowlingVenue.Slab(root, "Thatch", new Vector3(s * half / 2, 4.6f + rise / 2, -7.6f), new Vector3(Mathf.Sqrt(half * half + rise * rise), .28f, 16.2f), new Vector3(0, 0, -s * ang), thatch);
            }
            BowlingClubLanes.Box(root, "RidgeBeam", new Vector3(0, 6.15f, -7.6f), new Vector3(.32f, .32f, 16.4f), teakDark);

            // the carved name board over the masking, in a teak frame
            BowlingClubLanes.Box(root, "SignFrame", new Vector3(0, 2.95f, deckFrom - .28f), new Vector3(5.1f, 1.35f, .08f), teakDark);
            BowlingAlleyKit.Sign(root, "TikiSign", "SignTiki_Emission", new Vector3(0, 2.95f, deckFrom - .33f), new Vector2(4.8f, 1.2f), 1.1f);

            // Palms on the beach, in two groves (two draws each side).
            var trunks = new List<CombineInstance>(); var fronds = new List<CombineInstance>();
            var rng = new System.Random(41);
            foreach (float s in new[] { -1f, 1f })
                for (int i = 0; i < 9; i++)
                {
                    float z = -14 + i * 4.6f + (float)rng.NextDouble() * 2.4f;
                    float x = s * (outer + 2.4f + (float)rng.NextDouble() * 6 + (i % 2) * 3);
                    BowlingVenue.Palm(trunks, fronds, new Vector3(x, -.1f, z), 6.5f + (float)rng.NextDouble() * 3.5f, .35f + (float)rng.NextDouble() * .3f, s > 0 ? -90 + (float)rng.NextDouble() * 60 - 30 : 90 + (float)rng.NextDouble() * 60 - 30, 100 + i + (s > 0 ? 50 : 0));
                }
            // and two framing the view past the pins
            BowlingVenue.Palm(trunks, fronds, new Vector3(-outer - 1.2f, -.1f, end + 6), 9.5f, .45f, 70, 7);
            BowlingVenue.Palm(trunks, fronds, new Vector3(outer + 1.6f, -.1f, end + 8), 10.5f, .5f, -60, 8);
            BowlingVenue.Combine(root, "PalmTrunks", trunks, BowlingClubLanes.Surface(new Color(.48f, .38f, .28f), .2f));
            BowlingVenue.Combine(root, "PalmFronds", fronds, BowlingClubLanes.Surface(new Color(.22f, .40f, .14f), .35f));

            // Driftwood bleachers behind the settees, the players' bench, a tiki bar at the back.
            var drift = BowlingClubLanes.Surface(new Color(.74f, .66f, .56f), .3f, boards, new Vector2(.5f, 4));
            BowlingClubLanes.Gallery(root, new Vector3(-6.5f, BowlingAlleyKit.SetteeFloor, -11.6f), new Vector3(0, 0, -1), 21, 3, 0, drift, rope, venue, alongX: true);
            BowlingVenue.Settee(root, BowlingClubLanes.Surface(new Color(.10f, .52f, .56f), .45f), bamboo, teakDark);   // a teal cushioned bench
            foreach (float s in new[] { -1f, 1f })
            {
                BowlingClubLanes.Box(root, "Bar", new Vector3(s * 10.2f, .37f, -12.4f), new Vector3(3.4f, 1.1f, .8f), teak);
                BowlingClubLanes.Box(root, "BarTop", new Vector3(s * 10.2f, .94f, -12.3f), new Vector3(3.6f, .06f, 1), bamboo);
            }
            BowlingAlleyKit.SetteeSeats(venue.Seats);

            // Tiki torches along the pergola posts, and paper lanterns strung under the eaves.
            var poles = new List<CombineInstance>(); var flames = new List<CombineInstance>();
            var sphere = BowlingVenue.Primitive(PrimitiveType.Sphere);
            foreach (float s in new[] { -1f, 1f })
                for (float z = 8.5f; z <= 18; z += 3.2f)
                {
                    var at = new Vector3(s < 0 ? BowlingAlleyKit.BankLeft - .5f : BowlingAlleyKit.BankRight + .5f, BowlingAlleyKit.SetteeFloor, z);
                    poles.Add(BowlingVenue.Part(cyl, at + Vector3.up * .8f, Quaternion.identity, new Vector3(.07f, .8f, .07f)));
                    poles.Add(BowlingVenue.Part(cyl, at + Vector3.up * 1.62f, Quaternion.identity, new Vector3(.16f, .1f, .16f)));
                    flames.Add(BowlingVenue.Part(sphere, at + Vector3.up * 1.86f, Quaternion.identity, new Vector3(.13f, .26f, .13f)));
                }
            BowlingVenue.Combine(root, "TorchPoles", poles, bamboo);
            var flame = BowlingClubLanes.Glow(new Color(1f, .5f, .14f), 7);
            BowlingVenue.Combine(root, "TorchFlames", flames, flame, false);
            fx.AddFlicker(null, flame);
            Color[] paper = { new Color(1f, .55f, .2f), new Color(1f, .4f, .55f), new Color(.3f, .85f, .8f) };
            for (int c = 0; c < paper.Length; c++)
            {
                var lanterns = new List<CombineInstance>();
                foreach (float s in new[] { -1f, 1f })
                    for (int k = c; k < 30; k += paper.Length)
                    {
                        float z = -14.5f + k * 1.15f, sag = .25f * Mathf.Sin(Mathf.Repeat(k * 1.15f / 3.45f, 1) * Mathf.PI);
                        lanterns.Add(BowlingVenue.Part(sphere, new Vector3(s * (outer - .1f), 4.0f - sag, z), Quaternion.identity, new Vector3(.26f, .32f, .26f)));
                    }
                var lm = BowlingClubLanes.Glow(paper[c], 2.2f);
                BowlingVenue.Combine(root, "Lanterns", lanterns, lm, false);
                fx.AddPulse(lm, .7f, .08f, c * 2);
            }
            // warm lantern light over the lounge
            foreach (float x in new[] { -1.4f, 1.4f })
                BowlingClubLanes.Light(root, "LoungeLantern", LightType.Point, new Vector3(x, 2.8f, BowlingClubLanes.LoungeZ), Vector3.zero, new Color(1f, .72f, .45f), 1.6f, 4);

            // the panorama's horizon (53 % up the image) lands at about eye height; its sea fills in past the sand
            BowlingClubLanes.SkyDome(root, "Environment/LuminousCoast/ArchipelagoSky", -45, 43, 1.0f);

            // Light: the sun is the key, from the sea side and a little behind, high enough that the
            // pergola stripes the lanes rather than the roof shading them; the sky fills from above,
            // the sand bounces warm from below.
            BowlingVenue.Ambient(new Color(.52f, .66f, .90f), new Color(.82f, .68f, .54f), new Color(.60f, .48f, .34f));
            BowlingVenue.Fog(new Color(.80f, .84f, .90f), 45, 260);
            BowlingClubLanes.Key(root, new Color(1f, .82f, .62f), 2.0f, new Vector3(34, -58, 0), .78f);
            BowlingClubLanes.BowlerLights(root, new Color(1f, .9f, .78f), 4.5f, 4.5f);

            BowlingClubLanes.Probes(root, venue, 2 * outer, new Color(.55f, .68f, .86f), 1.0f);
            venue.Post = BowlingClubLanes.Post(root, camera, new BowlingClubLanes.PostLook
            {
                BloomThreshold = 1.15f, BloomIntensity = .55f, BloomScatter = .6f, BloomTint = new Color(1f, .9f, .8f),
                Exposure = .1f, Contrast = 12, Saturation = 14, Temperature = 12,
                Vignette = .18f, VignetteColor = new Color(.2f, .1f, .05f),
            });
            venue.Crowd = Majestic.MajesticCrowd.Build(root, venue.Seats, lod: true);
            return venue;
        }
    }
}
