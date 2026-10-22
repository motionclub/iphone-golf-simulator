using System.Linq;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    public class FemaleDeformationTests
    {
        [Test]
        public void ShoulderRepairPreservesTheExactNeutralSurfaceAndNormalizedWeights()
        {
            var prefab=Resources.Load<GameObject>("Tennis/OriginalSeamBlinkFinish/Female");
            var body=prefab.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r=>r.name=="Body");
            var original=body.sharedMesh;var repaired=HeroShoulderWeights.Prepare(body);
            CollectionAssert.AreEqual(original.vertices,repaired.vertices);
            CollectionAssert.AreEqual(original.normals,repaired.normals);
            CollectionAssert.AreEqual(original.triangles,repaired.triangles);
            CollectionAssert.AreEqual(original.bindposes,repaired.bindposes);
            CollectionAssert.AreEqual(original.uv,repaired.uv);
            foreach(var w in repaired.boneWeights)Assert.That(w.weight0+w.weight1+w.weight2+w.weight3,Is.EqualTo(1).Within(.00001f));
            Assert.AreSame(original,body.sharedMesh,"The imported source must remain untouched.");
        }

        [Test]
        public void NeutralSkirtAndUnderShortsKeepTheirOriginalBinding()
        {
            var prefab=TennisCustomization.HeroBase(true);
            var source=prefab.GetComponent<MatchHeroLook>().kit.First(r=>r&&r.name=="Kit_Bottom").sharedMesh;
            var go=Object.Instantiate(prefab);
            try {
                var look=go.GetComponent<MatchHeroLook>();look.SetSkin(look.skinTone);
                var skirt=look.kit.First(r=>r&&r.name=="Kit_Bottom");
                CollectionAssert.AreEqual(source.vertices,skirt.sharedMesh.vertices);
                CollectionAssert.AreEqual(source.boneWeights,skirt.sharedMesh.boneWeights);
                CollectionAssert.AreEqual(source.triangles,skirt.sharedMesh.triangles);
            } finally {Object.DestroyImmediate(go);}
        }

        [Test]
        public void BackhandAndServeContactTransformsStayExact()
        {
            var go=Object.Instantiate(TennisCustomization.HeroBase(true));
            try {
                var look=go.GetComponent<MatchHeroLook>();look.SetSkin(look.skinTone);
                var driver=go.GetComponent<HeroTennisDriver>();driver.ResolvePerformanceClips();
                var safety=new HeroPoseSafety(look);
                foreach(var id in new[]{HeroTennisDriver.Clip.Backhand,HeroTennisDriver.Clip.BackhandWide,HeroTennisDriver.Clip.Serve}) {
                    var slot=driver.slots.First(s=>s.id==id);slot.clip.SampleAnimation(go,slot.contact);
                    var hand=look.Bone(HumanBodyBones.RightHand);var p=hand.position;var q=hand.rotation;
                    var left=look.Bone(HumanBodyBones.LeftHand);var lp=left.position;
                    safety.Apply(true,id==HeroTennisDriver.Clip.Serve,0,id!=HeroTennisDriver.Clip.Serve);
                    Assert.That(Vector3.Distance(p,hand.position),Is.LessThan(.00001f),id+" racket contact");
                    Assert.That(Quaternion.Angle(q,hand.rotation),Is.LessThan(.05f));
                    if(id!=HeroTennisDriver.Clip.Serve)Assert.That(Vector3.Distance(lp,left.position),Is.LessThan(.00001f));
                }
            } finally {Object.DestroyImmediate(go);}
        }

        [Test]
        public void WaveWristDoesNotHyperextendOrMoveTheHandAnchor()
        {
            var go=Object.Instantiate(TennisCustomization.HeroBase(true));
            try {
                var look=go.GetComponent<MatchHeroLook>();look.SetSkin(look.skinTone);
                var driver=go.GetComponent<HeroTennisDriver>();driver.ResolvePerformanceClips();
                var clip=driver.slots.First(s=>s.id==HeroTennisDriver.Clip.IntroWave).clip;var safety=new HeroPoseSafety(look);
                var hand=look.Bone(HumanBodyBones.LeftHand);var lower=look.Bone(HumanBodyBones.LeftLowerArm);var middle=look.Bone(HumanBodyBones.LeftMiddleProximal);
                for(int frame=0;frame<=60;frame++) {
                    clip.SampleAnimation(go,clip.length*frame/60f);var p=hand.position;safety.RelaxWaveWrist();
                    Assert.That(Vector3.Distance(p,hand.position),Is.LessThan(.00001f));
                    safety.Apply(false);p=hand.position;safety.LimitWaveWristFlexion();
                    Assert.That(Vector3.Distance(p,hand.position),Is.LessThan(.00001f));
                    Assert.That(Vector3.Angle(middle.position-hand.position,hand.position-lower.position),Is.LessThanOrEqualTo(55.01f));
                }
            } finally {Object.DestroyImmediate(go);}
        }
    }
}
