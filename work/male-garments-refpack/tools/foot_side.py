import sys; sys.path.insert(0,'tools'); from raster import *
H='MatchHero_Male'
body=part(H,'body'); sock=part(H,'Kit_Sock_R'); shoe=part(H,'Kit_Shoe_R')
P,T=body; keep=(P[T][:,:,2].max(1)<.35)&(P[T][:,:,0].min(1)>.05); body=(P,T[keep])
# right side view (+x looking toward -x): screen x = -y (hero faces -Y, toe toward -y -> left?) use screen x=+y? toe on the right: toe direction -y => screen x = -y
view=[[0,-1,0],[0,0,1],[1,0,0]]
org=np.array([.18,-0.03,.10]); sc=1800
im=render([(body[0],body[1],(214,160,120)),(sock[0],sock[1],(240,240,240)),(shoe[0],shoe[1],(120,170,230))],view,sc,org,(900,600))
im.save('trace/foot_side_today.png')
im2=render([(body[0],body[1],(214,160,120))],view,sc,org,(900,600)); im2.save('trace/foot_side_body.png')
