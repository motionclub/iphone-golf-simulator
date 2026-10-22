# BEFORE | MODERN TARGET | classic charm (small). Usage: python3 build_sheets.py [after_dir] -> adds AFTER panel.
# Run from targets-2026-10-14/. Needs Pillow. Reads current/*.jpg and refs/.
import sys,os,textwrap
from PIL import Image,ImageDraw,ImageFont
B=lambda s:ImageFont.truetype(next(p for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/System/Library/Fonts/Supplemental/Arial Bold.ttf','/Library/Fonts/Arial Bold.ttf'] if os.path.exists(p)),s)
C='current/';R='refs/';A=sys.argv[1] if len(sys.argv)>1 else None
# name, title, current, modern ref, modern label, classic ref, classic label, wrong now, modern technique, keep from classic
S=[
('01_tennis_resort_lighting','TENNIS RESORT - LIGHT + COURT','tennis_resort_1_gameplay','modern_mariotennisfever_2026_grass_court.jpg','Mario Tennis Fever (2026)','switchsports_42d806.jpg','Switch Sports 2022',
 'One flat teal court on a slightly darker teal surround; flat light, grey shadows; nothing has material response.',
 'Stylized PBR-ish court (grain + soft spec), baked GI bounce so the court colour tints nearby walls/players, soft contact shadows, detailed stadium dressing and crowd.',
 'Clean readable court geometry and bright cheerful palette.'),
('02_tennis_close_cam','TENNIS CLOSE OVER-SHOULDER CAM (NEW DEFAULT)','tennis_resort_2_close','modern_astrobot_2024_grass_tree_gi.jpg','Astro Bot (2024)','switchsports_a8af66.jpg','Switch Sports 2022',
 'Hero is a dark shape on teal; no rim; background as sharp as foreground.',
 'Strong rim + warm key, rich skylight bounce, depth of field on the far background (cheap: 1/4-res blur on High only), bloom on sky/water, flower/grass detail near camera.',
 'Hero stays big and readable; simple uncluttered framing.'),
('03_tennis_surface','TENNIS COURT SURFACE + LINES + NET','tennis_resort_4_surface','modern_mariotennisfever_2026_wonder_court.jpg','Mario Tennis Fever (2026)','mta_marina_hard.jpg','Mario Tennis Aces 2018',
 'No grain or wear; thin dull lines; net is a dark smear.',
 'Layered surface material: fine acrylic/grass normal + roughness variation, baseline wear decals, crisp emissive-ish white lines, real net mesh (alpha-tested) with tape, contrasting run-off.',
 'Hard / clay / grass variety and bold run-off colour bands.'),
('04_tennis_rooftop','TENNIS SKYSCRAPER / ROOFTOP','tennis_skyscraper_1_gameplay','modern_mariokartworld_2025_night_city.jpg','Mario Kart World (2025)','mariotennisaces_eshop_445941.jpg','Mario Tennis Aces 2018',
 'Dim dusk, dark-green court sinks into the floor; skyline is flat cards.',
 'Night city with hundreds of lit windows (emissive atlas), warm street/flood light pools, bloom, atmospheric glow on the skyline, reflective wet-look floor via material params.',
 'Stadium floodlight drama and a court that is always the brightest thing.'),
('05_tennis_volcano','TENNIS VOLCANO / CRATER','tennis_volcano_1_gameplay','modern_dkbananza_2025_lava_world.jpg','Donkey Kong Bananza (2025)','mta_inferno_court.jpg','Mario Tennis Aces 2018',
 'Almost black; court and lines barely readable; lava light never reaches the court.',
 'Lava as a light source: warm bounce baked onto rock and court, emissive flowing lava with crust, heat-haze cards, ember particles, light shafts through smoke (cards).',
 'Light stone court framed by dark crater, lava rivers beside the court.'),
('06_golf_tee','GOLF TEE - CLIFFSIDE 07','golf_07_clear_1_tee_gameplay','modern_mariokartworld_2025_grass_meadow.jpg','Mario Kart World (2025)','mariogolfsuperrush_eshop_e4ffb9.jpg','Mario Golf Super Rush 2021',
 'Neon uniform lime turf with heavy stripes; realistic pines; flat gradient sky; no shadows on turf.',
 'High-detail grass: GPU-instanced grass tufts near camera with wind sway, colour variation and subsurface backlight; round toy trees with soft AO; painted volumetric-looking clouds.',
 'Clear fairway/rough/green readability and a centred tee view.'),
('07_golf_approach_depth','GOLF APPROACH - WINDMILL LINKS 20','golf_20_clear_2_approach','modern_dkbananza_2025_meadow_depth.jpg','Donkey Kong Bananza (2025)','mgsr_JPBonnyGreensAlt.jpg','Mario Golf Super Rush 2021',
 'Single row of trees on a flat horizon; no hills; everything same saturation.',
 'Aerial perspective: distance + height fog tinted by sky, layered silhouettes, sun glow/god rays (cards), flower fields in foreground, soft cloud shadows sliding over fairway.',
 'Rolling hills and course layout readability from the Mario Golf overview.'),
('08_golf_island','GOLF ISLAND - WILD ISLES 14','golf_14_clear_2_approach','modern_astrobot_2024_water_sky.jpg','Astro Bot (2024)','mgsr_MGSR_UK_Ridgerock_Lake.jpg','Mario Golf Super Rush 2021',
 'Trees/rocks float on water as cut-outs; obvious tiled water normal; flat sky.',
 'Stylized water: depth-based colour (shallow turquoise to deep blue), animated foam lines at shore, sparkly sun specular, sky reflection (planar-free: cubemap), big cumulus sky.',
 'Real landforms carrying foliage; dramatic cliffs.'),
('09_golf_magma','GOLF MAGMA - EMBER CAUSEWAY 22','golf_22_clear_2_approach','modern_dkbananza_2025_warm_canyon.jpg','Donkey Kong Bananza (2025)','mta_inferno_court.jpg','Mario Tennis Aces 2018',
 'Lava is a loud tiled pattern; turf neon green under a sunset; black rock reads as void.',
 'Warm baked bounce on every surface, rim-lit rock edges, emissive lava with flow-map motion, thick atmospheric haze, embers.',
 'Bold lava silhouette and fun danger feel.'),
('10_golf_snow','GOLF SNOW - FROSTBITE FJORD 17','golf_17_clear_2_approach','modern_dkbananza_2025_snow.jpg','Donkey Kong Bananza (2025)','mgsr_Blustery_Basin_View.png','Mario Golf Super Rush 2021',
 'Flat cyan ice with drawn cracks; snow with no blue shadow or sparkle.',
 'Snow with subsurface softness, blue shadows, glitter specular, frosted foliage; ice with depth, refraction-look gradient and white rim.',
 'Frosted tree silhouettes and a clear icy hazard read.'),
('11_golf_rain_storm','GOLF WEATHER - RAIN / STORM','golf_20_storm_1_tee_gameplay','modern_tinyglade_2024_night_damp.jpg','Tiny Glade (2024)','mgsr_MGSR_UK_Wildweather_Woods.jpg','Mario Golf Super Rush 2021',
 'Rain/storm just greys the frame; turf stays bright and dry; rain hard to see.',
 'Wet look via material params (darker albedo, lower roughness, sky-cubemap reflections, puddle mask on paths/bunkers), moody cool key, rain sheets as cards toward horizon, lightning flash lights scene.',
 'Storm still playable: course shapes stay readable.'),
('12_golf_fog','GOLF WEATHER - FOG','golf_07_fog_2_approach','modern_tinyglade_2024_haze_dof.jpg','Tiny Glade (2024)','botw_37559b.jpg','Zelda BotW 2017',
 'Uniform grey wall; kills all colour.',
 'Soft tinted height fog + low-lying fog cards, colour kept near camera, warm sun glow through fog, slight DOF on far layers.',
 'Silhouette layering for depth.'),
('13_golf_gusty','GOLF WEATHER - GUSTY','golf_07_gusty_1_tee_gameplay','modern_sky_cotl_wind_grass.jpg','Sky: Children of the Light','botw_713726.jpg','Zelda BotW 2017',
 'Looks identical to Clear.',
 'Wind you can see: grass/foliage vertex sway driven by wind strength+direction, leaf/petal particles, fast cloud shadows, flags and tree crowns leaning.',
 'Big sky with readable cloud motion.'),
('14_hub_plaza','HUB - COUNTRY CLUB PLAZA','hub_2_walk','modern_tinyglade_2024_cozy_village.jpg','Tiny Glade (2024)','acnh_0f7818.jpg','Animal Crossing 2020',
 'Strongest scene; lamps/windows do not glow; paving flat; props float slightly.',
 'Rich baked GI and AO, warm emissive windows/lamps with bloom, micro-detail on stone/paving, soft DOF on background, gentle dust motes.',
 'Classic Country Club layout and palette; cosy ACNH-style charm.'),
]
W,H=1100,619;SW,SH=440,248
def fit(p,w,h):
  im=Image.open(p).convert('RGB');s=max(w/im.width,h/im.height);im=im.resize((int(im.width*s),int(im.height*s)));l=(im.width-w)//2;t=(im.height-h)//2;return im.crop((l,t,l+w,t+h))
def wrap(d,x,y,t,f,fill,width):
  for line in textwrap.wrap(t,width):d.text((x,y),line,font=f,fill=fill);y+=f.size+6
  return y
out='sheets' if not A else 'sheets_after';os.makedirs(out,exist_ok=True);thumbs=[]
for n,title,cur,mref,mlab,cref,clab,bad,tech,keep in S:
  big=[(C+cur+'.jpg','BEFORE (current 2026-10-14)',(255,170,120))]
  if A: big.append((os.path.join(A,cur+'.jpg'),'AFTER',(150,255,150)))
  big.append((R+mref,'MODERN TARGET - '+mlab,(140,220,255)))
  cw=len(big)*(W+10)+SW+20;c=Image.new('RGB',(cw,H+300),(24,24,30));d=ImageDraw.Draw(c)
  d.text((10,10),title,font=B(38),fill='white')
  for i,(p,lab,col) in enumerate(big):
    if os.path.exists(p): c.paste(fit(p,W,H),(10+i*(W+10),64))
    d.text((10+i*(W+10),H+72),lab,font=B(25),fill=col)
  x=10+len(big)*(W+10)
  c.paste(fit(R+cref,SW,SH),(x,64))
  d.text((x,SH+72),'CLASSIC CHARM - '+clab,font=B(18),fill=(200,200,200))
  d.text((x,SH+98),'layout / charm only',font=B(18),fill=(255,120,120))
  d.text((x,SH+120),'(NOT a fidelity target)',font=B(18),fill=(255,120,120))
  y=wrap(d,10,H+112,'WRONG NOW: '+bad,B(23),(255,140,140),170)
  y=wrap(d,10,y+6,'MODERN TECHNIQUE TO COPY: '+tech,B(23),(255,235,140),170)
  wrap(d,10,y+6,'KEEP FROM CLASSIC: '+keep,B(23),(170,230,170),170)
  c.save(f'{out}/{n}.jpg',quality=86);thumbs.append(c.resize((c.width//4,c.height//4)))
tw,th=thumbs[0].size;o=Image.new('RGB',(tw*2,th*((len(thumbs)+1)//2)),'black')
for i,t in enumerate(thumbs):o.paste(t,((i%2)*tw,(i//2)*th))
o.save(f'{out}/00_overview.jpg',quality=85);print('ok',len(S))
