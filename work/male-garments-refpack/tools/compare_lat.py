"""compare_lat.py <tag> <design> <side> : reference lateral crop | our lateral at the same scale | outline overlay."""
import sys; sys.argv += [] ; exec(open('tools/preview_shoe.py').read().split("c=P.mean(0); sc=1150")[0].replace("tag, design, side = sys.argv[1:4]; out = sys.argv[4] if len(sys.argv)>4 else f'build/{tag}_sheet.png'","tag, design, side = sys.argv[1:4]"))
from seg import load, classify
REF = {'male_tennis': ('13-tennis-shoe-detail', (62, 590, 670), (20, 230, 780, 620), np.array([217,215,211.])),
       'male_golf': ('14-golf-shoe-detail', (50, 548, 640), (20, 230, 760, 600), np.array([212,210,206.]))}
sheet, (x0, y0, Lp), box, bg = REF[design]
ref = load(sheet)[box[1]:box[3], box[0]:box[2]]
W, H = box[2] - box[0], box[3] - box[1]
sc = Lp / D['Ls']
# shoe frame: heel back (s=0) and sole bottom (h=0) -> reference pixels
yb = -D['heel_off']; zb = D['zb']
# our model is in mesh space: toe toward -y for both sides here; lateral view of R = looking from +x
view = [[0,-1,0],[0,0,1],[1,0,0]] if side=='R' else [[0,1,0],[0,0,1],[-1,0,0]]
# find heel back + ground of the built shoe in mesh space: s4/h4 fields give it directly
s4v, h4v = d['v_s4'], d['v_h4']
i0 = np.argmin(np.abs(s4v)); # a vertex near s=0
# solve the mapping screen = A*mesh: use two vertices' (s,h)
Q = P @ np.asarray(view, float).T
# linear fit of s4 against screen x, h4 against screen y
ax = np.polyfit(Q[:,0], s4v, 1); ay = np.polyfit(Q[:,1], h4v, 1)
# screen origin such that s=0 -> x0-box0, h=0 -> y0-box1
org_x = (0 - ax[1]) / ax[0]; org_y = (0 - ay[1]) / ay[0]
img = Image.new('RGB', (W, H), (214,212,208))
dr = ImageDraw.Draw(img)
n=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
Lg=np.array([.35,-.45,.82]); Lg/=np.linalg.norm(Lg); sh=np.clip(n@Lg,0,1)*.55+.45
xs = (x0-box[0]) + (Q[T][:,:,0]-org_x)*sc*np.sign(ax[0]); ys = (y0-box[1]) - (Q[T][:,:,1]-org_y)*sc*np.sign(ay[0])
dep = Q[T][:,:,2].mean(1)
for i in np.argsort(dep):
    dr.polygon([(xs[i,0],ys[i,0]),(xs[i,1],ys[i,1]),(xs[i,2],ys[i,2])], fill=tuple(int(v) for v in col[i]*sh[i]))
ours = np.asarray(img).astype(float)
fg_r, _ = classify(ref, bg); fg_o = np.abs(ours - np.array([214,212,208])).sum(2) > 6
ov = ref.copy()*.6 + 255*.4
ov[fg_o & ~fg_r] = [230, 60, 60]; ov[fg_r & ~fg_o] = [60, 120, 230]
iou = (fg_o & fg_r).sum() / max(1, (fg_o | fg_r).sum())
out = np.concatenate([ref, ours, ov], 1).astype(np.uint8)
Image.fromarray(out).save(f'build/{tag}_lat_cmp.png'); print('IoU %.3f' % iou)
# outline curves in sheet units: per column (s), the top and bottom of each silhouette
def curves(m):
    cols = np.nonzero(m.any(0))[0]; top = {}; bot = {}
    for c in cols:
        r = np.nonzero(m[:, c])[0]; top[c] = r.min(); bot[c] = r.max()
    return top, bot
fg_r2 = fg_r.copy(); fg_r2[(y0 - box[1]) + 3:] = False      # ground shadow
tr, br = curves(fg_r2); to, bo = curves(fg_o)
print('   s    ref_top  our_top   ref_bot  our_bot   (h = sheet units)')
for sv in np.linspace(-.02, 1.02, 27):
    c = int(round(x0 - box[0] + sv * Lp))
    f = lambda d: ('%7.3f' % ((y0 - box[1] - d[c]) / Lp)) if c in d else '    -  '
    print('%6.3f  %s  %s   %s  %s' % (sv, f(tr), f(to), f(br), f(bo)))
