from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/full-visual-overhaul/tennis/motion11';w.mkdir(exist_ok=True)
f=r/'Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs';s=f.read_text()
s=s.replace('readonly float[] upperBlend = new float[Count]; float upperFade;','AvatarMask strokeUpperMask,reactionUpperMask;bool usingReactionMask;\n        float reactionLegShare;public float ReactionLegShare => reactionLegShare;\n        readonly float[] upperBlend = new float[Count]; float upperFade;')
s=s.replace('if (!IsStroke((Clip)i)) continue;','if (!IsStroke((Clip)i) && !(Match&&IsReaction((Clip)i))) continue;')
s=s.replace('''            layers.SetLayerMaskFromAvatarMask(1, upper);''','''            strokeUpperMask=upper;
            if(Match){reactionUpperMask=new AvatarMask();UpperBodyMask(reactionUpperMask,false);}
            layers.SetLayerMaskFromAvatarMask(1, upper);''',1)
s=s.replace('void UpperBodyMask(AvatarMask mask)','void UpperBodyMask(AvatarMask mask,bool includeHips=true)')
s=s.replace('paths.Add(PathOf(Bone(HumanBodyBones.Hips)));','if(includeHips)paths.Add(PathOf(Bone(HumanBodyBones.Hips)));')
s=s.replace('''        void OnDestroy()''','''        static bool IsReaction(Clip c) => c>=Clip.HitPerfect&&c<=Clip.MatchLose;
        void SetUpperMask(bool reaction)
        {
            if(!Match||usingReactionMask==reaction)return;
            usingReactionMask=reaction;layers.SetLayerMaskFromAvatarMask(1,reaction?reactionUpperMask:strokeUpperMask);
        }
        void OnDestroy()''',1)
s=s.replace('''            graph.Evaluate(0);
            if(!Match){PostProcess(true,true);return;}''','''            SetUpperMask(false);
            graph.Evaluate(0);
            if(!Match){PostProcess(true,true);return;}''')
s=s.replace('''            float fullAction = FluidOff ? actionWeight''','''            bool movingReaction=Match&&juiceActive&&!actionActive&&IsReaction(juice);
            reactionLegShare=Mathf.MoveTowards(reactionLegShare,movingReaction?Mathf.SmoothStep(0,1,Mathf.InverseLerp(.15f,.7f,move)):0,dt/.10f);
            float fullAction = FluidOff ? actionWeight''')
s=s.replace('''            if (fullAction > 0)''','''            if(movingReaction)fullAction*=1-reactionLegShare;
            if (fullAction > 0)''',1)
s=s.replace('''                // the stroke that just ended keeps''','''                // A short reaction rides real walk/run legs during repositioning;
                // its approved full-body performance returns once planted.
                if(movingReaction&&reactionLegShare>.001f)
                {upperW=actionWeight*reactionLegShare;upperFade=upperW;upperFadeClip=(int)juice;}
                else
                // the stroke that just ended keeps''',1)
s=s.replace('''else if (juiceActive && id == juice) time[k] = Math.Max(0, juiceTime);''','''else if (juiceActive && id == juice) {time[k]=Math.Max(0,juiceTime);if(upperPlayables[k].IsValid())upperPlayables[k].SetTime(time[k]);}''')
s=s.replace('''int wantUp = actionActive && IsStroke(action) ? (int)action : upperFadeClip;''','''int wantUp = movingReaction ? (int)juice : actionActive && IsStroke(action) ? (int)action : upperFadeClip;''')
s=s.replace('''            layers.SetInputWeight(1, upperW); UpperLayerWeight = upperW;''','''            SetUpperMask(!actionActive&&IsReaction((Clip)upperFadeClip));
            layers.SetInputWeight(1, upperW); UpperLayerWeight = upperW;''')
s=s.replace('''            if (Match && juiceActive && IsEmote(juice))''','''            if(Match&&reactionLegShare>.85f&&Moving()>.5f)
            {for(int f=0;f<2;f++){locked[f]=false;lockW[f]=0;stepping[f]=false;}return true;}
            if (Match && juiceActive && IsEmote(juice))''')
# Lift the pelvis before solving landing feet/brace, keeping the whole shape above court.
s=s.replace('''            // A grounded scissor shape replaces''','''            float clearance=Mathf.Max(0,actor.transform.position.y+.31f*reach-hips.position.y);
            if(head)clearance=Mathf.Max(clearance,actor.transform.position.y+.15f*reach-head.position.y);
            hips.position+=Vector3.up*clearance;
            // A grounded scissor shape replaces''')
s=s.replace('hipLocal.x+(trailing?-side*.32f:side*.15f), .10f+(trailing?.07f:0),hipLocal.z+(trailing?-.40f:.19f)','hipLocal.x+(trailing?-side*.42f:side*.26f), .10f+(trailing?.07f:0),hipLocal.z+(trailing?-.50f:.34f)')
(w/'HeroTennisDriver.cs').write_text(s)
print('Motion11 stage: above-floor pelvis/head in dive, wider lead/trailing landing footprint, short-reaction upper layer over authored moving feet')
