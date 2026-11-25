using System.Linq;
using GolfArcade.Game;
using NUnit.Framework;
using UnityEngine;
namespace GolfArcade.Tests {
    public class PartyCosmeticsTests {
        [Test] public void UnknownIdsCannotBecomeResourcePaths() {
            Assert.AreEqual("standard",PartyCosmetics.ValidClub("../../Hero/golfer_m"));
            Assert.AreEqual("standard",PartyCosmetics.ValidBall(null));
            Assert.AreEqual("standard",PartyCosmetics.ValidExtra("extra.missing"));
        }
        [Test] public void EveryStyleHasFourClubsOnBothExactRigs() {
            foreach(var id in PartyCosmetics.Clubs) foreach(var sex in new[]{"Male","Female"}) {
                var original=Resources.Load<GameObject>("Golf/Equipment/"+sex);
                var item=Resources.Load<GameObject>("Golf/Equipment/Party/"+id.Substring(6)+"/"+sex);
                Assert.IsNotNull(item,id+sex);
                var variants=item.GetComponentsInChildren<SkinnedMeshRenderer>(true);
                Assert.AreEqual(4,variants.Length);
                foreach(var r in variants) {
                    var src=original.GetComponentsInChildren<SkinnedMeshRenderer>(true).Single(x=>x.name==r.name);
                    Assert.LessOrEqual(r.sharedMesh.triangles.Length/3,16000);
                    var actualBounds=ClubBounds(r);var expectedBounds=ClubBounds(src);
                    int lengthAxis=0;for(int axis=1;axis<3;axis++)if(expectedBounds.size[axis]>expectedBounds.size[lengthAxis])lengthAxis=axis;
                    for(int axis=0;axis<3;axis++) {
                        Assert.GreaterOrEqual(actualBounds.min[axis],expectedBounds.min[axis]-.001f,id+sex+r.name+" lower envelope");
                        Assert.LessOrEqual(actualBounds.max[axis],expectedBounds.max[axis]+.001f,id+sex+r.name+" upper envelope");
                    }
                    Assert.Less(Mathf.Abs(actualBounds.min[lengthAxis]-expectedBounds.min[lengthAxis]),.001f,id+sex+r.name+" sole length");
                    Assert.Less(Mathf.Abs(actualBounds.max[lengthAxis]-expectedBounds.max[lengthAxis]),.001f,id+sex+r.name+" butt length");
                    var standardPoints=ClubPoints(src);var visualPoints=ClubPoints(r);
                    foreach(var point in standardPoints.Where(v=>v.magnitude<.159f)) {
                        float nearest=float.PositiveInfinity;foreach(var visual in visualPoints)nearest=Mathf.Min(nearest,(visual-point).sqrMagnitude);
                        Assert.Less(Mathf.Sqrt(nearest),.0002f,id+sex+r.name+" original grip vertex moved");
                    }
                    var binds=src.bones.Select((b,i)=>(b.name,src.sharedMesh.bindposes[i])).ToDictionary(x=>x.name,x=>x.Item2);
                    for(int i=0;i<r.bones.Length;i++) {
                        Assert.IsTrue(binds.ContainsKey(r.bones[i].name));
                        var a=binds[r.bones[i].name];var b=r.sharedMesh.bindposes[i];
                        for(int row=0;row<4;row++)for(int col=0;col<4;col++)Assert.Less(Mathf.Abs(a[row,col]-b[row,col]),.0002f,id+sex+r.name);
                    }
                    Assert.IsEmpty(item.GetComponentsInChildren<Collider>(true),"Cosmetic cannot change collision");
                    for(int material=0;material<r.sharedMaterials.Length;material++) {
                        if(!r.sharedMaterials[material].name.StartsWith("Party_caramel"))continue;
                        var uv=r.sharedMesh.uv;Assert.AreEqual(r.sharedMesh.vertexCount,uv.Length,"Wood needs real UVs");
                        Assert.Greater(r.sharedMesh.GetTriangles(material).Select(v=>uv[v]).Distinct().Count(),20,"Poly Haven wood cannot sample one constant texel");
                    }
                }
            }
        }
        static Vector3[] ClubPoints(SkinnedMeshRenderer r) {
            int club=System.Array.FindIndex(r.bones,b=>b.name=="Club");var bind=r.sharedMesh.bindposes[club];
            return r.sharedMesh.vertices.Select(v=>bind.MultiplyPoint3x4(v)).ToArray();
        }
        static Bounds ClubBounds(SkinnedMeshRenderer r) {
            int club=System.Array.FindIndex(r.bones,b=>b.name=="Club");Assert.GreaterOrEqual(club,0);
            var bind=r.sharedMesh.bindposes[club];var vertices=r.sharedMesh.vertices;
            var bounds=new Bounds(bind.MultiplyPoint3x4(vertices[0]),Vector3.zero);
            foreach(var v in vertices)bounds.Encapsulate(bind.MultiplyPoint3x4(v));return bounds;
        }
        [Test] public void BallPatternsAndSourceDetailsExistOffline() {
            foreach(var id in PartyCosmetics.Balls){var map=PartyCosmetics.BallTexture(id);Assert.IsNotNull(map,id);Assert.AreEqual(512,map.width);}
            foreach(var name in new[]{"woven","leather","metal"})Assert.IsNotNull(Resources.Load<Texture2D>("Cosmetics/Cosmetic_"+name));
        }
    }
}
