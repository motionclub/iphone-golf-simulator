"""Read-only diagnostics on proof retargets; these alone cannot certify G7.

Uses the frozen hero-dressed bind-ray/home-triangle method, with its covered
sample counts, lost correspondences and flipped normals disclosed. Golf's
3 mm limit is used for candidates. No old tennis 15 mm allowance is imported.
Full triangle collision, garment edges and V4 finger motion remain unverified.
"""
import bpy, json, sys, hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import evaluated_co, mesh_tris, mesh_co, activate_clip
from follow_lib import bvh_from, vertex_normals, compute_zone

W=Path(__file__).resolve().parents[1];sex=sys.argv[-1]
sc=bpy.context.scene;rig=bpy.data.objects['Rig_'+sex]
body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M']
names=['Golf_Polo','Golf_Trousers' if sex=='Male' else 'Golf_PleatedSkort',
       'Golf_Glove_Left','Golf_Glove_Right','Golf_Shoe_L','Golf_Shoe_R']
if sex=='Female':names.append('Golf_InnerShorts')
pieces={n:bpy.data.objects[n] for n in names}
cap={o.name:o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('Golf_Cap','Golf_Visor','Golf_CurvedBrim','Golf_BrimStitch'))}
before=hashlib.sha256(repr([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in body.data.vertices]).encode()).hexdigest()
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
sc.frame_set(0);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();b0=evaluated_co(body,dg)
bt=mesh_tris(body.data);bn0=vertex_normals(body);body_bvh=bvh_from(b0,bt)
head0=np.array(rig.matrix_world@rig.data.bones['Head'].matrix_local,dtype=float)
cap0={n:evaluated_co(o,dg) for n,o in cap.items()}
info={}
for n,o in pieces.items():
    co=evaluated_co(o,dg);tri=mesh_tris(o.data)
    z,ht,hb,_,_=compute_zone(co,tri,b0,bn0,body_bvh)
    edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]])
    edges=np.unique(np.sort(edges,axis=1),axis=0)
    lengths=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)
    info[n]=dict(zone=z,tri=tri,ht=ht,hb=hb,edges=edges,lengths=lengths)
    print('BIND',sex,n,'covered body samples',len(z),'of',len(b0),flush=True)

poses=[]
for hand in ['RH','LH']:
    for state in ['ReadyIdle','Top','Impact','Finish']:
        action='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}'
        activate_clip(rig,action);sc.frame_set(0);bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get();b=evaluated_co(body,dg)
        row=dict(action=action,handedness=hand,state=state,pieces={},headwear={})
        for n,o in pieces.items():
            if n==('Golf_Glove_Right' if hand=='RH' else 'Golf_Glove_Left'):continue
            d=info[n];z,tri,ht,hb=d['zone'],d['tri'],d['ht'],d['hb']
            co=evaluated_co(o,dg)
            record=dict(covered_body_samples=len(z),total_body_vertices=len(b),sample_scope='bind rays within 35 mm with a two-wall shell pattern; not full surface coverage')
            if len(z):
                T=tri[ht];a,c,e=co[T[:,0]],co[T[:,1]],co[T[:,2]]
                P=a*hb[:,0:1]+c*hb[:,1:2]+e*hb[:,2:3]
                N=np.cross(c-a,e-a);N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-18)
                h=np.einsum('ij,ij->i',b[z]-P,N)
                dist=np.linalg.norm(b[z]-P,axis=1);near=dist<=.06
                k=int(np.argmax(np.where(near,h,-np.inf))) if near.any() else None
                record.update(candidate_poke_max_mm=float(max(0,h[near].max())*1000) if near.any() else None,
                              candidate_over_3mm=int(((h>.003)&near).sum()),
                              lost_home_correspondences=int((~near).sum()),
                              worst_body_vertex=int(z[k]) if k is not None else None,
                              candidate_status='FAIL' if ((h>.003)&near).any() or (~near).any() else 'INCOMPLETE: no candidate >3 mm; coverage not exhaustive')
            else:record.update(candidate_status='UNMEASURED: no covered samples',candidate_poke_max_mm=None)
            if 'Glove' in n:
                edges=d['edges'];mask=d['lengths']>.002
                ratio=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)[mask]/d['lengths'][mask]
                record['edge_ratio']=dict(edges_over_2mm=int(mask.sum()),min=float(ratio.min()),p01=float(np.percentile(ratio,1)),max=float(ratio.max()),scope='strain diagnostic; finger volume/collision and gripping still unverified')
            row['pieces'][n]=record
        head=np.array(rig.matrix_world@rig.pose.bones['Head'].matrix,dtype=float)
        transform=head@np.linalg.inv(head0)
        for n,o in cap.items():
            expect=cap0[n]@transform[:3,:3].T+transform[:3,3]
            actual=evaluated_co(o,dg)
            delta=np.linalg.norm(expect-actual,axis=1)*1000
            row['headwear'][n]=dict(vertices=len(delta),rigid_head_drift_max_mm=float(delta.max()),within_2mm=bool(delta.max()<=2),scope='drift from initial rigid Head attachment; bind clearance/collision not certified')
        poses.append(row)
        worst=max((p.get('candidate_poke_max_mm') or 0) for p in row['pieces'].values())
        print('POSE',sex,hand,state,'candidate poke mm',round(worst,3),flush=True)

after=hashlib.sha256(repr([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in body.data.vertices]).encode()).hexdigest()
assert before==after,'Body changed by measurement'
out=dict(sex=sex,body_unchanged=True,source=str(Path(bpy.data.filepath)),poses=poses,
         G7='FAIL: construction/coverage/finger grip/collision verification incomplete; any candidates must be investigated',
         thresholds_mm=dict(poke=3,headwear_drift=2),
         limitations=['Bind-zone vertex samples do not verify all triangle interiors or garment edges.',
                     'The V4 rig has no finger bones; these fingers use ReadyIdle-derived poses.',
                     'Lost home correspondences are reported as failures, never converted to zero.',
                     'Headwear drift verifies attachment stability, not bind fit or hair collision.'])
(W/f'data/deform_draft_{sex}.json').write_text(json.dumps(out,indent=2)+'\n')
print('G7 draft diagnostics saved; no PASS claimed',flush=True)
