"""overlay of mesh normal classes on the plate (front/q3L/q3R): red where the mesh surface faces down (ny<-0.35), green where faces up (ny>0.5).
blender -b --factory-startup --python nrm_overlay.py -- <nrmdir> <outdir>"""
import sys
sys.path.insert(0, '.')
exec(open('photo.py').read().split("if __name__ == '__main__':")[0])
nd, od = sys.argv[sys.argv.index('--') + 1:][:2]
Path(od).mkdir(parents=True, exist_ok=True)
up = 2
for name in ('front', 'q3L', 'q3R', 'left'):
    N, m = load_normals(Path(nd) / f'{name}_nrm.exr')
    box = BOX[name]
    p = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB').crop(box).resize(((box[2]-box[0])*up, (box[3]-box[1])*up), Image.LANCZOS)).astype(float)
    ov = p.copy()
    down = m & (N[..., 1] < -0.35); upw = m & (N[..., 1] > 0.55)
    ov[down] = 0.55 * ov[down] + 0.45 * np.array([255, 40, 40])
    ov[upw] = 0.8 * ov[upw] + 0.2 * np.array([40, 255, 40])
    # contour lines of ny = -0.35 (edge pixels)
    fx0, fy0, fx1, fy1 = FACE[name]
    sl = (slice((fy0 - box[1]) * up, (fy1 - box[1] + 40) * up), slice((fx0 - box[0] - 20) * up, (fx1 - box[0] + 20) * up))
    Image.fromarray(np.concatenate([p[sl], ov[sl]], axis=1).astype(np.uint8)).save(Path(od) / f'nrmov_{name}.png')
print('done')
