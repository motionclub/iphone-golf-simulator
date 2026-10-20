using System.Collections.Generic;
using GolfArcade.Course;
using UnityEngine;

namespace GolfArcade.Game
{
    /// The things moving about a hole, drawn: a striped hot-air balloon with its basket, ropes and
    /// burner; a golf cart with its canopy, its driver and a bag on the back, wheels turning as it
    /// goes; gulls with beating wings. Toy-like and bright, in the game's soft plastic. Each is
    /// posed every frame from its path at the movers' clock (CourseMovers.Now), so what the player
    /// sees is where the ball will meet it. A hit wobbles the balloon, sends a gull tumbling and
    /// makes the cart honk (React). Lives under the hole, and goes with it.
    public sealed class MoverView : MonoBehaviour
    {
        CourseMovers movers;
        readonly List<Transform> bodies = new();
        readonly List<(Transform left, Transform right)> wings = new();
        readonly List<Transform[]> wheels = new();
        readonly List<Transform> flames = new();
        readonly Dictionary<int, float> hitAt = new();
        readonly List<Object> dreamResources=new();
        void OnDestroy(){foreach(var resource in dreamResources)if(resource)Destroy(resource);}
        double lastClock;
        bool paused;

        public static MoverView Build(Transform parent, CourseMovers movers)
        {
            var go = new GameObject("Movers");
            go.transform.SetParent(parent, false);
            var view = go.AddComponent<MoverView>();
            view.movers = movers;
            for (int i = 0; i < movers.All.Length; i++)
            {
                var m = movers.All[i];
                var root = new GameObject($"{m.Kind} {i}").transform;
                root.SetParent(go.transform, false);
                view.bodies.Add(root);
                view.wings.Add((null, null));
                view.wheels.Add(null);
                view.flames.Add(null);
                switch (m.Kind)
                {
                    case MoverKind.RockGate: case MoverKind.WindLift:
                        var body=m.Body(0,0);
                        var stone=HoleView.Primitive(PrimitiveType.Sphere,m.Kind==MoverKind.RockGate?"Solid floating rock":"Visible wind lift",m.Kind==MoverKind.RockGate?new Color(.38f,.46f,.49f):new Color(.35f,.85f,.9f),root);
                        stone.transform.localScale=Vector3.one*(float)(body.r*2);
                        if(m.Kind==MoverKind.RockGate){
                            var mesh=Instantiate(stone.GetComponent<MeshFilter>().sharedMesh);var vertices=mesh.vertices;
                            for(int k=0;k<vertices.Length;k++){var v=vertices[k];vertices[k]*=.96f+.04f*Mathf.Sin(v.x*13+v.y*17+v.z*9);}
                            view.dreamResources.Add(mesh);mesh.vertices=vertices;mesh.RecalculateNormals();stone.GetComponent<MeshFilter>().sharedMesh=mesh;
                            var mat=new Material(Shader.Find("Universal Render Pipeline/Lit"));mat.SetColor("_BaseColor",new Color(.63f,.68f,.67f));
                            view.dreamResources.Add(mat);mat.SetTexture("_BaseMap",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_C"));mat.SetTexture("_BumpMap",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_N"));mat.EnableKeyword("_NORMALMAP");mat.SetFloat("_Smoothness",.15f);stone.GetComponent<Renderer>().sharedMaterial=mat;
                        }
                        if(m.Kind==MoverKind.WindLift){
                            Destroy(stone);
                            var material=new Material(Shader.Find("Universal Render Pipeline/Unlit"));material.SetColor("_BaseColor",new Color(.4f,.9f,.85f));view.dreamResources.Add(material);
                            var arrow=new GameObject("Current direction").AddComponent<LineRenderer>();arrow.transform.SetParent(root,false);arrow.useWorldSpace=false;arrow.sharedMaterial=material;arrow.widthMultiplier=.15f;arrow.positionCount=5;
                            var direction=new Vector3((float)m.LiftDirection.X,0,(float)m.LiftDirection.D).normalized;var right=Vector3.Cross(Vector3.up,direction);float size=(float)body.r*.8f;
                            arrow.SetPositions(new[]{-direction*size,direction*size,direction*size*.55f+right*size*.4f,direction*size,direction*size*.55f-right*size*.4f});
                            for(int ring=0;ring<3;ring++){
                                var spiral=new GameObject("Lift current").AddComponent<LineRenderer>();spiral.transform.SetParent(root,false);spiral.useWorldSpace=false;spiral.sharedMaterial=material;spiral.widthMultiplier=.07f;spiral.positionCount=48;
                                for(int k=0;k<48;k++){float f=k/47f, y=Mathf.Lerp(-.85f,.85f,f),r=(float)body.r*Mathf.Sqrt(1-y*y)*.9f,a=f*Mathf.PI*4+ring*Mathf.PI*2/3;spiral.SetPosition(k,new Vector3(Mathf.Cos(a)*r,y*(float)body.r,Mathf.Sin(a)*r));}
                            }
                        }
                        break;
                    case MoverKind.Launchpad: view.BuildPad(root, i, m); break;
                    case MoverKind.Target: view.BuildTarget(go.transform, root, i, m); break;
                    case MoverKind.Balloon: view.BuildBalloon(root, i, m.Variant); break;
                    case MoverKind.Cart: view.BuildCart(root, i); break;
                    case MoverKind.Twister: view.BuildTwister(root, i); break;
                    default: view.BuildGull(root, i); break;
                }
                // (the minimap draws only the course; nothing on it is solid)
                foreach (var t in root.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = BallLook.OverlayLayer;
            }
            view.Pose();
            return view;
        }

        /// Freeze them (the game's pause).
        public void SetPaused(bool on) => paused = on;

        void Update()
        {
            if (movers == null) return;
            if (!paused) movers.Advance(Time.deltaTime);
            Pose();
        }

        /// The ball met mover `index`: the balloon wobbles, a gull tumbles away and comes back.
        public void React(int index) { if (index >= 0 && index < bodies.Count) hitAt[index] = Time.time; }

        void Pose()
        {
            double t = movers.Now;
            double step = t - lastClock; lastClock = t;
            for (int i = 0; i < movers.All.Length; i++)
            {
                var m = movers.All[i]; var root = bodies[i];
                if (!root) continue;
                var (x, y, d) = m.At(t);
                float heading = (float)m.HeadingAt(t);
                float since = hitAt.TryGetValue(i, out var at) ? Time.time - at : 99f;
                switch (m.Kind)
                {
                    case MoverKind.RockGate: case MoverKind.WindLift:
                        root.SetPositionAndRotation(new Vector3((float)x,(float)y,(float)d),m.Kind==MoverKind.WindLift?Quaternion.identity:Quaternion.Euler(0,(float)t*2,0));break;
                    case MoverKind.Launchpad: PosePad(i, m, t, since); break;
                    case MoverKind.Target: PoseTarget(i, root, new Vector3((float)x, (float)y, (float)d), since); break;
                    case MoverKind.Balloon:
                    {
                        root.position = new Vector3((float)x, (float)y, (float)d);
                        // it turns slowly as it drifts; struck, the envelope wobbles like a jelly and settles
                        root.rotation = Quaternion.Euler(0, (float)(t * 5 % 360), 0);
                        float wob = since < 1.6f ? Mathf.Sin(since * 18f) * Mathf.Exp(-since * 2.6f) * 0.12f : 0f;
                        root.GetChild(0).localScale = new Vector3(1 + wob, 1 - wob, 1 + wob);
                        var flame = flames[i];
                        if (flame) { float f = 0.7f + 0.3f * Mathf.PerlinNoise(Time.time * 6f, i); flame.localScale = new Vector3(0.45f, 0.8f * f, 0.45f); }
                        break;
                    }
                    case MoverKind.Cart:
                    {
                        // level with the ground under it, front to back
                        var ahead = m.At(t + 0.12); var behind = m.At(t - 0.12);
                        float run = Mathf.Max(0.01f, new Vector2((float)(ahead.x - behind.x), (float)(ahead.d - behind.d)).magnitude);
                        float pitch = -Mathf.Atan2((float)(ahead.y - behind.y), run) * Mathf.Rad2Deg;
                        root.position = new Vector3((float)x, (float)y, (float)d);
                        float bump = since < 0.5f ? Mathf.Sin(since * 30f) * Mathf.Exp(-since * 8f) * 3f : 0f;
                        root.rotation = Quaternion.Euler(pitch, heading, bump);
                        var spin = wheels[i];
                        if (spin != null)
                        {
                            var before = m.At(t - step);
                            float travelled = new Vector2((float)(x - before.x), (float)(d - before.d)).magnitude;
                            float roll = travelled / 0.28f * Mathf.Rad2Deg * Mathf.Sign((float)step);   // over the wheel's radius
                            foreach (var w in spin) if (w) w.Rotate(Vector3.right, roll, Space.Self);
                        }
                        break;
                    }
                    case MoverKind.Twister:
                    {
                        // it leans and sways, its walls spinning at their own speeds, faster near the ground
                        root.SetPositionAndRotation(new Vector3((float)x, (float)y, (float)d),
                            Quaternion.Euler(4f * Mathf.Sin((float)t * 0.6f + i), 0, 5f * Mathf.Sin((float)t * 0.45f + 2 * i)));
                        if (spinners.TryGetValue(i, out var layers))
                            for (int k = 0; k < layers.Length; k++)
                                if (layers[k]) layers[k].localRotation = Quaternion.Euler(0, Time.time * (40f + 25f * k) % 360f, 0);
                        break;
                    }
                    default:
                    {
                        var p = new Vector3((float)x, (float)y, (float)d);
                        // banked into the turn it is circling
                        float bank = -Mathf.Clamp(Mathf.DeltaAngle(heading, (float)m.HeadingAt(t + 0.1)) * 5f, -28f, 28f);
                        var rot = Quaternion.Euler(0, heading, bank);
                        if (since < 1.2f)
                        {
                            // knocked tumbling, up out of the ball's way, and back to its circle
                            float k = Mathf.Sin(Mathf.Clamp01(since / 1.2f) * Mathf.PI);
                            p += Vector3.up * k * 2.2f;
                            rot *= Quaternion.Euler(since * 720f * (1 - since / 1.2f), 0, since * 540f * (1 - since / 1.2f));
                        }
                        root.SetPositionAndRotation(p, rot);
                        var (l, r) = wings[i];
                        // a few beats, then a glide
                        float cycle = Mathf.Repeat((float)t * 0.7f + i * 0.37f, 1f);
                        float beat = cycle < 0.55f || since < 1.2f ? Mathf.Sin((float)t * 11f + i) * 38f : 6f;
                        if (l) l.localRotation = Quaternion.Euler(0, 0, beat);
                        if (r) r.localRotation = Quaternion.Euler(0, 0, -beat);
                        break;
                    }
                }
            }
        }

        // ----- The launchpad and the target (QuirkyObstacles, 10-19) -----

        sealed class Pad { public Material glow, chevron; public LineRenderer charge; public LineRenderer[] chevrons; public Transform top, button; }
        readonly Dictionary<int, Pad> pads = new();
        readonly Dictionary<int, (Transform swing, Material face)> targets = new();
        static readonly Color PadCharged = new(.25f, 1f, .55f), PadSpent = new(.62f, .14f, .12f), PadReady = new(1f, .86f, .25f);

        Material Glow(Color c)
        {
            var m = new Material(Shader.Find("Universal Render Pipeline/Unlit")) { name = "Pad glow" };
            m.SetColor("_BaseColor", c); dreamResources.Add(m); return m;
        }

        LineRenderer Line(Transform parent, string name, Material m, float width, int count)
        {
            var l = new GameObject(name).AddComponent<LineRenderer>();
            l.transform.SetParent(parent, false); l.useWorldSpace = false; l.sharedMaterial = m; l.widthMultiplier = width; l.positionCount = count;
            l.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; l.alignment = LineAlignment.TransformZ;
            return l;
        }

        /// A launchpad: a dark plinth flush with the ground, a glowing face (green: charged, it fires; red: spent), a
        /// ring round its rim filling up toward the next charge (gold as it is about to fire), chevrons racing toward
        /// where it sends the ball, and a white plunger in the middle that kicks when it fires.
        void BuildPad(Transform root, int index, Mover m)
        {
            var at = m.At(0); float r = (float)Mover.PadRadius;
            root.SetPositionAndRotation(new Vector3((float)at.x, (float)at.y, (float)at.d),
                Quaternion.Euler(0, Mathf.Atan2((float)(m.Goal.X - at.x), (float)(m.Goal.D - at.d)) * Mathf.Rad2Deg, 0));
            Part(PrimitiveType.Cylinder, "Pad plinth", UiColor("2B2F3A"), root, new Vector3(0, -.12f, 0), new Vector3(2 * r, .38f, 2 * r));
            Part(PrimitiveType.Cylinder, "Pad rim", UiColor("F7C531"), root, new Vector3(0, .2f, 0), new Vector3(2 * r * 1.04f, .07f, 2 * r * 1.04f));
            var pad = new Pad { glow = Glow(PadCharged), chevron = Glow(Color.white) };
            var face = HoleView.Primitive(PrimitiveType.Cylinder, "Pad face", Color.white, root);
            face.GetComponent<Renderer>().sharedMaterial = pad.glow;
            face.transform.localPosition = new Vector3(0, .28f, 0); face.transform.localScale = new Vector3(2 * r * .88f, .03f, 2 * r * .88f);
            pad.top = face.transform;
            pad.button = Part(PrimitiveType.Sphere, "Pad plunger", UiColor("FFF6E8"), root, new Vector3(0, .3f, 0), new Vector3(1.1f, .4f, 1.1f)).transform;
            var ringMat = Glow(PadReady);
            pad.charge = Line(root, "Pad charge", ringMat, .32f, 49);
            pad.charge.transform.localRotation = Quaternion.Euler(90, 0, 0);
            pad.chevrons = new LineRenderer[3];
            for (int k = 0; k < 3; k++)
            {
                var c = Line(root, "Pad chevron", pad.chevron, .42f, 3);
                c.transform.localRotation = Quaternion.Euler(90, 0, 0);
                float z = -r * .3f + k * r * .42f, w = r * .34f;
                c.SetPositions(new[] { new Vector3(-w, z - w * .7f, -.38f), new Vector3(0, z, -.38f), new Vector3(w, z - w * .7f, -.38f) });
                pad.chevrons[k] = c;
            }
            pads[index] = pad;
        }

        void PosePad(int index, Mover m, double t, float since)
        {
            if (!pads.TryGetValue(index, out var pad)) return;
            double u = m.CycleAt(t), share = Mover.ChargedShare;
            bool charged = u < share;
            float now = (float)t, r = (float)Mover.PadRadius * .97f;
            // the face: a pulsing green while it is charged, a dull red while it recharges, flicking gold just before
            float until = (float)((1 - u) * m.Period);
            Color face = charged ? Color.Lerp(PadCharged, Color.white, .18f + .18f * Mathf.Sin(now * 14f))
                       : until < .7f && Mathf.Repeat(now * 8f, 1f) < .5f ? PadReady : PadSpent;
            pad.glow.SetColor("_BaseColor", face);
            // the rim fills round as it recharges; full (and green) while charged
            float fill = charged ? 1f : (float)((u - share) / (1 - share));
            int n = Mathf.Max(2, Mathf.RoundToInt(48 * fill) + 1);
            pad.charge.positionCount = n;
            for (int k = 0; k < n; k++) { float a = k / 48f * Mathf.PI * 2; pad.charge.SetPosition(k, new Vector3(Mathf.Sin(a) * r, Mathf.Cos(a) * r, -.36f)); }
            pad.charge.sharedMaterial.SetColor("_BaseColor", charged ? PadCharged : PadReady);
            for (int k = 0; k < 3; k++)
            {
                bool lit = charged && Mathf.Repeat(now * 2.6f - k / 3f, 1f) < .45f;
                pad.chevrons[k].gameObject.SetActive(charged);
                pad.chevrons[k].widthMultiplier = lit ? .5f : .3f;
            }
            pad.chevron.SetColor("_BaseColor", Color.white);
            // it fires: the plunger kicks up and the face squashes and springs back
            float kick = since < .6f ? Mathf.Sin(since / .6f * Mathf.PI) * Mathf.Exp(-since * 2f) : 0f;
            pad.button.localPosition = new Vector3(0, .3f + kick * 1.4f, 0);
            pad.top.localScale = new Vector3(2 * (float)Mover.PadRadius * .88f * (1 + kick * .08f), .03f, 2 * (float)Mover.PadRadius * .88f * (1 + kick * .08f));
        }

        /// A target: a bullseye board (red and white rings, facing the tee) hung on two rods from a trolley that runs
        /// along the crossbar of a yellow gantry standing over the rough. The gantry stays put; the board slides.
        void BuildTarget(Transform movers, Transform root, int index, Mover m)
        {
            var a = HoleView.ToWorld(m.RailFrom); var b = HoleView.ToWorld(m.RailTo);
            var rail = new Vector3(b.x - a.x, 0, b.z - a.z); float length = rail.magnitude; rail /= Mathf.Max(.01f, length);
            float boardR = (float)Mover.TargetRadius, barY = (float)m.Height + boardR + 1.1f, post = (float)Mover.TargetPost;
            var gantry = new GameObject($"Target gantry {index}").transform; gantry.SetParent(movers, false);
            Vector3 pa = a - rail * post, pb = b + rail * post;
            foreach (var p in new[] { pa, pb })
            {
                float ground = (float)HoleView.GroundHeight(HoleView.ToCourse(p)) - .3f, h = barY - ground;
                Part(PrimitiveType.Cylinder, "Gantry post", UiColor("F7C531"), gantry, new Vector3(p.x, ground + h / 2, p.z), new Vector3(.7f, h / 2, .7f));
                Part(PrimitiveType.Cube, "Gantry foot", UiColor("2B2F3A"), gantry, new Vector3(p.x, ground + .45f, p.z), new Vector3(1.8f, 1.1f, 1.8f));
                Part(PrimitiveType.Sphere, "Gantry cap", UiColor("F4513A"), gantry, new Vector3(p.x, barY + .2f, p.z), Vector3.one * 1.1f);
            }
            var bar = Part(PrimitiveType.Cylinder, "Gantry rail", UiColor("FFF6E8"), gantry, new Vector3((pa.x + pb.x) / 2, barY, (pa.z + pb.z) / 2), new Vector3(.45f, (length + 2 * post) / 2, .45f));
            bar.transform.rotation = Quaternion.FromToRotation(Vector3.up, rail);
            foreach (var t in gantry.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = BallLook.OverlayLayer;
            // the board faces back up the hole, toward the tee
            var face = Vector3.Cross(rail, Vector3.up);
            var tee = HoleView.Current ? HoleView.ToWorld(HoleView.Current.Hole.Tee) : a - face * 50;
            if (Vector3.Dot(face, tee - a) < 0) face = -face;
            root.rotation = Quaternion.LookRotation(face, Vector3.up);
            var swing = new GameObject("Board swing").transform; swing.SetParent(root, false); swing.localPosition = new Vector3(0, barY - (float)m.Height, 0);
            Part(PrimitiveType.Cube, "Trolley", UiColor("2B2F3A"), swing, new Vector3(0, 0, 0), new Vector3(2.6f, .7f, 1.0f));
            float drop = barY - (float)m.Height;
            foreach (int side in new[] { -1, 1 })
                Part(PrimitiveType.Cylinder, "Hanger", UiColor("FFF6E8"), swing, new Vector3(side * boardR * .45f, -drop / 2, 0), new Vector3(.18f, drop / 2, .18f));
            var colours = new[] { UiColor("F4513A"), UiColor("FFF6E8"), UiColor("F4513A"), UiColor("FFF6E8"), UiColor("F7C531") };
            Material faceMat = null;
            for (int k = 0; k < colours.Length; k++)
            {
                float rr = boardR * (1 - k * .2f);
                var ring = Part(PrimitiveType.Cylinder, "Bullseye ring", colours[k], swing, new Vector3(0, -drop, .05f + k * .06f), new Vector3(2 * rr, .05f, 2 * rr), new Vector3(90, 0, 0));
                if (k == 0) { faceMat = new Material(Toy(colours[0])); dreamResources.Add(faceMat); ring.GetComponent<Renderer>().sharedMaterial = faceMat; }
            }
            targets[index] = (swing, faceMat);
        }

        void PoseTarget(int index, Transform root, Vector3 at, float since)
        {
            root.position = at;
            if (!targets.TryGetValue(index, out var t) || !t.swing) return;
            // struck: the board swings back on its hangers and rocks to rest, its outer ring flashing gold
            float swing = since < 2.4f ? -38f * Mathf.Sin(since * 7f) * Mathf.Exp(-since * 1.9f) : 0f;
            t.swing.localRotation = Quaternion.Euler(swing, 0, 0);
            if (t.face) t.face.color = since < 1.2f && Mathf.Repeat(since * 6f, 1f) < .5f ? UiColor("FFE066") : UiColor("F4513A");
        }

        // ----- The models -----

        static readonly Dictionary<Color, Material> toys = new();
        /// The game's soft plastic: a lit colour with a little sheen.
        public static Material Toy(Color c)
        {
            if (toys.TryGetValue(c, out var m) && m) return m;
            m = new Material(HoleView.Mat(c)) { name = "Toy " + ColorUtility.ToHtmlStringRGB(c) };
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", 0.38f);
            toys[c] = m;
            return m;
        }

        static GameObject Part(PrimitiveType type, string name, Color c, Transform parent, Vector3 pos, Vector3 scale, Vector3 euler = default)
        {
            var go = HoleView.Primitive(type, name, c, parent);
            go.GetComponent<Renderer>().sharedMaterial = Toy(c);
            go.transform.localPosition = pos; go.transform.localScale = scale; go.transform.localRotation = Quaternion.Euler(euler);
            return go;
        }

        static readonly Color[][] BalloonPalettes =
        {
            new[] { UiColor("F4513A"), UiColor("FFF6E8"), UiColor("F7C531") },
            new[] { UiColor("3E8EF0"), UiColor("FFF6E8"), UiColor("FF8A3D") },
            new[] { UiColor("9B5DE5"), UiColor("F15BB5"), UiColor("FEE440") },
            new[] { UiColor("00BBF9"), UiColor("00C49A"), UiColor("FEE440") },
        };
        static Color UiColor(string hex) => ColorUtility.TryParseHtmlString("#" + hex, out var c) ? c : Color.white;

        void BuildBalloon(Transform root, int index, int variant)
        {
            var palette = BalloonPalettes[Mathf.Abs(variant) % BalloonPalettes.Length];
            var envelope = new GameObject("Envelope").transform;
            envelope.SetParent(root, false);
            var mf = envelope.gameObject.AddComponent<MeshFilter>();
            var mr = envelope.gameObject.AddComponent<MeshRenderer>();
            mf.sharedMesh = EnvelopeMesh((float)Mover.Envelope, palette.Length);
            var mats = new Material[palette.Length];
            for (int i = 0; i < mats.Length; i++) mats[i] = Toy(palette[i]);
            mr.sharedMaterials = mats;
            float mouthY = -(float)Mover.Envelope * 1.28f;
            Part(PrimitiveType.Cylinder, "Skirt", UiColor("3A2F3A"), root, new Vector3(0, mouthY - 0.15f, 0), new Vector3(1.25f, 0.18f, 1.25f));
            // the basket: wicker, a darker rim, and the ropes up to the mouth
            float basketY = -(float)Mover.BasketDrop;
            Part(PrimitiveType.Cube, "Basket", UiColor("B07A45"), root, new Vector3(0, basketY, 0), new Vector3(1.55f, 1.15f, 1.55f));
            Part(PrimitiveType.Cube, "Rim", UiColor("7A4E2A"), root, new Vector3(0, basketY + 0.6f, 0), new Vector3(1.68f, 0.16f, 1.68f));
            var top = new Vector3(0, mouthY - 0.2f, 0);
            foreach (var corner in new[] { new Vector3(0.7f, 0, 0.7f), new Vector3(-0.7f, 0, 0.7f), new Vector3(0.7f, 0, -0.7f), new Vector3(-0.7f, 0, -0.7f) })
            {
                var from = new Vector3(corner.x, basketY + 0.65f, corner.z);
                var to = top + corner * 0.75f;
                var rope = Part(PrimitiveType.Cylinder, "Rope", UiColor("4A3A30"), root, (from + to) / 2, new Vector3(0.05f, (to - from).magnitude / 2, 0.05f));
                rope.transform.localRotation = Quaternion.FromToRotation(Vector3.up, to - from);
                rope.GetComponent<Renderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
            var flame = HoleView.Primitive(PrimitiveType.Sphere, "Burner flame", Color.white, root);
            flame.GetComponent<Renderer>().sharedMaterial = HoleView.UnlitMat(UiColor("FFB23F"));
            flame.GetComponent<Renderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            flame.transform.localPosition = new Vector3(0, mouthY - 0.6f, 0);
            flames[index] = flame.transform;
        }

        /// The envelope: a sphere over a tapering cone down to the mouth, in `colours` alternating
        /// gores (one mesh, a submesh a colour, so the shading runs smoothly over the seams).
        static Mesh EnvelopeMesh(float radius, int colours)
        {
            const int gores = 12, perGore = 3, rings = 22;
            int segments = gores * perGore;
            var verts = new List<Vector3>(); var normals = new List<Vector3>();
            // the profile, top to mouth: (height, radius)
            var profile = new Vector2[rings + 1];
            for (int r = 0; r <= rings; r++)
            {
                float u = r / (float)rings;
                if (u <= 0.5f) { float phi = u / 0.5f * Mathf.PI / 2; profile[r] = new Vector2(radius * Mathf.Cos(phi), radius * Mathf.Sin(phi)); }
                else
                {
                    float v = (u - 0.5f) / 0.5f;
                    float h = -radius * 1.28f * v;
                    float w = radius * (0.24f + 0.76f * Mathf.Pow(Mathf.Max(0f, Mathf.Cos(v * Mathf.PI / 2)), 0.85f));   // (cos 90° comes out a hair below 0)
                    profile[r] = new Vector2(h, w);
                }
            }
            for (int r = 0; r <= rings; r++)
                for (int s = 0; s <= segments; s++)
                {
                    float a = s / (float)segments * Mathf.PI * 2;
                    verts.Add(new Vector3(Mathf.Cos(a) * profile[r].y, profile[r].x, Mathf.Sin(a) * profile[r].y));
                }
            var tris = new List<int>[colours];
            for (int c = 0; c < colours; c++) tris[c] = new List<int>();
            for (int r = 0; r < rings; r++)
                for (int s = 0; s < segments; s++)
                {
                    int i0 = r * (segments + 1) + s, i1 = i0 + 1, i2 = i0 + segments + 1, i3 = i2 + 1;
                    var list = tris[(s / perGore) % colours];
                    list.Add(i0); list.Add(i1); list.Add(i2);
                    list.Add(i1); list.Add(i3); list.Add(i2);
                }
            var mesh = new Mesh { name = "Balloon envelope" };
            mesh.SetVertices(verts);
            mesh.subMeshCount = colours;
            for (int c = 0; c < colours; c++) mesh.SetTriangles(tris[c], c);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        void BuildCart(Transform root, int index)
        {
            var white = UiColor("F7F5EF"); var canopy = UiColor("2FA36B"); var tyre = UiColor("26282C"); var seat = UiColor("C9A27A");
            var body = new GameObject("Body").transform; body.SetParent(root, false);
            Part(PrimitiveType.Cube, "Chassis", white, body, new Vector3(0, 0.5f, 0), new Vector3(1.25f, 0.42f, 2.3f));
            Part(PrimitiveType.Cube, "Cowl", white, body, new Vector3(0, 0.82f, 0.82f), new Vector3(1.18f, 0.36f, 0.62f), new Vector3(-14, 0, 0));
            Part(PrimitiveType.Cube, "Bumper", UiColor("3B3F46"), body, new Vector3(0, 0.38f, 1.18f), new Vector3(1.3f, 0.16f, 0.12f));
            Part(PrimitiveType.Cube, "Seat", seat, body, new Vector3(0, 0.82f, -0.12f), new Vector3(1.05f, 0.18f, 0.6f));
            Part(PrimitiveType.Cube, "Back rest", seat, body, new Vector3(0, 1.1f, -0.44f), new Vector3(1.05f, 0.5f, 0.12f));
            foreach (float sx in new[] { -0.55f, 0.55f })
                foreach (float sz in new[] { 0.62f, -0.5f })
                    Part(PrimitiveType.Cylinder, "Post", UiColor("D7D9DC"), body, new Vector3(sx, 1.45f, sz), new Vector3(0.06f, 0.55f, 0.06f));
            Part(PrimitiveType.Cube, "Canopy", canopy, body, new Vector3(0, 2.02f, 0.05f), new Vector3(1.38f, 0.1f, 1.62f));
            Part(PrimitiveType.Cube, "Canopy trim", UiColor("F7F5EF"), body, new Vector3(0, 1.95f, 0.05f), new Vector3(1.42f, 0.05f, 1.66f));
            Part(PrimitiveType.Cylinder, "Steering column", UiColor("3B3F46"), body, new Vector3(-0.28f, 1.08f, 0.42f), new Vector3(0.05f, 0.26f, 0.05f), new Vector3(-30, 0, 0));
            Part(PrimitiveType.Cylinder, "Wheel", UiColor("3B3F46"), body, new Vector3(-0.28f, 1.3f, 0.3f), new Vector3(0.32f, 0.03f, 0.32f), new Vector3(-55, 0, 0));
            // the driver, waving a little as the cart goes round
            Part(PrimitiveType.Capsule, "Driver", UiColor("F25F5C"), body, new Vector3(-0.28f, 1.22f, -0.12f), new Vector3(0.42f, 0.36f, 0.34f));
            Part(PrimitiveType.Sphere, "Head", UiColor("E8B48F"), body, new Vector3(-0.28f, 1.72f, -0.1f), new Vector3(0.3f, 0.32f, 0.3f));
            Part(PrimitiveType.Cylinder, "Cap", UiColor("1F4E8C"), body, new Vector3(-0.28f, 1.86f, -0.08f), new Vector3(0.31f, 0.05f, 0.31f));
            Part(PrimitiveType.Cube, "Peak", UiColor("1F4E8C"), body, new Vector3(-0.28f, 1.84f, 0.1f), new Vector3(0.24f, 0.03f, 0.16f));
            // a bag on the back, club heads out of the top
            Part(PrimitiveType.Cylinder, "Bag", UiColor("1F4E8C"), body, new Vector3(0, 1.0f, -1.02f), new Vector3(0.36f, 0.42f, 0.36f), new Vector3(12, 0, 0));
            for (int k = 0; k < 3; k++)
                Part(PrimitiveType.Cube, "Club head", UiColor("C7CCD3"), body, new Vector3(-0.1f + 0.1f * k, 1.5f, -1.12f + 0.04f * k), new Vector3(0.07f, 0.1f, 0.16f));
            var spin = new List<Transform>();
            foreach (float sx in new[] { -0.6f, 0.6f })
                foreach (float sz in new[] { 0.74f, -0.74f })
                {
                    var hub = new GameObject("Wheel hub").transform; hub.SetParent(body, false);
                    hub.localPosition = new Vector3(sx, 0.28f, sz);
                    Part(PrimitiveType.Cylinder, "Tyre", tyre, hub, Vector3.zero, new Vector3(0.56f, 0.1f, 0.56f), new Vector3(0, 0, 90));
                    Part(PrimitiveType.Cube, "Hub cap", UiColor("D7D9DC"), hub, new Vector3(sx > 0 ? 0.11f : -0.11f, 0, 0), new Vector3(0.02f, 0.26f, 0.08f));
                    spin.Add(hub);
                }
            wheels[index] = spin.ToArray();
        }

        readonly Dictionary<int, Transform[]> spinners = new();

        /// A twister: three walls of swirling cloud round its middle, wide at the top and pinched
        /// to a point at the ground, each streaked and spun at its own speed; a skirt of dust where
        /// it touches down, and debris whirling up it.
        void BuildTwister(Transform root, int index)
        {
            // the funnel's walls: GolfArcade/Twister winds and spins its streaks; the dirt round its foot is plain soft particles
            var mat = new Material(ShotEffects.ParticleMaterial()) { name = "Twister dust", mainTexture = Texture2D.whiteTexture };
            var funnelShader = Resources.Load<Shader>("Golf/Twister");
            var walls = funnelShader ? new Material(funnelShader) { name = "Twister" } : mat;
            var layers = new Transform[2];
            for (int k = 0; k < layers.Length; k++)
            {
                var go = new GameObject("Funnel " + k);
                go.transform.SetParent(root, false);
                go.AddComponent<MeshFilter>().sharedMesh = FunnelMesh(1f - 0.22f * k, k);
                var mr = go.AddComponent<MeshRenderer>(); mr.sharedMaterial = walls;
                mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; mr.receiveShadows = false;
                // the inner wall is drawn first, the outer over it
                mr.sortingOrder = -k;
                layers[k] = go.transform;
            }
            spinners[index] = layers;
            // where it touches down: a low skirt of dust and spray
            var skirt = new GameObject("Dust skirt");
            skirt.transform.SetParent(root, false);
            skirt.AddComponent<MeshFilter>().sharedMesh = SkirtMesh();
            var sr = skirt.AddComponent<MeshRenderer>(); sr.sharedMaterial = mat;
            sr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            // debris whirling up and round it
            var debris = new GameObject("Debris").AddComponent<ParticleSystem>();
            debris.transform.SetParent(root, false);
            debris.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = debris.main;
            main.loop = true; main.playOnAwake = true; main.maxParticles = 400; main.simulationSpace = ParticleSystemSimulationSpace.Local;
            main.startLifetime = new ParticleSystem.MinMaxCurve(2.2f, 3.4f); main.startSpeed = 0; main.gravityModifier = 0;
            main.startSize = new ParticleSystem.MinMaxCurve(0.2f, 0.55f);
            main.startColor = new ParticleSystem.MinMaxGradient(new Color(0.32f, 0.27f, 0.2f, 0.95f), new Color(0.26f, 0.38f, 0.2f, 0.95f));
            var shape = debris.shape; shape.enabled = true; shape.shapeType = ParticleSystemShapeType.Circle; shape.radius = 3.2f; shape.rotation = new Vector3(-90, 0, 0);
            var vel = debris.velocityOverLifetime; vel.enabled = true; vel.space = ParticleSystemSimulationSpace.Local;
            // (every axis in the same mode, a range: Unity refuses to mix a constant with a range)
            vel.x = new ParticleSystem.MinMaxCurve(0f, 0f); vel.z = new ParticleSystem.MinMaxCurve(0f, 0f);
            vel.y = new ParticleSystem.MinMaxCurve(5f, 9f);
            vel.orbitalX = new ParticleSystem.MinMaxCurve(0f, 0f); vel.orbitalZ = new ParticleSystem.MinMaxCurve(0f, 0f);
            vel.orbitalY = new ParticleSystem.MinMaxCurve(4f, 6f);
            vel.radial = new ParticleSystem.MinMaxCurve(0.6f, 1.2f);
            var emission = debris.emission; emission.rateOverTime = 110;
            var pr = debris.GetComponent<ParticleSystemRenderer>();
            pr.sharedMaterial = ShotEffects.ParticleMaterial();
            pr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            debris.Play();
            // and the cloud of dirt it churns up round its foot, billowing round and out
            var dust = new GameObject("Dust cloud").AddComponent<ParticleSystem>();
            dust.transform.SetParent(root, false);
            dust.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var dm = dust.main;
            dm.loop = true; dm.playOnAwake = true; dm.maxParticles = 120; dm.simulationSpace = ParticleSystemSimulationSpace.Local;
            dm.startLifetime = new ParticleSystem.MinMaxCurve(2.5f, 4f); dm.startSpeed = 0; dm.gravityModifier = 0;
            dm.startSize = new ParticleSystem.MinMaxCurve(3.5f, 7f);
            dm.startColor = new ParticleSystem.MinMaxGradient(new Color(0.45f, 0.39f, 0.31f, 0.38f), new Color(0.38f, 0.36f, 0.33f, 0.3f));
            var ds = dust.shape; ds.enabled = true; ds.shapeType = ParticleSystemShapeType.Circle; ds.radius = 3.5f; ds.rotation = new Vector3(-90, 0, 0);
            var dv = dust.velocityOverLifetime; dv.enabled = true; dv.space = ParticleSystemSimulationSpace.Local;
            dv.x = new ParticleSystem.MinMaxCurve(0f, 0f); dv.z = new ParticleSystem.MinMaxCurve(0f, 0f);
            dv.orbitalX = new ParticleSystem.MinMaxCurve(0f, 0f); dv.orbitalZ = new ParticleSystem.MinMaxCurve(0f, 0f);
            dv.y = new ParticleSystem.MinMaxCurve(0.4f, 1.6f); dv.orbitalY = new ParticleSystem.MinMaxCurve(1.5f, 2.5f); dv.radial = new ParticleSystem.MinMaxCurve(1.2f, 2.4f);
            var dc = dust.colorOverLifetime; dc.enabled = true;
            var dg = new Gradient(); dg.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) }, new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(1, 0.25f), new GradientAlphaKey(0, 1) });
            dc.color = dg;
            var de = dust.emission; de.rateOverTime = 30;
            var dr = dust.GetComponent<ParticleSystemRenderer>();
            dr.sharedMaterial = ShotEffects.ParticleMaterial(); dr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            dust.Play();
        }

        /// One wall of the funnel: a flared lathe up to 32 yards, streaked by its vertex alpha, softest at the top and the ground.
        static Mesh FunnelMesh(float scale, int layer)
        {
            const int rings = 30, around = 32; const float height = 40f;
            var verts = new List<Vector3>(); var colours = new List<Color>(); var uvs = new List<Vector2>(); var tris = new List<int>();
            for (int j = 0; j <= rings; j++)
            {
                float v = j / (float)rings, h = v * height;
                float r = (1.0f + 10f * Mathf.Pow(v, 1.6f)) * scale;
                for (int i = 0; i <= around; i++)
                {
                    float a = i * Mathf.PI * 2 / around + v * (2.2f + layer);   // the wall twists as it climbs
                    verts.Add(new Vector3(Mathf.Cos(a) * r, h, Mathf.Sin(a) * r));
                    float fade = Mathf.Clamp01(v * 8f) * Mathf.Clamp01((1 - v) * 3f);
                    // dark storm cloud, browner low down where it is full of dirt
                    float g = Mathf.Lerp(0.2f, 0.4f, v) + 0.04f * layer;
                    // (the streaks are the shader's; the vertex alpha fades the funnel's top into the cloud and its foot into the dust)
                    colours.Add(new Color(g * Mathf.Lerp(1.12f, 1f, v), g * 1.02f, g * Mathf.Lerp(0.92f, 1.1f, v), fade * (layer == 0 ? 1f : 0.85f)));
                    // u round the funnel, v up it: the twister's shader winds its streaks by them
                    uvs.Add(new Vector2(i / (float)around, v));
                }
            }
            for (int j = 0; j < rings; j++)
                for (int i = 0; i < around; i++)
                {
                    int a0 = j * (around + 1) + i, a1 = a0 + 1, b0 = a0 + around + 1, b1 = b0 + 1;
                    tris.AddRange(new[] { a0, b0, a1, b0, b1, a1 });
                }
            var mesh = new Mesh { name = "Twister funnel " + layer };
            mesh.SetVertices(verts); mesh.SetColors(colours); mesh.SetUVs(0, uvs); mesh.SetTriangles(tris, 0);
            mesh.RecalculateNormals(); mesh.RecalculateBounds();
            return mesh;
        }

        static Mesh SkirtMesh()
        {
            const int around = 32; var verts = new List<Vector3> { new(0, 0.3f, 0) }; var colours = new List<Color> { new(0.42f, 0.37f, 0.3f, 0.45f) };
            var uvs = new List<Vector2> { new(0.5f, 0.5f) }; var tris = new List<int>();
            for (int i = 0; i <= around; i++)
            {
                float a = i * Mathf.PI * 2 / around;
                verts.Add(new Vector3(Mathf.Cos(a) * 9f, 2.2f + 0.7f * Mathf.Sin(a * 5), Mathf.Sin(a) * 9f));
                colours.Add(new Color(0.5f, 0.45f, 0.38f, 0f)); uvs.Add(new Vector2(0.5f, 0.5f));
                if (i > 0) tris.AddRange(new[] { 0, i + 1, i });
            }
            var mesh = new Mesh { name = "Twister skirt" };
            mesh.SetVertices(verts); mesh.SetColors(colours); mesh.SetUVs(0, uvs); mesh.SetTriangles(tris, 0); mesh.RecalculateBounds();
            return mesh;
        }

        void BuildGull(Transform root, int index)
        {
            var white = UiColor("FAFAF7"); var grey = UiColor("B8C0C8"); var tip = UiColor("2E3236");
            // a little bigger than life, the way the ball is: a speck on the sky reads as a gull
            var body = new GameObject("Body").transform; body.SetParent(root, false); body.localScale = Vector3.one * 1.5f;
            Part(PrimitiveType.Capsule, "Torso", white, body, Vector3.zero, new Vector3(0.24f, 0.32f, 0.24f), new Vector3(90, 0, 0));
            Part(PrimitiveType.Sphere, "Head", white, body, new Vector3(0, 0.08f, 0.3f), new Vector3(0.2f, 0.19f, 0.22f));
            Part(PrimitiveType.Cube, "Beak", UiColor("F6B53C"), body, new Vector3(0, 0.06f, 0.45f), new Vector3(0.05f, 0.05f, 0.13f));
            Part(PrimitiveType.Cube, "Tail", grey, body, new Vector3(0, 0.02f, -0.36f), new Vector3(0.16f, 0.03f, 0.16f));
            Transform Wing(float side)
            {
                var shoulder = new GameObject(side < 0 ? "Left wing" : "Right wing").transform;
                shoulder.SetParent(body, false); shoulder.localPosition = new Vector3(0.1f * side, 0.06f, 0.04f);
                Part(PrimitiveType.Cube, "Wing", grey, shoulder, new Vector3(0.32f * side, 0, 0), new Vector3(0.62f, 0.03f, 0.26f));
                Part(PrimitiveType.Cube, "Tip", tip, shoulder, new Vector3(0.7f * side, 0, -0.03f), new Vector3(0.18f, 0.025f, 0.18f));
                return shoulder;
            }
            wings[index] = (Wing(-1), Wing(1));
            foreach (var r in root.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        }
    }
}
