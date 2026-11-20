import json,sys,subprocess
n=sys.argv[1]; d=json.load(open(f'vid/{n}.json')); S=d.get('SLOW',1); T0=d['T0']; fr=[[f,(t-T0)/S] for f,t in d['frames']]; d['T0']=0; d['marks']={k:v/S for k,v in d['marks'].items()}; json.dump(d['marks'],open(f'vid/{n}_marks.json','w'))
lines=[]
for i,(f,t) in enumerate(fr):
    nt=fr[i+1][1] if i+1<len(fr) else d['T0']+d['marks']['end']+0.3
    lines.append(f"file '{f.split('/',1)[1]}'\nduration {max(nt-t,0.001):.4f}")
lines.append(f"file '{fr[-1][0].split('/',1)[1]}'")
open(f'vid/{n}.txt','w').write("\n".join(lines))
# offset: first frame timestamp vs T0
print(n,len(fr),'frames', 'span',fr[-1][1]-fr[0][1],'first_off',fr[0][1]-d['T0'])
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',f'vid/{n}.txt','-vf','scale=1080:1920:flags=lanczos,fps=30,format=yuv420p','-c:v','libx264','-crf','18',f'vid/{n}_raw.mp4'])
