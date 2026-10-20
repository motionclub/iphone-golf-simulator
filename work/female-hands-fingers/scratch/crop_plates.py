from PIL import Image, ImageDraw
B = '../../ArtDir/hero/base_lock/'
bald = Image.open(B + 'female_body_bald.jpg').convert('RGB')
multi = Image.open(B + 'female_multiangle_body.jpg').convert('RGB')
print(bald.size, multi.size)
def crop(im, box, scale, name):
    c = im.crop(box); c = c.resize((int(c.width*scale), int(c.height*scale)), Image.LANCZOS); c.save('tmp/'+name); print(name, c.size)
# bald front: viewer-left hand (character's right hand) and viewer-right hand (character's left)
crop(bald, (320, 330, 380, 430), 8, 'p_bald_front_vL.png')
crop(bald, (500, 330, 560, 430), 8, 'p_bald_front_vR.png')
# bald back
crop(bald, (730, 330, 790, 430), 8, 'p_bald_back_vL.png')
crop(bald, (910, 330, 970, 430), 8, 'p_bald_back_vR.png')
