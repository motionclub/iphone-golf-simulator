using UnityEngine;
using UnityEngine.Rendering;
using GolfArcade.Game;
using GolfArcade.Tennis;

namespace GolfArcade.EnvironmentArt
{
    /// Pilot pacing (golf's Luminous Coast and the dream environments): the same governor as tennis and bowling (FramePace). A ProMotion
    /// phone at 120 that cannot hold it drops to 60 for the rest of the match (it no longer goes back to 120 at the next hole, to stutter
    /// and drop again); at 60 rendering quality steps down instead. It never drops the game below 60.
    public sealed class LuminousCoastFrameBudget : MonoBehaviour
    {
        const float Grace = 8;
        readonly FrameWindow window = new FrameWindow(Grace);
        readonly PacePolicy policy = new PacePolicy();
        float calm; int generation = -1;

        void Update()
        {
            if (Application.isEditor) return;
            FramePace.Govern(this, window, policy, ref calm, ref generation, "LuminousCoast");
        }
    }
}
