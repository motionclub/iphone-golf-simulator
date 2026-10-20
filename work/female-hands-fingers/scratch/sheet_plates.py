from PIL import Image, ImageDraw
names = ['p_bald_front_vL.png','p_bald_front_vR.png','p_bald_back_vL.png','p_bald_back_vR.png']
ims = [Image.open('tmp/'+n) for n in names]
W = sum(i.width for i in ims) + 10*(len(ims)-1); H = max(i.height for i in ims)
s = Image.new('RGB', (W, H), (20,20,24)); x = 0
d = ImageDraw.Draw(s)
labels = ['bald FRONT: viewer-left hand', 'bald FRONT: viewer-right hand', 'bald BACK: viewer-left', 'bald BACK: viewer-right']
for i, im in enumerate(ims):
    s.paste(im, (x, 0)); d.text((x+6, 6), labels[i], fill=(255,230,120)); x += im.width + 10
s.save('proof/ref_plate_hands_bald_8x.png'); print(s.size)
