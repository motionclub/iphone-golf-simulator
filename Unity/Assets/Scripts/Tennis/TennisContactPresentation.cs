using UnityEngine;

namespace GolfArcade.Tennis
{
    // Physics runs at 120 Hz; the rendered rig is finalized at order 1000.
    // Flush once after that rig so a later physics substep cannot erase the
    // contact, and the ring and ball use the same displayed string position.
    [DefaultExecutionOrder(1100)]
    public sealed class TennisContactPresentation : MonoBehaviour
    {
        public TennisGame game;
        void LateUpdate() { if (game) game.FlushContactPresentation(); }
    }
}
