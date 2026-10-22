import sys; from PIL import Image
pre=sys.argv[1:]  # list of prefixes -> rows
ks=['palm','back','front','side','q3']
rows=[]
for p in pre:
    for h in 'RL':
        rows.append([Image.open(f'r/{p}_hand{h}_{k}.png').convert('RGB').resize((360,360)) for k in ks])
S=Image.new('RGB',(360*5,360*len(rows)))
for r,row in enumerate(rows):
    for c,im in enumerate(row): S.paste(im,(c*360,r*360))
S.save('r/sheet_'+'_'.join(pre)+'.png'); print(S.size)
