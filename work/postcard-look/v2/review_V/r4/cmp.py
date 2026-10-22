import re,glob,sys,ast
def parse(files):
    d={}
    for f in files:
        for l in open(f,errors='ignore'):
            m=re.match(r"MUT (\d+) (\S+) -> FAILED (\[.*?\])\s+NEW (\[.*\])",l)
            if m:
                d[(int(m[1]),m[2])]=(set(ast.literal_eval(m[3])),set(ast.literal_eval(m[4])))
            m=re.match(r"MUT (\d+) (\S+) -> HARNESS-ERROR",l)
            if m: d[(int(m[1]),m[2])]=("ERR",)
    return d
new=parse(glob.glob('r4/run_*.log'))
old=parse([f for f in glob.glob('mut*.log') if 'mut8_' not in f or True]+glob.glob('runs/*.log'))
print(len(new),len(old))
for k in sorted(new):
    n=new[k]; o=old.get(k)
    if o is None: print("NEWONLY",k,sorted(n[1]) if n[0]!="ERR" else n); continue
    if n[0]=="ERR" or o[0]=="ERR":
        if n[0]!=o[0]: print("ERRDIFF",k,n[:1],o[:1]); 
        continue
    if n[1]!=o[1]: print("DIFF",k,"old",sorted(o[1]),"new",sorted(n[1]))
