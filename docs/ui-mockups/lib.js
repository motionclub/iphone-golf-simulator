const INK={r:21/255,g:62/255,b:82/255}, CYAN={r:117/255,g:221/255,b:235/255}, WHITE={r:1,g:1,b:1}, DEEP={r:22/255,g:60/255,b:59/255}, DIV={r:111/255,g:158/255,b:172/255};
await Promise.all([{family:'Libre Baskerville',style:'Regular'},{family:'Inter',style:'Medium'},{family:'Inter',style:'Semi Bold'},{family:'Inter',style:'Bold'}].map(f=>figma.loadFontAsync(f)));
const GLASS_FILL=[{type:'GRADIENT_LINEAR',gradientStops:[{color:{r:1,g:1,b:1,a:0.933},position:0},{color:{r:0.89,g:0.969,b:1,a:0.863},position:0.5},{color:{r:0.906,g:0.91,b:1,a:0.929},position:1}],gradientTransform:[[0,1,0],[0.5,-0.5,0.5]]}];
const GLASS_FX=[{type:'BACKGROUND_BLUR',radius:24,visible:true},{type:'DROP_SHADOW',radius:32,color:{r:0.09,g:0.243,b:0.365,a:0.133},offset:{x:0,y:12},spread:0,visible:true,blendMode:'NORMAL'}];
const IMGS={};
function place(parent,n,x,y){parent.appendChild(n);n.x=x;n.y=y;return n;}
function frame(parent,name,x,y,w,h,clip=false){const f=figma.createFrame();f.name=name;f.resize(w,h);f.fills=[];f.clipsContent=clip;return place(parent,f,x,y);}
function glass(parent,name,x,y,w,h,r=24){const f=frame(parent,name,x,y,w,h,true);f.fills=GLASS_FILL;f.strokes=[{type:'SOLID',color:WHITE}];f.strokeWeight=2;f.strokeAlign='INSIDE';f.cornerRadius=r;f.effects=GLASS_FX;return f;}
function solid(parent,name,x,y,w,h,color,op=1,r=0){const f=frame(parent,name,x,y,w,h,true);f.fills=[{type:'SOLID',color,opacity:op}];f.cornerRadius=r;return f;}
function rect(parent,name,x,y,w,h,color,op=1,r=0){const n=figma.createRectangle();n.name=name;n.resize(w,h);n.fills=[{type:'SOLID',color,opacity:op}];n.cornerRadius=r;return place(parent,n,x,y);}
function ell(parent,name,x,y,w,h,color,op=1,stroke=null,sw=2){const n=figma.createEllipse();n.name=name;n.resize(w,h);n.fills=color?[{type:'SOLID',color,opacity:op}]:[];if(stroke){n.strokes=[{type:'SOLID',color:stroke.c,opacity:stroke.o??1}];n.strokeWeight=sw;}return place(parent,n,x,y);}
function vec(parent,name,x,y,w,h,data,color=INK,sw=4,fill=false){const v=figma.createVector();v.name=name;v.vectorPaths=[{windingRule:fill?'NONZERO':'NONE',data}];if(fill){v.fills=[{type:'SOLID',color}];v.strokes=[];}else{v.fills=[];v.strokes=[{type:'SOLID',color}];v.strokeWeight=sw;v.strokeCap='ROUND';v.strokeJoin='ROUND';}parent.appendChild(v);v.x=x;v.y=y;return v;}
function img(parent,key,x,y,w,h,r=0){const n=rect(parent,'Image · '+key,x,y,w,h,{r:0.8,g:0.85,b:0.88},1,r);IMGS[key]=n.id;return n;}
function T(parent,str,x,y,size,o={}){const t=figma.createText();t.fontName=o.serif?{family:'Libre Baskerville',style:'Regular'}:{family:'Inter',style:o.w||'Medium'};t.characters=str;t.fontSize=size;t.fills=[{type:'SOLID',color:o.color||INK,opacity:o.op??1}];if(o.caps){t.textCase='UPPER';t.letterSpacing={unit:'PERCENT',value:o.ls??6};}t.name=o.name||str.slice(0,32);parent.appendChild(t);t.textAutoResize='WIDTH_AND_HEIGHT';if(o.lh)t.lineHeight={unit:'PERCENT',value:o.lh};if(o.width){t.textAutoResize='HEIGHT';t.resize(o.width,t.height);t.textAlignHorizontal=o.align||'LEFT';}
 if(o.effects)t.effects=o.effects;
 t.x=o.ax==='center'?x-t.width/2:o.ax==='right'?x-t.width:x; t.y=o.ay==='middle'?y-t.height/2:o.ay==='bottom'?y-t.height:y; return t;}
const TXT_SHADOW=[{type:'DROP_SHADOW',radius:12,color:{r:0.05,g:0.15,b:0.2,a:0.55},offset:{x:0,y:2},spread:0,visible:true,blendMode:'NORMAL'}];
function shade(F){const r=figma.createRectangle();r.name='World legibility shade';r.resize(F.width,F.height);r.fills=[{type:'GRADIENT_LINEAR',gradientStops:[{color:{r:23/255,g:59/255,b:79/255,a:0.22},position:0},{color:{r:20/255,g:60/255,b:68/255,a:0},position:0.22},{color:{r:20/255,g:60/255,b:68/255,a:0},position:0.78},{color:{r:12/255,g:54/255,b:56/255,a:0.24},position:1}],gradientTransform:[[0,1,0],[-1,0,1]]}];return place(F,r,0,0);}
function scene(section,name,x,y,w,h,bgKey){const F=figma.createFrame();F.name=name;F.resize(w,h);F.clipsContent=true;F.fills=[{type:'SOLID',color:{r:0.75,g:0.86,b:0.92}}];section.appendChild(F);F.x=x;F.y=y;if(bgKey){img(F,bgKey,0,0,w,h);shade(F);}return F;}
async function getSection(){let s=figma.currentPage.findChild(n=>n.type==='SECTION'&&n.name==='G · Hybrid on real layout');if(!s){s=figma.createSection();s.name='G · Hybrid on real layout';figma.currentPage.appendChild(s);s.x=-1659;s.y=7900;s.resizeWithoutConstraints(10300,5400);}return s;}
// ---------- golf components ----------
function holePanel(F,x,y,d){const p=glass(F,'Hole info',x,y,320,156,24);
 T(p,d.hole,24,20,19,{w:'Semi Bold',caps:true,op:0.72,name:'Hole · par'});
 const n=T(p,d.dist,22,44,60,{serif:true,name:'Distance to pin'});
 T(p,'yd to pin',22+n.width+10,74,21,{name:'Distance unit'});
 T(p,d.club,24,118,20,{w:'Semi Bold',name:'Club · carry'});
 vec(p,'Wind glyph',222,123,22,14,'M 0 4 L 14 4 Q 20 4 20 0 M 0 10 L 18 10',INK,2.5);
 T(p,d.wind,296,118,20,{ax:'right',name:'Wind'});return p;}
function lieChip(F,x,y,title,sub,icon='ball'){const h=sub?70:56;const p=glass(F,'Lie / status chip',x,y,320,h,22);
 const cy=h/2; if(icon==='ball'){ell(p,'Lie ball',20,cy-17,34,34,{r:0.47,g:0.75,b:0.44},1,{c:WHITE},2);} else {ell(p,'Status icon',20,cy-16,32,32,CYAN,0.8);vec(p,'Wind swirl',27,cy-6,18,12,'M 0 4 L 12 4 Q 17 4 17 0 M 0 10 L 15 10',INK,2.2);}
 if(sub){T(p,title,68,10,26,{serif:true,name:'Lie'});T(p,sub,68,44,15,{w:'Semi Bold',caps:true,op:0.65,name:'Lie detail'});} else T(p,title,68,cy,24,{serif:true,ay:'middle',name:'Status'});return p;}
function shotMap(F,x,y,key,tags){const W=268,H=372;const p=glass(F,'Shot map',x,y,W,H,24);T(p,'Shot map',20,16,24,{serif:true,name:'Map heading'});
 const iw=W-28,ih=Math.round(iw*191/154);img(p,key,14,58,iw,ih,16);const s=iw/154;
 (tags||[]).forEach(([lab,cx,cy])=>{const g=glass(p,'Shot tag '+lab,14+cx*s-34,58+cy*s-15,68,30,15);T(g,lab,34,15,15,{w:'Semi Bold',ax:'center',ay:'middle'});});return p;}
function powerMeter(F,x,y,fill,valueTxt){const W=80,H=304;const p=glass(F,'Power meter (vertical)',x,y,W,H,24);
 T(p,'Power',W/2,16,14,{w:'Semi Bold',caps:true,ax:'center',op:0.75});
 const rx=(W-16)/2,ry=44,rh=208;rect(p,'Power rail',rx,ry,16,rh,INK,0.13,8);rect(p,'Sweet spot',rx-6,ry+rh*0.06,28,rh*0.12,CYAN,1,8);
 if(fill>0){const fh=rh*fill;rect(p,'Power fill',rx+3,ry+rh-fh,10,fh,INK,1,5);ell(p,'Timing pearl',W/2-13,ry+rh-fh-13,26,26,INK,1,{c:WHITE},3);}
 T(p,valueTxt,W/2,H-16,20,{serif:true,ax:'center',ay:'bottom',name:'Power yards'});return p;}
function clubSelect(F,x,y,sel){const p=glass(F,'Select club',x,y,340,114,24);T(p,'Select club',18,12,15,{w:'Semi Bold',caps:true,op:0.72});
 [['PT','Putter'],['DR','Driver'],['HY','Hybrid']].forEach(([a,b],i)=>{const on=a===sel;const tx=18+i*104;const t=on?solid(p,'Club '+b+' (selected)',tx,40,96,60,INK,1,14):solid(p,'Club '+b,tx,40,96,60,INK,0.06,14);if(!on){t.strokes=[{type:'SOLID',color:INK,opacity:0.16}];t.strokeWeight=1.5;t.strokeAlign='INSIDE';}
 T(t,a,48,6,25,{serif:true,ax:'center',color:on?WHITE:INK});T(t,b,48,36,14,{w:'Semi Bold',ax:'center',color:on?WHITE:INK,op:on?0.85:0.7});});return p;}
function pinPill(F,cx,y,dist){const g=glass(F,'Pin marker',cx-90,y,180,48,24);T(g,'Pin',26,24,15,{w:'Semi Bold',caps:true,ay:'middle',op:0.7});T(g,dist,70,24,24,{serif:true,ay:'middle'});rect(F,'Pin stem',cx-1.5,y+48,3,22,WHITE,0.9,1);ell(F,'Pin foot',cx-5,y+68,10,10,WHITE,0.95);return g;}
