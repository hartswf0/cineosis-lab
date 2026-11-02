# Hand-off between the editor and the Floorboard, with SIMULATED hand tracks on both (no camera here).
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8813);U='http://127.0.0.1:8813/cineosis-lab/lab/wg-film-test.html';OUT='out4';import os;os.makedirs(OUT,exist_ok=True)
P={"v":3,"c":0,"g":0,"s":[["","w:wg_003",0.3667,4.3667,1,[]],["","w:wg_289",0.3333,4.3333,1,[]]],"t":[]}
R=[]
def log(step,**k):R.append(dict(step=step,**k));print(step,k)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':1280,'height':800})
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(U);pg.wait_for_timeout(2500)
    pg.evaluate("p=>{STK.openFilm(STK.filmFrom(p));STK.openSource('shm:giraffe-walks-past');}",P);pg.wait_for_timeout(1500)
    f=ctx.new_page();f.set_viewport_size({'width':420,'height':760});f.on('pageerror',lambda e:errs.append('floor: '+str(e)));f.goto(U+'?floor');f.wait_for_timeout(3000)
    f.screenshot(path=OUT+'/f0-idle.png')
    J=lambda s:pg.evaluate(s);F=lambda s:f.evaluate(s)
    pg.bring_to_front()
    # the figure under a pinch on the editor
    gx,gy=J("(()=>{const a=STK.SB;const r=document.querySelector('#cv').getBoundingClientRect();for(let y=.3;y<.95;y+=.03)for(let x=.05;x<.95;x+=.03){const px=(a.x+a.w*x)/STK.dpr,py=(a.y+a.h*y)/STK.dpr;if(STK.figAt&&STK.figAt(px,py))return [r.x+px,r.y+py];}return null})()") or [0,0]
    if not gx:
        gx,gy=J("(()=>{const a=STK.SB,r=document.querySelector('#cv').getBoundingClientRect();return [r.x+(a.x+a.w*.25)/STK.dpr,r.y+(a.y+a.h*.62)/STK.dpr]})()")
    H=lambda t:pg.evaluate("t=>STK.simHands(t)",t)
    FH=lambda t:f.evaluate("t=>STK.floorHands(t)",t)
    n=J('STK.H.undo.length')
    H([{'id':'Right','x':gx,'y':gy,'closed':False,'pose':'open'}]);H([{'id':'Right','x':gx,'y':gy,'closed':True,'pose':'pinch'}]);pg.wait_for_timeout(100)
    h1=J("STK.HOLD&&[STK.HOLD.state,STK.HOLD.by]")
    H([]);pg.wait_for_timeout(450);H([]);pg.wait_for_timeout(100)
    lab=J("document.querySelector('#heard').textContent");h2=J("STK.HOLD&&STK.HOLD.state")
    pg.screenshot(path=OUT+'/e1-pass.png')
    log('editor: pinch the giraffe, then the hand leaves the laptop camera',held=h1,after_loss=h2,status=lab)
    f.wait_for_timeout(500);fh=F("STK.FLs.hold&&STK.FLs.hold.state");f.screenshot(path=OUT+'/f1-incoming.png')
    # the pinched hand arrives over the Floorboard: caught on arrival
    FH([{'id':'Right','x':200,'y':600,'closed':True,'pose':'pinch'}]);f.wait_for_timeout(300)
    st=J("STK.HOLD&&[STK.HOLD.state,STK.HOLD.by]");mine=F("STK.FLs.mine")
    for k in range(1,9): FH([{'id':'Right','x':200+k*12,'y':600-k*30,'closed':True,'pose':'pinch'}]);f.wait_for_timeout(60)
    f.wait_for_timeout(200);prev=J("STK.HOLD&&STK.HOLD.prev");f.screenshot(path=OUT+'/f2-carrying.png');pg.screenshot(path=OUT+'/e2-on-floor.png')
    log('Floor: the pinched hand arrives and catches it; carrying moves the preview on the editor too',floor_saw_hold=fh,editor_state=st,floor_mine=mine,editor_preview=prev)
    # the hand is lost over the Floorboard: paused, nothing placed
    FH([]);f.wait_for_timeout(120);FH([]);f.wait_for_timeout(350);FH([])
    pz=[F("STK.FLs.paused"),J("STK.HOLD&&STK.HOLD.fp"),J('STK.H.undo.length')==n];f.screenshot(path=OUT+'/f3-paused.png')
    FH([{'id':'Right','x':260,'y':420,'closed':False,'pose':'open'}]);f.wait_for_timeout(200);still=[F("STK.FLs.paused"),J('STK.H.undo.length')==n]
    log('Floor: hand lost while carrying pauses; an open hand coming back does not place',paused=pz,after_open_hand=still)
    # pinch again, carry, open: placed
    FH([{'id':'Right','x':260,'y':420,'closed':True,'pose':'pinch'}]);f.wait_for_timeout(100);FH([{'id':'Right','x':300,'y':560,'closed':True,'pose':'pinch'}]);f.wait_for_timeout(100)
    FH([{'id':'Right','x':300,'y':560,'closed':False,'pose':'open'}]);f.wait_for_timeout(600)
    pl=[J('STK.H.undo.length')==n+1,J("STK.H.undo.slice(-1)[0]&&STK.H.undo.slice(-1)[0].label"),J("STK.HOLD"),J("(()=>{const s=STK.film.shots.find(s=>s.figs.length);return s?[STK.film.shots.indexOf(s),s.figs[0].keys[0]]:null})()")]
    f.wait_for_timeout(300);f.screenshot(path=OUT+'/f4-placed.png');pg.screenshot(path=OUT+'/e4-placed.png')
    log('Floor: pinch again, carry, open the hand: placed as one undo step',placed=pl)
    pg.keyboard.press('z');pg.wait_for_timeout(300);log('undo on the editor',figures=J("STK.film.shots.map(s=>s.figs.length)"))
    # touch path: hold by pointer on the editor, catch by touch on the Floor, cancel with the x
    pg.bring_to_front();pg.mouse.move(gx,gy);pg.mouse.down();pg.mouse.up();pg.wait_for_timeout(300);n=J('STK.H.undo.length')
    f.bring_to_front();f.mouse.move(150,500);f.mouse.down();f.mouse.move(180,460,steps=4);f.wait_for_timeout(200);t1=[J("STK.HOLD&&STK.HOLD.state"),F("STK.FLs.mine")]
    f.mouse.up();f.wait_for_timeout(500);t2=[J('STK.H.undo.length')==n+1,J("STK.HOLD")]
    log('touch: a locked hold on the editor, finger down on the Floor catches, lift places',during=t1,after=t2)
    pg.keyboard.press('z');pg.wait_for_timeout(200);pg.mouse.move(gx,gy);pg.mouse.down();pg.mouse.up();pg.wait_for_timeout(500);n=J('STK.H.undo.length')
    f.mouse.move(150,500);f.mouse.down();f.wait_for_timeout(200);vis=F("!document.querySelector('#flX').hidden");f.mouse.up();
    # that release placed it; undo, hold again, cancel with the x instead
    pg.keyboard.press('z');pg.wait_for_timeout(200);pg.mouse.move(gx,gy);pg.mouse.down();pg.mouse.up();pg.wait_for_timeout(600);n=J('STK.H.undo.length')
    f.click('#flX');f.wait_for_timeout(500);c=[J("STK.HOLD"),J('STK.H.undo.length')==n]
    log('cancel on the Floor with the x',x_visible_while_held=vis,after=c)
    log('page errors',errors=errs)
    json.dump(R,open(OUT+'/handoff.json','w'),indent=1);b.close()
