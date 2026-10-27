using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// GARMENT PIPELINE (work/clothing-v2/pipeline, GARMENT_PIPELINE.md): pose correctives of ANY V2 garment piece. The pipeline solves, per
    /// stress pose, the smallest smooth outward lift that keeps the cloth outside the skin and the garments under it, compresses those lifts
    /// into a few blend shapes (GP_PoseNN) and fits a Gaussian RBF over pose features. Each frame this component computes the same 33 features
    /// as work/clothing-v2/pipeline/gp/features.py (10 segment directions in their parent bone's rest frame + the trunk rotation vector / 90 deg)
    /// and sets every shape to clamp01(sum_a coef[a,s] * exp(-|f - anchor_a|^2 / 2 sigma^2)). Profile per piece:
    /// Resources/<Sport>/KitsV2/<Sex>/KitV2_<Sport>_<Sex>_<Tag>_correctives (featureMode "gp-rbf"). Garment only: body, rig and clips untouched.
    [DefaultExecutionOrder(1225), DisallowMultipleComponent]
    public sealed class GarmentPoseCorrectives : MonoBehaviour
    {
        [Serializable] sealed class Profile { public string featureMode; public string[] shapes; public int anchorCount, featureCount; public float sigma; public float[] anchors, coef; }
        static readonly string[,] Segments = {
            { "UpperChest", "LeftUpperArm", "LeftLowerArm" }, { "UpperChest", "RightUpperArm", "RightLowerArm" },
            { "LeftUpperArm", "LeftLowerArm", "LeftHand" }, { "RightUpperArm", "RightLowerArm", "RightHand" },
            { "Hips", "LeftUpperLeg", "LeftLowerLeg" }, { "Hips", "RightUpperLeg", "RightLowerLeg" },
            { "LeftUpperLeg", "LeftLowerLeg", "LeftFoot" }, { "RightUpperLeg", "RightLowerLeg", "RightFoot" },
            { "Hips", "Spine", "Neck" }, { "UpperChest", "Neck", "Head" } };
        sealed class Piece { public SkinnedMeshRenderer renderer; public Profile profile; public int[] shapeIndex; public float[] weights; }

        public MatchHeroLook look;
        readonly List<Piece> pieces = new List<Piece>();
        Transform[,] seg; Quaternion[] segRest; Transform hips, upperChest; Quaternion hipsRest, chestRest;
        float[] features; float[] phi; bool ready, failed;

        public static void Attach(MatchHeroLook look)
        {
            if (!look || !look.kitV2) return;
            var c = look.GetComponent<GarmentPoseCorrectives>() ?? look.gameObject.AddComponent<GarmentPoseCorrectives>();
            c.look = look;
        }

        /// root-space rest rotation of a body bone, from the body's bind poses (the pipeline's rest frame).
        Quaternion RestRotation(Transform bone)
        {
            var body = look.body; int i = Array.IndexOf(body.bones, bone);
            if (i < 0) return Quaternion.Inverse(transform.rotation) * bone.rotation;
            var m = transform.worldToLocalMatrix * body.transform.localToWorldMatrix * body.sharedMesh.bindposes[i].inverse;
            return Quaternion.LookRotation(m.GetColumn(2), m.GetColumn(1));
        }

        bool Init()
        {
            if (ready) return true;
            if (failed) return false;
            if (!look) look = GetComponent<MatchHeroLook>();
            if (!look || !look.kitV2 || look.kit == null || !look.body) return false;
            string sport = look.KitSportFolder, sex = look.female ? "Female" : "Male";
            foreach (var r in look.kit)
            {
                if (!r || !r.sharedMesh || !MatchHeroLook.IsKitV2(r.sharedMesh) || r.sharedMesh.blendShapeCount == 0) continue;
                var text = Resources.Load<TextAsset>($"{sport}/KitsV2/{sex}/KitV2_{sport}_{sex}_{r.name.Substring(4).Replace("_", "")}_correctives");
                if (!text) continue;
                var p = JsonUtility.FromJson<Profile>(text.text);
                if (p == null || p.featureMode != "gp-rbf" || p.shapes == null || p.anchors == null) continue;
                var piece = new Piece { renderer = r, profile = p, shapeIndex = p.shapes.Select(s => r.sharedMesh.GetBlendShapeIndex(s)).ToArray(), weights = new float[p.shapes.Length] };
                pieces.Add(piece);
            }
            if (pieces.Count == 0) { failed = true; return false; }
            var all = GetComponentsInChildren<Transform>(true).GroupBy(t => t.name).ToDictionary(g => g.Key, g => g.First());
            seg = new Transform[Segments.GetLength(0), 3]; segRest = new Quaternion[Segments.GetLength(0)];
            for (int i = 0; i < Segments.GetLength(0); i++)
            {
                for (int j = 0; j < 3; j++) if (!all.TryGetValue(Segments[i, j], out seg[i, j])) { failed = true; return false; }
                segRest[i] = RestRotation(seg[i, 0]);
            }
            if (!all.TryGetValue("Hips", out hips) || !all.TryGetValue("UpperChest", out upperChest)) { failed = true; return false; }
            hipsRest = RestRotation(hips); chestRest = RestRotation(upperChest);
            features = new float[Segments.GetLength(0) * 3 + 3];
            phi = new float[pieces.Max(p => p.profile.anchorCount)];
            return ready = true;
        }

        void Features()
        {
            var toRoot = Quaternion.Inverse(transform.rotation);
            int f = 0;
            for (int i = 0; i < Segments.GetLength(0); i++)
            {
                var d = transform.InverseTransformVector(seg[i, 2].position - seg[i, 1].position);
                var rf = toRoot * seg[i, 0].rotation;                       // parent rotation now (root space)
                var v = (segRest[i] * Quaternion.Inverse(rf) * d).normalized;  // in the parent's rest frame
                features[f++] = v.x; features[f++] = v.y; features[f++] = v.z;
            }
            // trunk: UpperChest relative to Hips, rest-relative, as a rotation vector in degrees / 90
            var ra = toRoot * hips.rotation * Quaternion.Inverse(hipsRest);
            var rc = toRoot * upperChest.rotation * Quaternion.Inverse(chestRest);
            var rd = Quaternion.Inverse(ra) * rc;
            rd.ToAngleAxis(out float angle, out Vector3 axis);
            if (angle > 180) { angle = 360 - angle; axis = -axis; }
            if (float.IsNaN(axis.x) || angle < 1e-4f) axis = Vector3.zero;
            var tv = axis * (angle / 90f);
            features[f++] = tv.x; features[f++] = tv.y; features[f++] = tv.z;
        }

        public void Apply()
        {
            if (!Init()) return;
            Features();
            foreach (var p in pieces)
            {
                var pr = p.profile; int k = pr.featureCount, A = pr.anchorCount, S = pr.shapes.Length;
                float inv = 1f / (2 * pr.sigma * pr.sigma);
                for (int a = 0; a < A; a++)
                {
                    float d = 0; int o = a * k;
                    for (int j = 0; j < k; j++) { float e = features[j] - pr.anchors[o + j]; d += e * e; }
                    phi[a] = Mathf.Exp(-d * inv);
                }
                for (int s = 0; s < S; s++)
                {
                    float w = 0;
                    for (int a = 0; a < A; a++) w += phi[a] * pr.coef[a * S + s];
                    w = Mathf.Clamp01(w);
                    if (p.shapeIndex[s] >= 0 && Mathf.Abs(w - p.weights[s]) > 1e-4f) { p.renderer.SetBlendShapeWeight(p.shapeIndex[s], 100 * w); p.weights[s] = w; }
                }
            }
        }

        void LateUpdate() => Apply();
    }
}
