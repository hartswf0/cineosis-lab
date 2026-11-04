# Butter Pair: the bed turns to face the laptop. The laptop off each side of the phone; the flash finds it; the bed's frame turns;
# the located camera still lines up with the flash dots; the phone draws the turned bed and a touch lands where it should.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8864);U='http://127.0.0.1:8864/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:900])
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1500);E=lambda s:pg.evaluate(s)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(1200);fl.evaluate("BP.PSET.done=true;FV.cam=true");pg.bring_to_front()
    out={}
    for name,pos in [('beyond the top edge',[0.0375,0.475]),('off the right side',[0.0375+0.44,0.0375]),('off the left side',[0.0375-0.44,0.0375]),('beyond the near edge',[0.0375,0.0375-0.44])]:
        r=E("""((P)=>{BP.ORIENT.k=0;const c=[P[0],P[1],.27],tg=[.0375,.0375,.1];BP.SIM.setA(c,tg,62);const g=BP.geoFromImage(BP.SIM.flash(.0015),4/3);BP.GEO.A=g;BP.GEO.rev++;
          const before=BP.layoutAngle();const q=BP.orientFix();const g2=BP.GEO.A,pts=BP.flashPts(),img=g.img;let err=0;pts.forEach((p,k)=>{const a=BP.projA(g2,p.U,p.V,0),i=img[k];if(i)err=Math.max(err,Math.hypot(a.x-i.x,a.y-i.y));});
          return {angle_before:Math.round(before),turned_quarters:q,k:BP.ORIENT.k,angle_after:Math.round(BP.layoutAngle()),laptop_cm:[Math.round(g2.C[0]*100),Math.round(g2.C[1]*100),Math.round(g2.C[2]*100)],flash_reproj_px_at_640:Math.round(err*640*10)/10};})(%s)"""%json.dumps(pos))
        out[name]=r
    log('the laptop off each side of the phone',out)
    # leave it turned a quarter (laptop off the right side) and look at the phone
    E("""(()=>{BP.ORIENT.k=0;BP.SIM.setA([.0375+.44,.0375,.27],[.0375,.0375,.1],62);const g=BP.geoFromImage(BP.SIM.flash(.0015),4/3);BP.GEO.A=g;BP.orientFix();BP.SCENE.bricks=[{id:'r',c:'red',w:4,d:2,i:2,j:0,l:0,rot:0,name:'red'},{id:'b',c:'blue',w:2,d:2,i:0,j:6,l:0,rot:0,name:'blue'}];BP.SCENE.rev++;})()""")
    pg.wait_for_timeout(1200);fl.wait_for_timeout(600);fl.screenshot(path=OUT+'/orient-phone.png');pg.screenshot(path=OUT+'/orient-laptop.png')
    rt=fl.evaluate("""(()=>{const G=FV.geo,rk=FV.rk,dpr=G.dpr,r=document.querySelector('#cvF').getBoundingClientRect(),out=[];for(const [U,V] of [[.01,.01],[.06,.02],[.03,.07]]){const s=fq([U,V],-rk),x=(G.ox+s[0]/(.075/8)*G.cs)/dpr+r.left,y=(G.oy+(8-s[1]/(.075/8))*G.cs)/dpr+r.top,p=flPt({clientX:x,clientY:y});out.push({bed:[U,V],back:[+(p.u*.075).toFixed(4),+(p.v*.075).toFixed(4)]});}return {rk,out};})()""")
    log('phone touch through the turn',rt)
    log('errors',errs);json.dump(R,open(OUT+'/orient.json','w'),indent=1);b.close()
