"""The proof scene, driven through the interface with real pointer and keyboard input, recorded on video.
   Writes proof/out/: steps.json (every action and its measured result), screenshots, the recording, the project file, the exported film,
   preview frames and exported frames compared."""
import json, os, sys, time, subprocess, shutil
sys.path.insert(0, os.path.dirname(__file__)); import serve
from playwright.sync_api import sync_playwright
OUT=os.path.join(os.path.dirname(__file__),'out'); shutil.rmtree(OUT,ignore_errors=True); os.makedirs(OUT+'/rec')
URL='http://127.0.0.1:8801/cineosis-lab/lab/wg-film-test.html'
srv=serve.start(8801); LOG=[]
def log(step,**k):
    k['step']=step; LOG.append(k); print(json.dumps(k)[:400]); sys.stdout.flush()
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required','--use-gl=swiftshader'])
    ctx=b.new_context(viewport={'width':1280,'height':800},record_video_dir=OUT+'/rec',record_video_size={'width':1280,'height':800},accept_downloads=True)
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:300]))
    pg.goto(URL,wait_until='load'); pg.wait_for_timeout(5000)
    J=lambda s:pg.evaluate(s)
    shots=lambda:J("STK.film.shots.map(s=>[s.take.src,+s.take.in.toFixed(3),+s.take.out.toFixed(3),s.figs.length])")
    def rect(sel): return pg.locator(sel).first.bounding_box()
    def band(u,lower): r=rect('#band'); return r['x']+u*r['width'], r['y']+r['height']*(.78 if lower else .22)
    def shot(name): pg.screenshot(path=f'{OUT}/{name}.png')
    log('open',mode=J('STK.MODE'),source=J('STK.SRC.src'))
    # 1 · inspect three clips and mark a take from each
    pg.click('#tray button[data-s="w:wg_003"]'); pg.wait_for_timeout(1500)
    x0,y=band(.08,True); x1,_=band(.48,True); pg.mouse.move(x0,y); pg.mouse.down(); pg.mouse.move(x1,y,steps=12); pg.mouse.up(); shot('01-source-marked')
    log('mark by dragging the lower band',source='w:wg_003',mark=J("[STK.SRC.mi,STK.SRC.mo]"))
    pg.click('#sIns'); pg.wait_for_timeout(500); log('insert take 1',shots=shots())
    pg.click('#tray button[data-s="w:wg_009"]'); pg.wait_for_timeout(1500)
    pg.mouse.click(*band(.15,False)); pg.keyboard.press('i'); pg.mouse.click(*band(.55,False)); pg.keyboard.press('o')
    log('mark with I and O after scrubbing',source='w:wg_009',mark=J("[STK.SRC.mi,STK.SRC.mo]"))
    pg.click('#sIns'); pg.wait_for_timeout(500); log('insert take 2',shots=shots())
    pg.click('#tray button[data-s="w:wg_289"]'); pg.wait_for_timeout(1500)
    x0,y=band(.12,True); x1,_=band(.55,True); pg.mouse.move(x0,y); pg.mouse.down(); pg.mouse.move(x1,y,steps=12); pg.mouse.up()
    pg.click('#sIns'); pg.wait_for_timeout(500); log('insert take 3',shots=shots(),total=J('STK.total()'))
    # 2 · play the sequence with sound; measure the mixer while it plays
    pg.keyboard.press('2'); pg.keyboard.press('Home'); pg.wait_for_timeout(300)
    J("""(()=>{const a=STK.AC.createAnalyser();a.fftSize=2048;STK.MASTER.connect(a);window.__an=a;window.__rms=[];window.__rt=setInterval(()=>{const d=new Float32Array(2048);a.getFloatTimeDomainData(d);let s=0;for(const v of d)s+=v*v;window.__rms.push([+STK.T.toFixed(2),+Math.sqrt(s/d.length).toFixed(4)]);},150);})()""")
    pg.keyboard.press(' '); pg.wait_for_timeout(1800); shot('02-playing'); pg.wait_for_timeout(int(J('STK.total()')*1000)); 
    rms=J("(()=>{clearInterval(window.__rt);return window.__rms})()"); heardSound=sum(1 for t,v in rms if v>0.005)
    log('play the sequence',playing_after=J('STK.playing'),ac=J('STK.AC&&STK.AC.state'),rms_samples=len(rms),samples_with_sound=heardSound,rms_max=max(v for t,v in rms))
    # 3 · reorder the middle take: drag it to the end; the insertion mark shows before release
    before=shots(); t2=pg.locator('#strip .sh').nth(1).bounding_box(); s=rect('#strip')
    pg.mouse.move(t2['x']+t2['width']/2,t2['y']+t2['height']/2); pg.mouse.down(); pg.mouse.move(s['x']+s['width']-6,t2['y']+t2['height']/2,steps=20)
    ins=J("[!document.querySelector('#ins').hidden,document.querySelector('#ghost')&&document.querySelector('#ghost').textContent]"); shot('03-reorder-preview')
    pg.mouse.up(); pg.wait_for_timeout(300); after=shots(); aud=J('STK.playing'); pg.wait_for_timeout(3300)
    log('reorder the middle take',insertion_mark_shown=ins[0],ghost=ins[1],before=[x[0] for x in before],after=[x[0] for x in after],audition_started=aud)
    # 4 · trim a boundary: drag shot 1's out handle; both frames show while dragging
    tot0=J('STK.total()'); h=pg.locator('#strip .sh').nth(0).locator('i.b').bounding_box()
    pg.mouse.move(h['x']+h['width']/2,h['y']+h['height']/2); pg.mouse.down(); pg.mouse.move(h['x']-60,h['y']+h['height']/2,steps=15); pg.wait_for_timeout(600); shot('04-trim-two-frames')
    mid=J("[STK.film.shots[0].take.out,STK.total()]"); pg.mouse.up(); pg.wait_for_timeout(300); aud=J('STK.playing'); pg.wait_for_timeout(3300)
    log('trim the out point of shot 1',total_before=tot0,during=mid,after=shots()[0],total_after=J('STK.total()'),audition_started=aud)
    st0=shots(); hn=J('STK.H.undo.length'); h=pg.locator('#strip .sh').nth(2).locator('i.a').bounding_box()
    pg.mouse.move(h['x']+h['width']/2,h['y']+h['height']/2); pg.mouse.down(); pg.mouse.move(h['x']+50,h['y']+h['height']/2,steps=8); mid=shots()[2]; pg.keyboard.press('Escape'); pg.mouse.up(); pg.wait_for_timeout(300)
    log('cancel a trim with Escape',during=mid,after=shots()[2],unchanged=shots()==st0,history_steps_added=J('STK.H.undo.length')-hn)
    # 5 · open one shot, add a figure, record a movement by dragging while it plays
    t2=pg.locator('#strip .sh').nth(1).bounding_box(); pg.mouse.click(t2['x']+t2['width']/2,t2['y']+8); pg.wait_for_timeout(400)
    pg.click('#tray button[data-f]'); pg.wait_for_timeout(1500); fig=J("STK.SEL"); shot('05-figure-added')
    pg.mouse.click(t2['x']+t2['width']/2,t2['y']+8); pg.wait_for_timeout(500)
    def figScreen():
        return J("""(()=>{const e=STK.film.shots.flatMap(s=>s.figs).find(f=>f.id===STK.SEL)||STK.film.shots[1].figs[0];const c=document.querySelector('#cv').getBoundingClientRect(),b=STK.box,d=STK.dpr;const k=e.keys[0];return [c.left+(b.x+k.x*b.w)/d,c.top+(b.y+k.y*b.h)/d]})()""")
    fx,fy=figScreen(); pg.keyboard.press(' '); pg.wait_for_timeout(200); pg.mouse.move(fx,fy); pg.mouse.down()
    for i in range(30):
        pg.mouse.move(fx-200+i*14,fy-40+abs(15-i)*3); pg.wait_for_timeout(50)
    shot('06-recording-path'); pg.mouse.up(); pg.wait_for_timeout(300); pg.keyboard.press(' ') if J('STK.playing') else None
    keys=J("STK.film.shots[1].figs.map(f=>f.keys.length)"); log('record a movement while playing',figure=fig,keys_per_figure=keys,history=J("STK.H.undo.slice(-3).map(h=>h.label)"))
    # 6 · leave for the table view and come back: selection and playhead survive; undo and redo the last change
    sel0=J("[STK.SHOT,STK.SEL,+STK.T.toFixed(3)]"); pg.keyboard.press('3'); pg.wait_for_timeout(800); shot('07-table'); pg.keyboard.press('2'); pg.wait_for_timeout(400); sel1=J("[STK.SHOT,STK.SEL,+STK.T.toFixed(3)]")
    k0=J("STK.film.shots[1].figs[0].keys.length"); pg.keyboard.press('z'); pg.wait_for_timeout(300); k1=J("STK.film.shots[1].figs[0].keys.length"); pg.keyboard.press('Shift+Z'); pg.wait_for_timeout(300); k2=J("STK.film.shots[1].figs[0].keys.length")
    log('views keep selection and position; undo then redo',before=sel0,after=sel1,same=sel0==sel1,keys_now=k0,after_undo=k1,after_redo=k2,heard=J("document.querySelector('#heard').textContent"))
    # 7 · save, reload, replay, export
    pg.click('#sendB'); 
    with pg.expect_download() as d: pg.click('#pop button[data-o="json"]')
    d.value.save_as(OUT+'/project.stack.json'); data0=J('STK.filmData()')
    pg.wait_for_timeout(800); pg.reload(wait_until='load'); pg.wait_for_timeout(5000); data1=J('STK.filmData()'); proj=json.load(open(OUT+'/project.stack.json'))
    log('save, reload',reload_equal=data0==data1,project_file_equal=proj==data1,shots=len(data1['s']))
    pg.keyboard.press('2'); pg.keyboard.press('Home'); pg.keyboard.press(' '); pg.wait_for_timeout(int(J('STK.total()')*1000)+600); shot('08-replayed'); log('replay after reload',ended=not J('STK.playing'))
    pg.click('#sendB')
    with pg.expect_download(timeout=90000) as d: pg.click('#pop button[data-o="video"]')
    d.value.save_as(OUT+'/export.webm'); log('export',size=os.path.getsize(OUT+'/export.webm'))
    # preview frames, drawn by the same evaluator from the paused editor, at times inside each shot
    S=J('STK.starts()'); L=[x[2]-x[1] for x in shots()]; T=[]
    for a,l in zip(S,L): T+= [round(a+.35*l,3), round(a+.8*l,3)]
    for t in T:
        u=pg.evaluate("""async t=>{STK.setPlay(false);STK.seek(t);const t1=performance.now();while(performance.now()-t1<4000){STK.syncVideos(t,false);const c=STK.film.shots.find((s,i)=>t>=STK.starts()[i]&&t<STK.starts()[i]+STK.len(s));const v=c&&STK.VID['g:'+c.id];if(v&&v.readyState>=2&&!v.seeking&&Math.abs(v.currentTime-(c.take.in+t-STK.starts()[STK.film.shots.indexOf(c)]))<.05)break;await new Promise(r=>setTimeout(r,60));}
          await new Promise(r=>setTimeout(r,250));const cv=document.createElement('canvas');cv.width=1280;cv.height=720;STK.frameAt(cv.getContext('2d'),t,1280,720,{cap:true,clean:true});return cv.toDataURL('image/png');}""",t)
        import base64; open(f'{OUT}/prev_{t:.3f}.png','wb').write(base64.b64decode(u.split(',')[1]))
    json.dump({'times':T},open(OUT+'/times.json','w'))
    log('errors',page_errors=errs)
    ctx.close(); b.close()
json.dump(LOG,open(OUT+'/steps.json','w'),indent=1)
vid=[f for f in os.listdir(OUT+'/rec') if f.endswith('.webm')]
if vid: shutil.move(OUT+'/rec/'+vid[0],OUT+'/proof-recording.webm')
print('done')
