"""blender -b file.blend --python dump_blend.py -- out.npz : exact dump of every mesh object for audits"""
import bpy, numpy as np, sys, json
out=sys.argv[sys.argv.index('--')+1]
arrs={}; meta={'objects':[]}
for o in bpy.data.objects:
    m={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix_world':[list(map(float,r)) for r in o.matrix_world],
       'hide_render':bool(o.hide_render),'modifiers':[x.type for x in o.modifiers]}
    if o.type=='MESH':
        me=o.data; n=len(me.vertices)
        co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); arrs[f'{o.name}/co']=co.reshape(-1,3)
        ps=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get('loop_start',ps); arrs[f'{o.name}/poly_start']=ps
        pt=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get('loop_total',pt); arrs[f'{o.name}/poly_total']=pt
        lv=np.empty(len(me.loops),np.int32); me.loops.foreach_get('vertex_index',lv); arrs[f'{o.name}/loop_vert']=lv
        ed=np.empty(len(me.edges)*2,np.int32); me.edges.foreach_get('vertices',ed); arrs[f'{o.name}/edges']=ed
        mi=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get('material_index',mi); arrs[f'{o.name}/mat_index']=mi
        sm=np.empty(len(me.polygons),np.int8); me.polygons.foreach_get('use_smooth',sm); arrs[f'{o.name}/smooth']=sm
        if 'custom_normal' in me.attributes:
            rw=np.empty(len(me.loops)*2,np.int32); me.attributes['custom_normal'].data.foreach_get('value',rw); arrs[f'{o.name}/custom_normal_raw']=rw.reshape(-1,2)
        for uv in me.uv_layers:
            u=np.empty(len(me.loops)*2,np.float32); uv.data.foreach_get('uv',u); arrs[f'{o.name}/uv/{uv.name}']=u.reshape(-1,2)
        m.update(verts=n,polys=len(me.polygons),loops=len(me.loops),edges=len(me.edges),tris=int(sum(t-2 for t in pt)),
                 materials=[x.name if x else None for x in me.materials],vgroups=[g.name for g in o.vertex_groups],
                 shape_keys=[k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [],
                 attributes=sorted(a.name for a in me.attributes),has_custom_normals=bool(me.has_custom_normals),uv_layers=[u.name for u in me.uv_layers])
    meta['objects'].append(m)
np.savez_compressed(out,**arrs)
json.dump(meta,open(out.replace('.npz','.json'),'w'),indent=1)
print("dumped",out,len(arrs),"arrays")
