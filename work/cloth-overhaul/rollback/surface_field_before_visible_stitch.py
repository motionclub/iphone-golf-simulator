import numpy as np

def field(P,piece,sex):
 x,y,z=P.T;h=np.zeros_like(x);fold=np.zeros_like(x);cavity=np.ones_like(x);trim=np.zeros_like(x);fabric=np.zeros_like(x)
 def g(d,w):return np.exp(-(d/w)**2)
 front=np.clip(-y/.065,0,1);back=np.clip(y/.05,0,1)
 if piece=='Kit_Top':
  hem=.956 if sex=='Male' else .989
  # Double-needle turned hem and princess/side seam construction, all in physical metres.
  for offset in [0,.0045]:
   seam=g(z-hem-offset,.00075);stitch=(.5+.5*np.cos(x*2*np.pi/.0035))**6
   h+=.00032*seam*stitch;cavity-=.28*seam*stitch
  side=g(np.abs(x)-(.175 if sex=='Male' else .136),.0012)*g(z-1.13,.16)
  if sex=='Female':side+=g(np.abs(x)-(.065+.04*(z-1.1)),.0011)*front*g(z-1.17,.15)
  h-=.00038*side;cavity-=.12*side
  waist=g(z-(1.025 if sex=='Male' else 1.04)-.12*np.abs(x),.022)*(0.5+0.5*np.sin(x*85))
  pit=g(np.abs(x)-(.235 if sex=='Male' else .14),.075)*g(z-(1.205 if sex=='Male' else 1.16)+.45*(np.abs(x)-(.235 if sex=='Male' else .14)),.018)
  shoulder=g(z-(1.30 if sex=='Male' else 1.255)-.10*np.cos(x*14),.012)*back
  fold=np.clip((waist+pit)+.7*shoulder,0,1)
  h-=.0013*fold
  collar=(z>(1.325 if sex=='Male' else 1.28))&(np.abs(x)<.14);fabric[collar]=1
  # Cuff zones are physical bands, not the old thin collar piping.
  sleeve=(np.abs(x)>(.258 if sex=='Male' else .125))&(z<(1.235 if sex=='Male' else 1.148));fabric[sleeve]=1
  cuff=g(z-(1.174 if sex=='Male' else 1.125)+.55*(np.abs(x)-(.30 if sex=='Male' else .18)),.0035)*sleeve
  trim=np.maximum(trim,cuff);h+=.00065*cuff
  # Buttonhole bartacks alongside the existing three real buttons.
  for bz in ([1.365,1.328,1.29] if sex=='Male' else [1.30,1.269,1.238]):
   hole=g(x-.010,.0035)*g(z-bz,.00075)*front;h-=.00025*hole;cavity-=.30*hole
 elif piece=='Kit_Bottom':
  if sex=='Male':
   hem=.594+.045*np.abs(y+.035);k=g(z-hem,.0012);st=(.5+.5*np.cos((x+y)*2*np.pi/.004))**6;h+=.0004*k*st;cavity-=.20*k*st
   crotch=g(x,.055)*g(z-.806-.6*np.abs(x),.014)*front
   hip=g(np.abs(x)-.17,.055)*g(z-.858-.45*(np.abs(x)-.15),.012)*front
   fold=np.clip(crotch+hip,0,1);h-=.0015*fold
   pocket=g(np.abs(x)-(.15+.50*(.905-z)),.0014)*g(z-.86,.053)*front;h-=.0007*pocket;cavity-=.3*pocket
   fly=g(x,.0013)*g(z-.878,.04)*front;h-=.00045*fly;cavity-=.12*fly
   cord=(np.abs(x)<.04)&(z>.89)&(y<-.185);fabric[cord]=5
  else:
   theta=np.arctan2(y,x);phase=(theta/(2*np.pi)*12)%1;d=np.minimum(np.abs(phase-.72),1-np.abs(phase-.72))
   taper=np.clip((.945-z)/.23,0,1);pleat=g(d,.045)*taper
   h-=.0015*pleat;fold=.8*pleat
   hem=.642+.020*np.abs(y);k=g(z-hem,.0011);st=(.5+.5*np.cos(theta*135))**6;h+=.00042*k*st;cavity-=.25*k*st
  band=z>(.925 if sex=='Male' else .955);fabric[band]=1;trim[band]=1
 elif 'Sock' in piece:
  fabric[:]=0;fabric[z>.235]=1
  cuff=g(z-(.294 if sex=='Male' else .279),.002);h+=.0008*cuff;cavity-=.14*cuff
  dense=(z<.05)|((y>(.045 if sex=='Male' else .07))&(z<.10));fabric[dense]=1
 elif 'Shoe' in piece:
  fabric[:]=2
  foam=(z<.014)&(z>-.015);fabric[foam]=4
  rubber=z<=-.015;fabric[rubber]=3;trim[rubber]=1
  toe=y<(-.169 if sex=='Male' else -.10);fabric[toe]=3
  # Transverse toe-cap panel, heel counter, double panel stitching.
  for yy in ([-.168,.026] if sex=='Male' else [-.10,.066]):
   s=g(y-yy,.001);dash=(.5+.5*np.cos(x*2*np.pi/.0038))**6;h-=.0005*s;cavity-=.22*s*dash
  toeedge=g(y-(-.168 if sex=='Male' else -.10),.003)*np.clip(z/.03,0,1);h+=.0009*toeedge
  heel=y>(.067 if sex=='Male' else .095);trim[heel&(z>.085)]=1
  center=(.203 if sex=='Male' else .128)*np.sign(x)
  lace=(np.abs(x-center)<.031)&(y>(-.18 if sex=='Male' else -.102))&(y<(-.075 if sex=='Male' else -.024))&(z>(.07 if sex=='Male' else .048));fabric[lace]=5
  # Herringbone high tread on sole faces; foam gets a faint, broad pebble break.
  chevron=np.sin((y+np.abs(x-center)*.8)*2*np.pi/.009)
  h+=rubber*(.00065*np.maximum(chevron,0));h+=foam*.00013*np.sin(x*700)*np.sin(y*680)
 return h,fold,np.clip(cavity,.70,1),trim,fabric
