# Butter Pair: locating the laptop camera by tilting the screen. A synthetic laptop camera: a textured room, and the Floor's dots only while the screen points at it.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8845);U='http://127.0.0.1:8845/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:600])
FAKE="""(()=>{const g0=BP.geoFromImage(BP.SIM.flash(0),4/3),cv=document.createElement('canvas');cv.width=640;cv.height=480;const x=cv.getContext('2d');
 /* a room: random light and dark blocks on a tall sheet, so moving it up and down is visible */
 const room=document.createElement('canvas');room.width=640;room.height=1600;const r=room.getContext('2d');let s=11;const rnd=()=>{s=(s*16807)%2147483647;return s/2147483647;};r.fillStyle='#4a463f';r.fillRect(0,0,640,1600);for(let i=0;i<900;i++){const v=Math.floor(40+rnd()*160);r.fillStyle='rgb('+v+','+v+','+(v-10)+')';r.fillRect(rnd()*640,rnd()*1600,8+rnd()*60,6+rnd()*40);}
 let k=null;const bc=new BroadcastChannel('butter-pair');bc.onmessage=e=>{if(e.data.type==='flash')k=e.data.k;};
 window.FK={dy:0,phone:false};const P=(U,V)=>{const p=BP.projA(g0,U,V,0);return [p.x*640,p.y*480];};
 (function d(){x.drawImage(room,0,-560+FK.dy);if(FK.phone){x.fillStyle='#111';x.beginPath();[[0,0],[.15,0],[.15,.075],[0,.075]].forEach(([U,V],i)=>{const [a,b]=P(U,V);i?x.lineTo(a,b):x.moveTo(a,b);});x.closePath();x.fill();
   if(k!=null&&k>=0){const c=[[.06,.1],[.94,.1],[.94,.9],[.06,.9],[.5,.5]][k],[a,b]=P(c[0]*.15,c[1]*.075);x.fillStyle='#fff';x.beginPath();x.ellipse(a,b,7,3,0,0,7);x.fill();}}requestAnimationFrame(d);})();
 const v=document.querySelector('#vidA');v.srcObject=cv.captureStream(30);v.play();BP.HND={stop(){}};window.TRUEG=g0;return g0.f;})()"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--autoplay-policy=no-user-gesture-required']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    lap=ctx.new_page();lap.on('pageerror',lambda e:errs.append('laptop: '+str(e)));lap.goto(U);lap.wait_for_timeout(1200)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(1500);lap.bring_to_front()
    L=lap.evaluate;f=L(FAKE);lap.wait_for_timeout(800)
    for true_deg in [25,-12]:
        L("(()=>{BP.GEO.A=null;BP.GEO.rev++;FK.dy=0;FK.phone=false;BP.LAUNCH.on=true;window._r=null;BP.tiltLocate?0:0;})()")
        L("(()=>{window._r='running';BP.LRUN.camA().then(()=>window._r=JSON.stringify(BP.LAUNCH.rows.filter(Boolean).slice(-1)));})();0")
        for i in range(200):        # the first flash fails: the screen points away from the phone; wait for the cue to tilt
            lap.wait_for_timeout(200)
            if L("BP.TILT.phase==='find'"):break
        lap.wait_for_timeout(2500)
        L("FK.phone=true")           # the person tilts the screen forward: the phone comes into view
        for i in range(120):
            lap.wait_for_timeout(250)
            if L("BP.TILT.phase==='track'"):break
        found=L("BP.GEO.A&&BP.GEO.A.src!=='tilt'")
        lap.screenshot(path=OUT+'/tilt-found.png')
        # tilt back over 3 s: the room slides down by f*tan(angle) pixels; the phone leaves the view
        fpx=f*480;L("FK.phone=false")
        import math
        steps=30
        for i in range(1,steps+1):
            ang=true_deg*i/steps;L("FK.dy=%f"%(fpx*math.tan(math.radians(ang))));lap.wait_for_timeout(100)
        if i==steps//2:lap.screenshot(path=OUT+'/tilt-moving.png')
        for i in range(60):
            lap.wait_for_timeout(200)
            if L("window._r!=='running'"):break
        res=L("({row:window._r,measured_deg:+BP.TILT.deg.toFixed(2),src:BP.GEO.A&&BP.GEO.A.src,C:BP.GEO.A&&BP.GEO.A.C.map(x=>Math.round(x*1000)),looks:BP.GEO.A&&+(Math.asin(BP.GEO.A.R[2][2])*180/Math.PI).toFixed(1),flash_looks:+(Math.asin(TRUEG.R[2][2])*180/Math.PI).toFixed(1)})")
        res['true_deg']=true_deg;res['found_by_flash_first']=found
        log('tilt back %d degrees'%true_deg,res)
    log('errors',errs)
    json.dump(R,open(OUT+'/tilt.json','w'),indent=1);b.close()
