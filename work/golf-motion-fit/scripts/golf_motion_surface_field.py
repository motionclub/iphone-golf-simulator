"""Logo-free, neutral construction relief in bind-space metres."""
import numpy as np
def gaussian(d,width):return np.exp(-(d/width)**2)
def stitch(coord,spacing=.004):return gaussian(np.remainder(coord+spacing/2,spacing)-spacing/2,.00055)
def field(p,piece,sex):
 x,y,z=p.T;n=len(p);h=np.zeros(n);fold=np.zeros(n);cavity=np.ones(n);trim=np.zeros(n);fabric=np.full(n,7.0)
 if piece=='Kit_Top':
  hem=gaussian(z-.975,.0022);vent=gaussian(abs(y)-.006,.0018)*(abs(x)>.15)*(z<.986)
  placket=gaussian(abs(x)-.019,.0016)*(z>1.21)*(z<1.37)*(y<-.025)
  shoulder=gaussian(z-(1.39 if sex=='Male' else 1.30),.0025)*(abs(x)>.07)
  seam=hem+placket+vent+.4*shoulder;h+=seam*.00035;h+=seam*stitch(x+z)*.00018
  waist=gaussian(z-1.035,.10)*(abs(x)<.18);h+=.0011*np.sin((z+x*.32)*85)*waist;fold=abs(np.sin((z+x*.32)*85))*waist*.30
  cavity=np.clip(1-.16*seam, .74,1);fabric[:]=7
 elif piece=='Kit_Bottom':
  fabric[:]=6
  if sex=='Male':
   centre=np.where(x>0,.108,-.108);crease=gaussian(x-centre,.003)*(y<-.03)*(z>.14)*(z<.88)
   h+=crease*.0008;seam=gaussian(z-.123,.002)+gaussian(z-.976,.002)+gaussian(abs(x)-.215,.0022)*(z>.45)
   h+=.00035*seam+.00016*seam*stitch(y+z);fold=.25*gaussian(z-.17,.032)*abs(np.sin(z*110));h+=.0010*np.sin(z*110)*gaussian(z-.17,.032)
  else:
   radial=np.arctan2(x,-y);t=np.clip((.985-z)/.44,0,1);pleat=np.cos(radial*18)
   h+=.0016*pleat*t*t;fold=np.maximum(-pleat,0)*t*.35
   seam=gaussian(z-.545,.002)+gaussian(z-.985,.002);h+=.00035*seam+.00016*seam*stitch(x+y)
  cavity=np.clip(1-.14*seam-.12*fold,.74,1)
 elif piece=='Kit_Head':
  fabric[:]=6;r=np.sqrt(x*x+y*y);az=np.arctan2(x,y);panels=gaussian(np.sin(az*3)*r,.0013)*(z>1.49)
  brim=gaussian(z-1.493,.0018)*(y<-.075);h+=panels*.0005+brim*stitch(x,.0038)*.0003
  cavity=np.clip(1-.18*panels-.12*brim,.74,1)
 elif piece.startswith('Kit_Glove'):
  fabric[:]=8;dots=gaussian(np.remainder(x,.006)-.003,.0007)*gaussian(np.remainder(z,.006)-.003,.0007)
  h-=dots*.00026;cavity=np.clip(1-.25*dots,.74,1)
  h+=.0004*np.sin(z*90)*gaussian(z-(1.03 if sex=='Male' else .98),.04)
 elif piece.startswith('Kit_Sock'):
  fabric[:]=1;h+=.0002*np.cos(z*500);cavity[:]=.98
 else:
  fabric[:]=9;welt=gaussian(z-.035,.002);h+=.00055*welt+.0002*welt*stitch(y)
  panel=gaussian(abs(y)-.068,.0025)*(z>.06);h+=.00045*panel+.00016*panel*stitch(x+z)
  cavity=np.clip(1-.16*welt-.16*panel,.74,1)
 return h,fold,cavity,trim,fabric
