# Butter Pair: Builders (call and response) with a simulated hand that answers each call; Tell it (words to bricks);
# the phone-turned check on the third real run's numbers.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8856);U='http://127.0.0.1:8856/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:900])
SETUP="""(()=>{BP.resetModel();BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'t');BP.BCAM.on=true;BP.BCAM.p=Object.assign({},BP.B0);BP.BCAM.report={B_fov_deg:78,B_turn_deg:0,B_mirrored:false,used:true,lifts:0,fit_mm:{A:0,B:0,height:0},A_moved_mm:0,A_turned_deg:0};BP.GEO.L=.075;})()"""
AUTO="""(()=>{const c=BP.CALL.cur;if(!c||BP.CALL.done)return null;const H0=BP.SIM.H0,CW=.15/16,CD=.075/8,t=BP.TR.find(x=>!x.ptr&&x.X&&x.lostAt===null),P0=t?[t.X.U,t.X.V,H0]:[.075,.0375,H0],held=BP.TR.find(x=>!x.ptr&&x.grasp),fp=b=>b.rot?{w:b.d,d:b.w}:{w:b.w,d:b.d},cen=(i,j)=>[(i+.5)*CW,(j+.5)*CD,H0];let K,pc=null;
 if(c.k==='lift'){const bs=BP.SCENE.bricks.filter(x=>x.c===c.c).sort((a,b)=>b.l-a.l),b=bs[0],f=fp(b),A=cen(b.i+Math.floor(f.w/2),b.j+Math.floor(f.d/2));A[2]=H0+.01*b.l;K=[{t:0,P:P0,closed:false},{t:.9,P:A,closed:false},{t:1.3,P:A,closed:true},{t:12,P:A,closed:true}];}
 else if(c.k==='V'){K=[{t:0,P:P0,closed:false,pose:'V'},{t:12,P:P0,closed:false,pose:'V'}];pc={V:[[0,12,'B']]};}
 else if(c.k==='palm'){const P=c.p==='top'?[.15*.55,.075*.75,.23]:[.075,.0375,H0];K=[{t:0,P,closed:false,orient:c.p==='top'?'wall':undefined},{t:12,P,closed:false,orient:c.p==='top'?'wall':undefined}];}
 else if(held){const g=held.grasp,b=BP.SCENE.bricks.find(x=>x.id===g.brick),f=g.rot?{w:b.d,d:b.w}:{w:b.w,d:b.d},fr=g.from;let ti=fr.i,tj=fr.j;
  if(c.k==='dir'){if(c.d==='up')tj=fr.j+2;if(c.d==='down')tj=fr.j-2;if(c.d==='left')ti=fr.i-3;if(c.d==='right')ti=fr.i+3;}
  else if(c.k==='on'||c.k==='stack'){const x=BP.SCENE.bricks.filter(y=>y.id!==b.id&&(c.k==='stack'||y.c===c.c)).sort((a,b)=>b.l-a.l)[0];ti=x.i;tj=x.j;}
  else if(c.k==='floor'){const s=BP.freeSpot(f.w,f.d);ti=s.i;tj=s.j;}
  const B=cen(ti+Math.min(g.off.i,f.w-1),tj+Math.min(g.off.j,f.d-1));K=[{t:0,P:P0,closed:true},{t:1.6,P:B,closed:true},{t:2.1,P:B,closed:true},{t:2.5,P:[B[0],B[1],H0+.02],closed:false},{t:12,P:[B[0],B[1],H0+.03],closed:false}];}
 else return 'no hold';const sc={dur:12,hands:[K]};if(pc)sc.poseCam=pc;BP.RUN={sc,t0:performance.now(),name:'auto',next:[],last:null};return c.w;})()"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1500);E=lambda s:pg.evaluate(s)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(1200);fl.evaluate("BP.PSET.done=true;FV.cam=true");pg.bring_to_front()
    E(SETUP);E("BP.callStart()");seen=None;calls=[];t0=time.time();shot=0
    while time.time()-t0<200 and E("BP.CALL.n")<12:
        pg.wait_for_timeout(250);st=E("({t0:BP.CALL.t0,w:BP.CALL.word,done:BP.CALL.done,n:BP.CALL.n})")
        if st['done'] is None and st['w'] and st['t0']!=seen and E("!!BP.CALL.cur"):
            seen=st['t0'];r=E(AUTO);calls.append({'call':st['w']})
            if len(calls)==3 and not shot:pg.wait_for_timeout(700);pg.screenshot(path=OUT+'/builders-laptop.png');fl.screenshot(path=OUT+'/builders-floor.png');shot=1
        if st['done'] is not None and calls and 'ok' not in calls[-1]:calls[-1]['ok']=st['done']['ok']
    E("BP.RUN=null");log('Builders: a simulated hand answers the calls',{'calls':calls,'score':E("BP.CALL.score"),'hits':E("BP.CALL.hits"),'of':E("BP.CALL.n"),'stats':E("Object.fromEntries(Object.entries(BP.CALL.stats).map(([k,s])=>[k,s.ok+'/'+(s.ok+s.miss)]))")})
    pg.wait_for_timeout(300);pg.screenshot(path=OUT+'/builders-panel.png');E("BP.callStop()")
    # tell it
    E("BP.playStart(null,'free')");pg.wait_for_timeout(300);out=[]
    for q in ['add a blue 2x2','add a red','put the red on the blue','where is the red','what is on the blue','move it toward the laptop 3','turn it','add two yellow 1x2','how many yellow','move the green left','put the yellow on the red','remove the blue','undo','make me a castle']:
        a=E("BP.tell(%s)"%json.dumps(q));pg.wait_for_timeout(250);out.append([q,a])
    log('Tell it',{'exchanges':out,'bricks':E("BP.SCENE.bricks.map(b=>[b.c,b.w+'x'+b.d,b.i,b.j,b.l])")})
    E("document.querySelector('#tellIn').value='put the yellow on the red';document.querySelector('#tellF').requestSubmit()");pg.wait_for_timeout(500);pg.screenshot(path=OUT+'/tell.png')
    # the third real run's laptop camera position
    log('phone turned away from the laptop (third real run numbers)',E("(()=>{const g=BP.geoFromImage(BP.SIM.flash(.0015),4/3);BP.setGeo(Object.assign(g,{C:[0.7609,0.0470,0.4422]}),'t');return {angle:Math.round(BP.layoutAngle())};})()"))
    log('errors',errs);json.dump(R,open(OUT+'/builders.json','w'),indent=1);b.close()
