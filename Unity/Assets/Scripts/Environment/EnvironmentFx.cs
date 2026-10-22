using UnityEngine;
using GolfArcade.Course;

namespace GolfArcade.EnvironmentArt
{
    /// Palette/coverage recipes consumed by existing confirmed-event pools.
    /// Event selection, particle timing, audio, haptics and camera feedback stay owned by gameplay.
    public static class EnvironmentFx
    {
        public static bool Active=>EnvironmentLook.Stage>=6;
        // The native preference already reaches this policy (also used for
        // thermal/Low presentation). Keep core feedback, reduce decorative motion.
        public static bool Reduced=>Active && GolfArcade.Game.PresentationPolicy.Constrained;
        public static int ParticleCount(int count)=>Reduced?(count+2)/3:count;
        // Keep every caller's random draws; thinning only the emission avoids
        // changing the shared Unity random sequence used outside presentation.
        public static int ParticleAt(int index)=>Reduced && index%3!=0?0:1;
        public static float MotionScale=>Reduced?.45f:1f;
        public static Color Impact(Color color,bool charged)
        {
            if(!Active)return color;
            color.a=Mathf.Min(color.a,charged?.68f:.58f);return color;
        }
        public static void Landing(CourseLie lie,ref Color a,ref Color b)
        {
            if(!Active)return;
            switch(lie) {
                case CourseLie.Green: a=new(.62f,.78f,.31f,.75f);b=new(.36f,.53f,.22f,.65f);break;
                case CourseLie.Rough:case CourseLie.OutOfBounds: a=new(.35f,.49f,.24f,.75f);b=new(.48f,.39f,.26f,.65f);break;
                case CourseLie.Bunker:a=new(.88f,.78f,.59f,.78f);b=new(.67f,.55f,.38f,.64f);break;
                case CourseLie.Ice:a=new(.87f,.96f,1f,.85f);b=new(.48f,.72f,.91f,.7f);break;
                default:a.a=.75f;b.a=.65f;break;
            }
        }
    }
}
