# Butter Pair, the new flow in two windows: flash registration through a synthetic camera A, touch dots, Floor motion, witness views, recording.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8827);U='http://127.0.0.1:8827/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,**v):R[k]=v;print(k,json.dumps(v)[:500])
# the synthetic laptop camera: a dim noisy room, the phone as a dark quad in perspective, the flashed dot where the true pose puts it
FAKE="""(()=>{const g0=BP.geoFromImage(BP.SIM.flash(0),4/3),cv=document.createElement('canvas');cv.width=640;cv.height=480;const x=cv.getContext('2d');let k=null;const bc=new BroadcastChannel('butter-pair');bc.onmessage=e=>{if(e.data.type==='flash')k=e.data.k;};
 const P=(U,V)=>{const p=BP.projA(g0,U,V,0);return [p.x*640,p.y*480];};
 function draw(){x.fillStyle='#4a463f';x.fillRect(0,0,640,480);for(let i=0;i<300;i++){x.fillStyle='rgba(255,255,255,'+(Math.random()*.06)+')';x.fillRect(Math.random()*640,Math.random()*480,3,3);}
  x.fillStyle='#111';x.beginPath();[[0,0],[.15,0],[.15,.075],[0,.075]].forEach(([U,V],i)=>{const [a,b]=P(U,V);i?x.lineTo(a,b):x.moveTo(a,b);});x.closePath();x.fill();
  if(k!=null&&k>=0){const c=[[.06,.1],[.94,.1],[.94,.9],[.06,.9],[.5,.5]][k],[a,b]=P(c[0]*.15,c[1]*.075);x.fillStyle='#fff';x.beginPath();x.ellipse(a,b,7,3,0,0,7);x.fill();}requestAnimationFrame(draw);}
 draw();const v=document.querySelector('#vidA');v.srcObject=cv.captureStream(30);v.play();BP.HND={stop(){}};window.TRUEC=g0.C;return true;})()"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--autoplay-policy=no-user-gesture-required']);ctx=b.new_context(viewport={'width':1280,'height':800},accept_downloads=True)
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    lap=ctx.new_page();lap.on('pageerror',lambda e:errs.append('laptop: '+str(e)));lap.goto(U);lap.wait_for_timeout(1500)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(2000)
    L=lambda s:lap.evaluate(s);F=lambda s:fl.evaluate(s)
    L(FAKE);lap.wait_for_timeout(800)
    log('linked',floors=L("BP.floors()"),video=L("document.querySelector('#vidA').videoWidth"))
    t0=time.time();lap.evaluate("(async()=>{await BP.LRUN.camA();BP.startTcal();})()")
    # watch the Floor go dark and light its dots
    shots=0
    for i in range(80):
        fl.wait_for_timeout(100)
        if shots<2 and F("BP.FV.flash")==(2 if shots==0 else 4):fl.screenshot(path=OUT+'/f-flash-%d.png'%shots);shots+=1
        if L("!BP.FL.busy")and i>5:break
    g=L("(()=>{const g=BP.GEO.A;return g&&{n:g.n,res:g.res,C:g.C.map(x=>Math.round(x*1000)),true:TRUEC.map(x=>Math.round(x*1000)),pts:g.img}})()")
    log('flash through the synthetic camera',seconds=round(time.time()-t0,1),geo=g,tcal=L("BP.TCAL.on"),log=L("BP.LOG.slice(0,3)"))
    lap.wait_for_timeout(900);fl.wait_for_timeout(300);fl.screenshot(path=OUT+'/f-tcal.png')
    # the B witness: the Floor sends its own picture
    F("(()=>{const c=document.createElement('canvas');c.width=96;c.height=72;const x=c.getContext('2d');x.fillStyle='#223';x.fillRect(0,0,96,72);x.fillStyle='#efa13a';x.fillRect(30,20,30,30);BP.fsend({type:'thumb',cam:'B',img:c.toDataURL('image/jpeg',.6)});})()")
    # touch the three dots on the Floor
    for k in range(3):
        d=F("(()=>{const v=BP.FV.view;return v&&v.tcal?{k:v.tcal.k,dot:v.tcal.dots[v.tcal.k]}:null})()")
        if not d:break
        geo=F("BP.FV.geo");dpr=geo['dpr'];x=(geo['ox']+d['dot']['U']/0.15*geo['cs']*16/16*1)/dpr
        x=(geo['ox']+d['dot']['U']/(0.15/16)*geo['cs'])/dpr;y=(geo['oy']+(8-d['dot']['V']/(0.075/8))*geo['cs'])/dpr
        fl.mouse.move(x,y);fl.mouse.down();fl.wait_for_timeout(350);fl.mouse.up();fl.wait_for_timeout(500)
    log('touch dots',tcal_on=L("BP.TCAL.on"),log=L("BP.LOG.slice(0,4)"))
    lap.wait_for_timeout(500);lap.screenshot(path=OUT+'/l-after-cal.png');fl.screenshot(path=OUT+'/f-after-cal.png')
    log('laptop registration panel',text=L("document.querySelector('#calS').innerText"),space=L("document.querySelector('#spaceL').innerText"))
    # record, then carry the Floor: motion messages from the phone, then still
    lap.click('#recB')
    F("(()=>{let n=0;const id=setInterval(()=>{BP.fsend({type:'imu',b:n<8?25:1,g:n<8?-8:0,mov:n<8});if(++n>20)clearInterval(id);},120);})()")
    lap.wait_for_timeout(1300);moving=L("BP.FLR.mov");fl.wait_for_timeout(100)
    lap.wait_for_timeout(1400)
    for i in range(80):
        lap.wait_for_timeout(100)
        if L("!BP.FL.busy&&BP.GEO.A&&!BP.GEO.A.stale"):break
    log('Floor carried and put down',moving_seen=moving,stale_then_found=L("BP.GEO.A&&!BP.GEO.A.stale"),log=L("BP.LOG.slice(0,5)"))
    with lap.expect_download() as dl:lap.click('#recB')
    path=OUT+'/session.json';dl.value.save_as(path);d=json.load(open(path))
    kinds={};[kinds.__setitem__(e['k'],kinds.get(e['k'],0)+1) for e in d['ev']]
    log('recording saved',events=len(d['ev']),kinds=kinds,has_cal=bool(d['cal']['GEO']['A']))
    log('replay of the saved file',n=L("BP.replay(%s,true)"%json.dumps(d)))
    log('page errors',errors=errs)
    json.dump(R,open(OUT+'/ui2.json','w'),indent=1);b.close()
