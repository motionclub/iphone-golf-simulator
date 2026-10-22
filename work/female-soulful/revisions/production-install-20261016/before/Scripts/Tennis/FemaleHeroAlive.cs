using System;
using System.Collections.Generic;
using GolfArcade.Game;
using GolfArcade.Course;
using UnityEngine;
using Unity.Profiling;

namespace GolfArcade.Tennis
{
    /// Small cosmetic layer for the female only. Source meshes, rig, clips, gameplay and
    /// cameras remain authoritative. Two garment morph weights per piece, no frame vertex loops.
    [DefaultExecutionOrder(1120), DisallowMultipleComponent]
    public sealed class FemaleHeroAlive : MonoBehaviour
    {
        public const float SkirtTravel = .010f, TopTravel = .005f;
        public MatchHeroLook Look { get; private set; }
        public float IdleWeight { get; private set; }
        public Vector2 HeadDegrees => gaze;
        public float ClothWeight => pieces.Count == 0 ? 0 : pieces[0].spring.x;
        public int GarmentCount => pieces.Count;
        static readonly ProfilerMarker TickMarker = new("FemaleHeroAlive.Tick");
        Transform chest, spine, head, hips;
        HeroTennisDriver tennis; GolferView golfer; GolfGame golf;
        MatchHeroFacePerformance face;
        Vector2 gaze, gazeVelocity;
        float clock, resultAge;
        GolfGame.State lastGolfState;
        bool ownsMood;
        readonly List<Piece> pieces = new();
        sealed class Piece
        {
            public SkinnedMeshRenderer renderer;
            public Mesh source, mesh;
            public Transform anchor, leftArm, rightArm;
            public Vector3 lastPosition, lastVelocity;
            public Quaternion lastRotation, lastLeftArm, lastRightArm;
            public Vector2 spring, velocity;
            public int left, right;
            public bool sampled;
        }

        public static bool EnabledFor(MatchHeroLook look) => look && look.female;
        public static void Attach(MatchHeroLook look)
        {
            if (!EnabledFor(look) || look.GetComponent<FemaleHeroAlive>()) return;
#if UNITY_EDITOR
            if (Environment.GetEnvironmentVariable("FEMALE_ALIVE") == "0") return;
#endif
            look.gameObject.AddComponent<FemaleHeroAlive>().Initialize(look);
        }
        void Initialize(MatchHeroLook look)
        {
            Look = look; chest = look.Bone(HumanBodyBones.Chest); spine = look.Bone(HumanBodyBones.Spine);
            head = look.Bone(HumanBodyBones.Head); hips = look.Bone(HumanBodyBones.Hips);
            face = look.GetComponent<MatchHeroFacePerformance>();
            if (look.kit == null) return;
            foreach (var r in look.kit)
            {
                if (!r || !r.sharedMesh || !MatchHeroLook.IsKitV2(r.sharedMesh)) continue;
                bool bottom = r.name == "Kit_Bottom";
                if (!bottom && r.name != "Kit_Top") continue;
                var p = new Piece { renderer = r, source = r.sharedMesh, anchor = bottom ? hips : chest };
                if (!p.anchor || !p.source.isReadable) continue;
                if (!bottom) { p.leftArm=look.Bone(HumanBodyBones.LeftUpperArm);p.rightArm=look.Bone(HumanBodyBones.RightUpperArm); }
                var map = look.transform.worldToLocalMatrix * r.transform.localToWorldMatrix;
                p.mesh = BuildClothMorphs(p.source, map, bottom);
                p.left = p.mesh.GetBlendShapeIndex("Alive_Left");p.right = p.mesh.GetBlendShapeIndex("Alive_Right");
                r.sharedMesh = p.mesh; pieces.Add(p);
            }
        }

        // Outward radial displacements keep inner/outer hem walls together. Zero at the
        // waist/collar; never pulls a garment toward skin. All values are in hero metres.
        public static Mesh BuildClothMorphs(Mesh source, Matrix4x4 toHero, bool skirt)
        {
            var mesh = Instantiate(source);mesh.name = source.name + " (female alive)";mesh.hideFlags = HideFlags.DontSave;
            var v = source.vertices;var left = new Vector3[v.Length];var right = new Vector3[v.Length];
            float low = float.MaxValue, high = float.MinValue, halfWidth = 0;
            foreach (var vertex in v) { var q=toHero.MultiplyPoint3x4(vertex);low=Mathf.Min(low,q.y);high=Mathf.Max(high,q.y);halfWidth=Mathf.Max(halfWidth,Mathf.Abs(q.x)); }
            var inverse=toHero.inverse;
            for (int i=0;i<v.Length;i++)
            {
                var q=toHero.MultiplyPoint3x4(v[i]);float height=Mathf.InverseLerp(low,high,q.y);
                float hem=1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(skirt?.12f:0,skirt?.62f:.24f,height));
                float sleeve=skirt?0:Mathf.SmoothStep(0,1,Mathf.InverseLerp(.58f,.90f,Mathf.Abs(q.x)/Mathf.Max(.01f,halfWidth)))
                    *(1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(.78f,.96f,height)));
                float mask=Mathf.Max(hem,sleeve);
                var radial=new Vector3(q.x,0,q.z);if(radial.sqrMagnitude<.00001f)continue;
                var delta=inverse.MultiplyVector(radial.normalized*(skirt?SkirtTravel:TopTravel)*mask);
                float side=Mathf.SmoothStep(0,1,Mathf.InverseLerp(-.04f,.04f,q.x));
                left[i]=delta*(1-side);right[i]=delta*side;
            }
            mesh.AddBlendShapeFrame("Alive_Left",100,left,null,null);
            mesh.AddBlendShapeFrame("Alive_Right",100,right,null,null);
            var bounds=mesh.bounds;bounds.Expand(.03f);mesh.bounds=bounds;
            return mesh;
        }

        void LateUpdate()
        {
            using (TickMarker.Auto()) Tick();
        }
        void Tick()
        {
            if (!EnabledFor(Look) || Time.deltaTime<=0) return;
            float dt=Mathf.Min(Time.deltaTime,1f/30);clock+=dt;
            if (!tennis && !Look.golfKit) tennis=GetComponentInParent<HeroTennisDriver>();
            if (!golfer && Look.golfKit) { golfer=GetComponentInParent<GolferView>();golf=FindFirstObjectByType<GolfGame>(); }
            // Replays restore already posed bones; applying an additive layer again would accumulate.
            if (tennis && tennis.game && tennis.game.ReplayPlaying || golf && golf.Replaying) return;
            bool idle=false;
            if (tennis && tennis.actor)
            {
                bool betweenPoints=tennis.game&&(tennis.game.Flow is TennisGame.Phase.PointOver or TennisGame.Phase.MatchOver);
                idle=(tennis.CurrentAction is HeroTennisDriver.Clip.Ready or HeroTennisDriver.Clip.Idle)
                    &&!tennis.actor.Swinging&&(betweenPoints||tennis.actor.PrepareAmount<.01f&&!tennis.actor.PrepareServe)
                    &&Mathf.Abs(tennis.actor.Speed)+Mathf.Abs(tennis.actor.ForwardSpeed)<.15f
                    &&!(tennis.game&&tennis.game.DiveActive);
            }
            else if(golfer) idle=golfer.AliveAtRest;
            // Contact poses get no additional body offset, including the first load frame.
            IdleWeight=idle?Mathf.MoveTowards(IdleWeight,1,dt*3):0;
            if(IdleWeight>0 && chest && spine)
            {
                float breath=Mathf.Sin(clock*1.48f)+.18f*Mathf.Sin(clock*2.21f+.7f);
                float sway=Mathf.Sin(clock*.62f)+.28f*Mathf.Sin(clock*1.13f+1.7f);
                chest.rotation=Quaternion.AngleAxis(breath*.75f*IdleWeight,transform.right)*chest.rotation;
                spine.rotation=Quaternion.AngleAxis(sway*.5f*IdleWeight,transform.forward)*spine.rotation;
                if(head)head.rotation=Quaternion.AngleAxis(-sway*.3f*IdleWeight,transform.forward)*head.rotation;
            }
            UpdateAttention(dt);
            foreach(var p in pieces) TickCloth(p,dt);
        }

        void UpdateAttention(float dt)
        {
            if(!face)face=GetComponent<MatchHeroFacePerformance>();
            if(tennis && face)
            {
                bool wave=tennis.CurrentAction==HeroTennisDriver.Clip.IntroWave;
                if(wave){face.ForcedMood=MatchHeroFacePerformance.Mood.Happy;ownsMood=true;}
                else if(ownsMood){face.ForcedMood=MatchHeroFacePerformance.Mood.None;ownsMood=false;}
                return; // Existing tennis eye / head tracker retains ownership.
            }
            if(!golfer||!golf||!head||!face)return;
            bool performing=!string.IsNullOrEmpty(golfer.Performing)&&golfer.Performing!="Idle";
            if(golf.Current!=lastGolfState){resultAge=0;lastGolfState=golf.Current;}else resultAge+=dt;
            bool result=golf.Current is GolfGame.State.Result or GolfGame.State.HoleDone or GolfGame.State.RoundDone;
            if(!performing)
            {
                var mood=MatchHeroFacePerformance.Mood.None;
                if(result&&resultAge<1.6f&&golf.LastShot!=null)
                    mood=golf.LastShot.IsHoled?MatchHeroFacePerformance.Mood.Happy:
                        golf.LastShot.PenaltyStrokes>0||golf.ClubInHand==GolfArcade.Shot.GolfClub.Putter
                            ||golf.LastShot.Lie is CourseLie.Rough or CourseLie.Bunker?MatchHeroFacePerformance.Mood.Sad:
                        MatchHeroFacePerformance.Mood.Happy;
                face.ForcedMood=mood;ownsMood=true;
            }
            else { ownsMood=false; } // GolferView's authored emote mood owns this interval.
            Vector2 wanted=Vector2.zero;
            if(!performing)
            {
                Vector3 target=golf.BallPosition;
                // At address keep eyes on the ball, with a brief pin check between breaths.
                if(golfer.AliveAtRest&&golf.CurrentHole!=null && clock%6.7f>4.9f)
                    target=HoleView.ToWorld(golf.CurrentHole.Pin)+Vector3.up*.35f;
                var local=transform.InverseTransformDirection(target-head.position);
                wanted=new Vector2(Mathf.Clamp(Mathf.Atan2(local.x,Mathf.Max(.15f,local.z))*Mathf.Rad2Deg,-16,16),
                    Mathf.Clamp(-Mathf.Atan2(local.y,new Vector2(local.x,local.z).magnitude)*Mathf.Rad2Deg,-8,10));
                face.ForcedGaze=new Vector2(wanted.x/16,-wanted.y/10)*.0018f;
                // Eyes update now; the head follows a slower critically damped target.
                if(!golfer.AliveAtRest&&golf.Current!=GolfGame.State.Flight)wanted=Vector2.zero;
            }
            else face.ForcedGaze=Vector2.zero;
            gaze=Vector2.SmoothDamp(gaze,wanted,ref gazeVelocity,.23f,90,dt);
            if(!performing)head.rotation=Quaternion.AngleAxis(gaze.x,transform.up)*Quaternion.AngleAxis(gaze.y,transform.right)*head.rotation;
        }

        void TickCloth(Piece p,float dt)
        {
            if(!p.renderer||!p.anchor||p.renderer.sharedMesh!=p.mesh)return;
            var pos=p.anchor.position;var rot=p.anchor.rotation;
            if(!p.sampled){p.lastPosition=pos;p.lastRotation=rot;p.sampled=true;
                if(p.leftArm)p.lastLeftArm=p.leftArm.rotation;if(p.rightArm)p.lastRightArm=p.rightArm.rotation;}
            var velocity=(pos-p.lastPosition)/dt;
            // Teleports, scene setup and replay jumps should not kick the fabric.
            bool jump=(pos-p.lastPosition).sqrMagnitude>.25f;
            var acceleration=jump?Vector3.zero:(velocity-p.lastVelocity)/dt;
            float turn=jump?0:Quaternion.Angle(p.lastRotation,rot)/dt;
            var local=transform.InverseTransformDirection(acceleration);
            float energy=Mathf.Clamp01(acceleration.magnitude*.012f+turn*.002f);
            float bias=Mathf.Clamp(local.x*.012f,-.28f,.28f);
            float rest=.055f+.045f*Mathf.Sin(clock*1.48f+(p.anchor==hips?.7f:0));
            float armLeft=!jump&&p.leftArm?Quaternion.Angle(p.lastLeftArm,p.leftArm.rotation)/dt*.0015f:0;
            float armRight=!jump&&p.rightArm?Quaternion.Angle(p.lastRightArm,p.rightArm.rotation)/dt*.0015f:0;
            Vector2 target=new Vector2(Mathf.Clamp01(rest+energy+bias+armLeft),Mathf.Clamp01(rest+energy-bias+armRight));
            if(jump){p.spring=Vector2.zero;p.velocity=Vector2.zero;velocity=Vector3.zero;}
            // Stable substeps, mild underdamping: garment carries on after the pose stops.
            int steps=Mathf.Max(1,Mathf.CeilToInt(dt*120));float h=dt/steps;
            for(int i=0;i<steps;i++){
                p.velocity+=(target-p.spring)*(90*h)-p.velocity*(13*h);
                p.spring+=p.velocity*h;
                p.spring=new Vector2(Mathf.Clamp01(p.spring.x),Mathf.Clamp01(p.spring.y));
            }
            p.renderer.SetBlendShapeWeight(p.left,p.spring.x*100);p.renderer.SetBlendShapeWeight(p.right,p.spring.y*100);
            p.lastPosition=pos;p.lastVelocity=velocity;p.lastRotation=rot;
            if(p.leftArm)p.lastLeftArm=p.leftArm.rotation;if(p.rightArm)p.lastRightArm=p.rightArm.rotation;
        }
        void OnDisable()
        {
            foreach(var p in pieces)if(p.renderer&&p.renderer.sharedMesh==p.mesh){p.renderer.SetBlendShapeWeight(p.left,0);p.renderer.SetBlendShapeWeight(p.right,0);}
            if(face&&ownsMood)face.ForcedMood=MatchHeroFacePerformance.Mood.None;
            if(face&&Look&&Look.golfKit)face.ForcedGaze=Vector2.zero;
        }
        void OnDestroy()
        {
            foreach(var p in pieces){if(p.renderer&&p.renderer.sharedMesh==p.mesh)p.renderer.sharedMesh=p.source;if(p.mesh)Destroy(p.mesh);}
        }
    }
}
