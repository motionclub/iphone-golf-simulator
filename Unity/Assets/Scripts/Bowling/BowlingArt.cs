using UnityEngine;

namespace GolfArcade.Bowling
{
    /// The club ball and the regulation pin (Blender-built, work/bowling-ball-pin; installed in
    /// Resources/Bowling). Both meshes are +Y up in metres with identity transforms: the pin's
    /// origin is the centre of its base, the ball's its centre. If the art is missing, the
    /// procedural pin (BowlingPinShape) and the greybox ball stand in.
    public static class BowlingArt
    {
        static GameObject pin, ball, colliders;
        static Mesh[] hulls;
        static Material pinMaterial, ballMaterial;

        static GameObject Load(ref GameObject cache, string path) => cache ? cache : cache = Resources.Load<GameObject>(path);

        public static bool HasPin => Load(ref pin, "Bowling/Pin");
        public static bool HasBall => Load(ref ball, "Bowling/Ball_Club");

        /// The pin's three convex collision hulls (base→belly, belly→neck, neck→top), or the procedural ones.
        public static Mesh[] PinHulls()
        {
            if (hulls != null) return hulls;
            if (Load(ref colliders, "Bowling/Pin_Colliders"))
            {
                var found = new Mesh[3];
                foreach (var mf in colliders.GetComponentsInChildren<MeshFilter>(true))
                {
                    string n = mf.name;
                    int i = n.Contains("Base") ? 0 : n.Contains("Neck") ? 1 : n.Contains("Head") ? 2 : -1;
                    if (i >= 0) found[i] = mf.sharedMesh;
                }
                if (found[0] && found[1] && found[2] && found[0].isReadable) return hulls = found;
            }
            return hulls = BowlingPinShape.Hulls();
        }

        /// Lacquered: a smooth base under a full clear coat (URP Complex Lit), so pins and ball carry
        /// a sharp second highlight and mirror the lit masking, LEDs and lane. Plain Lit if Complex
        /// Lit is not in the build.
        static Material Lit(Texture albedo, float smoothness, Texture metallicSmoothness = null)
        {
            var complex = Shader.Find("Universal Render Pipeline/Complex Lit");
            var m = new Material(complex ? complex : Shader.Find("Universal Render Pipeline/Lit"));
            if (complex)
            {
                m.SetFloat("_ClearCoatMask", 1); m.SetFloat("_ClearCoatSmoothness", .97f);
                m.EnableKeyword("_CLEARCOAT");
            }
            m.SetFloat("_EnvironmentReflections", 1); m.SetFloat("_SpecularHighlights", 1);
            m.SetColor("_BaseColor", Color.white);
            m.SetTexture("_BaseMap", albedo);
            m.SetFloat("_Metallic", 0); m.SetFloat("_Smoothness", smoothness);
            if (metallicSmoothness)
            {
                m.SetTexture("_MetallicGlossMap", metallicSmoothness);
                m.EnableKeyword("_METALLICSPECGLOSSMAP");
                m.SetFloat("_SmoothnessTextureChannel", 0);   // smoothness from the metallic map's alpha
            }
            m.enableInstancing = true;
            return m;
        }

        /// A pin to look at (with its LODs), or the procedural one.
        public static GameObject Pin(Transform parent)
        {
            if (!HasPin) return BowlingAlley.Pin(parent, BowlingPinShape.Build(), BowlingAlley.PinMaterials());
            if (!pinMaterial)
            {
                pinMaterial = Lit(Resources.Load<Texture2D>("Bowling/Pin_Albedo"), .9f);
                pinMaterial.SetColor("_BaseColor", new Color(.82f, .81f, .79f));   // off-white lacquer: keeps the shading out of clipping
            }
            var go = Object.Instantiate(pin, parent, false);
            go.name = "Pin";
            foreach (var r in go.GetComponentsInChildren<MeshRenderer>(true)) r.sharedMaterial = pinMaterial;
            return go;
        }

        /// The club ball to look at, or the greybox one.
        public static GameObject Ball(Transform parent)
        {
            if (!HasBall) return BowlingAlley.Ball(parent);
            ballMaterial ??= Lit(Resources.Load<Texture2D>("Bowling/Ball_Club_Albedo"), 1, Resources.Load<Texture2D>("Bowling/Ball_Club_MetallicSmoothness"));
            var go = Object.Instantiate(ball, parent, false);
            go.name = "ClubBall";
            foreach (var r in go.GetComponentsInChildren<MeshRenderer>(true)) r.sharedMaterial = ballMaterial;
            return go;
        }
    }
}
