using UnityEngine;

namespace GolfArcade.Bowling
{
    /// The P0 greybox of Club Lanes: regulation lane, gutters, markings, pin deck, kickbacks,
    /// masking, pit and two neighbour lanes each side. Real venue art replaces this later
    /// (PLAN_Bowling.md §7); everything here sits exactly on the BowlingLane dimensions.
    public static class BowlingAlley
    {
        public const float LanePitch = 1.65f;        // centre to centre of neighbouring lanes

        public static readonly Color Maple = new Color(.86f, .69f, .48f), Pine = new Color(.90f, .76f, .56f), Teal = new Color(.28f, .52f, .50f),
            Cream = new Color(.93f, .89f, .80f), Ink = new Color(.12f, .10f, .09f), Gutter = new Color(.30f, .31f, .33f);

        public static Material Lit(Color color, float smooth = .2f, Texture tex = null, Vector2? tiling = null)
        {
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            m.SetColor("_BaseColor", color);
            if (tex) { m.SetTexture("_BaseMap", tex); if (tiling.HasValue) m.SetTextureScale("_BaseMap", tiling.Value); }
            m.SetFloat("_Smoothness", smooth); m.SetFloat("_Metallic", 0);
            return m;
        }

        /// 39 boards across: each board a slightly different tone, with a thin seam between.
        internal static Texture2D Boards()
        {
            const int perBoard = 16, h = 64;
            int w = BowlingLane.Boards * perBoard;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Repeat, name = "LaneBoards", anisoLevel = 4 };
            var px = new Color32[w * h];
            var rng = new System.Random(7);
            for (int b = 0; b < BowlingLane.Boards; b++)
            {
                float tone = .93f + (float)rng.NextDouble() * .1f;
                for (int x = 0; x < perBoard; x++)
                    for (int y = 0; y < h; y++)
                    {
                        float grain = .97f + .03f * Mathf.Sin((y * .4f + b * 3.1f) + Mathf.Sin(x * .9f + b) * 1.5f);
                        float v = x == 0 ? .78f : tone * grain;
                        byte c = (byte)Mathf.Clamp(v * 255, 0, 255);
                        px[y * w + b * perBoard + x] = new Color32(c, c, c, 255);
                    }
            }
            tex.SetPixels32(px); tex.Apply(true);
            return tex;
        }

        internal static GameObject Box(Transform parent, string name, Vector3 centre, Vector3 size, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            Object.Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localPosition = centre; go.transform.localScale = size;
            go.GetComponent<MeshRenderer>().sharedMaterial = mat;
            return go;
        }

        static GameObject Quad(Transform parent, string name, Mesh mesh, Vector3 pos, float yaw, Vector3 scale, Material mat)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos; go.transform.localRotation = Quaternion.Euler(0, yaw, 0); go.transform.localScale = scale;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            go.AddComponent<MeshRenderer>().sharedMaterial = mat;
            return go;
        }

        static Mesh Arrow()
        {
            var m = new Mesh { name = "LaneArrow" };
            m.vertices = new[] { new Vector3(-.5f, 0, 0), new Vector3(0, 0, 1), new Vector3(.5f, 0, 0) };
            m.triangles = new[] { 0, 1, 2 };
            m.normals = new[] { Vector3.up, Vector3.up, Vector3.up };
            return m;
        }

        static Mesh Disc(int n = 16)
        {
            var v = new Vector3[n + 1]; var t = new int[n * 3]; var nr = new Vector3[n + 1];
            nr[0] = Vector3.up;
            for (int i = 0; i < n; i++)
            {
                float a = -i * 2 * Mathf.PI / n;
                v[i + 1] = new Vector3(Mathf.Cos(a) * .5f, 0, Mathf.Sin(a) * .5f); nr[i + 1] = Vector3.up;
                t[i * 3] = 0; t[i * 3 + 1] = i + 1; t[i * 3 + 2] = (i + 1) % n + 1;
            }
            return new Mesh { name = "Disc", vertices = v, triangles = t, normals = nr };
        }

        /// One lane (bed, gutters, markings, deck, kickbacks, masking) with its foul line at local z = 0.
        static void Lane(Transform root, float x, bool main, Texture2D boards, Material approach)
        {
            var lane = new GameObject(main ? "Lane" : "NeighbourLane").transform;
            lane.SetParent(root, false); lane.localPosition = new Vector3(x, 0, 0);
            float w = BowlingLane.HalfWidth, g = BowlingLane.GutterWidth, end = BowlingLane.LaneEnd;
            var bed = Lit(Pine, .82f, boards, new Vector2(1, 30));
            var deckMat = Lit(Maple, .78f, boards, new Vector2(1, 1.5f));
            var ink = Lit(Ink, .3f);
            Box(lane, "Bed", new Vector3(0, -.03f, (BowlingLane.FoulToHeadPin - .6f) / 2), new Vector3(2 * w, .06f, BowlingLane.FoulToHeadPin - .6f), bed);
            Box(lane, "PinDeck", new Vector3(0, -.03f, (BowlingLane.FoulToHeadPin - .6f + end) / 2), new Vector3(2 * w, .06f, end - (BowlingLane.FoulToHeadPin - .6f)), deckMat);
            var gutter = Lit(Gutter, .55f);
            var capping = Lit(Cream, .35f);
            foreach (float s in new[] { -1f, 1f })
            {
                Box(lane, "Gutter", new Vector3(s * (w + g / 2), -BowlingLane.GutterDepth - .02f, end / 2), new Vector3(g, .04f, end), gutter);
                Box(lane, "Capping", new Vector3(s * (w + g + .06f), .015f, (BowlingLane.FoulToHeadPin - .6f) / 2), new Vector3(.12f, .09f, BowlingLane.FoulToHeadPin - .6f), capping);
                Box(lane, "Kickback", new Vector3(s * (BowlingLane.KickbackX + .05f), .45f, (BowlingLane.FoulToHeadPin - .6f + end + 1.2f) / 2), new Vector3(.1f, .95f, end + 1.2f - (BowlingLane.FoulToHeadPin - .6f)), Lit(Teal, .25f));
            }
            Box(lane, "Pit", new Vector3(0, -.32f, end + .55f), new Vector3(2 * (BowlingLane.KickbackX + .1f), .05f, 1.1f), Lit(Ink, .05f));
            Box(lane, "Cushion", new Vector3(0, .4f, end + 1.15f), new Vector3(2 * (BowlingLane.KickbackX + .1f), 1.5f, .1f), Lit(new Color(.08f, .08f, .09f), .05f));
            Box(lane, "Masking", new Vector3(0, 1.6f, BowlingLane.FoulToHeadPin - .75f), new Vector3(2 * (BowlingLane.KickbackX + .15f), 1.3f, .2f), Lit(Teal, .3f));
            Box(lane, "MaskingTrim", new Vector3(0, .93f, BowlingLane.FoulToHeadPin - .74f), new Vector3(2 * (BowlingLane.KickbackX + .15f), .06f, .22f), Lit(new Color(.78f, .62f, .34f), .6f));
            Box(lane, "Approach", new Vector3(0, -.03f, -BowlingLane.ApproachLength / 2 - .4f), new Vector3(2 * (w + g + .12f), .06f, BowlingLane.ApproachLength + .8f), approach);
            Box(lane, "FoulLine", new Vector3(0, .001f, .005f), new Vector3(2 * (w + g), .002f, .012f), ink);

            if (main) Markings(lane);
        }

        /// The lane's inlaid markings: target arrows, lane dots, approach dots, range finders.
        internal static void Markings(Transform lane)
        {
            var ink = Lit(Ink, .3f);
            var arrow = Arrow(); var disc = Disc();
            foreach (int b in BowlingLane.ArrowBoards)
            {
                float z = Mathf.Lerp(BowlingLane.ArrowsFar, BowlingLane.ArrowsNear, Mathf.Abs(b - 20) / 15f);
                Quad(lane, "Arrow" + b, arrow, new Vector3(BowlingLane.BoardX(b), .002f, z), 0, new Vector3(BowlingLane.BoardWidth * .9f, 1, .2f), ink);
            }
            foreach (int b in new[] { 3, 5, 8, 11, 14, 26, 29, 32, 35, 37 })
                Quad(lane, "Dot" + b, disc, new Vector3(BowlingLane.BoardX(b), .002f, BowlingLane.LaneDots), 0, Vector3.one * .02f, ink);
            foreach (float z in BowlingLane.ApproachDots)
                foreach (int b in new[] { 3, 5, 8, 11, 14, 20, 26, 29, 32, 35, 37 })
                    Quad(lane, "ApproachDot", disc, new Vector3(BowlingLane.BoardX(b), .002f, -z), 0, Vector3.one * .025f, ink);
            foreach (float s in new[] { -1f, 1f })
                Quad(lane, "RangeFinder", arrow, new Vector3(BowlingLane.BoardX(s < 0 ? 30 : 10), .002f, BowlingLane.RangeFinders), 0, new Vector3(BowlingLane.BoardWidth * .6f, 1, .6f), ink);
        }

        public static Transform Build(Transform parent)
        {
            var root = new GameObject("ClubLanes_Greybox").transform;
            root.SetParent(parent, false);
            var boards = Boards();
            var approach = Lit(Maple, .5f, boards, new Vector2(1.18f, 3));
            for (int i = -2; i <= 2; i++) Lane(root, i * LanePitch, i == 0, boards, approach);

            // The room: floor behind the approach, side walls, the back wall above the masking, a ceiling with light strips.
            float span = 5 * LanePitch + 1;
            Box(root, "Floor", new Vector3(0, -.08f, -9), new Vector3(span + 4, .1f, 8), Lit(new Color(.42f, .30f, .30f), .15f));
            Box(root, "WallBack", new Vector3(0, 3.4f, BowlingLane.FoulToHeadPin - .7f), new Vector3(span, 2.6f, .2f), Lit(Cream, .1f));
            Box(root, "Ceiling", new Vector3(0, 4.6f, 6), new Vector3(span + 4, .1f, 34), Lit(new Color(.85f, .82f, .76f), .05f));
            foreach (float s in new[] { -1f, 1f })
                Box(root, "WallSide", new Vector3(s * (span / 2 + .1f), 2.3f, 6), new Vector3(.2f, 4.8f, 34), Lit(new Color(.80f, .74f, .64f), .1f));
            var glow = Lit(Color.white, 0);
            glow.SetColor("_EmissionColor", new Color(1, .95f, .85f) * 2.5f); glow.EnableKeyword("_EMISSION");
            for (int i = 0; i < 6; i++) Box(root, "LightStrip", new Vector3(0, 4.53f, -3 + i * 4), new Vector3(span - 1, .04f, .25f), glow);
            return root;
        }

        public static Material[] PinMaterials() => new[] { Lit(new Color(.96f, .96f, .95f), .86f), Lit(new Color(.80f, .08f, .10f), .86f) };

        public static GameObject Pin(Transform parent, Mesh mesh, Material[] mats)
        {
            var go = new GameObject("Pin");
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            go.AddComponent<MeshRenderer>().sharedMaterials = mats;
            return go;
        }

        /// The club ball (greybox): deep teal with a cream band and three dark holes, so its spin reads on the TV.
        public static GameObject Ball(Transform parent)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            go.name = "ClubBall";
            Object.Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localScale = Vector3.one * BowlingLane.BallRadius * 2;
            go.GetComponent<MeshRenderer>().sharedMaterial = Lit(new Color(.10f, .38f, .40f), .92f);
            var band = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            Object.Destroy(band.GetComponent<Collider>());
            band.transform.SetParent(go.transform, false);
            band.transform.localScale = new Vector3(1.004f, .045f, 1.004f);
            band.transform.localRotation = Quaternion.Euler(0, 0, 90);
            band.GetComponent<MeshRenderer>().sharedMaterial = Lit(Cream, .9f);
            var hole = Lit(new Color(.03f, .03f, .03f), .2f);
            foreach (var dir in new[] { new Vector3(0, .62f, -.78f), new Vector3(-.13f, .95f, .28f), new Vector3(.13f, .95f, .28f) })
            {
                var h = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                Object.Destroy(h.GetComponent<Collider>());
                h.transform.SetParent(go.transform, false);
                var d = dir.normalized;
                h.transform.localPosition = d * .47f;
                h.transform.localRotation = Quaternion.FromToRotation(Vector3.up, d);
                h.transform.localScale = new Vector3(.16f, .08f, .16f);
                h.GetComponent<MeshRenderer>().sharedMaterial = hole;
            }
            return go;
        }
    }
}
