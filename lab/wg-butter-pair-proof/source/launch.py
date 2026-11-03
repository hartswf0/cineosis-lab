# Butter Pair build 1: the Launch checklist end to end (simulated hand), the agreement check, rig error, health states, confirming pinch.
import sys,json,time;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8833);U='http://127.0.0.1:8833/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:700])
GEST="""(()=>{const W=.15,D=.075,H0=BP.SIM.H0,st=1.8+2.0,K=[],pc=[];
 BP.TEST.steps.forEach((s,k)=>{const t0=k*st;let P=[W/2,D/2,H0],closed=false,pose,orient;if(s.id==='pinch')closed=true;if(s.id==='Vflat'||s.id==='Vup'){pose='V';pc.push([t0,t0+st,s.id==='Vflat'?'B':'A']);}if(s.id==='fist')pose='fist';if(s.id==='palmTop'){orient='wall';P=[W*.55,D*.9,.23];}
  K.push({t:t0+.05,P:k?K[K.length-1].P:P,closed:false,pose:k?K[K.length-1].pose:pose,orient:k?K[K.length-1].orient:orient});K.push({t:t0+.8,P,closed,pose,orient});K.push({t:t0+st-.02,P,closed,pose,orient});});
 BP.RUN={sc:{dur:BP.TEST.steps.length*st+.5,hands:[K],poseCam:{V:pc}},t0:performance.now(),name:'launch-gest',next:[],last:null};})()"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':860})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1800);E=lambda s:pg.evaluate(s)
    # 1. Launch, end to end
    E("(()=>{BP.resetModel();BP.reset();BP.CAL.B=null;BP.BPAIRS.length=0;window._imu=setInterval(()=>BP.imuIn({mov:false,b:1,g:1},performance.now()),100);document.querySelector('#launchB').click();BP.launchRun();})()")
    seen=set();shots=0;t0=time.time()
    while time.time()-t0<150:
        pg.wait_for_timeout(150);st=E("BP.LAUNCH.on?BP.LAUNCH.rows.length+':'+(['level','camA','floor','palms','gest'][BP.LAUNCH.step]):'done'")
        if st=='done':break
        k=st.split(':')[1]
        if k in seen:continue
        seen.add(k)
        if k=='floor':pg.wait_for_timeout(200);E("BP.RUN={sc:BP.SIM.SCRIPTS.tapcal(),t0:performance.now(),name:'tapcal',next:[],last:null}")
        if k=='palms':E("BP.RUN={sc:BP.SIM.SCRIPTS.twopalms(),t0:performance.now(),name:'twopalms',next:[],last:null}");pg.wait_for_timeout(1500);pg.screenshot(path=OUT+'/launch-palms.png')
        if k=='gest':pg.wait_for_timeout(300);E(GEST);pg.wait_for_timeout(5000);pg.screenshot(path=OUT+'/launch-gest.png')
    E("BP.RUN=null;clearInterval(window._imu)");pg.wait_for_timeout(400);pg.screenshot(path=OUT+'/launch-done.png')
    log('launch, end to end (simulated hand)',E("({seconds:null,done:BP.LAUNCH.done,rows:BP.LAUNCH.rows.map(r=>r&&[r.id,r.st,r.text]),baseline_hands:BP.LAUNCH.baseline&&BP.LAUNCH.baseline.hands.length})"))
    # 2. the agreement check: no false alarms when the pose is right
    def isolations(): return E("BP.LOG.filter(l=>l.includes('laptop camera isolated')).length")
    E("(()=>{BP.LOG.length=0;BP.resetModel();BP.reset();BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'test')})()")
    ok=E("(()=>{const r=[];for(const s of ['path','handoff','blackout','gestures','palms']){BP.resetModel();BP.reset();const m=BP.measure(s);r.push([s,m.rms_mm]);}return r})()")
    log('agreement check, correct pose: isolations over five scripts',{'isolations':isolations(),'rms':ok})
    # a wrong pose: camera A believed 5 degrees off in yaw (about 4 cm at the Floor)
    E("""(()=>{BP.LOG.length=0;const g=JSON.parse(JSON.stringify(BP.GEO.A)),a=5*Math.PI/180,c=Math.cos(a),s=Math.sin(a);/* turn the bed axes about camera up */
      g.R=g.R.map(r=>[c*r[0]+s*r[2],r[1],-s*r[0]+c*r[2]]);g.t=[c*g.t[0]+s*g.t[2],g.t[1],-s*g.t[0]+c*g.t[2]];const C=[0,1,2].map(i=>-(g.R[i][0]*g.t[0]+g.R[i][1]*g.t[1]+g.R[i][2]*g.t[2]));g.C=C;BP.GEO.A=g;BP.GEO.rev++;})()""")
    E("BP.resetModel();BP.reset()");m=E("BP.measure('path')")
    log('agreement check, camera A pose 5 degrees wrong',{'isolations':isolations(),'state_at_end':E("BP.healthOf(performance.now()).k"),'path_rms_mm':m['rms_mm'],'log':E("BP.LOG.filter(l=>l.includes('isolated')||l.includes('agrees')).slice(0,3)")})
    # 3. camera A placed from a hand-measured rig: 3 degrees of tilt and 2 cm of distance wrong
    E("""(()=>{BP.LOG.length=0;const t=BP.geoFromImage(BP.SIM.flash(0),4/3),a=3*Math.PI/180,c=Math.cos(a),s=Math.sin(a);const g=JSON.parse(JSON.stringify(t));
      /* tilt about the camera's own x axis, then move it 2 cm along the table toward the Floor */
      g.R=g.R.map(r=>[r[0],c*r[1]-s*r[2],s*r[1]+c*r[2]]);g.t=[g.t[0],c*g.t[1]-s*g.t[2],s*g.t[1]+c*g.t[2]];g.C=[0,1,2].map(i=>-(g.R[i][0]*g.t[0]+g.R[i][1]*g.t[1]+g.R[i][2]*g.t[2]));g.C[1]-=.02;g.t=[0,1,2].map(j=>-(g.R[0][j]*g.C[0]+g.R[1][j]*g.C[1]+g.R[2][j]*g.C[2]));
      BP.GEO.A=null;BP.rigLoad(g,'test with error');})()""")
    rr=[]
    for s in ['path','handoff','gestures']:
        E("BP.resetModel();BP.reset()");rr.append([s,E("BP.measure('%s').rms_mm"%s)])
    log('camera A from a rig 3 degrees and 2 cm off',{'isolations':isolations(),'rms':rr,'tolerance_mm':45})
    # 4. health states
    E("BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'test')")
    hs={}
    for name,mask in [('both',None),('A only',{'A':True,'B':False}),('B only',{'A':False,'B':True})]:
        E("BP.resetModel();BP.reset()");E("BP.measure('path',{mask:%s})"%(json.dumps(mask) if mask else 'null'))
        hs[name]=E("(()=>{const t=BP.TR.find(x=>!x.ptr);return t?{state:BP.healthOf(t.seen).k,text:BP.healthOf(t.seen).text,hsrc:t.hsrc}:null})()")
    E("BP.resetModel();BP.reset()");E("BP.measure('blackout')")
    log('health states',hs)
    # 5. laptop camera only: lift the butter brick where both see the hand, lower the hand to 5 cm (too low for the Floor camera), open: held, not placed; pinch and open again: placed
    E("""(()=>{const W=.15,D=.075,H0=BP.SIM.H0,CW=W/16,CD=D/8,P=[(10+2)*CW,(4+1)*CD,H0],L=[P[0]-.03,P[1],.05];
      BP.SIM.SCRIPTS._low=()=>({dur:4.2,hands:[[{t:0,P,closed:false},{t:.5,P,closed:true},{t:1.0,P,closed:true},{t:2.0,P:L,closed:true},{t:2.4,P:L,closed:false},{t:4.2,P:L,closed:false}]]});
      BP.SIM.SCRIPTS._confirm=()=>({dur:2.0,hands:[[{t:0,P:L,closed:false},{t:.5,P:L,closed:true},{t:1.1,P:L,closed:false},{t:2.0,P:L,closed:false}]]});})()""")
    E("BP.resetModel();BP.reset();BP.LOG.length=0");h1=E("BP.measure('_low').commands")
    held=E("(()=>{const t=BP.TR.find(x=>x.grasp);return t?{state:t.state,confirm:t.confirm,live:t.live,health:BP.healthOf(t.seen).k}:null})()")
    h2=E("BP.measure('_confirm').commands")
    log('laptop camera only: confirming pinch',{'first_release_commands':h1,'held':held,'second_pinch_and_release':h2,'log':E("BP.LOG.slice(0,4)")})
    log('errors',errs)
    json.dump(R,open(OUT+'/launch.json','w'),indent=1);b.close()
