using System;
using System.IO;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Local pose corrections for the new female garments. The neutral body, skeleton
    /// and clips stay intact. Full chest-relative arm rotations retain axial twist.
    [DefaultExecutionOrder(1215), DisallowMultipleComponent]
    public sealed class FemaleShoulderFit : MonoBehaviour
    {
        [Serializable] sealed class Anchor { public int side; public float[] rotation; }
        [Serializable] sealed class Profile { public Anchor[] anchors; }
        MatchHeroLook look;
        Transform chest;
        readonly Transform[] upper = new Transform[2], lower = new Transform[2];
        readonly Vector3[] down = new Vector3[2];
        Profile profile;
        Quaternion[] rotations;
        int[] shapes;
        Mesh owned, prepared;
        public static void Attach(MatchHeroLook hero)
        {
            if (!hero || !hero.female || hero.GetComponent<FemaleShoulderFit>()) return;
            var fit = hero.gameObject.AddComponent<FemaleShoulderFit>(); fit.look = hero;
        }
        bool Init()
        {
            if (owned && look && look.body && prepared == look.body.sharedMesh) return true;
            // Accessories and a golf-hand switch can rebuild the coverage mesh.
            // A derived copy retains these shape indices; a fresh cover needs them again.
            if (owned && look && look.body && look.body.sharedMesh && look.body.sharedMesh.GetBlendShapeIndex("FemaleShoulderFit_0") >= 0)
            { prepared = look.body.sharedMesh; return true; }
            if (!look || !look.body || !look.body.sharedMesh) return false;
            string resource = (look.golfKit ? "Golf" : "Tennis") + "/KitsV2/Female/FemaleShoulderFit";
            var bytes = Resources.Load<TextAsset>(resource);
            var json = Resources.Load<TextAsset>(resource + "Profile");
            if (!bytes || !json) return false;
            profile = JsonUtility.FromJson<Profile>(json.text);
            var body = look.body; var source = body.sharedMesh;
            chest = look.Bone(HumanBodyBones.Chest);
            upper[0] = look.Bone(HumanBodyBones.LeftUpperArm); upper[1] = look.Bone(HumanBodyBones.RightUpperArm);
            lower[0] = look.Bone(HumanBodyBones.LeftLowerArm); lower[1] = look.Bone(HumanBodyBones.RightLowerArm);
            if (!chest || !upper[0] || !upper[1] || !lower[0] || !lower[1]) return false;
            using var r = new BinaryReader(new MemoryStream(bytes.bytes));
            int vertices = r.ReadInt32(), active = r.ReadInt32(), count = r.ReadInt32();
            if (vertices != source.vertexCount || count != profile.anchors.Length) throw new InvalidDataException("Female shoulder correction topology mismatch");
            var indices = new int[active]; for (int i = 0; i < active; i++) indices[i] = r.ReadInt32();
            var previousOwned = owned;
            owned = Instantiate(source); owned.name = source.name + " (female shoulder fit)"; owned.hideFlags = HideFlags.DontSave;
            shapes = new int[count]; rotations = new Quaternion[count];
            var previous = new float[source.blendShapeCount]; for (int i = 0; i < previous.Length; i++) previous[i] = body.GetBlendShapeWeight(i);
            for (int k = 0; k < count; k++)
            {
                var dp = new Vector3[vertices]; var dn = new Vector3[vertices];
                for (int i = 0; i < active; i++) dp[indices[i]] = new Vector3(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
                for (int i = 0; i < active; i++) dn[indices[i]] = new Vector3(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
                string name = "FemaleShoulderFit_" + k;
                owned.AddBlendShapeFrame(name, 100, dp, dn, null); shapes[k] = owned.GetBlendShapeIndex(name);
                var q = profile.anchors[k].rotation; rotations[k] = new Quaternion(q[0], q[1], q[2], q[3]);
            }
            body.sharedMesh = owned; prepared = owned;
            if (previousOwned) { if (Application.isPlaying) Destroy(previousOwned); else DestroyImmediate(previousOwned); }
            for (int i = 0; i < previous.Length; i++) body.SetBlendShapeWeight(i, previous[i]);
            var bind = source.bindposes; int ci = Array.IndexOf(body.bones, chest);
            for (int side = 0; side < 2; side++)
            {
                var sh = bind[Array.IndexOf(body.bones, upper[side])].inverse.GetColumn(3);
                var el = bind[Array.IndexOf(body.bones, lower[side])].inverse.GetColumn(3);
                down[side] = bind[ci].MultiplyVector(el - sh).normalized;
            }
            return true;
        }
        public void Apply()
        {
            if (!Init()) return;
            for (int i = 0; i < shapes.Length; i++) look.body.SetBlendShapeWeight(shapes[i], 0);
            for (int side = 0; side < 2; side++)
            {
                var q = Quaternion.Inverse(chest.rotation) * upper[side].rotation;
                float elevation = Vector3.Angle(down[side], chest.InverseTransformDirection(lower[side].position - upper[side].position));
                float fade = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(35, 70, elevation));
                int a = -1, b = -1; float da = float.MaxValue, db = float.MaxValue;
                for (int k = 0; k < shapes.Length; k++) if (profile.anchors[k].side == side)
                {
                    float dot = Quaternion.Dot(q, rotations[k]); float d = Mathf.Max(0, 1 - dot * dot);
                    if (d < da) { b = a; db = da; a = k; da = d; } else if (d < db) { b = k; db = d; }
                }
                if (a < 0) continue;
                float blend = b < 0 ? 0 : da / Mathf.Max(1e-8f, da + db);
                look.body.SetBlendShapeWeight(shapes[a], 100 * fade * (1 - blend));
                if (b >= 0) look.body.SetBlendShapeWeight(shapes[b], 100 * fade * blend);
            }
        }
        void LateUpdate() => Apply();
        void OnDestroy() { if (owned) { if (Application.isPlaying) Destroy(owned); else DestroyImmediate(owned); } }
    }
}
