const S=await getSection(); const out={};
const HD={hole:'Hole 01 · Par 4',dist:'416',club:'Driver · 240',wind:'Calm'};
// G1 Golf aim
{const F=scene(S,'G · Golf — Aim (tee)',100,120,1920,1080,'bg_golf_aim');
 holePanel(F,24,24,HD); lieChip(F,24,192,'Tee','Clean lie');
 shotMap(F,1628,24,'map_golf_aim',[['100%',56,93],['75%',97,109],['50%',58,127],['25%',100,145]]);
 pinPill(F,1120,252,'416 yd');
 powerMeter(F,24,512,0,'— yd'); clubSelect(F,24,944,'DR'); out.aim=F.id;}
// G2 Perfect callout
{const F=scene(S,'G · Golf — Perfect swing callout',2120,120,1920,1080,'bg_golf_perfect');
 holePanel(F,24,24,HD); lieChip(F,24,192,'Tee','Clean lie');
 shotMap(F,1628,24,'map_golf_perfect',[]);
 powerMeter(F,24,512,0.9,'— yd'); clubSelect(F,24,944,'DR');
 const c=glass(F,'Swing callout · Perfect',712,52,496,132,30);rect(c,'Accent',28,34,6,64,CYAN,1,3);
 T(c,'Perfect!',262,66,82,{serif:true,ax:'center',ay:'middle',name:'Callout'}); out.perfect=F.id;}
// G3 Ball flight / shot result
{const F=scene(S,'G · Golf — Ball flight (perfect contact)',4140,120,1920,1080,'bg_golf_shot_result');
 holePanel(F,24,24,HD); lieChip(F,24,192,'Gusty',null,'wind');
 shotMap(F,1628,24,'map_golf_shot_result',[]);
 const pill=glass(F,'Contact quality pill',760,22,400,64,32);rect(pill,'Accent dot',26,26,12,12,CYAN,1,6);T(pill,'Perfect contact',212,32,28,{serif:true,ax:'center',ay:'middle'});
 T(F,'56 yds',1048,465,46,{serif:true,color:WHITE,ax:'center',ay:'middle',effects:TXT_SHADOW,name:'Live carry (in-world)'});
 out.shot=F.id;}
return {out,IMGS,section:S.id};
