from pathlib import Path
import json,difflib,numpy as np
R=Path.cwd();W=R/'work/reference-rebuild/forehand-pole1';S=R/'Unity/Assets/Scripts/Tennis';O=W/'candidate';O.mkdir(exist_ok=True)
# Authored local normal change: retain the original normal basis, add only the
# geometric difference introduced by this fixed waist shape.
p=json.loads((W/'MaleForehandOpenWaist.json').read_text());can=json.loads((R/'proof/reference-rebuild/character-motion-matrices17/poses/male_intro.json').read_text())['parts'][1];v=np.array(can['vertices']).reshape(-1,3);t=np.array(can['triangles']).reshape(-1,3);d=np.zeros_like(v);d[np.array(p['indices'])]=np.array(p['deltas']).reshape(-1,3)
def normals(v):
 n=np.zeros_like(v);face=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]])
 for k in range(3):np.add.at(n,t[:,k],face)
 return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
dn=normals(v+d)-normals(v);changed=np.where((np.linalg.norm(d,axis=1)>1e-6)|(np.linalg.norm(dn,axis=1)>1e-6))[0];p['indices']=changed.tolist();p['deltas']=d[changed].ravel().tolist();p['normalDeltas']=dn[changed].ravel().tolist();(O/'MaleForehandOpenWaist.json').write_text(json.dumps(p,separators=(',',':')))
name='HeroTennisDriver.cs';src=(S/name).read_text();s=src
# Place correction after all hand contact/recovery work, before garments.
old='''                    juiceActive && IsEmote(juice), juiceActive && !IsEmote(juice), Time.deltaTime);

        }'''
new='''                    juiceActive && IsEmote(juice), juiceActive && !IsEmote(juice), Time.deltaTime);
            float poseTime = physicsSubstep && actor && actor.Swinging
                ? StrokeTime((int)action, actor.SignedTimeToContact) : (float)actionTime;
            ApplyOpenForehandClearance(actionActive ? action : Clip.Ready, poseTime,
                actionActive ? Mathf.Max(actionWeight, UpperLayerWeight) : 0);

        }'''
assert old in s;s=s.replace(old,new,1)
old='''            if (cosmetics) cosmetics.SetCelebrating(c == Clip.CelebratePoint || c == Clip.MatchWin);
            FinalizeGarments();'''
new='''            if (cosmetics) cosmetics.SetCelebrating(c == Clip.CelebratePoint || c == Clip.MatchWin);
            ApplyOpenForehandClearance(c, t, 1);
            FinalizeGarments();'''
assert old in s;s=s.replace(old,new,1)
insert='''        // The male open forehand folds its forearm through the right waist at
        // contact. Swivel the elbow about the unchanged shoulder-to-wrist axis;
        // restore the wrist orientation so every finger and racket socket stays
        // on the exact original contact transform. Only this authored clip window
        // receives the correction; the matching sparse shirt fit is finalized later.
        void ApplyOpenForehandClearance(Clip clip, float poseTime, float blend)
        {
            if (!Match || matchLook.female || matchLook.golfKit) return;
            if (!garmentCorrectives) garmentCorrectives = matchLook.GetComponent<HeroGarmentPoseCorrectives>();
            float relative = poseTime - contact[(int)Clip.ForehandOpen];
            float window = 1 - Mathf.SmoothStep(0, 1, Mathf.Clamp01(Mathf.Abs(relative) / .16f));
            float amount = clip == Clip.ForehandOpen && !(isPlayer && game && game.DiveActive)
                ? window * Mathf.Clamp01(blend) : 0;
            if (garmentCorrectives) garmentCorrectives.OpenForehandWaist = amount;
            if (amount <= .00001f) return;
            var upper = Bone(HumanBodyBones.RightUpperArm);
            var lower = Bone(HumanBodyBones.RightLowerArm);
            var hand = Bone(HumanBodyBones.RightHand);
            if (!upper || !lower || !hand) return;
            var axis = hand.position - upper.position;
            if (axis.sqrMagnitude < .000001f) return;
            var handRotation = hand.rotation;
            var lowerRotation = lower.rotation;
            var swivel = Quaternion.AngleAxis(60f * amount, axis.normalized);
            upper.rotation = swivel * upper.rotation;
            lower.rotation = swivel * lowerRotation;
            hand.rotation = handRotation;
        }

'''
anchor='''        public float ContactOf(Clip c) => contact[(int)c];''';assert anchor in s;s=s.replace(anchor,insert+anchor,1);(O/name).write_text(s);(W/(name+'.patch')).write_text(''.join(difflib.unified_diff(src.splitlines(True),s.splitlines(True),fromfile='a/Unity/Assets/Scripts/Tennis/'+name,tofile='b/Unity/Assets/Scripts/Tennis/'+name)))
name='HeroGarmentPoseCorrectives.cs';src=(S/name).read_text();s=src
old='''  const string Prefix="TailoredSleeve_";''';new='''  [Serializable] public sealed class SparseWaistFit { public int vertexCount;public int[] indices;public float[] deltas,normalDeltas; }
  const string OpenWaistShape="MaleForehandOpenWaist";
  public float OpenForehandWaist { get; set; }
  static SparseWaistFit openWaist;
  static bool openWaistLoaded;
  int openWaistIndex=-1;
  const string Prefix="TailoredSleeve_";''';assert old in s;s=s.replace(old,new,1)
old='''   prepared[(src,hero.female)]=result;''';new='''   if(!hero.female){
    if(!openWaistLoaded){var text=Resources.Load<TextAsset>("Tennis/Correctives/MaleForehandOpenWaist");openWaist=text?JsonUtility.FromJson<SparseWaistFit>(text.text):null;openWaistLoaded=true;}
    if(openWaist!=null){
     if(openWaist.vertexCount!=p.vertexCount||openWaist.deltas?.Length!=openWaist.indices.Length*3||openWaist.normalDeltas?.Length!=openWaist.deltas.Length)throw new InvalidOperationException("Invalid open-forehand waist fit");
     var sourceD=new Vector3[p.vertexCount];var sourceN=new Vector3[p.vertexCount];
     for(int k=0;k<openWaist.indices.Length;k++){int j=openWaist.indices[k];if(j<0||j>=p.vertexCount)throw new InvalidOperationException("Invalid open-forehand waist vertex");sourceD[j]=new Vector3(openWaist.deltas[k*3],openWaist.deltas[k*3+1],openWaist.deltas[k*3+2]);sourceN[j]=new Vector3(openWaist.normalDeltas[k*3],openWaist.normalDeltas[k*3+1],openWaist.normalDeltas[k*3+2]);}
     var dv=new Vector3[positions.Length];var dn=new Vector3[positions.Length];
     for(int i=0;i<dv.Length;i++){int j=transfer[i];if(j<0)continue;dv[i]=sourceD[j];dn[i]=sourceN[j];}
     result.AddBlendShapeFrame(OpenWaistShape,100,dv,dn,null);
    }
   }
   prepared[(src,hero.female)]=result;''';assert old in s;s=s.replace(old,new,1)
old='''indices=profile.anchors.Select(a=>previous.GetBlendShapeIndex(Prefix+a.shape)).ToArray();}''';new='''indices=profile.anchors.Select(a=>previous.GetBlendShapeIndex(Prefix+a.shape)).ToArray();openWaistIndex=previous.GetBlendShapeIndex(OpenWaistShape);}''';assert old in s;s=s.replace(old,new,1)
old='''   if(!Init())return;
   for(int i=0;i<8;i++)''';new='''   if(!Init())return;
   if(openWaistIndex>=0)top.SetBlendShapeWeight(openWaistIndex,Mathf.Clamp01(OpenForehandWaist)*100);
   for(int i=0;i<8;i++)''';assert old in s;s=s.replace(old,new,1)
(O/name).write_text(s);(W/(name+'.patch')).write_text(''.join(difflib.unified_diff(src.splitlines(True),s.splitlines(True),fromfile='a/Unity/Assets/Scripts/Tennis/'+name,tofile='b/Unity/Assets/Scripts/Tennis/'+name)))
print('Candidate authored in',O,'position vertices',int((np.linalg.norm(d,axis=1)>1e-6).sum()),'sparse attributes',len(changed))
