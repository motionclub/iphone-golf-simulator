using UnityEngine;
using UnityEngine.Rendering;
using GolfArcade.Game;
using GolfArcade.Tennis;

namespace GolfArcade.EnvironmentArt
{
    /// Pilot-only pacing: when frames are repeatedly late, trade rendering quality for time
    /// (TennisQuality.StepDown) and keep the 60 fps target. It never drops the game to 30:
    /// a 30 fps draw also makes the 30 fps-keyed character clips read as stepped. A 120 Hz
    /// loop still falls back to 60. No simulation/time-scale changes.
    public sealed class LuminousCoastFrameBudget : MonoBehaviour
    {
        const float Window=2, Grace=8;
        float settle=Grace,elapsed,sinceDrawn;
        int frames,late,generation,originalDrawRate,appliedRate;
        readonly FrameBudgetPolicy policy=new();

        void Update()
        {
            if(Application.isEditor || Time.timeScale==0)return;
            if(generation!=InputRate.Generation) {
                generation=InputRate.Generation;ResetWindow();settle=Mathf.Max(settle,4);
            }
            sinceDrawn+=Time.unscaledDeltaTime;
            if(!OnDemandRendering.willCurrentFrameRender)return;
            float dt=sinceDrawn;sinceDrawn=0;
            if(settle>0){settle-=dt;return;}
            int drawRate=Mathf.Max(1,Application.targetFrameRate/Mathf.Max(1,OnDemandRendering.renderFrameInterval));
            if(originalDrawRate==0)originalDrawRate=drawRate;
            frames++;if(dt>1.25f/drawRate)late++;elapsed+=dt;
            if(elapsed<Window)return;
            int next=policy.Observe(drawRate,frames,late);
            if(next!=drawRate) {
                // Stop the optional 120 Hz input loop before choosing the draw rate;
                // otherwise its later teardown would reset the chosen target.
                InputRate.Stop();OnDemandRendering.renderFrameInterval=1;
                Application.targetFrameRate=next;appliedRate=next;settle=4;
                Debug.Log($"[LuminousCoast] sustained late frames: {drawRate} -> {next}fps; art quality retained");
            }
            else if(policy.SustainedLate && TennisQuality.StepDown()) {
                settle=4;policy.Reset();
                Debug.Log($"[LuminousCoast] sustained late frames at {drawRate}fps; reducing rendering quality, keeping the rate");
            }
            elapsed=0;frames=late=0;
        }
        void ResetWindow(){elapsed=sinceDrawn=0;frames=late=0;policy.Reset();}
        void OnDestroy()
        {
            // Native loading selects its next target before unloading this scene.
            // Do not restore over that selection, even when both targets are 60.
            var session=FindFirstObjectByType<NativeSportsSession>();
            if(session && !session.Ready)return;
            // A hole transition within the same ready session restores its target.
            if(appliedRate>0 && Application.targetFrameRate==appliedRate && OnDemandRendering.renderFrameInterval==1)
                Application.targetFrameRate=originalDrawRate;
        }
    }

    public sealed class FrameBudgetPolicy
    {
        int lateWindows;
        public bool SustainedLate=>lateWindows>=3;
        public void Reset()=>lateWindows=0;
        /// The draw rate to use after a window: a 120 Hz loop falls to 60 when it keeps missing,
        /// and 60 (or less) stays as it is -- the caller lowers quality instead (SustainedLate).
        public int Observe(int drawRate,int frames,int late)
        {
            lateWindows=frames>0 && late*100>=frames*10 ? lateWindows+1 : 0;
            if(!SustainedLate || drawRate<=60)return drawRate;
            lateWindows=0;
            return 60;
        }
    }
}
