# Butter Pair interface: real mouse and touch; the Floor in a second window; observations across a relay between separate browsers.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8823);U='http://127.0.0.1:8823/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out7';RL='ws://127.0.0.1:1884/mqtt'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R=[];errs=[]
def log(step,**k):R.append(dict(step=step,**k));print(step,json.dumps(k)[:300])
def until(f,ms=8000):
    t=time.time()
    while time.time()-t<ms/1000:
        try:
            if f(): return round((time.time()-t)*1000)
        except Exception: pass
        time.sleep(.03)
    return None
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    def ctxp(**kw):
        c=b.new_context(**kw);c.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'));return c
    ctx=ctxp(viewport={'width':1280,'height':800})
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append('laptop: '+str(e)));pg.goto(U);pg.wait_for_timeout(1800);J=lambda s:pg.evaluate(s)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');F=lambda s:fl.evaluate(s)
    ms=until(lambda:J("BP.floors()")>0 and F("!!BP.FV.scene"),6000);log('a Floor in a second window links and gets the bricks',ms=ms,floor_bricks=F("BP.FV.scene&&BP.FV.scene.length"))
    def scr(i,j,l=0):
        return J(f"(()=>{{const v=new THREE.Vector3({i}-8+.5,{l}*1.2+1.2,-({j}-4+.5));v.project(BP.R3.cam);const r=document.querySelector('#cv3').getBoundingClientRect();return [r.x+(v.x+1)/2*r.width,r.y+(1-v.y)/2*r.height]}})()")
    pg.bring_to_front();x,y=scr(6,3);x2,y2=scr(11,6)
    pg.mouse.move(x,y);pg.wait_for_timeout(250);over=J("(BP.TR.find(t=>t.ptr==='mouse')||{}).target");over=over and over['id']
    pg.mouse.down();pg.wait_for_timeout(120);pg.mouse.move(x2,y2,steps=12);pg.wait_for_timeout(200);pg.screenshot(path=OUT+'/u1-mouse-carry.png');held=J("(BP.TR.find(t=>t.ptr==='mouse')||{}).state")
    fl.screenshot(path=OUT+'/u1-floor-sees-carry.png');pg.mouse.up();pg.wait_for_timeout(300)
    log('mouse: hover the red brick, press, drag, release',over=over,state_while_dragging=held,red=J("(b=>[b.i,b.j,b.l])(BP.SCENE.bricks.find(b=>b.id==='red'))"),last=J("BP.LOG[0]"))
    pg.keyboard.press('z');pg.wait_for_timeout(200);log('Z undoes it',red=J("(b=>[b.i,b.j,b.l])(BP.SCENE.bricks.find(b=>b.id==='red'))"))
    # touch on the Floor: press the butter brick, drag, lift the finger
    G=F("BP.FV.scene&&1");geo=F("(()=>{const r=document.querySelector('#cvF').getBoundingClientRect();return [r.x,r.y,r.width,r.height]})()")
    def fpt(u,v):
        g=F("(()=>{const r=document.querySelector('#cvF').getBoundingClientRect(),G=BP.FV.geo||{};return [r.x,r.y,G.cs,G.ox,G.oy,G.dpr]})()")
        rx,ry,cs,ox,oy,d=g;return [rx+(ox+u*16*cs)/d, ry+(oy+(1-v)*8*cs)/d]
    fl.bring_to_front();a=fpt(11.5/16,4.5/8);c=fpt(3.5/16,1.5/8)
    fl.mouse.move(*a);fl.mouse.down();fl.wait_for_timeout(300);fl.mouse.move(c[0],c[1],steps=10);fl.wait_for_timeout(400);fl.screenshot(path=OUT+'/u2-floor-touch-carry.png')
    st=J("(BP.TR.find(t=>t.ptr&&t.ptr.startsWith('touch'))||{}).state");fl.wait_for_timeout(600);st2=J("(BP.TR.find(t=>t.ptr&&t.ptr.startsWith('touch'))||{}).state")
    fl.mouse.up();ms=until(lambda:J("BP.SCENE.bricks.find(b=>b.id==='butter').i")!=10,4000)
    log('Floor touch: press the butter brick, drag, hold still, lift',while_dragging=st,held_still_600ms=st2,placed_ms=ms,butter=J("(b=>[b.i,b.j,b.l])(BP.SCENE.bricks.find(b=>b.id==='butter'))"),lessons=J("BP.LDONE"))
    fl.click('#flU');ms=until(lambda:J("BP.SCENE.bricks.find(b=>b.id==='butter').i")==10,3000);log('Undo on the Floor',ms=ms)
    # the demo on both screens
    pg.bring_to_front();pg.click('#demoB');pg.wait_for_timeout(9800);pg.screenshot(path=OUT+'/u3-demo-handoff-A.png');fl.screenshot(path=OUT+'/u3-demo-handoff-floor.png')
    pg.wait_for_timeout(2600);pg.screenshot(path=OUT+'/u4-demo-handoff-B.png');fl.screenshot(path=OUT+'/u4-floor.png')
    pg.wait_for_timeout(5200);pg.screenshot(path=OUT+'/u5-demo-blackout.png');fl.screenshot(path=OUT+'/u5-floor-blackout.png')
    until(lambda:not J("BP.RUN"),30000);pg.wait_for_timeout(300);pg.screenshot(path=OUT+'/u6-demo-done.png')
    log('demo ran: calibrate, hand-off, blackout, gestures',cal=J("({rev:BP.CAL.rev,res:BP.CAL.res,check:BP.CAL.check})"),lessons=J("BP.LDONE"),log=J("BP.LOG.slice(0,14).reverse()"))
    # across devices: separate browser contexts and a relay; the phone sends camera-B observations
    pg.close();fl.close()
    lap=ctxp(viewport={'width':1280,'height':800}).new_page();lap.on('pageerror',lambda e:errs.append('laptop2: '+str(e)));lap.goto(U+'?relay='+RL);lap.wait_for_timeout(1500);L=lambda s:lap.evaluate(s)
    lap.click('#floorB');until(lambda:L("BP.MQ.socks.some(s=>s.ok)"));code=lap.inner_text('#roomC');lap.click('#popX')
    b2=p.chromium.launch();c2=b2.new_context(viewport={'width':844,'height':390},has_touch=True,is_mobile=True);c2.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'));ph=c2.new_page();ph.on('pageerror',lambda e:errs.append('phone: '+str(e)));ph.goto(U+'?floor&relay='+RL);ph.wait_for_timeout(1500)
    ph.click('#flCode');ph.keyboard.type(code);ph.click('#flRoomF button');ms=until(lambda:L("BP.floors()")>0 and ph.evaluate("!!BP.FV.scene"),10000)
    log('phone joins by typed code across the relay',code=code,ms=ms)
    L("BP.resetModel();BP.calStart();BP.measure('calibrate');BP.resetModel();")
    # both pages generate the same hand: the laptop as camera A locally, the phone as camera B through the relay
    script="""(cam,closed,dur)=>new Promise(res=>{const W=.15,D=.075;const t0=performance.now();const iv=setInterval(()=>{const t=(performance.now()-t0)/1000;const P=[.0656+(t>1.2?-.035*Math.min(1,(t-1.2)/1.5):0),.028+(t>1.2?.02*Math.min(1,(t-1.2)/1.5):0),.24];const o=BP.SIM.observe(cam,{P,closed:closed(t),label:'Right'});
      if(cam==='B'){if(o)BP.fsend({type:'obs',cam:'B',t:performance.now(),asp:4/3,hands:[{id:o.id,pose:o.pose,lm:BP.packLm(o.lm)}]});}else{if(o)BP.ingest('A',[o],4/3,performance.now(),performance.now());}if(t>dur){clearInterval(iv);res(1);}},33);})"""
    closed="t=>t>.6&&t<3.2"
    ph.evaluate(f"window.__run=({script})('B',{closed},4.2);0");L(f"window.__run=({script})('A',{closed},4.2);0")
    tl=[]
    for k in range(16):
        time.sleep(.3);tl.append(L("BP.TR.filter(t=>!t.ptr).map(t=>t.state+'['+Object.entries(t.src).filter(([c,s])=>performance.now()-s.t<220).map(([c,s])=>c+(s.closed?':pinch':':open')).join(',')+']').join(' ')"))
        if k==5: lap.screenshot(path=OUT+'/u7-relay-laptop.png');ph.screenshot(path=OUT+'/u7-relay-phone.png')
    log('one hand: the laptop camera locally and the phone camera through the relay',timeline=tl,phone_view=ph.evaluate("(v=>v&&v.tracks.map(t=>t.state))(BP.FV.view)"),events=L("BP.LOG.slice(0,3).reverse()"),newdbg=L("BP.NEWDBG"))
    log('page errors',errors=errs);json.dump(R,open(OUT+'/pairui.json','w'),indent=1);b.close()
