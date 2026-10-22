import bpy,sys
base=sys.argv[sys.argv.index('--')+1]
with bpy.data.libraries.load(base) as (df,dt): dt.objects=df.objects
b={o.name[:-4]:o for o in dt.objects if o}
for n in ('MARKER_PIN','MARKER_TEE','BALL_START','HOLE_CUP','FLAG','FLAG_POLE','TEE_MARKER_1','TEE_MARKER_2','MARKER_UP'):
    c=bpy.data.objects[n]; print("MK",n,tuple(round(x,4) for x in b[n].location),tuple(round(x,4) for x in c.location), c.parent)
