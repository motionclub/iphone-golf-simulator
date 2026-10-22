using GolfArcade.Course;
using GolfArcade.EnvironmentArt;
using GolfArcade.Game;
using UnityEngine;
namespace GolfArcade.Tennis
{
    /// Conditions commit at game boundaries only. Axial drag is invariant under end swap.
    public sealed class TennisConditions : MonoBehaviour
    {
        public static Weather Weather {get; private set;}
        public static bool Active {get; private set;}
        int lastGame=-1,lastSeed;WeatherView view;DreamEnvironment environment;TennisGame game;TennisFx fx;bool ashOut;
        public static float DragFor(Weather condition)=>condition==Weather.Storm?.035f:condition==Weather.Gusty?.025f:0;
        public static float BounceFor(Weather condition,int venue)=>condition.IsWet()?(venue==2?.99f:.97f):1;
        public static int Epoch(TennisMatch match)=>match.PlayerGames+match.OpponentGames+20*(match.PlayerSets+match.OpponentSets);
        public static Weather For(int seed,int epoch,int venue)=>DreamConditions.WeatherFor(seed,epoch+venue*31);
        public static float AirDrag => Active?DragFor(Weather):0;
        public static float BounceScale => Active?BounceFor(Weather,(int)TennisVenue.Current):1;
        public static void Boundary(TennisGame game,TennisMatch? score=null)
        {
            if(!DreamEnvironment.Enabled)return;
            var c=game.GetComponent<TennisConditions>();if(!c)c=game.gameObject.AddComponent<TennisConditions>();
            c.game=game;
            var match=score??game.Match;int epoch=Epoch(match);
            if(epoch==c.lastGame && c.lastSeed==(DreamEnvironment.Session?.seed??0))return;c.lastGame=epoch;
            if(DreamEnvironment.Session==null)DreamEnvironment.StartSession(Random.Range(1,int.MaxValue));
            DreamEnvironment.CommitClockBoundary();
            c.lastSeed=DreamEnvironment.Session.seed;
            Weather=For(DreamEnvironment.Session.seed,epoch,(int)TennisVenue.Current);Active=true;DreamEnvironment.Session.epoch=epoch;
#if UNITY_EDITOR || DEVELOPMENT_BUILD
            if(System.Enum.TryParse<Weather>(System.Environment.GetEnvironmentVariable("DREAM_WEATHER"),true,out var forced))Weather=forced;
#endif
            if(!c.view)c.view=WeatherView.Create(c.transform,EventSounds.Create(c.transform));
            var camera=game.GameplayCamera;
            var hole=new Hole{Centerline=new[]{CoursePoint.Zero,new CoursePoint(0,80)},Ground=_=>0,Theme=TennisVenue.Current==TennisVenueKind.Volcano?"magma":""};
            if(c.environment){c.environment.Release();Destroy(c.environment.gameObject);}
            c.environment=DreamEnvironment.Install(game.transform,true,Weather,100+(int)TennisVenue.Current);
            c.view.Begin(camera,hole,Weather,new Wind(Weather==Weather.Storm?10:Weather==Weather.Gusty?7:2,45));
            DreamWorldArt.Tennis(game.transform,(int)TennisVenue.Current);
            DreamVisibility.Reset(); // court fog has a generous local clear envelope, never golf occlusion
        }
        public static bool CraterOutIsCosmetic(TennisVenueKind venue,Vector3 ball,bool pointEnded) => venue==TennisVenueKind.Volcano && pointEnded && (Mathf.Abs(ball.x)>TennisVenue.DeckHalfX||Mathf.Abs(ball.z)>TennisVenue.DeckHalfZ) && ball.y<=TennisRules.BallRadius;
        void LateUpdate()
        {
            if(!game)return;
            var ball=game.BallPosition;bool ended=game.Flow==TennisGame.Phase.PointOver||game.Flow==TennisGame.Phase.MatchOver;
            if(!ended||TennisVenue.OverDeck(ball)){ashOut=false;return;}
            if(!ashOut&&CraterOutIsCosmetic(TennisVenue.Current,ball,ended)){
                if(!fx)fx=game.GetComponentInChildren<TennisFx>();if(fx)fx.LavaOut(ball);ashOut=true;
            }
        }
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Reset(){Active=false;Weather=Weather.Clear;}
        void OnDestroy()=>Reset();
    }
}
