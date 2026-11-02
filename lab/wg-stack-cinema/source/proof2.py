"""SCION Cinema in Hand: the proof scene through the interface. Pointer and keyboard are real input events; the camera hands are
   SIMULATED (synthetic tracks fed to the same hand handler) because no camera exists here. Writes out2/."""
import json, os, sys, shutil, base64
sys.path.insert(0, os.path.dirname(__file__)); import serve
from playwright.sync_api import sync_playwright
OUT=os.path.join(os.path.dirname(__file__),'out2'); shutil.rmtree(OUT,ignore_errors=True); os.makedirs(OUT+'/rec')
URL='http://127.0.0.1:8805/cineosis-lab/lab/wg-film-test.html'; serve.start(8805); LOG=[]
def log(step,**k): k['step']=step; LOG.append(k); print(json.dumps(k)[:330]); sys.stdout.flush()
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required','--use-gl=swiftshader'])
    ctx=b.new_context(viewport={'width':1280,'height':800},record_video_dir=OUT+'/rec',record_video_size={'width':1280,'height':800},accept_downloads=True)
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:300])); J=pg.evaluate
    pg.goto(URL,wait_until='load'); pg.wait_for_timeout(5000)
    shot=lambda n: pg.screenshot(path=f'{OUT}/{n}.png')
    takes=lambda: J("STK.film.shots.map(s=>[s.take.src,+s.take.in.toFixed(3),+s.take.out.toFixed(3),s.figs.map(f=>f.kind+':'+f.keys.length)])")
    cv=lambda: pg.locator('#cv').bounding_box()
    def at(rect,u,v):  # a point inside SB or FB, in page coordinates
        c=cv(); r=J(f"(()=>{{const R=STK.{rect},d=STK.dpr;return [R.x/d,R.y/d,R.w/d,R.h/d]}})()"); return c['x']+r[0]+u*r[2], c['y']+r[1]+v*r[3]
    def giraffe():
        c=cv(); return J("""(()=>{const S=STK.SB,d=STK.dpr,s=Math.max(S.w/480,S.h/360),dx=S.x+(S.w-480*s)/2,dy=S.y+(S.h-360*s)/2;return [(dx+90*s)/d,(dy+210*s)/d]})()"""), c
    def band(u,lower):
        r=pg.locator('#band').bounding_box(); return r['x']+u*r['width'], r['y']+r['height']*(.78 if lower else .22)
    def tray(src): pg.locator(f'#tray button[data-s="{src}"]').scroll_into_view_if_needed(); pg.click(f'#tray button[data-s="{src}"]'); pg.wait_for_timeout(1200)
    log('open on an empty project',mode=J('STK.MODE'),A=J('STK.SRC.src'),B=J('STK.SRC.b'),shots=len(takes())); shot('00-empty')
    # 1 · find in the archive, hold one, keep another for comparison
    pg.keyboard.press('1'); pg.wait_for_timeout(1200); shot('01-archive-wall')
    pg.locator('#wall .wt[data-s="w:wg_003"]').scroll_into_view_if_needed(); pg.click('#wall .wt[data-s="w:wg_003"] img'); pg.wait_for_timeout(1500)
    pg.click('#sB'); tray('w:wg_009')
    log('archive: hold one source, keep another as B',mode=J('STK.MODE'),A=J('STK.SRC.src'),B=J('STK.SRC.b')); shot('02-held-with-B')
    x,y=at('SB',.85,.15); pg.mouse.click(x,y); pg.wait_for_timeout(800); log('swap A and B by clicking B',A=J('STK.SRC.src'),B=J('STK.SRC.b'))
    # 2 · scrub forward and back (position), shuttle (rate) with neutral, J K L; settle; mark; insert
    x0,y0=at('SB',.3,.5); pg.mouse.move(x0,y0); pg.mouse.down(); pg.mouse.move(x0+250,y0,steps=10); t1=J('STK.SRC.t'); pg.mouse.move(x0+60,y0,steps=8); t2=J('STK.SRC.t'); pg.mouse.up()
    log('scrub by dragging the picture (position)',forward_to=t1,back_to=t2)
    s=pg.locator('#shut').bounding_box(); cx=s['x']+s['width']/2; cy=s['y']+s['height']/2; pg.mouse.move(cx,cy); pg.mouse.down(); pg.mouse.move(cx+4,cy); r0=J('STK.SRC.rate'); ta=J('STK.SRC.t')
    pg.mouse.move(cx+60,cy,steps=5); pg.wait_for_timeout(700); r1=J('STK.SRC.rate'); tb=J('STK.SRC.t'); shot('03-shuttle'); pg.mouse.up(); r2=J('STK.SRC.rate')
    log('shuttle (rate): small movement stays neutral; a larger one plays; letting go stops',rate_near_middle=r0,rate_dragged=r1,moved_s=round(tb-ta,3),rate_after_release=r2)
    pg.keyboard.press('j'); pg.wait_for_timeout(500); rj=J('STK.SRC.rate'); pg.keyboard.press('k'); log('J plays backward, K stops',rate_J=rj,rate_K=J('STK.SRC.rate'))
    x0,y=band(.05,True); x1,_=band(.62,True); pg.mouse.move(x0,y); pg.mouse.down(); pg.mouse.move(x1,y,steps=12); pg.mouse.up(); pg.click('#sIns'); pg.wait_for_timeout(500)
    x,y=at('SB',.85,.15); pg.mouse.click(x,y); pg.wait_for_timeout(1200)   # B corner: swap to the other candidate
    pg.mouse.click(*band(.12,False)); pg.keyboard.press('i'); pg.mouse.click(*band(.62,False)); pg.keyboard.press('o'); pg.click('#sIns'); pg.wait_for_timeout(500)
    tray('w:wg_289'); x0,y=band(.05,True); x1,_=band(.70,True); pg.mouse.move(x0,y); pg.mouse.down(); pg.mouse.move(x1,y,steps=12); pg.mouse.up(); pg.click('#sIns'); pg.wait_for_timeout(500)
    log('three takes form the sequence',takes=takes(),total=J('STK.total()'))
    # 3 · enter take 2, lift the moving figure from its film, carry it, preview, place
    t2=pg.locator('#strip .sh').nth(1).bounding_box(); pg.mouse.click(t2['x']+t2['width']/2,t2['y']+30); pg.wait_for_timeout(300)
    tray('shm:giraffe-walks-past'); pg.wait_for_timeout(800); (gx,gy),c=giraffe(); gx+=c['x']; gy+=c['y']
    pg.mouse.move(gx,gy); pg.wait_for_timeout(300); shot('04-target-lift'); hov=J("document.querySelector('#cv').style.cursor")
    pg.mouse.down(); fx,fy=at('FB',.55,.86); pg.mouse.move(fx,fy,steps=18); pg.wait_for_timeout(400); shot('05-held-preview'); st=J("[STK.HOLD.state,STK.HOLD.prev]")
    pg.mouse.up(); pg.wait_for_timeout(500); shot('06-placed')
    log('lift the giraffe and place it in shot 2',cursor_on_target=hov,held=st,after=takes()[1],history=J("STK.H.undo.slice(-1).map(h=>h.label)"))
    n=J('STK.H.undo.length'); pg.keyboard.press('z'); pg.wait_for_timeout(300); a1=takes()[1][3]; pg.keyboard.press('Shift+Z'); pg.wait_for_timeout(300); a2=takes()[1][3]
    log('undo and redo the compound lift-and-place',figures_after_undo=a1,figures_after_redo=a2,steps=n)
    # cancel another: release outside the film; and lock then Escape
    pg.mouse.move(gx,gy); pg.mouse.down(); pg.mouse.move(gx,gy-150,steps=8); pg.mouse.up(); pg.wait_for_timeout(300); c1=[J('STK.H.undo.length')==n,J("document.querySelector('#heard').textContent")]
    pg.mouse.move(gx,gy); pg.mouse.down(); pg.mouse.up(); locked=J('STK.HOLD&&STK.HOLD.state'); pg.keyboard.press('Escape'); c2=[J('STK.HOLD'),J('STK.H.undo.length')==n]
    log('cancel: release outside the film returns it; a locked hold cancels with Escape',release_outside=c1,locked=locked,after_escape=c2)
    # 4 · poses: a beginning pose (where it was placed) and an end pose; replay reproduces the movement
    pg.keyboard.press('3'); pg.wait_for_timeout(400); S=J('STK.starts()'); L=J('STK.film.shots.map(s=>STK.len(s))')
    st_=pg.locator('#strip').bounding_box(); tot=J('STK.total()'); px=st_['x']+st_['width']*(S[1]+L[1]*.85)/tot; pg.mouse.click(px,st_['y']+4); pg.wait_for_timeout(500)
    pg.click('#chips button[data-k]:not([data-k="ground"]):not(.add)'); pg.wait_for_timeout(300); pg.click('#acts button[data-a="pose"]'); pg.wait_for_timeout(300)
    k=J("(()=>{const e=STK.film.shots[1].figs[0],c=document.querySelector('#cv').getBoundingClientRect(),b=STK.box,d=STK.dpr,i=1,lt=STK.T-STK.starts()[i],q=STK.at(e,lt);return [c.left+(b.x+q.x*b.w)/d,c.top+(b.y+(q.y-.1)*b.h)/d]})()")
    pg.mouse.move(*k); pg.mouse.down(); pg.mouse.move(k[0]-280,k[1]-30,steps=12); shot('07-end-pose'); pg.mouse.up(); pg.wait_for_timeout(300)
    keys=J("STK.film.shots[1].figs[0].keys")
    pg.locator('#cv').focus(); pg.keyboard.press('Home'); pg.keyboard.press('Shift+ArrowRight'); t_start=J('STK.T'); pg.keyboard.press(' '); pos=[]
    for i in range(6): pg.wait_for_timeout(int(L[1]*1000/6)); pos.append(J("(()=>{const e=STK.film.shots[1].figs[0],lt=STK.T-STK.starts()[1];return [+lt.toFixed(2),+STK.at(e,lt).x.toFixed(3)]})()"))
    pg.keyboard.press(' ') if J('STK.playing') else None; shot('08-replayed')
    log('poses: start and end; replay moves it with no input',replay_from=t_start,keys=keys,positions_during_replay=pos,history=J("STK.H.undo.slice(-2).map(h=>h.label)"))
    # 5 · return to the film: move shot 3 before shot 2 (insertion shown), watch with sound
    before=[x[0] for x in takes()]; t3=pg.locator('#strip .sh').nth(2).bounding_box(); j=pg.locator('#strip .sh').nth(1).bounding_box()
    pg.mouse.move(t3['x']+t3['width']/2,t3['y']+30); pg.mouse.down(); pg.mouse.move(j['x']+12,j['y']+30,steps=16); ins=J("[!document.querySelector('#ins').hidden,document.querySelector('#ghost')&&document.querySelector('#ghost').textContent]"); shot('09-reorder'); pg.mouse.up(); pg.wait_for_timeout(3400)
    J("""(()=>{const a=STK.AC.createAnalyser();STK.MASTER.connect(a);window.__r=[];window.__i=setInterval(()=>{const d=new Float32Array(2048);a.getFloatTimeDomainData(d);let s=0;for(const v of d)s+=v*v;window.__r.push(+Math.sqrt(s/d.length).toFixed(4));},150);})()""")
    pg.keyboard.press('Home'); pg.keyboard.press(' '); pg.wait_for_timeout(int(J('STK.total()')*1000)+400); rms=J("(()=>{clearInterval(window.__i);return window.__r})()")
    log('reorder with insertion shown, then watch the film with sound',insertion=ins,before=before,after=[x[0] for x in takes()],samples=len(rms),with_sound=sum(1 for v in rms if v>.005))
    # 6 · simulated hands: two roles; tracking loss pauses and reacquisition does not place
    pg.keyboard.press('2'); pg.wait_for_timeout(300); tray('shm:giraffe-walks-past'); pg.wait_for_timeout(600); (gx,gy),c=giraffe(); gx+=c['x']; gy+=c['y']; fx,fy=at('FB',.4,.85)
    H=lambda tr: J("t=>STK.simHands(t)",tr)
    H([{'id':'Right','x':gx,'y':gy,'closed':False,'pose':'open'}]); H([{'id':'Right','x':gx,'y':gy,'closed':True,'pose':'pinch'}]); h1=J('STK.HOLD&&[STK.HOLD.state,STK.HOLD.by]')
    for i in range(1,8): H([{'id':'Right','x':gx+(fx-gx)*i/8,'y':gy+(fy-gy)*i/8,'closed':True,'pose':'pinch'}]); pg.wait_for_timeout(40)
    H([]); pg.wait_for_timeout(200); H([]); pg.wait_for_timeout(250); H([]); h2=J('STK.HOLD&&STK.HOLD.state'); shot('10-tracking-paused')
    n=J('STK.H.undo.length'); H([{'id':'Right','x':fx,'y':fy,'closed':False,'pose':'open'}]); pg.wait_for_timeout(200); H([{'id':'Right','x':fx,'y':fy,'closed':False,'pose':'open'}]); h3=[J('STK.HOLD&&STK.HOLD.state'),J('STK.H.undo.length')==n]
    pg.click('#acts button[data-a="cancel"]'); h4=[J('STK.HOLD'),J('STK.H.undo.length')==n]
    log('SIMULATED hands: lift by pinch, tracking lost while held, reacquired, cancelled',held_by=h1,after_loss=h2,after_reacquire_open_hand=h3,after_cancel=h4)
    sx,sy=at('SB',.75,.5); H([{'id':'Left','x':sx,'y':sy,'closed':True,'pose':'pinch'}]); H([{'id':'Left','x':sx,'y':sy,'closed':True,'pose':'pinch'},{'id':'Right','x':900,'y':500,'closed':True,'pose':'pinch'}])
    H([{'id':'Left','x':sx,'y':sy,'closed':True,'pose':'pinch'},{'id':'Right','x':915,'y':500,'closed':True,'pose':'pinch'}]); n0=J('STK.SRC.rate')
    H([{'id':'Left','x':sx,'y':sy,'closed':True,'pose':'pinch'},{'id':'Right','x':1050,'y':500,'closed':True,'pose':'pinch'}]); n1=J('STK.SRC.rate'); roles=J("[STK.HR.own,STK.HR.time]"); shot('11-two-hands')
    H([{'id':'Right','x':1050,'y':500,'closed':True,'pose':'pinch'},{'id':'Left','x':sx,'y':sy,'closed':True,'pose':'pinch'}]); n2=J('STK.SRC.rate')   # hands listed in the other order
    H([{'id':'Left','x':sx,'y':sy,'closed':True,'pose':'pinch'},{'id':'Right','x':1050,'y':500,'closed':False,'pose':'open'}]); n3=J('STK.SRC.rate'); H([])
    log('SIMULATED hands: left holds the source, right controls rate',rate_within_dead_zone=n0,rate_moved=n1,roles=roles,rate_when_order_swapped=n2,rate_after_right_opens=n3)
    # 7 · the Floorboard window places a held figure
    f=ctx.new_page(); f.set_viewport_size({'width':900,'height':520}); f.goto(URL+'?floor'); f.wait_for_timeout(3500)
    pg.bring_to_front(); n=J('STK.H.undo.length'); pg.mouse.move(gx,gy); pg.mouse.down(); pg.mouse.up(); f.mouse.move(300,420); f.wait_for_timeout(400); f.screenshot(path=f'{OUT}/12-floorboard.png'); f.mouse.down(); f.mouse.up(); f.wait_for_timeout(800)
    log('Floorboard window places the held figure',placed=J('STK.H.undo.length')==n+1,label=J("STK.H.undo.slice(-1)[0].label"),floor_shot=J("STK.film.shots.indexOf(STK.film.shots.find(s=>s.id===STK.SHOT))")); f.close()
    pg.keyboard.press('z'); pg.wait_for_timeout(300)
    # repeated source instance: duplicate shot 1 and trim one copy; the other is unchanged
    pg.keyboard.press('3'); t1=pg.locator('#strip .sh').nth(0).bounding_box(); pg.mouse.click(t1['x']+t1['width']/2,t1['y']+30); pg.click('#acts button[data-a="dup"]'); pg.wait_for_timeout(300)
    h=pg.locator('#strip .sh').nth(1).locator('i.b').bounding_box(); pg.mouse.move(h['x']+6,h['y']+20); pg.mouse.down(); pg.mouse.move(h['x']-40,h['y']+20,steps=6); pg.mouse.up(); pg.wait_for_timeout(3300)
    tk=takes(); log('two instances of one source, one trimmed',shot1=tk[0][:3],shot2=tk[1][:3]); pg.keyboard.press('z'); pg.wait_for_timeout(300); pg.keyboard.press('z'); pg.wait_for_timeout(300)
    lat=J('STK.LAT.list'); log('latency from input event to the end of the frame that shows it (headless, software drawing)',n=len(lat),median=sorted(lat)[len(lat)//2] if lat else None,p90=sorted(lat)[int(len(lat)*.9)] if lat else None,max=max(lat) if lat else None)
    # 8 · save, reload, reopen the same shot and moment; export
    t2=pg.locator('#strip .sh').nth(2).bounding_box(); pg.mouse.click(t2['x']+t2['width']*.4,t2['y']+30); pg.wait_for_timeout(500)
    data0=J('STK.filmData()'); sel0=J('[STK.film.shots.findIndex(s=>s.id===STK.SHOT),+STK.T.toFixed(2)]'); pg.wait_for_timeout(700)
    pg.click('#sendB')
    with pg.expect_download() as d: pg.click('#pop button[data-o="json"]')
    d.value.save_as(OUT+'/project.stack.json')
    pg.reload(wait_until='load'); pg.wait_for_timeout(5500); data1=J('STK.filmData()'); sel1=J('[STK.film.shots.findIndex(s=>s.id===STK.SHOT),+STK.T.toFixed(2)]'); shot('13-reopened')
    log('save, reload, reopen',same_film=data0==data1,project_file_same=json.load(open(OUT+'/project.stack.json'))==data1,shot_and_moment_before=sel0,after=sel1,total=J('STK.total()'))
    pg.click('#sendB')
    with pg.expect_download(timeout=120000) as d: pg.click('#pop button[data-o="video"]')
    d.value.save_as(OUT+'/export.webm'); log('export',bytes=os.path.getsize(OUT+'/export.webm'))
    S=J('STK.starts()'); L=J('STK.film.shots.map(s=>STK.len(s))'); T=[]
    for a,l in zip(S,L): T+=[round(a+.3*l,3),round(a+.75*l,3)]
    for t in T:
        u=pg.evaluate("""async t=>{STK.setPlay(false);STK.seek(t);const t1=performance.now();while(performance.now()-t1<4000){STK.syncVideos(t,false);const i=STK.film.shots.findIndex((s,i)=>t>=STK.starts()[i]&&t<STK.starts()[i]+STK.len(s)),c=STK.film.shots[i],v=c&&STK.VID['g:'+c.id];if(v&&v.readyState>=2&&!v.seeking&&Math.abs(v.currentTime-(c.take.in+t-STK.starts()[i]))<.05)break;await new Promise(r=>setTimeout(r,60));}
          await new Promise(r=>setTimeout(r,300));const cv=document.createElement('canvas');cv.width=1280;cv.height=720;STK.frameAt(cv.getContext('2d'),t,1280,720,{cap:true,clean:true});return cv.toDataURL('image/png');}""",t)
        open(f'{OUT}/prev_{t:.3f}.png','wb').write(base64.b64decode(u.split(',')[1]))
    json.dump({'times':T},open(OUT+'/times.json','w'))
    log('page errors',errors=errs); ctx.close(); b.close()
json.dump(LOG,open(OUT+'/steps.json','w'),indent=1)
v=[x for x in os.listdir(OUT+'/rec') if x.endswith('.webm')]
if v: shutil.move(OUT+'/rec/'+v[0],OUT+'/proof-recording.webm')
print('done')
