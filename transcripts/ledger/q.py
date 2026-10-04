import sys,re,glob,os
au=sys.argv[1]; pat=re.compile(sys.argv[2],re.I); n=int(sys.argv[3]) if len(sys.argv)>3 else 6
k=0
for f in sorted(glob.glob(f'sources/{au}/*')):
    t=open(f,errors='ignore').read()
    for m in pat.finditer(t):
        print(os.path.basename(f),'|',t[max(0,m.start()-170):m.end()+200].replace('\n',' '));print(); k+=1
        if k>=n: sys.exit()
