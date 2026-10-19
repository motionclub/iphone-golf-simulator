using System.Linq;
using GolfArcade.CharacterLod;
using GolfArcade.Game;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// CHARACTER LOD (character-lod chat, 2026-10-17): the invariants HeroLod relies on. LOD meshes only ever reference original
    /// vertices (same skin weights / blendshapes / normals / UVs), the compacted copies carry those vertices byte for byte, and the
    /// level bands keep close-ups on the original renderers.
    public sealed class CharacterLodTests
    {
        [Test]
        public void BandsKeepCloseUpsOnTheOriginalMeshes()
        {
            Assert.AreEqual(0, HeroLod.Band(.95f), "a close-up must stay on LOD0");
            Assert.AreEqual(0, HeroLod.Band(HeroLod.Bands[0]), "the close-up edge itself is LOD0");
            Assert.AreEqual(2, HeroLod.Band(.39f), "golf tee view (~0.39 of the screen height)");
            Assert.AreEqual(HeroLod.Levels - 1, HeroLod.Band(.005f), "a few-pixel hero takes the last level");
            for (int i = 1; i < HeroLod.Bands.Length; i++) Assert.Less(HeroLod.Bands[i], HeroLod.Bands[i - 1], "bands descend");
            for (int l = 1; l < HeroLod.Levels; l++) { Assert.Less(HeroLod.Ratio[l], HeroLod.Ratio[l - 1]); Assert.Greater(HeroLod.MaxError[l], HeroLod.MaxError[l - 1]); }
        }

        [Test]
        public void ShippedCacheDecodes()
        {
            var (entries, ok) = HeroLodCache.Validate();
            Assert.IsTrue(ok, "Resources/CharacterLOD/HeroLodCache.bytes has a malformed entry");
            TestContext.WriteLine($"cache entries: {entries} (0 = no cache shipped: heroes compute their LODs at runtime)");
        }

        static SkinnedMeshRenderer BiggestGarment()
        {
            var kit = Resources.Load<GameObject>(HeroAssets.GolfKitPrefab(false));
            Assert.IsNotNull(kit, "golf kit prefab");
            return kit.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r => r.sharedMesh && r.sharedMesh.isReadable)
                .OrderByDescending(r => r.sharedMesh.triangles.Length).First();
        }

        [Test]
        public void SimplifiedTrianglesReferenceOnlyOriginalVertices()
        {
            var mesh = BiggestGarment().sharedMesh;
            var input = HeroLodLibrary.Extract(mesh, null);
            int before = input.submeshes.Sum(s => s.Length) / 3;
            for (int l = 1; l < HeroLod.Levels; l++)
            {
                var r = HeroLodSimplifier.Simplify(input, HeroLod.Ratio[l], HeroLod.MaxError[l]);
                Assert.LessOrEqual(r.maxError, HeroLod.MaxError[l] + 1e-6, "level " + l + " error budget");
                Assert.Less(r.triangles, before, "level " + l + " drops triangles");
                Assert.AreEqual(mesh.subMeshCount, r.submeshes.Length);
                foreach (var sub in r.submeshes)
                    for (int i = 0; i < sub.Length; i += 3)
                    {
                        Assert.That(sub[i] >= 0 && sub[i] < mesh.vertexCount && sub[i + 1] < mesh.vertexCount && sub[i + 2] < mesh.vertexCount);
                        Assert.That(sub[i] != sub[i + 1] && sub[i + 1] != sub[i + 2] && sub[i] != sub[i + 2], "no degenerate triangles");
                    }
            }
        }

        [Test]
        public void CompactedLodCarriesTheOriginalVertexData()
        {
            var mesh = BiggestGarment().sharedMesh;
            var r = HeroLodSimplifier.Simplify(HeroLodLibrary.Extract(mesh, null), .3, .0035);
            var lod = HeroLodLibrary.Compact(mesh, r.submeshes);
            try
            {
                var v0 = mesh.vertices; var n0 = mesh.normals; var u0 = mesh.uv;
                var v1 = lod.vertices; var n1 = lod.normals; var u1 = lod.uv;
                var per0 = mesh.GetBonesPerVertex().ToArray(); var all0 = mesh.GetAllBoneWeights().ToArray();
                var per1 = lod.GetBonesPerVertex().ToArray(); var all1 = lod.GetAllBoneWeights().ToArray();
                int[] Start(byte[] per) { var st = new int[per.Length + 1]; for (int i = 0; i < per.Length; i++) st[i + 1] = st[i] + per[i]; return st; }
                var s0 = Start(per0); var s1 = Start(per1);
                Assert.AreEqual(mesh.bindposes.Length, lod.bindposes.Length);
                Assert.AreEqual(mesh.blendShapeCount, lod.blendShapeCount);
                Assert.AreEqual(mesh.name, lod.name, "MatchHeroLook.IsKitV2 reads the name");
                for (int s = 0; s < mesh.subMeshCount; s++)
                {
                    var a = r.submeshes[s]; var b = lod.GetTriangles(s);
                    Assert.AreEqual(a.Length, b.Length);
                    for (int i = 0; i < a.Length; i++)
                    {
                        Assert.AreEqual(v0[a[i]], v1[b[i]]); Assert.AreEqual(n0[a[i]], n1[b[i]]);
                        if (u0.Length > 0) Assert.AreEqual(u0[a[i]], u1[b[i]]);
                        if (per0.Length > 0)
                        {
                            Assert.AreEqual(per0[a[i]], per1[b[i]], "bones per vertex");
                            for (int k = 0; k < per0[a[i]]; k++)
                            {
                                var x = all0[s0[a[i]] + k]; var y = all1[s1[b[i]] + k];
                                Assert.AreEqual(x.boneIndex, y.boneIndex, $"bone index, vertex {a[i]} slot {k}");
                                Assert.AreEqual(x.weight, y.weight, 1e-6f, $"bone weight, vertex {a[i]} slot {k}");
                            }
                        }
                    }
                }
            }
            finally { Object.DestroyImmediate(lod); }
        }
    }
}
