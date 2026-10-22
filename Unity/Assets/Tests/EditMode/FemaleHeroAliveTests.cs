using System;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;
namespace GolfArcade.Tests
{
    public sealed class FemaleHeroAliveTests
    {
        [Test]
        public void MaleNeverGetsAnAliveComponent()
        {
            var go=new GameObject("male guard");go.SetActive(false);
            try {
                var look=go.AddComponent<MatchHeroLook>();look.female=false;
                Assert.That(FemaleHeroAlive.EnabledFor(look),Is.False);
                FemaleHeroAlive.Attach(look);
                Assert.That(go.GetComponent<FemaleHeroAlive>(),Is.Null);
            } finally {Object.DestroyImmediate(go);}
        }
        [TestCase("Tennis/Customization/PlayerFemale",false)]
        [TestCase("Tennis/Customization/PlayerFemaleGolfKit",true)]
        public void RealGarmentsKeepSourceBindingsAndBoundedOutwardMotion(string path,bool golf)
        {
            var prefab=Resources.Load<GameObject>(path);Assert.That(prefab,Is.Not.Null);
            var look=prefab.GetComponent<MatchHeroLook>();int count=0;
            foreach(var r in look.kit) {
                if(r.name!="Kit_Top"&&r.name!="Kit_Bottom")continue;
                var source=r.sharedMesh;var original=source.vertices;
                var map=look.transform.worldToLocalMatrix*r.transform.localToWorldMatrix;
                bool bottom=r.name=="Kit_Bottom";
                var mesh=FemaleHeroAlive.BuildClothMorphs(source,map,bottom);
                try {
                    Assert.That(mesh.vertices,Is.EqualTo(original));Assert.That(source.vertices,Is.EqualTo(original));
                    Assert.That(mesh.bindposes,Is.EqualTo(source.bindposes));Assert.That(mesh.boneWeights,Is.EqualTo(source.boneWeights));
                    Assert.That(mesh.subMeshCount,Is.EqualTo(source.subMeshCount));
                    for(int sub=0;sub<source.subMeshCount;sub++)Assert.That(mesh.GetTriangles(sub),Is.EqualTo(source.GetTriangles(sub)));
                    Assert.That(mesh.blendShapeCount,Is.EqualTo(source.blendShapeCount+2));
                    float maximum=0;int moving=0,pinned=0;
                    var a=new Vector3[mesh.vertexCount];var b=new Vector3[mesh.vertexCount];
                    mesh.GetBlendShapeFrameVertices(mesh.GetBlendShapeIndex("Alive_Left"),0,a,null,null);
                    mesh.GetBlendShapeFrameVertices(mesh.GetBlendShapeIndex("Alive_Right"),0,b,null,null);
                    for(int i=0;i<a.Length;i++) {
                        var delta=map.MultiplyVector(a[i]+b[i]);var p=map.MultiplyPoint3x4(original[i]);
                        maximum=Mathf.Max(maximum,delta.magnitude);
                        Assert.That(Vector3.Dot(new Vector3(p.x,0,p.z),delta),Is.GreaterThanOrEqualTo(-1e-7));
                        Assert.That(Mathf.Abs(delta.y),Is.LessThan(1e-6));
                        if(delta.magnitude>.0001f)moving++;else pinned++;
                    }
                    Assert.That(maximum,Is.InRange(.001f,(bottom?FemaleHeroAlive.SkirtTravel:FemaleHeroAlive.TopTravel)+1e-5f));
                    Assert.That(moving,Is.GreaterThan(100));Assert.That(pinned,Is.GreaterThan(100));
                    TestContext.WriteLine($"{path}/{r.name}: vertices={mesh.vertexCount} maxOutward={maximum:F6}m moving={moving} pinned={pinned}");
                    count++;
                } finally {Object.DestroyImmediate(mesh);}
            }
            Assert.That(count,Is.EqualTo(2));
        }
    }
}
