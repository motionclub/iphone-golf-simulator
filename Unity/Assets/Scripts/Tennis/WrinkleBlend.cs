using System;
using System.Linq;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// POSE-DRIVEN WRINKLES (2026-11-19, work/clothing-tex-1119/wrinkles): the AAA "wrinkle map" technique. Each garment carries up to
    /// six wrinkle normal maps baked from a Blender cloth sim of that garment in a key pose (the cloth's springs rest at the unposed
    /// lengths, so it buckles exactly where that pose compresses it). Every frame the garment's own pose-corrective weights (the
    /// existing GP_Pose blend shapes, already driven by the pose readers) are compared with each key pose's weights; the closer the
    /// body is to a key pose, the more of that pose's folds show. No folds at rest. Off: WRINKLES=0.
    [DefaultExecutionOrder(32100)]
    public sealed class WrinkleBlend : MonoBehaviour
    {
        [Serializable] class Data { public string garment; public string[] textures; public Row[] keys; }
        [Serializable] class Row { public float[] w; }
        static readonly int W0 = Shader.PropertyToID("_WrW0"), W1 = Shader.PropertyToID("_WrW1"), On = Shader.PropertyToID("_WrOn"), Gain = Shader.PropertyToID("_WrGain");
        static readonly int[] Tex = { Shader.PropertyToID("_Wr0"), Shader.PropertyToID("_Wr1"), Shader.PropertyToID("_Wr2") };

        SkinnedMeshRenderer skin; Material[] materials; float[][] keys; float sigma2, keyNorm; float[] smooth = new float[6]; float[] g;
        public Vector4 DebugW0, DebugW1;

        public static void Attach(MatchHeroLook look)
        {
            if (!look || look.kit == null || Environment.GetEnvironmentVariable("WRINKLES") == "0") return;
            string sport = look.golfKit ? "Golf" : string.IsNullOrEmpty(look.kitSport) ? "Tennis" : look.kitSport;
            string sex = look.female ? "Female" : "Male";
            foreach (var r in look.kit)
            {
                if (!r || (r.name != "Kit_Top" && r.name != "Kit_Bottom") || !r.sharedMesh) continue;
                string id = $"{sport}_{sex}_{r.name.Substring(4)}";
                var asset = Resources.Load<TextAsset>($"Wrinkles/{id}");
                if (!asset) continue;
                // JsonUtility can't read jagged arrays: the json stores keys as [{"w":[...]}]
                var data = JsonUtility.FromJson<Data>(asset.text);
                if (data?.keys == null || data.keys.Length == 0) continue;
                var mats = r.sharedMaterials.Where(m => m && m.HasProperty("_WeaveTile")).ToArray();
                for (int t = 0; t < data.textures.Length && t < 3; t++)
                {
                    var tex = Resources.Load<Texture2D>($"Wrinkles/{id}_{data.textures[t]}");
                    foreach (var m in mats) if (tex) m.SetTexture(Tex[t], tex);
                }
                var c = r.gameObject.AddComponent<WrinkleBlend>();
                c.skin = r; c.materials = mats; c.keys = data.keys.Select(k => k.w.Select(x => x / 100f).ToArray()).ToArray();
                // kernel width: a third of the typical distance between key poses
                float sum = 0; int n = 0;
                for (int i = 0; i < c.keys.Length; i++) for (int j = i + 1; j < c.keys.Length; j++) { sum += Dist2(c.keys[i], c.keys[j]); n++; }
                c.keyNorm = c.keys.Average(k => Mathf.Sqrt(k.Sum(x => x * x)));
                c.sigma2 = Mathf.Max(.25f * c.keyNorm * c.keyNorm, (n > 0 ? sum / n : .5f) * .5f);
                foreach (var m in mats) { m.SetFloat(On, 1); m.SetFloat(Gain, float.TryParse(Environment.GetEnvironmentVariable("WRINKLE_GAIN"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var gv) ? gv : 3f); }
                Debug.Log($"[WrinkleBlend] {id}: {c.keys.Length} key poses, {data.textures.Length} maps, sigma2 {c.sigma2:0.###}");
            }
        }

        static float Dist2(float[] a, float[] b) { float s = 0; for (int i = 0; i < Mathf.Min(a.Length, b.Length); i++) { float d = a[i] - b[i]; s += d * d; } return s; }

        void LateUpdate()
        {
            if (!skin || materials == null) return;
            var mesh = skin.sharedMesh; int count = mesh.blendShapeCount;
            if (g == null || g.Length != count) g = new float[count];
            for (int i = 0; i < count; i++) g[i] = skin.GetBlendShapeWeight(i) / 100f;
            // Which key pose the body is closest to (normalised RBF), times how strongly it is posed at all
            // (the corrective activity relative to the key poses' typical activity). Wide kernel: no dead zones between keys.
            float total = 0; var w = new float[6]; float gn = Mathf.Sqrt(g.Sum(x => x * x));
            for (int k = 0; k < keys.Length && k < 6; k++) { w[k] = Mathf.Exp(-Dist2(g, keys[k]) / sigma2); total += w[k]; }
            float act = Mathf.Clamp01(gn / Mathf.Max(.05f, keyNorm) * 1.15f);
            float norm = total > 1e-5f ? act / total : 0;
            float lp = 1 - Mathf.Exp(-Time.deltaTime / .08f);
            for (int k = 0; k < 6; k++) smooth[k] = Mathf.Lerp(smooth[k], w[k] * norm, lp);
            DebugW0 = new Vector4(smooth[0], smooth[1], smooth[2], smooth[3]); DebugW1 = new Vector4(smooth[4], smooth[5], 0, 0);
            foreach (var m in materials) { m.SetVector(W0, DebugW0); m.SetVector(W1, DebugW1); }
        }
    }
}
