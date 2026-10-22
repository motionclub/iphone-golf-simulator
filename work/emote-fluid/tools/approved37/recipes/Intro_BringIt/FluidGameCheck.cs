using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
[InitializeOnLoad] public static class FluidGameCheck {
 const BindingFlags B=BindingFlags.Instance|BindingFlags.NonPublic; const string Flag="FluidGameCheck"; static IEnumerator script;
 static FluidGameCheck(){EditorApplication.update+=Tick;}
 public static void Run(){EditorSettings.enterPlayModeOptionsEnabled=true;EditorSettings.enterPlayModeOptions=EnterPlayModeOptions.DisableDomainReload;EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");SessionState.SetBool(Flag,true);EditorApplication.isPlaying=true;}
 static void Tick(){if(!SessionState.GetBool(Flag,false)||!EditorApplication.isPlaying)return;var g=Object.FindFirstObjectByType<TennisGame>();if(!g||!g.Initialized)return;if(script==null)script=Go(g);try{if(!script.MoveNext())Done(0);}catch(Exception e){Debug.LogException(e);Done(1);}}
 static void Done(int c){SessionState.SetBool(Flag,false);Time.captureFramerate=0;if(Application.isBatchMode)EditorApplication.Exit(c);else EditorApplication.isPlaying=false;}
 static string Hash(string path){using(var sha=SHA256.Create())return BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-","").ToLowerInvariant();}
 static string F(float x)=>x.ToString("R",CultureInfo.InvariantCulture);
 static string V(Vector3 p)=>F(p.x)+";"+F(p.y)+";"+F(p.z);
 static Vector3[] Positions(TennisGame g,HeroTennisDriver d){var root=g.Player.transform;return new[]{root.InverseTransformPoint(d.matchLook.Bone(HumanBodyBones.Head).position),root.InverseTransformPoint(d.matchLook.Bone(HumanBodyBones.LeftHand).position),root.InverseTransformPoint(d.matchLook.Bone(HumanBodyBones.RightHand).position)};}
 static IEnumerator Go(TennisGame g){
 string dir=Path.GetFullPath(Environment.GetEnvironmentVariable("FG_OUT")??"../work/emote-fluid/proof/in_game");Directory.CreateDirectory(dir);bool female=Environment.GetEnvironmentVariable("FG_FEMALE")=="1";string sex=female?"female":"male",rival=female?"Viktor":"Nadia";
 Time.captureFramerate=60;g.AutoPlay=false;g.ManualSimulation=false;TennisGame.AutoPlayTimingJitter=0;
 var pres=g.GetComponent<TennisPresentation>();if(pres)pres.Finish();g.SelectCharacter(female);g.ConfigureMatch(TennisGame.Mode.Campaign,rival,rival,"FLUIDITY CHECK",1,6);if(pres)pres.Finish();
 for(int j=0;j<90;j++)yield return null;
 string[] files={"Emote_Scuba","Emote_Thrust","Emote_Spike","Intro_Wave","Intro_BringIt","Intro_Pushups"};
 string[] clips={"EmoteScuba","EmoteThrust","EmoteSpike","IntroWave","IntroBringIt","IntroPushups"};float[] lengths={4.7f,3.5f,3.2f,2,3,3};var results=new List<string>();
 for(int c=0;c<clips.Length;c++){
  if(c>=3){g.ConfigureMatch(TennisGame.Mode.Campaign,rival,rival,"FLUIDITY CHECK",1,6);if(pres)pres.Finish();for(int j=0;j<90;j++)yield return null;}
  if(c<3){typeof(TennisGame).GetProperty("Flow").GetSetMethod(true).Invoke(g,new object[]{TennisGame.Phase.PointOver});typeof(TennisGame).GetField("resetTimer",B).SetValue(g,10000f);g.Player.Prepare(0,false);g.Opponent.Prepare(0,false);g.Player.ReachTossHand(Vector3.zero,0);g.Opponent.ReachTossHand(Vector3.zero,0);for(int j=0;j<60;j++)yield return null;}
  var d=g.Player.GetComponentInChildren<HeroTennisDriver>();var old=Positions(g,d);int played=d.EmotesPlayed;float timer=0,t0=Time.time,end=-1,next=-1;bool seen=false;int guard=0;var samples=new List<Vector3[]>();var times=new List<float>();var ct=new List<float>();var rows=new List<string>{"sample,elapsed,clipTime,active,flow,head,leftHand,rightHand"};
  if(c<3){typeof(TennisGame).GetProperty("Flow").GetSetMethod(true).Invoke(g,new object[]{TennisGame.Phase.Rally});typeof(TennisGame).GetField("resetTimer",B).SetValue(g,0f);g.Player.Prepare(0,false);g.Opponent.Prepare(0,false);Debug.Log("[FluidGameCheck] pre-award state="+d.State+" swing="+g.Player.Swinging+" lastKey="+typeof(HeroTennisDriver).GetField("lastGameKey",B).GetValue(d)+" games="+g.Match.PlayerGames);var mf=typeof(TennisGame).GetField("match",B);object m=mf.GetValue(g);typeof(TennisMatch).GetField("PlayerPoints").SetValue(m,3);typeof(TennisMatch).GetField("OpponentPoints").SetValue(m,0);mf.SetValue(g,m);HeroTennisDriver.PickedTaunt=c;typeof(TennisGame).GetMethod("AwardPoint",B).Invoke(g,new object[]{true,true});timer=(float)typeof(TennisGame).GetField("resetTimer",B).GetValue(g);}
  else{d.IntroPick=c-3;foreach(string flag in new[]{"rivalEmoted","playerEmoted","umpireCalled"})typeof(TennisPresentation).GetField(flag,B).SetValue(pres,false);typeof(TennisPresentation).GetField("t",B).SetValue(pres,0f);}
  samples.Add(old);times.Add(-1f/60);ct.Add(0);rows.Add("0,"+F(-1f/60)+",0,false,pre-trigger,"+V(old[0])+","+V(old[1])+","+V(old[2]));
  while(guard++<60*30){yield return null;if(!seen&&!d.EmoteActive){old=Positions(g,d);continue;}if(!seen){seen=true;t0=Time.time;samples[0]=old;}
   float elapsed=Time.time-t0;var p=Positions(g,d);samples.Add(p);times.Add(elapsed);ct.Add(d.PlayingClipTime);rows.Add((samples.Count-1)+","+F(elapsed)+","+F(d.PlayingClipTime)+","+d.EmoteActive+","+g.Flow+","+V(p[0])+","+V(p[1])+","+V(p[2]));
   if(end<0&&!d.EmoteActive)end=elapsed;if(c<3&&next<0&&(g.Flow==TennisGame.Phase.PlayerServeHold||g.Flow==TennisGame.Phase.OpponentServe))next=elapsed;
   if(end>=0&&elapsed>=end+.2f&&(c>=3||next>=0))break;
  }
  float worst=0;int frame=-1,bone=-1;float at=-1;
  for(int j=1;j<samples.Count;j++){bool edge=ct[j]<=.15f&&times[j]<=.3f||end>=0&&times[j]>=end-.15f&&times[j]<=end+.15f;if(!edge)continue;for(int b=0;b<3;b++){float step=Vector3.Distance(samples[j][b],samples[j-1][b])*1000;if(step>worst){worst=step;frame=j;bone=b;at=times[j];}}}
  bool started=seen&&d.EmotesPlayed==played+1&&d.LastEmotePlayed==clips[c];bool covered=c>=3||end>0&&next>=end-.02f&&timer>2.4f;bool ok=started&&end>0&&covered&&worst<=30;
  string row="{\"hero\":\""+sex+"\",\"clip\":\""+clips[c]+"\",\"entry\":\""+(c<3?"AwardPoint/EmoteHoldCheck game-win sequence":"TennisPresentation.Drive match-start sequence")+"\",\"started\":"+started.ToString().ToLower()+",\"ended_s\":"+F(end)+",\"next_point_s\":"+F(next)+",\"serve_timer_s\":"+F(timer)+",\"serve_covers_taunt\":"+covered.ToString().ToLower()+",\"blend_max_mm\":"+F(worst)+",\"frame60\":"+frame+",\"bone_index_head_left_right\":"+bone+",\"elapsed_s\":"+F(at)+",\"limit_mm\":30,\"ok\":"+ok.ToString().ToLower()+"}";
  string title=female?"Female":"Male";string asset="Assets/Characters/MatchHeroes/"+title+"/"+title+"_"+files[c]+".fbx";row=row.Substring(0,row.Length-1)+",\"fbx_sha256\":\""+Hash(asset)+"\",\"meta_sha256\":\""+Hash(asset+".meta")+"\"}";
  results.Add(row);File.WriteAllText(dir+"/"+sex+"_"+clips[c]+".csv",string.Join("\n",rows)+"\n");Debug.Log("[FluidGameCheck] "+row);if(pres)pres.Finish();HeroTennisDriver.PickedTaunt=-1;
 }
 File.WriteAllText(dir+"/"+sex+".json","[\n"+string.Join(",\n",results)+"\n]\n");
 }
}
}
