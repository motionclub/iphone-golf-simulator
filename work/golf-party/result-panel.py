from pathlib import Path
p=Path('Unity/Assets/Scripts/UI/ShotResultPanel.cs');s=p.read_text()
s=s.replace('Text quality, distance, carry;', '''Text quality, distance, carry, extra, countdown;
        Image progress;
        CanvasGroup summaryFade;
        float elapsed, targetDistance;
        string distanceUnit="yd";
        bool countDistance;
        void Update() {
            elapsed+=Time.unscaledDeltaTime;
            if(countDistance)distance.text=$"{Mathf.Lerp(0,targetDistance,1-Mathf.Pow(1-Mathf.Clamp01(elapsed/.65f),3)):F0} {distanceUnit}";
        }''')
s=s.replace('summary.localScale = Vector3.one * scale;', '''float t=GolfArcade.Game.PresentationPolicy.Constrained?1:Mathf.Clamp01(elapsed/.32f);
            float pop=1+Mathf.Sin(t*Mathf.PI)*.035f;
            summary.localScale = Vector3.one * scale * pop;
            summary.anchoredPosition=new Vector2(-36+(1-t)*70,-36);
            summaryFade.alpha=Mathf.Clamp01(t*2);''')
s=s.replace('(292 + 16)', '(370 + 16)')
s=s.replace('new Vector2(440,292)', 'new Vector2(440,370)')
s=s.replace('c.quality = GolfShotHud.Label', 'c.summaryFade=c.summary.gameObject.AddComponent<CanvasGroup>();\n            c.quality = GolfShotHud.Label')
s=s.replace('c.remaining = UiKit.Pill', '''c.extra=GolfShotHud.Label(c.summary,"Roll and apex",24,new Vector2(28,-282),new Vector2(384,62));
            c.extra.color=GolfShotHud.Mint;
            c.remaining = UiKit.Pill''')
s=s.replace('go.SetActive(false);', '''c.countdown=UiKit.Label(c.footer,"Next player countdown",25,TextAnchor.MiddleCenter,new Vector2(.5f,0),new Vector2(.5f,0),new Vector2(0,40),new Vector2(440,56),UiKit.Strong,false);
            c.countdown.color=Color.white;
            var bar=UiKit.Panel(c.footer,"Countdown track",GolfShotHud.Ink,new Vector2(0,0),new Vector2(1,0),Vector2.zero,new Vector2(0,6),false);
            c.progress=UiKit.Panel(bar.transform,"Time left",GolfShotHud.Mint,Vector2.zero,Vector2.one,Vector2.zero,Vector2.zero,false);
            c.progress.rectTransform.offsetMin=c.progress.rectTransform.offsetMax=Vector2.zero;
            c.countdown.gameObject.SetActive(false);c.progress.transform.parent.gameObject.SetActive(false);
            go.SetActive(false);''')
s=s.replace('gameObject.SetActive(true); LateUpdate();', '''elapsed=0;countDistance=false;extra.text="";
            next.gameObject.SetActive(true);countdown.gameObject.SetActive(false);progress.transform.parent.gameObject.SetActive(false);
            gameObject.SetActive(true); LateUpdate();''')
s=s.replace('quality.text = grade.TrimEnd', 'quality.color=gradeColor;\n            quality.text = grade.TrimEnd')
idx=s.rfind('    }')
s=s[:idx]+'''        public void ShowGolf(string player,string outcome,double carryYards,double rollYards,double apexYards,double remainingYards,bool putt,bool holed) {
            Show(player,GolfShotHud.Mint,outcome,new (string,string,string)[0],holed?"HOLED!":$"{remainingYards:F0} yd TO PIN",null,0,0,"",new[]{"WAVE","SCUBA","SPIKE"},null,_=>false);
            quality.text=player.ToUpperInvariant()+" · "+outcome;
            Icons.Fit(quality,18,28);
            targetDistance=(float)((carryYards+rollYards)*(putt?3:1));distanceUnit=putt?"ft":"yd";countDistance=true;
            carry.text=$"TOTAL DISTANCE\\nCARRY  {carryYards:F0} yd";
            extra.text=$"ROLL  {rollYards:F0} yd     APEX  {apexYards:F0} yd";
            // Phones own emote selection during multiplayer; the TV leaves the party visible.
            foreach(var button in emotes)button.gameObject.SetActive(false);
            footer.GetComponentsInChildren<Text>().FirstOrDefaultLabel();
        }
        public void SetCountdown(float seconds,string label) {
            next.gameObject.SetActive(false);countdown.gameObject.SetActive(true);progress.transform.parent.gameObject.SetActive(true);
            countdown.text=label+" IN "+Mathf.CeilToInt(Mathf.Max(0,seconds));
            progress.rectTransform.anchorMax=new Vector2(Mathf.Clamp01(seconds/3),1);
        }
''' + s[idx:]
s=s.replace('            footer.GetComponentsInChildren<Text>().FirstOrDefaultLabel();\n','')
s=s.replace('emotes[i].GetComponentInChildren<Text>().text = emoteLabels[i].ToUpperInvariant();','emotes[i].gameObject.SetActive(true);\n                emotes[i].GetComponentInChildren<Text>().text = emoteLabels[i].ToUpperInvariant();')
p.write_text(s)
