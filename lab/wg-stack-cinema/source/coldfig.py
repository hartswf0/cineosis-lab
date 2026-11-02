# Repair condition: a lifted, posed figure must appear in every exported frame of its shot, from a cold cache.
import sys, json, subprocess, os, glob, base64
sys.path.insert(0,'/home/claude/stack/proof'); import serve
from playwright.sync_api import sync_playwright
from PIL import Image
page_name=sys.argv[1]; out=sys.argv[2]; os.makedirs(out,exist_ok=True)
serve.start(8811)
PROJ={"v":3,"c":0,"g":0,"s":[["","w:wg_003",0.3667,2.3667,1,[]],
 ["","",0,4,1,[["m:shm:giraffe-walks-past|0|4.125|136",0.62,0,0,4,[[0,0.7,0.86,0.3],[3.5,0.3,0.8,0.3]]]]],
 ["","w:wg_289",0.3333,2.3333,1,[]]],"t":[]}
EMPTY=[{"v":3,"id":"cold","title":"","cap":False,"grade":False,"updated":1,"shots":[],"table":[],"ui":{}}]
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg=b.new_page(viewport={'width':1280,'height':800})
    pg.add_init_script("localStorage.setItem('wg-stack-films-v3',%s)"%json.dumps(json.dumps(EMPTY)))
    errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://127.0.0.1:8811/cineosis-lab/lab/'+page_name); pg.wait_for_timeout(2500)
    pg.evaluate("p=>{STK.openFilm(STK.filmFrom(p));STK.setMode('film');}",PROJ); pg.wait_for_timeout(300)
    pg.mouse.click(640,400); pg.wait_for_timeout(50)   # a user gesture for audio
    pg.evaluate("STK.setPlay(false)")
    starts=pg.evaluate("STK.starts()"); tot=pg.evaluate("STK.total()")
    pg.evaluate("STK.renderFilm()")
    pg.wait_for_function("window.__render",timeout=60000)
    data=pg.evaluate("async()=>{const b=new Uint8Array(await window.__render.arrayBuffer());let s='';for(let i=0;i<b.length;i+=32768)s+=String.fromCharCode(...b.subarray(i,i+32768));return btoa(s);}")
    open(out+'/export.webm','wb').write(base64.b64decode(data)); b.close()
fd=out+'/frames'; os.makedirs(fd,exist_ok=True); [os.remove(f) for f in glob.glob(fd+'/*.png')]
subprocess.run(['ffmpeg','-loglevel','error','-y','-i',out+'/export.webm','-vsync','0','-frame_pts','1',fd+'/%06d.png'],check=True)
pts=subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','frame=pts_time','-of','csv=p=0',out+'/export.webm'],capture_output=True,text=True).stdout.split()
pts=[float(x) for x in pts if x.strip()]
files=sorted(glob.glob(fd+'/*.png'))
a,z=starts[1]+0.05,starts[2]-0.05
rows=[]
for f,t in zip(files,pts):
    if not(a<=t<=z): continue
    im=Image.open(f).convert('L').resize((320,180)); n=sum(1 for v in im.getdata() if v>40)
    rows.append((round(t,3),n))
present=sum(1 for _,n in rows if n>150)
gaps=[round(pts[i+1]-pts[i],3) for i in range(len(pts)-1)]
r={'page':page_name,'film_total':round(tot,3),'last_video_frame':pts[-1] if pts else None,'frames_in_figure_shot':len(rows),
   'frames_with_figure':present,'min_pixels':min(n for _,n in rows) if rows else None,'max_gap_s':max(gaps) if gaps else None,'errors':errs,'rows':rows}
json.dump(r,open(out+'/coldfig.json','w'),indent=1)
print(json.dumps({k:v for k,v in r.items() if k!='rows'}))
print([n for _,n in rows])
