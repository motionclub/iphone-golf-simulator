using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.Tests
{
    /// FRAME_RATE_60B: 60 fps at 1080p or more. The quality step-down may drop effects but never the resolution,
    /// and nothing asks for a frame rate under 60.
    public class FrameRate60bEditTests
    {
        [Test] public void StepDownNeverLowersTheResolution()
        {
            var shared = UnityEngine.Rendering.GraphicsSettings.defaultRenderPipeline as UniversalRenderPipelineAsset;
            if (!shared) Assert.Ignore("no URP pipeline asset in this project");
            var urp = Object.Instantiate(shared);
            float shadow = QualitySettings.shadowDistance, lod = QualitySettings.lodBias;
            try
            {
                urp.renderScale = 1; urp.msaaSampleCount = 4; urp.shadowDistance = 60; urp.shadowCascadeCount = 2; QualitySettings.lodBias = 1.2f;
                int steps = 0;
                while (steps < 20 && TennisQuality.StepDown(urp)) { steps++; Assert.That(urp.renderScale, Is.EqualTo(1f), "step " + steps + " changed the render scale"); }
                Assert.That(steps, Is.GreaterThanOrEqualTo(4), "the step-down still has effects to give up");
                Assert.That(urp.shadowDistance, Is.GreaterThanOrEqualTo(TennisQuality.MinShadowDistance - .01f));
                Assert.That(urp.msaaSampleCount, Is.EqualTo(1));
            }
            finally { Object.DestroyImmediate(urp); QualitySettings.shadowDistance = shadow; QualitySettings.lodBias = lod; }
        }

        [Test] public void EveryTargetIsAtLeastSixty()
        {
            Assert.That(FrameRate.Target(60, 60), Is.EqualTo(60));
            Assert.That(FrameRate.Target(120, 60), Is.EqualTo(60));
            Assert.That(FrameRate.Target(120, 120), Is.EqualTo(120));
            Assert.That(FrameRate.Target(0, 120), Is.EqualTo(60));
            int old = Application.targetFrameRate;
            try { Application.targetFrameRate = -1; FrameRate.Lift(); Assert.That(Application.targetFrameRate, Is.EqualTo(60));
                  Application.targetFrameRate = 30; FrameRate.Lift(); Assert.That(Application.targetFrameRate, Is.EqualTo(60));
                  Application.targetFrameRate = 120; FrameRate.Lift(); Assert.That(Application.targetFrameRate, Is.EqualTo(120)); }
            finally { Application.targetFrameRate = old; }
        }
    }
}
