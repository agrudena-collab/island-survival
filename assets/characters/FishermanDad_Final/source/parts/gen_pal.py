import re
L=[l.rstrip("\n") for l in open(r"C:/Users/agrud/AppData/Local/Temp/claude/C--Users-agrud-Documents-RobloxProjects-MyRobloxGame/858e9159-e7ce-479b-bb1b-235e8d65f354/scratchpad/fd/fd.txt",encoding="utf-8")]
i=L.index("Tile")
rows=[];k=i+4
while k+3<len(L) and re.fullmatch(r"\d+",L[k].strip()):
    rows.append((int(L[k]),L[k+1].strip(),L[k+2].strip(),L[k+3].strip()));k+=4
assert len(rows)==49,len(rows)
for r in rows: assert re.fullmatch(r"#[0-9A-F]{6}",r[2]),r
out="PAL = [\n"+"".join('    (%r, %r, %r),\n'%(n,h,u) for _,n,h,u in rows)+"]\n"
open("parts/pal.py","w",encoding="utf-8").write(out);print(len(rows))
