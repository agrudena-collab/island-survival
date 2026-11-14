import json,sys
D=sys.argv[1]
c=json.load(open(D+'/data/colliders.json')); A=json.load(open(D+'/data/anchors.json'))
ground=[x for x in c if x['tag']=='Ground']; rest=[x for x in c if x['tag']!='Ground']
cols={}
for g in ground: cols.setdefault((g['min'][0],g['max'][0],g['min'][2],g['max'][2]),[]).append((g['min'][1],g['max'][1]))
merged=[]
for k,iv in cols.items():
    iv.sort(); cur=list(iv[0])
    for a,b in iv[1:]:
        if a<=cur[1]+1e-6: cur[1]=max(cur[1],b)
        else: merged.append((k,cur)); cur=[a,b]
    merged.append((k,cur))
boxes=[(x['group'],x['tag'],x['min']+x['max']) for x in rest]
for (x0,x1,z0,z1),(y0,y1) in merged: boxes.append(('Terrain','Ground',[x0,y0,z0,x1,y1,z1]))
G=sorted(set(b[0] for b in boxes)); T=sorted(set(b[1] for b in boxes))
def f(v): return ('%.2f'%v).rstrip('0').rstrip('.') or '0'
out=['-- GrillDadDistrict: colliders (%d boxes, Ground merged from %d) + anchors/lights. Re-runnable: clears old Colliders/Anchors first.'%(len(boxes),len(c)),
'-- Run in the Studio command bar after importing the FBX. Mapping: Roblox X=-x, Y=z, Z=y.',
'do local root=workspace:FindFirstChild("GrillDadDistrict") if root then local old=root:FindFirstChild("Colliders") if old then old:ClearAllChildren() end end end']
N=400
hdr='local G={%s} local T={%s}\n'%(','.join('"%s"'%g for g in G),','.join('"%s"'%t for t in T))
for i in range(0,len(boxes),N):
    rows=','.join('{%d,%d,%s}'%(G.index(g)+1,T.index(t)+1,','.join(f(v) for v in m)) for g,t,m in boxes[i:i+N])
    out.append('do\n'+hdr+'''local root=workspace:FindFirstChild("GrillDadDistrict") or Instance.new("Model") root.Name="GrillDadDistrict" root.Parent=workspace
local col=root:FindFirstChild("Colliders") or Instance.new("Folder",root) col.Name="Colliders"
local D={%s}
local tmp=Instance.new("Folder")
for _,r in ipairs(D) do local x0,y0,z0,x1,y1,z1=r[3],r[4],r[5],r[6],r[7],r[8]
local p=Instance.new("Part") p.Name="Col_"..G[r[1]].."_"..T[r[2]] p.Anchored=true p.Transparency=1 p.CastShadow=false p.CanTouch=false
p.Size=Vector3.new(math.max(x1-x0,0.05),math.max(z1-z0,0.05),math.max(y1-y0,0.05)) p.CFrame=CFrame.new(-(x0+x1)/2,(z0+z1)/2,(y0+y1)/2)
p:SetAttribute("Group",G[r[1]]) p.Parent=tmp end
for _,p in ipairs(tmp:GetChildren()) do p.Parent=col end tmp:Destroy()
end'''%rows)
arows=','.join('{"%s",%s,%s,%s,%s}'%(a['name'],f(a['pos'][0]),f(a['pos'][1]),f(a['pos'][2]),f(a.get('range',0))) for a in A)
out.append('''do
local root=workspace:FindFirstChild("GrillDadDistrict")
local af=root:FindFirstChild("Anchors") or Instance.new("Folder",root) af.Name="Anchors"
af:ClearAllChildren()
local A={%s}
for _,r in ipairs(A) do
 local p=Instance.new("Part") p.Name=r[1] p.Anchored=true p.CanCollide=false p.CanQuery=false p.CanTouch=false p.Transparency=1 p.Size=Vector3.new(1,1,1)
 p.CFrame=CFrame.new(-r[2],r[4],r[3]) p.Parent=af
 if r[5]>0 then local l=Instance.new("PointLight") l.Range=math.min(r[5],60) l.Brightness=0.9 l.Color=Color3.fromRGB(255,214,150) l.Parent=p end
end
end
print("GrillDadDistrict colliders:", #workspace.GrillDadDistrict.Colliders:GetChildren(), "anchors:", #workspace.GrillDadDistrict.Anchors:GetChildren())'''%arows)
open(sys.argv[2],'w').write('\n'.join(out))
print(len(c),'->',len(boxes),'anchors',len(A))
