#!/usr/bin/env python3
"""RACKET GRIP 2026-11-12: the racket-hand finger wrap may open a finger by its real bend (his curled bind pose left no room) and a
thumb that misses the handle stays lightly curled; her racket seat moves 12 mm. usage: patch_racket.py <Unity project dir>. Idempotent."""
import os, sys
S = os.path.join(sys.argv[1], 'Assets/Scripts/Tennis')

def patch(rel, pairs, marker):
    p = os.path.join(S, rel); s = open(p).read()
    if marker in s: print(rel, 'already patched'); return
    for a, b in pairs:
        if s.count(a) != 1: sys.exit(f'{rel}: anchor found {s.count(a)} times: {a[:70]}')
        s = s.replace(a, b)
    open(p, 'w').write(s); print(rel, 'patched')

patch('HeroGripPolish.cs', [
('''        const float GraspStep=2;   // degrees per closing step''',
'''        const float GraspStep=2;   // degrees per closing step
        /// RACKET GRIP 2026-11-12: a racket-hand finger may open by its real bend, and a thumb that misses the handle rests lightly curled.
        /// GRIP_WRAP_V2=0 (Editor) brings the old wrap back for A/B films.
        static bool WrapV2
        {
            get
            {
#if UNITY_EDITOR
                return System.Environment.GetEnvironmentVariable("GRIP_WRAP_V2")!="0";
#else
                return true;
#endif
            }
        }'''),
('''                    lo[j]=Mathf.Max(-35,(thumb?-25:-10)-current);hi[j]=Mathf.Max(lo[j],Mathf.Min(110,(thumb?ThumbLimit:WrapLimit)[j]-current));''',
'''                    lo[j]=Mathf.Max(-35,(thumb?-25:-10)-current);
                    // RACKET GRIP 2026-11-12: the floor above is counted from the bind pose, and a bind hand that is already curled (his) left
                    // no room to open: his fingers stayed up to 15 mm inside the handle. A finger may also open as far as its real bend now
                    // allows (straight, plus 10 degrees), measured on the bones.
                    if(!thumb&&WrapV2){
                        var hb=hero.Bone(left?HumanBodyBones.LeftHand:HumanBodyBones.RightHand);
                        Vector3 a0=j==0?(hb?joints[0].bone.position-hb.position:Vector3.zero):j==1?joints[1].bone.position-joints[0].bone.position:joints[2].bone.position-joints[1].bone.position;
                        Vector3 a1=j==0?joints[1].bone.position-joints[0].bone.position:j==1?joints[2].bone.position-joints[1].bone.position:joints[2].bone.TransformPoint(joints[2].tip)-joints[2].bone.position;
                        if(a0.sqrMagnitude>1e-10f&&a1.sqrMagnitude>1e-10f)lo[j]=Mathf.Max(-90,Mathf.Min(lo[j],-(Vector3.Angle(a0,a1)+10)));
                    }
                    hi[j]=Mathf.Max(lo[j],Mathf.Min(110,(thumb?ThumbLimit:WrapLimit)[j]-current));'''),
('''                var moving=new[]{true,true,true};''', '''                var moving=new[]{true,true,true};bool touched=false;'''),
('''                        if(hit==j)for(int k=0;k<=j;k++)moving[k]=false;''', '''                        touched=true;
                        if(hit==j)for(int k=0;k<=j;k++)moving[k]=false;'''),
('''                float b0=delta[0],b1=delta[1],b2=delta[2];''', '''                // RACKET GRIP 2026-11-12: a thumb that never meets the handle closed to its limits, tucked into the hand; it stays lightly curled instead
                if(WrapV2&&WrapDigitNames[f]=="Thumb"&&!touched&&Depth(0,delta)<=0)for(int j=0;j<3;j++)delta[j]=Mathf.Max(lo[j],delta[j]*.35f);
                float b0=delta[0],b1=delta[1],b2=delta[2];'''),
], 'RACKET GRIP 2026-11-12')

patch('HeroRacketSeat.cs', [
('''        public static Vector3 Offset(bool female) => female ? new Vector3(-.005f, 0, .005f) : new Vector3(.015f, 0, -.015f);''',
'''        /// RACKET GRIP 2026-11-12: her seat moved 12 mm (z .005 -> .017): her palm rests on the handle without sinking in and her thumb reaches
        /// it (seat sweep, work/anim-review-1112). His is unchanged: with the finger wrap able to open, his fingers close round the handle where it is.
        public static Vector3 Offset(bool female) => female ? new Vector3(-.005f, 0, .017f) : new Vector3(.015f, 0, -.015f);'''),
], 'RACKET GRIP 2026-11-12')
