using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// HERO BUILD (2026-11-11): forearm twist. Neither rig has twist bones, so all of the hand's roll landed in the few centimetres of
    /// skin that blend forearm and hand (a wrung wrist). Three helper bones per forearm take 33 / 66 / 92 % of the hand's roll about the
    /// forearm, and every forearm vertex shares its forearm weight between the two helpers nearest its position along the limb.
    /// The last helper's name ends in "LowerArm", so HeroArmSkinning still gives the wrist its volume-preserving blend.
    /// Runs before HeroArmSkinning (order 1200). HERO_BUILD=0 or HERO_TWIST=0 switches it off.
    [DefaultExecutionOrder(1100)]
    public sealed class HeroForearmTwist : MonoBehaviour
    {
        static readonly float[] Frac = { .33f, .66f, .92f }, At = { 0f, .33f, .66f, 1f };
        readonly Transform[] hand = new Transform[2]; readonly Quaternion[] rest = new Quaternion[2]; readonly Vector3[] axis = new Vector3[2];
        readonly Transform[,] node = new Transform[2, 3]; Mesh owned;

        public static void Build(MatchHeroLook look)
        {
            if (!HeroBuild.On || System.Environment.GetEnvironmentVariable("HERO_TWIST") == "0") return;
            var body = look ? look.body : null;
            if (!body || !body.sharedMesh || !body.sharedMesh.isReadable || body.GetComponent<HeroForearmTwist>()) return;
            body.gameObject.AddComponent<HeroForearmTwist>().Initialize(body);
        }

        void Initialize(SkinnedMeshRenderer body)
        {
            var bones = new List<Transform>(body.bones); owned = Instantiate(body.sharedMesh); owned.name = body.sharedMesh.name + " (forearm twist)"; owned.hideFlags = HideFlags.DontSave;
            var binds = new List<Matrix4x4>(owned.bindposes); var w = owned.boneWeights; var v = owned.vertices; int moved = 0;
            string[] side = { "Left", "Right" };
            for (int s = 0; s < 2; s++)
            {
                int il = bones.FindIndex(b => b && b.name == side[s] + "LowerArm"), ih = bones.FindIndex(b => b && b.name == side[s] + "Hand");
                if (il < 0 || ih < 0 || bones[ih].parent != bones[il]) continue;
                var local = binds[il] * binds[ih].inverse;                                   // the hand in forearm space, in the bind pose
                hand[s] = bones[ih]; rest[s] = local.rotation; axis[s] = ((Vector3)local.GetColumn(3)).normalized;
                Vector3 E = binds[il].inverse.GetColumn(3), W = binds[ih].inverse.GetColumn(3); float len2 = (W - E).sqrMagnitude;
                var anchor = new int[4]; anchor[0] = il;
                for (int k = 0; k < 3; k++)
                {
                    var t = new GameObject(k == 2 ? $"Twist3_{side[s]}LowerArm" : $"{side[s]}LowerArmTwist{k + 1}").transform; t.SetParent(bones[il], false);
                    node[s, k] = t; anchor[k + 1] = bones.Count; bones.Add(t); binds.Add(binds[il]);
                }
                for (int i = 0; i < w.Length; i++)
                {
                    var bw = w[i]; var ids = new List<int> { bw.boneIndex0, bw.boneIndex1, bw.boneIndex2, bw.boneIndex3 }; var ws = new List<float> { bw.weight0, bw.weight1, bw.weight2, bw.weight3 };
                    float wl = 0; for (int k = 3; k >= 0; k--) if (ids[k] == il && ws[k] > 0) { wl += ws[k]; ids.RemoveAt(k); ws.RemoveAt(k); }
                    if (wl <= 0) continue;
                    float tt = Mathf.Clamp01(Vector3.Dot(v[i] - E, W - E) / len2); int seg = tt < At[1] ? 0 : tt < At[2] ? 1 : 2; float u = Mathf.InverseLerp(At[seg], At[seg + 1], tt);
                    ids.Add(anchor[seg]); ws.Add(wl * (1 - u)); ids.Add(anchor[seg + 1]); ws.Add(wl * u);
                    // the four largest, renormalised
                    for (int a = 0; a < ids.Count; a++) for (int b = a + 1; b < ids.Count; b++) if (ws[b] > ws[a]) { (ws[a], ws[b]) = (ws[b], ws[a]); (ids[a], ids[b]) = (ids[b], ids[a]); }
                    while (ids.Count < 4) { ids.Add(0); ws.Add(0); }
                    float sum = ws[0] + ws[1] + ws[2] + ws[3]; if (sum <= 0) continue;
                    w[i] = new BoneWeight { boneIndex0 = ids[0], weight0 = ws[0] / sum, boneIndex1 = ids[1], weight1 = ws[1] / sum, boneIndex2 = ids[2], weight2 = ws[2] / sum, boneIndex3 = ids[3], weight3 = ws[3] / sum };
                    moved++;
                }
            }
            if (moved == 0) { Destroy(owned); owned = null; enabled = false; return; }
            owned.boneWeights = w; owned.bindposes = binds.ToArray(); body.sharedMesh = owned; body.bones = bones.ToArray();
            Debug.Log($"[HeroForearmTwist] {body.name}: forearm vertices re-weighted={moved} bones={bones.Count}");
            LateUpdate();
        }

        void LateUpdate()
        {
            for (int s = 0; s < 2; s++)
            {
                if (!hand[s]) continue;
                var d = hand[s].localRotation * Quaternion.Inverse(rest[s]); if (d.w < 0) d = new Quaternion(-d.x, -d.y, -d.z, -d.w);
                var p = axis[s] * Vector3.Dot(new Vector3(d.x, d.y, d.z), axis[s]); var twist = new Quaternion(p.x, p.y, p.z, d.w);
                float m = Mathf.Sqrt(Quaternion.Dot(twist, twist)); twist = m > 1e-5f ? new Quaternion(twist.x / m, twist.y / m, twist.z / m, twist.w / m) : Quaternion.identity;
                for (int k = 0; k < 3; k++) if (node[s, k]) node[s, k].localRotation = Quaternion.Slerp(Quaternion.identity, twist, Frac[k]);
            }
        }
        void OnDestroy() { if (owned) { if (Application.isPlaying) Destroy(owned); else DestroyImmediate(owned); } }
    }
}
