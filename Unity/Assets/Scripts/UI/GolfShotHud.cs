using GolfArcade.Course;
using GolfArcade.Shot;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// Small shared broadcast vocabulary: distance, club, wind, and matching power/landing colours.
    /// The map positions come from GolfGame's actual launch simulation, never screen estimates.
    /// The wind is an arrow (which way it blows, against the aim: up the screen is helping) and
    /// its speed; the lie has its own chip under the shot info — what the ball sits in and what
    /// that costs the club in hand.
    public sealed class GolfShotHud : MonoBehaviour
    {
        public static readonly Vector2 MapSize = new Vector2(360,440);
        public static readonly Color Ink = UiKit.Hex("10243D", .96f);
        public static readonly Color Mint = UiKit.Hex("D7F044");
        public static readonly Color[] Stops = { new(.52f,.85f,1), new(.5f,.95f,.78f), new(1,.88f,.42f), new(1,.61f,.36f) };
        Camera view; Canvas canvas; CanvasScaler scaler;
        Text hole, distance, club, wind, contact, liveYards, clubChange, lieName, lieCost;
        string[] clubYardStrings;
        RectTransform clubRoot, windArrow, lieRoot;
        Image lieSwatch; Image[] lieMarks = new Image[3];
        GolfMapPath projection;
        GolfClub? selectedClub; float clubChangedAt;
        RawImage mapImage; RectTransform infoRoot, mapRoot, meterRoot, contactRoot;
        RectTransform ball, pin, live;
        readonly RectTransform[] targets = new RectTransform[4];
        readonly RectTransform[] targetBadges = new RectTransform[4];
        readonly Text[] targetLabels = new Text[4];
        RectTransform liveBadge; Text liveLabel;
        // The glass layout, in canvas units at the 1920x1080 reference (the mock-ups' own numbers).
        const float Margin = 24, InfoWidth = 320, InfoHeight = 156, LieWidth = 320, LieHeight = 70, LieTallHeight = 92;
        // the power meter: a slim glass strip, or in the clear style a big bar that is the thing to look at
        static float MeterWidth => S(80, 128);
        static float MeterHeight => S(304, 470);
        static float RailW => S(16, 44);
        static float RailH => S(208, 330);
        static float RailY => S(44, 84);
        static float RailX => (MeterWidth - RailW) / 2;
        static float RailRim => S(5, 8);
        static float SweetW => RailW + S(12, 20);
        static float FillInset => S(3, 6);
        static float PearlOuter => S(26, 58);
        static float PearlInner => S(20, 44);
        const float ClubWidth = 340, ClubHeight = 114, TileW = 96, TileH = 60, TileGap = 8;
        static readonly Vector2 MapPanel = new(268, 372);
        bool flight, lieSet;
        float lieHeight = LieHeight;
        RectTransform meterSweet; Image meterFill, pearlRing, pearlCore;
        // the clear meter: four coloured bands (the same colours as the landing marks on the map), a labelled marker at the
        // end of each, and flames that build with the power
        readonly Image[] bandFills = new Image[4];
        readonly RectTransform[] markers = new RectTransform[4];
        readonly Text[] markerLabels = new Text[4];
        readonly Image[] markerDots = new Image[4];
        const int SideFlames = 10;
        Image flameGlow; RectTransform flameBack, flameFront;
        readonly Image[] sideOuter = new Image[SideFlames * 2];
        readonly Image[] crownOuter = new Image[3];
        float powerLoad, shownLoad;
        readonly System.Collections.Generic.List<Image> meterTicks = new();
        float[] checkpointLoads;
        struct ClubTile { public GlassGraphic bg; public Text abbr, name; }
        readonly ClubTile[] clubTiles = new ClubTile[3];
        readonly GolfClub[] tileClubs = new GolfClub[3];
        ThemedGraphic windTint, windArrowTint, lieCostTint;
        // the clear style's wind meter, top right beside the shot map: a round dial with a big arrow turned the way the wind
        // blows (up the screen helps), its speed under it and what that does to the shot in words
        RectTransform windDial; Text windCalm, windWords;
        // the clear style's club card: the club's picture, its name and carry, a dot a club
        RawImage clubPicture; Text clubName, clubYards; Image[] clubDots; Image meterSweetRim;
        static readonly string[] ClubPictures = { "Clubs/driver_toon", "Clubs/iron_toon", "Clubs/wedge_toon", "Clubs/putter_toon" };
        static Texture2D[] clubPictures;
        static readonly Color ArrowBlue = UiKit.Hex("2A84E6");
        // the lettering has no card to sit on in the clear style, so the small type is a little bigger
        static int S(int glass, int clear) => GlassKit.ClearStyle ? clear : glass;
        public static GolfShotHud Create(Camera camera)
        {
            var go = new GameObject("Golf broadcast",typeof(RectTransform));
            var h=go.AddComponent<GolfShotHud>();h.view=camera;
            h.canvas=UiKit.Canvas(go);h.canvas.renderMode=RenderMode.ScreenSpaceCamera;h.canvas.worldCamera=camera;h.canvas.planeDistance=.6f;h.canvas.sortingOrder=35;
            h.scaler=go.GetComponent<CanvasScaler>();h.scaler.referenceResolution=new Vector2(1920,1080);h.scaler.matchWidthOrHeight=1;
            // Hole card, top left: hole and par, the distance, the club and the wind.
            var info=GlassKit.Panel(go.transform,"Shot info",new Vector2(0,1),new Vector2(Margin,-Margin),new Vector2(InfoWidth,InfoHeight));
            h.infoRoot=info;
            h.hole=GlassKit.Label(info,"Hole",S(19,22),GlassKit.SemiBold,ThemeRole.PanelTextMuted,TextAnchor.UpperLeft,new Vector2(24,18),new Vector2(272,26));
            h.distance=GlassKit.Label(info,"Distance",60,GlassKit.Regular,ThemeRole.PanelText,TextAnchor.UpperLeft,new Vector2(22,38),new Vector2(280,74));
            h.club=GlassKit.Label(info,"Club",S(20,24),GlassKit.SemiBold,ThemeRole.PanelText,TextAnchor.UpperLeft,new Vector2(24,S(116,114)),new Vector2(190,32));
            // the wind: an arrow turned the way it blows, then its speed
            var arrow=UiKit.Panel(info,"Wind arrow",Color.white,new Vector2(0,1),new Vector2(0,1),new Vector2(205,-129),new Vector2(26,26),false);
            arrow.sprite=Arrow;arrow.raycastTarget=false;h.windArrow=arrow.rectTransform;h.windArrow.pivot=new Vector2(.5f,.5f);
            h.windArrowTint=ThemedGraphic.Bind(arrow.gameObject,ThemeRole.PanelText);
            h.wind=GlassKit.Label(info,"Wind",S(20,24),GlassKit.Medium,ThemeRole.PanelText,TextAnchor.UpperRight,new Vector2(176,S(116,114)),new Vector2(120,32));
            h.windTint=h.wind.GetComponent<ThemedGraphic>();
            if(GlassKit.ClearStyle)h.BuildWindDial(go.transform);
            // Lie chip under it: a ball dot of what the ball sits in, its name, and what it costs.
            var lie=GlassKit.Panel(go.transform,"Lie",new Vector2(0,1),new Vector2(Margin,-Margin-InfoHeight-12),new Vector2(LieWidth,LieHeight),22);
            h.lieRoot=lie;
            var ring=GlassKit.Dot(lie,"Ball ring",Color.white,Vector2.zero,38);
            ring.rectTransform.anchorMin=ring.rectTransform.anchorMax=new Vector2(0,.5f);ring.rectTransform.anchoredPosition=new Vector2(37,0);
            h.lieSwatch=UiKit.Panel(lie,"Swatch",Color.white,new Vector2(0,.5f),new Vector2(0,.5f),new Vector2(37,0),new Vector2(52,52),false);
            h.lieSwatch.rectTransform.pivot=new Vector2(.5f,.5f);h.lieSwatch.rectTransform.localScale=Vector3.one*(34f/52f);
            h.lieSwatch.sprite=UiKit.Circle;h.lieSwatch.raycastTarget=false;
            h.lieSwatch.gameObject.AddComponent<Mask>().showMaskGraphic=true;   // the marks stay inside the disc
            for(int i=0;i<h.lieMarks.Length;i++){
                h.lieMarks[i]=UiKit.Panel(h.lieSwatch.transform,"Mark",Color.white,new Vector2(.5f,.5f),new Vector2(.5f,.5f),Vector2.zero,Vector2.one,false);
                h.lieMarks[i].raycastTarget=false;
            }
            h.lieName=GlassKit.Label(lie,"Lie name",S(26,30),GlassKit.Regular,ThemeRole.PanelText,TextAnchor.UpperLeft,new Vector2(68,7),new Vector2(236,34));
            h.lieCost=GlassKit.Label(lie,"Lie cost",S(15,18),GlassKit.SemiBold,ThemeRole.PanelTextMuted,TextAnchor.UpperLeft,new Vector2(68,S(42,44)),new Vector2(244,40));
            h.lieCostTint=h.lieCost.GetComponent<ThemedGraphic>();
            lie.gameObject.SetActive(false);
            // Shot map, top right: its title, the course picture in rounded corners, and the yardage tags.
            h.mapRoot=GlassKit.Panel(go.transform,"Hole map",new Vector2(1,1),new Vector2(-Margin,-Margin),MapPanel);
            var title=GlassKit.Label(h.mapRoot,"Map title",S(24,28),GlassKit.Regular,ThemeRole.PanelText,TextAnchor.UpperLeft,new Vector2(20,13),new Vector2(220,32));title.text="Shot map";
            if(GlassKit.ClearStyle){   // a white rim and a soft drop round the picture, no card behind it
                var drop=GlassKit.Capsule(h.mapRoot,"Map drop",ThemeRole.Shadow,new Vector2(10,66),new Vector2(MapPanel.x-20,MapPanel.y-58-8),20);drop.color=new Color(0,.03f,.12f,.30f);Destroy(drop.GetComponent<ThemedGraphic>());
                GlassKit.Capsule(h.mapRoot,"Map rim",ThemeRole.PanelText,new Vector2(8,52),new Vector2(MapPanel.x-16,MapPanel.y-58-6),20);
            }
            var clip=GlassKit.Capsule(h.mapRoot,"Map clip",ThemeRole.Panel,new Vector2(14,58),new Vector2(MapPanel.x-28,MapPanel.y-58-16),16);
            clip.color=Color.white;Destroy(clip.GetComponent<ThemedGraphic>());   // (the mask only needs its shape)
            clip.gameObject.AddComponent<Mask>().showMaskGraphic=false;
            var mapGo=new GameObject("Course",typeof(RectTransform),typeof(RawImage));mapGo.transform.SetParent(clip.transform,false);
            h.mapImage=mapGo.GetComponent<RawImage>();h.mapImage.raycastTarget=false;
            var rt=h.mapImage.rectTransform;rt.anchorMin=Vector2.zero;rt.anchorMax=Vector2.one;rt.offsetMin=Vector2.zero;rt.offsetMax=Vector2.zero;
            var pathGo=new GameObject("Projected shot path",typeof(RectTransform),typeof(CanvasRenderer),typeof(GolfMapPath));pathGo.transform.SetParent(rt,false);
            h.projection=pathGo.GetComponent<GolfMapPath>();h.projection.raycastTarget=false;
            var pathRect=h.projection.rectTransform;pathRect.anchorMin=Vector2.zero;pathRect.anchorMax=Vector2.one;pathRect.offsetMin=pathRect.offsetMax=Vector2.zero;
            for(int i=0;i<4;i++){
                h.targets[i]=Mark(rt,"Landing "+(i+1),Stops[i],20);
                var badge=GlassKit.Panel(h.targets[i],"Power label",new Vector2(.5f,.5f),new Vector2(i%2==0?46:-46,0),new Vector2(62,28),14,false);
                var power=GlassKit.Label(badge,"Power",S(15,18),GlassKit.SemiBold,ThemeRole.PanelText,TextAnchor.MiddleCenter,Vector2.zero,new Vector2(62,28));
                h.targetBadges[i]=badge;h.targetLabels[i]=power;            }
            h.BuildClubTiles(go.transform);
            h.pin=Mark(rt,"Pin",new Color(1,.3f,.32f),16);
            h.ball=Mark(rt,"Ball",Color.white,16);
            h.live=Mark(rt,"Live landing",ThemeService.Current.accent,22);
            // a putt's live reading: the feet the backswing so far rolls, beside its dot
            var liveBadge=GlassKit.Panel(h.live,"Live label",new Vector2(.5f,.5f),new Vector2(-54,0),new Vector2(76,28),14,false);
            h.liveBadge=liveBadge;
            h.liveLabel=GlassKit.Label(liveBadge,"Feet",S(15,18),GlassKit.SemiBold,ThemeRole.PanelText,TextAnchor.MiddleCenter,Vector2.zero,new Vector2(76,28));
            liveBadge.gameObject.SetActive(false);
            // Power meter, left: a rail with the gold sweet spot near its top, a gold fill and a pearl.
            h.meterRoot=GlassKit.Panel(go.transform,"Power",new Vector2(0,1),Vector2.zero,new Vector2(MeterWidth,MeterHeight));
            var powerTitle=GlassKit.Label(h.meterRoot,"Power title",S(14,28),GlassKit.SemiBold,ThemeRole.PanelTextMuted,TextAnchor.UpperCenter,new Vector2(0,S(16,12)),new Vector2(MeterWidth,36));powerTitle.text="POWER";
            if(GlassKit.ClearStyle){
                var shade=GlassKit.Capsule(h.meterRoot,"Power drop",ThemeRole.Shadow,new Vector2(RailX-RailRim,RailY-RailRim+9),new Vector2(RailW+2*RailRim,RailH+2*RailRim),(RailW+2*RailRim)/2);
                Destroy(shade.GetComponent<ThemedGraphic>());shade.color=new Color(0,.03f,.12f,.32f);
                h.BuildFlamesBack();
                GlassKit.Capsule(h.meterRoot,"Power rim",ThemeRole.PanelText,new Vector2(RailX-RailRim,RailY-RailRim),new Vector2(RailW+2*RailRim,RailH+2*RailRim),(RailW+2*RailRim)/2);
                var track=GlassKit.Capsule(h.meterRoot,"Power rail",ThemeRole.MeterRail,new Vector2(RailX,RailY),new Vector2(RailW,RailH),RailW/2);
                Destroy(track.GetComponent<ThemedGraphic>());track.color=ThemeService.Current.textOutline;
                h.BuildBands();
                h.meterSweetRim=GlassKit.Capsule(h.meterRoot,"Sweet spot rim",ThemeRole.PanelText,Vector2.zero,new Vector2(SweetW+2*RailRim*.6f,RailH*.12f+2*RailRim*.6f),14);
            }else GlassKit.Capsule(h.meterRoot,"Power rail",ThemeRole.MeterRail,new Vector2(RailX,RailY),new Vector2(RailW,RailH),RailW/2);
            h.meterSweet=GlassKit.Capsule(h.meterRoot,"Sweet spot",ThemeRole.SweetSpot,Vector2.zero,new Vector2(SweetW,RailH*.12f),S(8,12)).rectTransform;
            h.PlaceSweetSpot(.94f);
            h.meterFill=GlassKit.Capsule(h.meterRoot,"Power fill",ThemeRole.MeterFill,new Vector2(RailX+FillInset,RailY+RailH),new Vector2(RailW-2*FillInset,0),(RailW-2*FillInset)/2);
            h.pearlRing=GlassKit.Dot(h.meterRoot,"Pearl ring",Color.white,new Vector2(MeterWidth/2,RailY+RailH),PearlOuter);
            h.pearlCore=GlassKit.Dot(h.meterRoot,"Timing pearl",Color.white,new Vector2(MeterWidth/2,RailY+RailH),PearlInner);ThemedGraphic.Bind(h.pearlCore.gameObject,ThemeRole.Pearl);
            h.pearlRing.enabled=h.pearlCore.enabled=false;h.meterFill.enabled=false;
            if(GlassKit.ClearStyle)h.BuildCrown();
            h.liveYards=GlassKit.Label(h.meterRoot,"Estimate",S(20,36),GlassKit.Regular,ThemeRole.PanelText,TextAnchor.LowerCenter,new Vector2(0,MeterHeight-S(44,56)),new Vector2(MeterWidth,S(28,44)));h.liveYards.text="— yd";
            var status=Panel(go.transform,"Contact",new Vector2(.5f,1),new Vector2(0,-40),new Vector2(340,64));
            h.contactRoot=status;
            h.contact=UiKit.Label(status,"Quality",26,TextAnchor.MiddleCenter,Vector2.zero,Vector2.one,Vector2.zero,Vector2.zero,UiKit.Display,false);
            status.gameObject.SetActive(false);
            return h;
        }
        public static RectTransform Panel(Transform parent,string name,Vector2 anchor,Vector2 pos,Vector2 size)
        {
            var r=UiKit.Panel(parent,name,Ink,anchor,anchor,pos,size).rectTransform;r.pivot=anchor;return r;
        }
        public static Text Label(Transform parent,string name,int size,Vector2 pos,Vector2 box)
        {
            var t=UiKit.Label(parent,name,size,TextAnchor.UpperLeft,new Vector2(0,1),new Vector2(0,1),pos,box,UiKit.Strong,false);t.rectTransform.pivot=new Vector2(0,1);t.color=Color.white;return t;
        }
        static RectTransform Mark(Transform parent,string name,Color colour,float size)
        {
            var rim=UiKit.Panel(parent,name,colour,new Vector2(.5f,.5f),new Vector2(.5f,.5f),Vector2.zero,new Vector2(size,size),false);rim.sprite=UiKit.Circle;rim.raycastTarget=false;
            var face=UiKit.Panel(rim.transform,"Golf ball",Color.white,Vector2.zero,Vector2.one,Vector2.zero,Vector2.zero,false);face.sprite=UiKit.Circle;face.rectTransform.offsetMin=Vector2.one*4;face.rectTransform.offsetMax=-Vector2.one*4;face.raycastTarget=false;
            // A few soft dimples keep the markers recognisable as golf balls at HUD size.
            if(size>=28)foreach(var offset in new[]{new Vector2(-4,3),new Vector2(4,3),new Vector2(0,-4)}){
                var d=UiKit.Panel(face.transform,"Dimple",new Color(.56f,.64f,.67f,.4f),new Vector2(.5f,.5f),new Vector2(.5f,.5f),offset,new Vector2(3,3),false);
                d.sprite=UiKit.Circle;d.raycastTarget=false;
            }
            return rim.rectTransform;
        }
        void LateUpdate()=>RefreshLayout();
        // Also called by offscreen captures after assigning their render target. CanvasScaler's
        // next Update otherwise uses the editor window size for a portrait camera capture.
        public void RefreshLayout()
        {
            if (!view || !canvas) return;
            canvas.targetDisplay=view.targetDisplay;
            bool portrait=view.aspect<1.2f;
            float scale=Mathf.Max(.1f, portrait ? view.pixelWidth/1080f : view.pixelHeight/1080f);
            scaler.uiScaleMode=CanvasScaler.ScaleMode.ConstantPixelSize;
            scaler.scaleFactor=scale; canvas.scaleFactor=scale;
            float top=Margin, left=Margin, right=Margin;
            if (view.targetDisplay==0 && !view.targetTexture)
            {
                var safe=Screen.safeArea;
                top+=Mathf.Max(0,Screen.height-safe.yMax)/scale;
                left+=safe.xMin/scale;right+=Mathf.Max(0,Screen.width-safe.xMax)/scale;
            }
            infoRoot.anchoredPosition=new Vector2(left,-top);
            lieRoot.anchoredPosition=new Vector2(left,-top-InfoHeight-12);
            mapRoot.anchoredPosition=new Vector2(-right,-top);
            mapRoot.sizeDelta=MapPanel;
            if(windDial)windDial.anchoredPosition=new Vector2(-right-MapPanel.x-12,-top);
            // the meter's top is 512 down a 1080-high picture; on the tall phone view it sits higher up
            meterRoot.anchorMin=meterRoot.anchorMax=new Vector2(0,portrait?.62f:1-(GlassKit.ClearStyle?330f:512f)/1080f);
            meterRoot.anchoredPosition=new Vector2(left,0);
            clubRoot.anchoredPosition=new Vector2(left,portrait?250:22);
            contactRoot.anchoredPosition=new Vector2(0,-top-(portrait?232:0));
            PlaceBelowLie();
        }
        /// The club picker, bottom left: SELECT CLUB over three tiles (the club in hand between its neighbours in the bag),
        /// the one in hand a solid button.
        void BuildClubTiles(Transform parent)
        {
            if (GlassKit.ClearStyle) { BuildClubCard(parent); return; }
            clubRoot = GlassKit.Panel(parent, "Club selection", Vector2.zero, new Vector2(Margin, 22), new Vector2(ClubWidth, ClubHeight));
            clubChange = GlassKit.Label(clubRoot, "Clubs heading", 15, GlassKit.SemiBold, ThemeRole.PanelTextMuted, TextAnchor.UpperLeft, new Vector2(18, 12), new Vector2(220, 22));
            clubChange.text = "SELECT CLUB";
            for (int i = 0; i < clubTiles.Length; i++)
            {
                var tile = GlassGraphic.Create(clubRoot, "Club tile " + (i + 1), 14);
                var rt = tile.rectTransform; rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0, 1);
                rt.anchoredPosition = new Vector2(18 + i * (TileW + TileGap), -40); rt.sizeDelta = new Vector2(TileW, TileH);
                var abbr = GlassKit.Label(rt, "Club code", 25, GlassKit.Regular, ThemeRole.PanelText, TextAnchor.UpperCenter, new Vector2(0, 7), new Vector2(TileW, 32));
                var name = GlassKit.Label(rt, "Club name", 14, GlassKit.SemiBold, ThemeRole.PanelText, TextAnchor.UpperCenter, new Vector2(4, 37), new Vector2(TileW - 8, 20));
                name.resizeTextForBestFit = true; name.resizeTextMinSize = 10; name.resizeTextMaxSize = 14;
                clubTiles[i] = new ClubTile { bg = tile, abbr = abbr, name = name };
            }
            ShowClubCard();
        }

        /// What each club carries from here (the controller's strings: "240 yd", the putter in feet), for the club in hand.
        public void SetClubYards(string[] yards) { clubYardStrings = yards; ShowClubCard(); }

        // The clear style's club card: the controller's, smaller, and with no card. CLUB between two rules, the club's picture, its
        // name and carry in the chunky lettering, a dot a club, and a round blue arrow either side.
        void BuildClubCard(Transform parent)
        {
            float width = 410, height = 178;
            clubRoot = GlassKit.Panel(parent, "Club selection", Vector2.zero, new Vector2(Margin, 22), new Vector2(width, height));
            clubChange = GlassKit.Label(clubRoot, "Clubs heading", 30, UiKit.Display, ThemeRole.PanelText, TextAnchor.MiddleCenter, new Vector2(115, 0), new Vector2(180, 36));
            clubChange.text = "CLUB";
            foreach (float side in new[] { -1f, 1f })
            {
                var rule = UiKit.Panel(clubRoot, "Rule", new Color(1, 1, 1, .85f), new Vector2(0, 1), new Vector2(0, 1), new Vector2(205 + side * 128 - 40, -16), new Vector2(80, 4));
                rule.raycastTarget = false;
            }
            const float rowY = 40;   // the row's top, down from the root's top
            clubPicture = new GameObject("Picture", typeof(RectTransform), typeof(RawImage)).GetComponent<RawImage>();
            clubPicture.transform.SetParent(clubRoot, false); clubPicture.raycastTarget = false;
            var prt = clubPicture.rectTransform; prt.anchorMin = prt.anchorMax = prt.pivot = new Vector2(0, 1);
            prt.anchoredPosition = new Vector2(76, -rowY); prt.sizeDelta = Vector2.one * 128;
            clubName = GlassKit.Label(clubRoot, "Club name", 30, UiKit.Display, ThemeRole.PanelText, TextAnchor.MiddleLeft, new Vector2(206, rowY + 2), new Vector2(160, 60));
            clubName.lineSpacing = .85f;
            clubYards = GlassKit.Label(clubRoot, "Club yards", 34, UiKit.Display, ThemeRole.PanelText, TextAnchor.MiddleLeft, new Vector2(206, rowY + 66), new Vector2(160, 42));
            int n = GolfClubs.All.Length; clubDots = new Image[n];
            for (int i = 0; i < n; i++) clubDots[i] = GlassKit.Dot(clubRoot, "Dot " + i, Color.white, new Vector2(205 + (i - (n - 1) / 2f) * 16, height - 8), 9);
            foreach (float side in new[] { -1f, 1f })
            {
                var round = UiKit.Pill(clubRoot, side < 0 ? "Club longer" : "Club shorter", ArrowBlue, new Vector2(0, 1), new Vector2(side < 0 ? 36 : width - 36, -(rowY + 62)), Vector2.one * 66, out var fill, 4);
                foreach (var layer in round.GetComponentsInChildren<Image>()) layer.type = Image.Type.Simple;
                var glyph = GlassKit.Label(fill.transform, "Label", 40, UiKit.Display, ThemeRole.PanelText, TextAnchor.MiddleCenter, Vector2.zero, Vector2.one * 66);
                glyph.rectTransform.anchorMin = glyph.rectTransform.anchorMax = new Vector2(.5f, .5f); glyph.rectTransform.pivot = new Vector2(.5f, .5f); glyph.rectTransform.anchoredPosition = Vector2.zero;
                glyph.text = side < 0 ? "◀" : "▶";
            }
            ShowClubCard();
        }

        static Texture2D ClubPicture(GolfClub club)
        {
            clubPictures ??= System.Array.ConvertAll(ClubPictures, path => { var t = Resources.Load<Texture2D>(path); if (t) t.wrapMode = TextureWrapMode.Clamp; return t; });
            return clubPictures[(int)club.Family()];
        }

        void ShowClubCard()
        {
            if (GlassKit.ClearStyle)
            {
                if (!clubName) return;
                var bag = GolfClubs.All; int at = selectedClub.HasValue ? System.Array.IndexOf(bag, selectedClub.Value) : -1;
                if (at < 0) { clubName.text = "CLUB"; clubYards.text = ""; clubPicture.enabled = false; }
                else
                {
                    var chosen = bag[at];
                    clubName.text = chosen.DisplayName().ToUpperInvariant().Replace(" WEDGE", "\nWEDGE");
                    clubYards.text = clubYardStrings != null && at < clubYardStrings.Length && !string.IsNullOrEmpty(clubYardStrings[at]) ? clubYardStrings[at].ToUpperInvariant() : "";
                    var picture = ClubPicture(chosen); clubPicture.texture = picture; clubPicture.enabled = picture;
                }
                for (int i = 0; i < clubDots.Length; i++) clubDots[i].color = i == at ? ThemeService.Current.accent : new Color(1, 1, 1, .8f);
                return;
            }
            if (clubTiles[0].bg == null) return;
            var all = GolfClubs.All; int index = selectedClub.HasValue ? System.Array.IndexOf(all, selectedClub.Value) : -1;
            // a window of three over the bag, the club in hand in the middle (at the ends, the first or last tile)
            int first = index < 0 ? 0 : Mathf.Clamp(index - 1, 0, Mathf.Max(0, all.Length - clubTiles.Length));
            for (int i = 0; i < clubTiles.Length; i++)
            {
                int at = first + i; bool has = at < all.Length;
                var t = clubTiles[i]; t.bg.gameObject.SetActive(has);
                if (!has) continue;
                var club = all[at]; tileClubs[i] = club;
                bool on = at == index;
                t.abbr.text = club.Label(); t.name.text = club.DisplayName();
                // the one in hand: a solid button with dark text; the others a faint tile with a hairline
                t.bg.SetFlat(Color.white, Color.white, 0, th => on ? (th.Get(ThemeRole.Button), Color.clear, 0f) : (new Color(1, 1, 1, .10f), new Color(1, 1, 1, .24f), 1.5f));
                t.abbr.GetComponent<ThemedGraphic>().role = on ? ThemeRole.ButtonText : ThemeRole.PanelText;
                t.name.GetComponent<ThemedGraphic>().role = on ? ThemeRole.ButtonText : ThemeRole.PanelTextMuted;
                t.name.font = on ? GlassKit.Bold : GlassKit.SemiBold;
                t.abbr.font = on ? GlassKit.SemiBold : GlassKit.Regular;
                t.abbr.GetComponent<ThemedGraphic>().Refresh(); t.name.GetComponent<ThemedGraphic>().Refresh();
            }
        }

        public void SetHole(int n,int par)=>hole.text=$"HOLE {n:00} · PAR {par}";
        RectTransform conditionsRoot;
        /// Today's conditions under the shot card: a chip for the weather and one for each twist,
        /// in their colours with their icons.
        public void SetConditions(EventFace[] faces)
        {
            if(conditionsRoot)Destroy(conditionsRoot.gameObject);
            conditionsRoot=null;
            conditionCount=faces?.Length??0;PlaceBounty();
            if(faces==null||faces.Length==0)return;
            conditionsRoot=new GameObject("Conditions",typeof(RectTransform)).GetComponent<RectTransform>();
            conditionsRoot.SetParent(infoRoot,false);
            conditionsRoot.anchorMin=conditionsRoot.anchorMax=conditionsRoot.pivot=new Vector2(0,0);
            conditionsRoot.sizeDelta=new Vector2(300,0);PlaceBelowLie();
            for(int i=0;i<faces.Length;i++){
                var f=faces[i];
                var chip=GlassKit.Panel(conditionsRoot,"Chip "+f.Title,new Vector2(0,1),new Vector2(0,-i*44),new Vector2(300,38),14,false);
                var key=UiKit.Panel(chip,"Colour",f.Colour,new Vector2(0,0),new Vector2(0,1),new Vector2(3,0),new Vector2(32,-6));key.raycastTarget=false;
                key.rectTransform.offsetMin=new Vector2(3,3);key.rectTransform.offsetMax=new Vector2(35,-3);
                var icon=Icons.Place(key.transform,f.Icon,Ink,new Vector2(.5f,.5f),Vector2.zero,24);icon.raycastTarget=false;
                var t=GlassKit.Label(chip,"Name",S(18,20),GlassKit.SemiBold,ThemeRole.PanelText,TextAnchor.MiddleLeft,new Vector2(48,0),new Vector2(244,38));
                t.text=f.Title.ToUpperInvariant();
            }
        }
        readonly System.Collections.Generic.List<RectTransform> ringMarks=new();
        RectTransform bountyRoot, coinsRoot; Text bountyTitle, bountyReward, coinsText; Image bountyMark, bountyKey;
        int conditionCount; float coinsBumpedAt=-9;
        /// The hole's bounty under the conditions: a gold chip with what to do and what it pays,
        /// ticked when done, crossed and dimmed when missed. Null takes it away.
        public void SetBounty(string title,int coins,int state,string icon)
        {
            if(title==null){if(bountyRoot)bountyRoot.gameObject.SetActive(false);return;}
            if(!bountyRoot){
                bountyRoot=GlassKit.Panel(infoRoot,"Bounty",new Vector2(0,0),Vector2.zero,new Vector2(300,62),14,false);
                bountyRoot.pivot=new Vector2(0,1);
                bountyKey=UiKit.Panel(bountyRoot,"Colour",Gold,new Vector2(0,0),new Vector2(0,1),Vector2.zero,new Vector2(46,0));bountyKey.raycastTarget=false;
                bountyMark=Icons.Place(bountyKey.transform,"star",Ink,new Vector2(.5f,.5f),Vector2.zero,30);bountyMark.raycastTarget=false;
                bountyReward=UiKit.Label(bountyRoot,"Reward",15,TextAnchor.UpperLeft,new Vector2(0,1),new Vector2(1,1),new Vector2(0,-6),new Vector2(0,20),UiKit.Strong,false);
                bountyReward.rectTransform.pivot=new Vector2(0,1);bountyReward.rectTransform.offsetMin=new Vector2(58,bountyReward.rectTransform.offsetMin.y);bountyReward.rectTransform.offsetMax=new Vector2(-8,-6);bountyReward.raycastTarget=false;
                bountyTitle=UiKit.Label(bountyRoot,"Task",19,TextAnchor.LowerLeft,Vector2.zero,new Vector2(1,0),new Vector2(0,6),new Vector2(0,30),UiKit.Strong,false);
                bountyTitle.rectTransform.pivot=new Vector2(0,0);bountyTitle.rectTransform.offsetMin=new Vector2(58,6);bountyTitle.rectTransform.offsetMax=new Vector2(-8,34);bountyTitle.raycastTarget=false;
                bountyTitle.horizontalOverflow=HorizontalWrapMode.Wrap;bountyTitle.verticalOverflow=VerticalWrapMode.Truncate;
                bountyTitle.resizeTextForBestFit=true;bountyTitle.resizeTextMinSize=12;bountyTitle.resizeTextMaxSize=19;
            }
            bountyRoot.gameObject.SetActive(true);
            bool done=state==1, missed=state==2;
            bountyKey.color=missed?UiKit.Hex("6B7785"):done?UiKit.Hex("5CD66B"):Gold;
            bountyMark.sprite=Icons.Get(done?"tick":missed?"cross":icon);
            bountyReward.text=done?$"BOUNTY DONE  ·  +{coins}":missed?"BOUNTY MISSED":$"BOUNTY  ·  +{coins} COINS";
            bountyReward.color=missed?new Color(1,1,1,.5f):Gold;
            bountyTitle.text=title.ToUpperInvariant();bountyTitle.color=missed?new Color(1,1,1,.5f):Color.white;
            PlaceBounty();
        }
        void PlaceBounty(){if(bountyRoot)bountyRoot.anchoredPosition=new Vector2(0,-10-BelowLie()-conditionCount*44);}
        // the chips under the hole card hang below the lie chip, not behind it
        float BelowLie()=>lieRoot&&lieRoot.gameObject.activeSelf?lieHeight+12:0;
        void PlaceBelowLie(){if(conditionsRoot)conditionsRoot.anchoredPosition=new Vector2(0,-10-BelowLie());PlaceBounty();}
        public static readonly Color Gold=UiKit.Hex("FFC93C");

        /// The round's coins under the shot map (null hides them); a new total pops the counter.
        public void SetCoins(int? coins)
        {
            if(coins==null){if(coinsRoot)coinsRoot.gameObject.SetActive(false);return;}
            if(!coinsRoot){
                coinsRoot=GlassKit.Panel(mapRoot,"Coins",new Vector2(1,0),new Vector2(0,-12),new Vector2(170,54),22,false);
                coinsRoot.pivot=new Vector2(1,1);
                var disc=Icons.Place(coinsRoot,"coin",Gold,new Vector2(0,.5f),new Vector2(30,0),36);disc.raycastTarget=false;
                coinsText=UiKit.Label(coinsRoot,"Count",28,TextAnchor.MiddleRight,Vector2.zero,Vector2.one,Vector2.zero,Vector2.zero,UiKit.Display,false);
                coinsText.rectTransform.offsetMin=new Vector2(54,0);coinsText.rectTransform.offsetMax=new Vector2(-16,0);coinsText.color=Gold;coinsText.raycastTarget=false;
            }
            coinsRoot.gameObject.SetActive(true);
            string text=coins.Value.ToString("N0");
            if(coinsText.text!=text&&coinsText.text.Length>0)coinsBumpedAt=Time.unscaledTime;
            coinsText.text=text;
        }
        void Update()
        {
            AnimateFlames();
            if(!coinsRoot)return;
            float t=Time.unscaledTime-coinsBumpedAt;
            coinsRoot.localScale=Vector3.one*(t<.4f?1+.28f*Mathf.Sin(t/.4f*Mathf.PI):1);
        }

        public void SetDistance(double n,string unit)=>distance.text=$"{n:F0}<size={S(21,24)}> {unit.ToLowerInvariant()} to pin</size>";
        public void SetClub(string name)=>club.text=System.Text.RegularExpressions.Regex.Replace(name," {2,}"," ");
        public void SetClubSelection(GolfClub selected, bool announce=false)
        {
            if(selectedClub==selected)return;
            clubChangedAt=Time.unscaledTime;selectedClub=selected;
            ShowClubCard();
        }
        /// `angle` is where the wind blows toward, degrees right of the aim: the arrow points that way on the screen.
        void BuildWindDial(Transform parent)
        {
            // (the hole card has no wind row in this style: the card's own arrow and speed are put away)
            windArrow.gameObject.SetActive(false);wind.gameObject.SetActive(false);
            windDial=new GameObject("Wind meter",typeof(RectTransform)).GetComponent<RectTransform>();windDial.SetParent(parent,false);
            windDial.anchorMin=windDial.anchorMax=windDial.pivot=new Vector2(1,1);windDial.sizeDelta=new Vector2(200,300);windDial.anchoredPosition=new Vector2(-Margin-MapPanel.x-12,-Margin);
            var caption=GlassKit.Label(windDial,"Wind caption",28,UiKit.Display,ThemeRole.PanelText,TextAnchor.UpperCenter,new Vector2(0,0),new Vector2(200,36));caption.text="WIND";
            var c=new Vector2(100,134);
            var shade=GlassKit.Dot(windDial,"Dial shadow",new Color(0,.03f,.12f,.30f),c+new Vector2(0,9),184);
            GlassKit.Dot(windDial,"Dial rim",Color.white,c,184);
            var face=GlassKit.Dot(windDial,"Dial face",ThemeService.Current.textOutline,c,164);
            // north, east, south and west on the face, so the arrow has something to turn against
            for(int i=0;i<4;i++){
                float a=i*Mathf.PI/2;var tick=GlassKit.Dot(windDial,"Mark",new Color(1,1,1,i==0?.95f:.55f),c+new Vector2(Mathf.Sin(a),Mathf.Cos(a))*68,i==0?12:8);
            }
            var arrow=UiKit.Panel(windDial,"Wind arrow",Color.white,new Vector2(0,1),new Vector2(0,1),new Vector2(c.x,-c.y),new Vector2(104,104),false);
            arrow.sprite=Arrow;arrow.raycastTarget=false;arrow.rectTransform.pivot=new Vector2(.5f,.5f);
            var edge=new Color(.03f,.11f,.3f,1);
            foreach(var d in new[]{new Vector2(3,-3),new Vector2(-3,3)}){var o=arrow.gameObject.AddComponent<Outline>();o.effectColor=edge;o.effectDistance=d;}
            windArrow=arrow.rectTransform;windArrowTint=null;windTint=null;
            windCalm=GlassKit.Label(windDial,"Calm",34,UiKit.Display,ThemeRole.PanelText,TextAnchor.MiddleCenter,new Vector2(0,c.y-24),new Vector2(200,48));windCalm.text="CALM";windCalm.gameObject.SetActive(false);
            wind=GlassKit.Label(windDial,"Wind speed",50,UiKit.Display,ThemeRole.PanelText,TextAnchor.UpperCenter,new Vector2(0,218),new Vector2(200,60));
            windWords=GlassKit.Label(windDial,"Wind words",24,UiKit.Display,ThemeRole.PanelTextMuted,TextAnchor.UpperCenter,new Vector2(-20,272),new Vector2(240,32));
        }

        public void SetWind(float angle,double mph,bool calm)
        {
            var w=new Wind(mph,0);
            if(windDial){
                bool hot=!calm&&mph>=Wind.ModerateMPH;
                var tone=hot?(w.IsStrong?Stops[3]:Stops[2]):Color.white;
                windArrow.gameObject.SetActive(!calm);windCalm.gameObject.SetActive(calm);
                windArrow.localRotation=Quaternion.Euler(0,0,-angle);
                windArrow.GetComponent<Image>().color=hot?tone:Color.white;
                float rel=Mathf.DeltaAngle(0,angle);
                wind.text=calm?"":$"{mph:F0}<size=26> mph</size>";wind.color=tone;
                windWords.text=calm?"":Mathf.Abs(rel)<=30?"HELPING":Mathf.Abs(rel)>=150?"INTO WIND":rel>0?"LEFT → RIGHT":"RIGHT → LEFT";
                windWords.color=hot?tone:new Color(1,1,1,.95f);
                return;
            }
            // white (the theme's text) in a calm or moderate wind; a strong one is warm
            bool warm=!calm&&mph>=Wind.ModerateMPH;
            var colour=warm?(w.IsStrong?Stops[3]:Stops[2]):ThemeService.Current.Get(ThemeRole.PanelText);
            windTint.enabled=windArrowTint.enabled=!warm;
            if(warm){wind.color=colour;windArrow.GetComponent<Image>().color=colour;}else{windTint.Refresh();windArrowTint.Refresh();}
            windArrow.gameObject.SetActive(!calm);
            windArrow.localRotation=Quaternion.Euler(0,0,-angle);
            // The arrow turns the way it blows (up the screen helps, down is into the wind); the card has room for the speed.
            wind.text=calm?"Calm":$"{mph:F0} mph";
            windArrow.anchoredPosition=new Vector2(InfoWidth-24-wind.preferredWidth-22,-129);
        }
        public void SetFlight(bool on){flight=on;clubRoot.gameObject.SetActive(!on);meterRoot.gameObject.SetActive(!on);lieRoot.gameObject.SetActive(!on&&lieSet);contact.transform.parent.gameObject.SetActive(on);PlaceBelowLie();}

        /// The ball's lie, before the shot: its name on a swatch of it, and what it costs the club in hand — the distance it
        /// keeps (CourseLies.PowerFactor) and whether it costs accuracy (CourseLies.Scatter).
        public void SetLie(CourseLie lie,GolfClub inHand)
        {
            lieSet=true;lieRoot.gameObject.SetActive(!flight);
            lieName.text=lie==CourseLie.Bunker?"Sand":lie==CourseLie.OutOfBounds?"Out":lie.Label();
            int cost=inHand==GolfClub.Putter?0:Mathf.RoundToInt((float)(1-lie.PowerFactor(inHand))*100);
            double wild=lie.Scatter().degrees;
            string aim=wild>=5?"MUCH LESS ACCURATE":wild>0?"LESS ACCURATE":null;
            lieCost.text=cost>0&&aim!=null?$"-{cost}% DISTANCE\n{aim}":cost>0?$"-{cost}% DISTANCE":aim??(lie.IsPuttingSurface()?"PUTTING SURFACE":"CLEAN LIE");
            bool warn=cost>0||aim!=null;
            lieCostTint.enabled=!warn;if(warn)lieCost.color=Stops[2];else lieCostTint.Refresh();
            // two lines of cost (distance and accuracy) want a taller chip
            lieHeight=lieCost.text.Contains("\n")?LieTallHeight:LieHeight;lieRoot.sizeDelta=new Vector2(LieWidth,lieHeight);PlaceBelowLie();
            var (fill,mark)=lie switch{
                CourseLie.Rough=>(UiKit.Hex("3E7A2E"),UiKit.Hex("1F4A18")),
                CourseLie.Bunker=>(UiKit.Hex("EED39A"),UiKit.Hex("B8955A")),
                CourseLie.Green or CourseLie.Fringe=>(UiKit.Hex("8FDB6A"),UiKit.Hex("B9EE98")),
                CourseLie.Ice=>(UiKit.Hex("D8F1FF"),UiKit.Hex("9CCBE6")),
                _=>(UiKit.Hex("6CC24A"),UiKit.Hex("8ED66C")),
            };
            lieSwatch.color=fill;
            // a hint of the surface on the swatch: blades of long grass, grains of sand, mown stripes
            for(int i=0;i<lieMarks.Length;i++){
                var r=lieMarks[i].rectTransform;lieMarks[i].color=mark;lieMarks[i].sprite=null;
                if(lie==CourseLie.Rough){r.sizeDelta=new Vector2(5,20);r.anchoredPosition=new Vector2(-11+11*i,i==1?2:-2);r.localRotation=Quaternion.Euler(0,0,12-12*i);}
                else if(lie==CourseLie.Bunker){lieMarks[i].sprite=UiKit.Circle;r.sizeDelta=new Vector2(7,7);r.anchoredPosition=new Vector2(-10+10*i,i==1?8:-5);r.localRotation=Quaternion.identity;}
                else{r.sizeDelta=new Vector2(10,44);r.anchoredPosition=new Vector2(-14+14*i,0);r.localRotation=Quaternion.Euler(0,0,30);lieMarks[i].color=i==1?fill:mark;}
            }
        }

        static Sprite arrowSprite;
        /// A plain arrow pointing up the screen, white, for tinting and turning.
        static Sprite Arrow
        {
            get
            {
                if(arrowSprite)return arrowSprite;
                const int n=64;var tex=new Texture2D(n,n,TextureFormat.RGBA32,false){wrapMode=TextureWrapMode.Clamp,name="Wind arrow"};
                var px=new Color32[n*n];
                for(int y=0;y<n;y++)for(int x=0;x<n;x++){
                    int inside=0;
                    for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++){
                        float u=(x+(sx+.5f)/4)/n-.5f,v=(y+(sy+.5f)/4)/n;
                        bool head=v>=.5f&&v<=.97f&&Mathf.Abs(u)<=.42f*(.97f-v)/.47f;
                        bool shaft=v>=.04f&&v<.5f&&Mathf.Abs(u)<=.1f;
                        if(head||shaft)inside++;
                    }
                    px[y*n+x]=new Color32(255,255,255,(byte)(inside*255/16));
                }
                tex.SetPixels32(px);tex.Apply();
                return arrowSprite=Sprite.Create(tex,new Rect(0,0,n,n),new Vector2(.5f,.5f),100);
            }
        }

        // ---- The clear meter's bands, markers and flames.
        // Flames: a handful of frames drawn by noise (white-hot core to orange to red tips, ragged edge, licking upward),
        // cycled so each tongue flickers. Colour is baked in; the meter only picks size, count and when to show them.
        const int FlameFrames = 8;
        static Sprite[] flameFrames;
        static Sprite[] Flames
        {
            get
            {
                if(flameFrames!=null&&flameFrames[0])return flameFrames;
                const int w=56,h=112;flameFrames=new Sprite[FlameFrames];
                for(int f=0;f<FlameFrames;f++){
                    var tex=new Texture2D(w,h,TextureFormat.RGBA32,false){wrapMode=TextureWrapMode.Clamp,filterMode=FilterMode.Bilinear,name="Flame "+f};
                    var px=new Color32[w*h];float seed=f*5.37f+1.9f;
                    for(int y=0;y<h;y++)for(int x=0;x<w;x++){
                        float u=(x+.5f)/w-.5f,v=(y+.5f)/h;
                        float n=Mathf.PerlinNoise(u*3.4f+seed,v*3.1f+seed*.7f);                  // ragged edge and uneven tongues
                        float n2=Mathf.PerlinNoise(u*7f+seed*1.3f,v*6f-seed);
                        float body=.43f*Mathf.Pow(1-v,.72f)*Mathf.Clamp01(v/.09f);              // fat foot, pulled up to a tip
                        float edge=body*(.5f+.85f*n);
                        float sway=(.12f*Mathf.Sin(v*5.5f+seed)+.06f*(n2-.5f))*v;
                        float d=Mathf.Abs(u-sway)/Mathf.Max(edge,1e-3f);
                        float tip=.78f+.22f*n2;                                                  // tongues end at different heights
                        float a=Mathf.Clamp01((1-d)*2.6f)*Mathf.Clamp01((tip-v)*5f);
                        float heat=Mathf.Clamp01((1-d)*(1.2f-v*.95f)+.12f*(n-.5f));
                        Color c=heat>.7f?Color.Lerp(new Color(1,.9f,.45f),new Color(1,1,.86f),(heat-.7f)/.3f)
                            :heat>.42f?Color.Lerp(new Color(1,.58f,.1f),new Color(1,.9f,.45f),(heat-.42f)/.28f)
                            :Color.Lerp(new Color(.9f,.15f,.05f),new Color(1,.58f,.1f),heat/.42f);
                        px[y*w+x]=new Color(c.r,c.g,c.b,a);
                    }
                    tex.SetPixels32(px);tex.Apply();
                    flameFrames[f]=Sprite.Create(tex,new Rect(0,0,w,h),new Vector2(.5f,0),100);
                }
                return flameFrames;
            }
        }
        Image FlameImage(Transform parent,string name)
        {
            var img=UiKit.Panel(parent,name,Color.white,new Vector2(0,1),new Vector2(0,1),Vector2.zero,new Vector2(24,48),false);
            img.sprite=Flames[0];img.type=Image.Type.Simple;img.raycastTarget=false;img.rectTransform.pivot=new Vector2(.5f,0);img.enabled=false;
            return img;
        }
        // four bands of the rail, each the colour of its landing mark on the map, with a divider between them and a labelled
        // marker (25% .. 100%) at the end of each; the old meter's sections, bigger
        void BuildBands()
        {
            float bandH=RailH/4,inner=RailW-2*FillInset;
            for(int i=0;i<4;i++){
                var band=UiKit.Panel(meterRoot,"Power band "+(i+1),Stops[i],new Vector2(0,1),new Vector2(0,1),new Vector2(RailX+FillInset,-(RailY+RailH-i*bandH)),new Vector2(inner,0),false);
                band.raycastTarget=false;band.rectTransform.pivot=new Vector2(0,0);bandFills[i]=band;   // (grows up from its foot)
            }
            for(int i=1;i<4;i++){
                var line=UiKit.Panel(meterRoot,"Band divider",Color.white,new Vector2(0,1),new Vector2(0,1),new Vector2(RailX,-(RailY+RailH-i*bandH)+2),new Vector2(RailW,4),false);
                line.raycastTarget=false;
            }
            float mx=RailX+RailW+RailRim+16;
            for(int i=0;i<4;i++){
                var holder=new GameObject("Marker "+(i+1),typeof(RectTransform)).GetComponent<RectTransform>();holder.SetParent(meterRoot,false);
                holder.anchorMin=holder.anchorMax=new Vector2(0,1);holder.pivot=new Vector2(.5f,.5f);holder.anchoredPosition=new Vector2(mx,-(RailY+RailH*(1-(i+1)*.25f)));holder.sizeDelta=Vector2.one;
                var ring=GlassKit.Dot(holder,"Ring",Color.white,Vector2.zero,26);ring.rectTransform.anchorMin=ring.rectTransform.anchorMax=new Vector2(.5f,.5f);ring.rectTransform.anchoredPosition=Vector2.zero;
                var dot=GlassKit.Dot(holder,"Dot",Stops[i],Vector2.zero,20);dot.rectTransform.anchorMin=dot.rectTransform.anchorMax=new Vector2(.5f,.5f);dot.rectTransform.anchoredPosition=Vector2.zero;
                var label=GlassKit.Label(holder,"Label",24,UiKit.Display,ThemeRole.PanelText,TextAnchor.MiddleLeft,Vector2.zero,new Vector2(80,34));
                label.rectTransform.anchorMin=label.rectTransform.anchorMax=new Vector2(.5f,.5f);label.rectTransform.pivot=new Vector2(0,.5f);label.rectTransform.anchoredPosition=new Vector2(18,0);
                label.text=$"{(i+1)*25}%";
                markers[i]=holder;markerLabels[i]=label;markerDots[i]=dot;
            }
        }
        // the glow and the licks of flame up both sides of the filled bar (behind its rim, so they come out from it)
        void BuildFlamesBack()
        {
            flameBack=new GameObject("Flames",typeof(RectTransform)).GetComponent<RectTransform>();flameBack.SetParent(meterRoot,false);
            flameBack.anchorMin=flameBack.anchorMax=new Vector2(0,1);flameBack.pivot=new Vector2(0,1);flameBack.anchoredPosition=Vector2.zero;flameBack.sizeDelta=Vector2.zero;
            flameGlow=UiKit.Panel(flameBack,"Heat glow",new Color(1,.45f,.1f,0),new Vector2(0,1),new Vector2(0,1),new Vector2(RailX-60,-(RailY-60)),new Vector2(RailW+120,RailH+120),false);
            flameGlow.sprite=GlassKit.ShadowSprite;flameGlow.type=Image.Type.Sliced;flameGlow.pixelsPerUnitMultiplier=1;flameGlow.raycastTarget=false;flameGlow.rectTransform.pivot=new Vector2(0,1);
            for(int i=0;i<SideFlames*2;i++)sideOuter[i]=FlameImage(flameBack,"Flame");
        }
        // the crown of flame on the pearl, in front of the bar
        void BuildCrown()
        {
            flameFront=new GameObject("Crown",typeof(RectTransform)).GetComponent<RectTransform>();flameFront.SetParent(meterRoot,false);
            flameFront.anchorMin=flameFront.anchorMax=new Vector2(0,1);flameFront.pivot=new Vector2(0,1);flameFront.anchoredPosition=Vector2.zero;flameFront.sizeDelta=Vector2.zero;
            for(int i=0;i<3;i++)crownOuter[i]=FlameImage(flameFront,"Crown flame");
            flameFront.SetSiblingIndex(pearlRing.transform.GetSiblingIndex());   // under the pearl
        }
        static float Noise(float seed)=>Mathf.PerlinNoise(Time.unscaledTime*9f+seed*7.31f,seed*3.7f);
        /// Where a club's flames start (the load, 0..1: 2.5 / 3 / 3.5 bars of the four) and how strong they get: the driver's
        /// is the show, the irons' less, the wedges' and chipper's least, and a putt has none.
        static (float from, float strength) FlameFor(GolfClub? club)
        {
            if(!club.HasValue)return (2,0);
            switch(club.Value){
                case GolfClub.Driver:return (2.5f/4,1f);
                case GolfClub.Putter:return (2,0);
                case GolfClub.Hybrid:case GolfClub.Iron5:case GolfClub.Iron:case GolfClub.Iron9:return (3f/4,.6f);
                default:return (3.5f/4,.4f);   // the wedges and the chipper
            }
        }
        // Fire on the bar once the load is past the club's mark: tongues along the filled bar above the mark, a crown on the pearl,
        // and a faint glow, growing to the top. Every tongue flickers: its frame changes, it sways, it breathes.
        void AnimateFlames()
        {
            if(flameBack==null)return;
            shownLoad=Mathf.MoveTowards(shownLoad,powerLoad,Time.unscaledDeltaTime*(powerLoad>shownLoad?4f:2.5f));
            var (from,strength)=FlameFor(selectedClub);
            float load=shownLoad,over=Mathf.Clamp01((load-from)/Mathf.Max(.05f,1-from));
            float heat=load>from?Mathf.SmoothStep(.12f,1f,over)*strength:0;
            bool lit=heat>.01f;
            flameGlow.enabled=lit;if(lit)flameGlow.color=new Color(1,.45f,.1f,.26f*heat);
            float leftX=RailX-RailRim+2,rightX=RailX+RailW+RailRim-2;
            for(int side=0;side<2;side++)for(int i=0;i<SideFlames;i++){
                int k=side*SideFlames+i;var img=sideOuter[k];
                float t=from+(i+.5f)/SideFlames*(1-from);                                   // along the bar, above the club's mark
                float a=lit?Mathf.Clamp01((load-t)/.05f):0;
                img.enabled=a>.01f;if(!img.enabled)continue;
                float n=Noise(k+1),beat=Time.unscaledTime*11f+k*1.7f;
                float height=(16+34*heat)*(.7f+.6f*n),width=height*.52f;
                var rt=img.rectTransform;rt.sizeDelta=new Vector2(width,height);rt.anchoredPosition=new Vector2(side==0?leftX:rightX,-(RailY+RailH*(1-t)));
                rt.localRotation=Quaternion.Euler(0,0,(side==0?7f:-7f)+Mathf.Sin(beat)*8f);
                img.sprite=Flames[(int)(Time.unscaledTime*12f+k*3)%FlameFrames];
                img.color=new Color(1,1,1,a*Mathf.Clamp01(.45f+heat));
            }
            if(flameFront==null)return;
            float topY=RailY+RailH*(1-load);
            for(int i=0;i<3;i++){
                var img=crownOuter[i];img.enabled=lit;if(!lit)continue;
                float n=Noise(40+i),main=i==0?1f:.6f,beat=Time.unscaledTime*10f+i*2.1f;
                float height=(22+58*Mathf.Pow(heat,1.1f))*main*(.82f+.36f*n),width=(24+22*heat)*main;
                var rt=img.rectTransform;rt.sizeDelta=new Vector2(width,height);
                rt.anchoredPosition=new Vector2(MeterWidth/2+(i==0?0:(i==1?-10f:10f)*(1+heat)),-topY+PearlOuter*.25f);
                rt.localRotation=Quaternion.Euler(0,0,(i==0?0:(i==1?12f:-12f))+Mathf.Sin(beat)*7f);
                img.sprite=Flames[(int)(Time.unscaledTime*12f+i*3)%FlameFrames];
                img.color=new Color(1,1,1,Mathf.Clamp01(.55f+heat));
            }
        }
        public void SetContact(string quality)=>contact.text=quality.TrimEnd('!')+" CONTACT";
        public void SetPower(float load,string yards){
            load=Mathf.Clamp01(load);powerLoad=load;
            float fillH=RailH*load,top=RailY+RailH-fillH;
            meterFill.enabled=pearlRing.enabled=pearlCore.enabled=load>.004f;
            if(bandFills[0]){
                // the old meter's four sections: each fills in its own colour as the load climbs through it
                meterFill.enabled=false;float bandH=RailH/4;
                for(int i=0;i<4;i++){var b=bandFills[i];b.rectTransform.sizeDelta=new Vector2(b.rectTransform.sizeDelta.x,bandH*Mathf.Clamp01(load*4-i));}
                for(int i=0;i<4;i++){
                    float at=checkpointLoads!=null&&i<checkpointLoads.Length?checkpointLoads[i]:(i+1)*.25f;bool reached=load>.02f&&load>=at-.004f;
                    markers[i].localScale=Vector3.one*(reached?1.2f:1f);
                    markerLabels[i].color=new Color(1,1,1,reached?1f:.85f);
                }
                pearlCore.color=Stops[Mathf.Clamp(Mathf.FloorToInt(load*4-.0001f),0,3)];
            }
            var fr=meterFill.rectTransform;fr.sizeDelta=new Vector2(RailW-2*FillInset,fillH);fr.anchoredPosition=new Vector2(RailX+FillInset,-top);
            foreach(var p in new[]{pearlRing,pearlCore})p.rectTransform.anchoredPosition=new Vector2(MeterWidth/2,-top);
            liveYards.text=string.IsNullOrEmpty(yards)?"— yd":yards;
        }
        /// The meter's checkpoints (the loads the four landing marks on the map are for): a small tick in each one's colour
        /// beside the rail, and the gold sweet spot on the one that reaches the pin, else on the top one (full power).
        public void SetCheckpoints(float[] loads,int pin=-1)
        {
            checkpointLoads=loads;
            while(meterTicks.Count<(loads?.Length??0)){
                var tick=UiKit.Panel(meterRoot,"Checkpoint tick",Color.white,new Vector2(0,1),new Vector2(0,1),Vector2.zero,new Vector2(S(10,16),S(3,5)),false);
                tick.raycastTarget=false;meterTicks.Add(tick);
            }
            for(int i=0;i<meterTicks.Count;i++){
                bool on=loads!=null&&i<loads.Length&&!bandFills[0];meterTicks[i].gameObject.SetActive(on);
                if(!on)continue;
                meterTicks[i].color=Stops[Mathf.Min(i,Stops.Length-1)];
                meterTicks[i].rectTransform.anchoredPosition=new Vector2(RailX-RailRim-S(9,14),-(RailY+RailH*(1-Mathf.Clamp01(loads[i]))-S(2,3)));
            }
            for(int i=0;i<markers.Length;i++)if(markers[i]&&loads!=null&&i<loads.Length)markers[i].anchoredPosition=new Vector2(markers[i].anchoredPosition.x,-(RailY+RailH*(1-Mathf.Clamp01(loads[i]))));
            float centre=loads==null||loads.Length==0?.94f:loads[pin>=0&&pin<loads.Length?pin:loads.Length-1];
            PlaceSweetSpot(Mathf.Min(centre,.94f));
        }
        void PlaceSweetSpot(float centre)
        {
            float h=RailH*.12f;
            meterSweet.anchorMin=meterSweet.anchorMax=meterSweet.pivot=new Vector2(0,1);
            meterSweet.anchoredPosition=new Vector2(RailX-(SweetW-RailW)/2,-(RailY+RailH*(1-Mathf.Clamp01(centre))-h/2));
            if(meterSweetRim){meterSweetRim.rectTransform.anchorMin=meterSweetRim.rectTransform.anchorMax=meterSweetRim.rectTransform.pivot=new Vector2(0,1);meterSweetRim.rectTransform.anchoredPosition=meterSweet.anchoredPosition+new Vector2(-RailRim*.6f,RailRim*.6f);}
        }
        public void Draw(Camera map,Texture texture,Hud.MapPlan plan)
        {
            mapImage.texture=texture;
            GolfArcade.EnvironmentArt.DreamVisibility.Mask(mapImage,map);
            projection.SetPath(map,flight?plan.Trace:plan.Path,flight?plan.TraceColor:new Color(.25f,.78f,1),!flight);
            void Place(RectTransform t,Vector3 world,bool show){var v=map.WorldToViewportPoint(world);t.gameObject.SetActive(show&&(t==ball||GolfArcade.EnvironmentArt.DreamVisibility.Visible(world))&&v.x>=0&&v.x<=1&&v.y>=0&&v.y<=1);t.anchorMin=t.anchorMax=new Vector2(v.x,v.y);t.anchoredPosition=Vector2.zero;}
            Place(ball,plan.Ball,plan.ShowBall);Place(pin,plan.Pin,true);Place(live,plan.Load,plan.ShowLoad&&!flight);
            // the rings still standing, little gold hoops on the map
            while(ringMarks.Count<plan.Rings.Count){var m=Icons.Place(mapImage.rectTransform,"ring",Gold,new Vector2(.5f,.5f),Vector2.zero,24);m.raycastTarget=false;ringMarks.Add(m.rectTransform);}
            for(int i=0;i<ringMarks.Count;i++)Place(ringMarks[i],i<plan.Rings.Count?plan.Rings[i]:Vector3.zero,i<plan.Rings.Count);
            for(int i=0;i<targets.Length;i++){
                Place(targets[i],i<plan.Targets.Count?plan.Targets[i]:Vector3.zero,!flight&&i<plan.Targets.Count);
                // a putt's marks say how far they roll; a full shot's say their share of the meter
                bool feet=i<plan.TargetLabels.Count;
                targetLabels[i].text=feet?plan.TargetLabels[i]:$"{(i+1)*25}%";
                targetBadges[i].sizeDelta=new Vector2(feet?76:62,28);
                // (a putt's all on the right, a ruler up the line; the live reading rides on the left)
                targetBadges[i].anchoredPosition=new Vector2(feet?54:(i%2==0?46:-46),0);
            }
            liveBadge.gameObject.SetActive(!string.IsNullOrEmpty(plan.LoadLabel));
            if(liveBadge.gameObject.activeSelf)liveLabel.text=plan.LoadLabel;
            live.SetAsLastSibling();
            ball.SetAsLastSibling();
        }
    }
}
