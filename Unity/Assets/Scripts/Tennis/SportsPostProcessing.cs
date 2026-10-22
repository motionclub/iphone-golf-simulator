using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.Tennis
{
    /// One owned volume per gameplay camera. Tier changes preserve tone mapping;
    /// only the expensive glow is dropped on Low.
    [DisallowMultipleComponent]
    public sealed class SportsPostProcessing : MonoBehaviour
    {
        public Volume Volume { get; private set; }
        Bloom bloom;
        DepthOfField dof;
        bool requestedDof;
        int lookRevision=-1;
        public void Initialize(Volume volume)
        {
            Volume = volume;
            Volume.profile.TryGet(out bloom);
            Volume.profile.TryGet(out dof);
            requestedDof=dof && dof.active;
            Refresh();
        }
        public void RequestDepthOfField(bool on)
        {
            requestedDof=on;Refresh();
        }
        void LateUpdate() => Refresh();
        void Refresh()
        {
            if (bloom) bloom.active = TennisQuality.Current != TennisQuality.Tier.Low;
            if (dof) dof.active=requestedDof && TennisQuality.Current==TennisQuality.Tier.High;
            if(Volume && lookRevision!=GolfArcade.EnvironmentArt.EnvironmentLook.Revision) {
                lookRevision=GolfArcade.EnvironmentArt.EnvironmentLook.Revision;
                GolfArcade.EnvironmentArt.EnvironmentLook.Post(Volume.profile);
            }
        }
        void OnDestroy()
        {
            if (!Volume || !Volume.profile) return;
            foreach (var component in Volume.profile.components) if (component) Destroy(component);
            Destroy(Volume.profile);
        }
    }
}
