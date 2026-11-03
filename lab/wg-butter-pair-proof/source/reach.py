# Butter Pair: toward and away. Reach practice with both cameras, with the laptop camera alone, and with a confused hand;
# whole-row stepping while carrying with one camera; the plan's move for a hand only one camera sees; the Floor's view.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8848);U='http://127.0.0.1:8848/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:700])
SETUP="""(()=>{BP.resetModel();BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'t');BP.BCAM.on=true;BP.BCAM.p=Object.assign({},BP.B0||{fB:%f,yaw:0,tx:0,ty:0,cu:-.004,cv:.0375,mir:1});BP.BCAM.report={B_fov_deg:78,B_turn_deg:0,B_mirrored:false,used:true,lifts:0,fit_mm:{A:0,B:0,height:0},A_moved_mm:0,A_turned_deg:0};})()"""
# a hand that goes to each target row in turn; 'confused': first the wrong way, then past the row, then into it
REACH="""((occl,confused)=>{const W=.15,D=.075,CD=D/8,H0=BP.SIM.H0;BP.RUN={sc:{dur:999,occl:occl?{B:[[0,999]]}:null,hands:[]},t0:performance.now(),name:'x',next:[],last:null};BP.GEO.L=.09;BP.reachStart();const zero=BP.REACH.phase==='zero';const T=BP.REACH.targets;const K=[{t:0,P:[W/2,D/2,H0],closed:false}];let t=zero?2.6:.5;if(zero)K.push({t,P:[W/2,D/2,H0],closed:false});
 for(const j of T){const prev=K[K.length-1].P[1],goal=(j+.5)*CD;if(confused&&K.length===(zero?2:1)){const wrong=prev-(goal-prev)*.8;K.push({t:t+=1.2,P:[W/2,Math.max(-.01,Math.min(D+.01,wrong)),H0],closed:false});K.push({t:t+=2.5,P:[W/2,Math.max(-.01,Math.min(D+.01,wrong)),H0],closed:false});const past=goal+(goal-prev)*.9;K.push({t:t+=1.0,P:[W/2,Math.max(-.01,Math.min(D+.01,past)),H0],closed:false});K.push({t:t+=2.5,P:[W/2,Math.max(-.01,Math.min(D+.01,past)),H0],closed:false});}
  K.push({t:t+=1.4,P:[W/2,goal,H0],closed:false});K.push({t:t+=3.2,P:[W/2,goal,H0],closed:false});}
 K.push({t:t+=5,P:K[K.length-1].P,closed:false});const sc={dur:t+1,hands:[K]};if(occl)sc.occl={B:[[0,999]]};BP.RUN={sc,t0:performance.now(),name:'reach',next:[],last:null};return {targets:T.map(j=>j+1),dur:t,zero};})(%s,%s)"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1500);E=lambda s:pg.evaluate(s)
    fl=ctx.new_page();fl.set_viewport_size({'width':844,'height':390});fl.on('pageerror',lambda e:errs.append('floor: '+str(e)));fl.goto(U+'?floor');fl.wait_for_timeout(1200);pg.bring_to_front()
    fB=E("BP.FB0||.823")
    for name,occl,conf in [('both cameras','false','false'),('laptop camera only','true','false'),('laptop camera only, a confused hand','true','true')]:
        E("BP.RUN=null;BP.REACH.on=false");pg.wait_for_timeout(200);E(SETUP%fB);info=E(REACH%(occl,conf));helps=[];shot=False
        t0=0
        while True:
            pg.wait_for_timeout(250);t0+=.25
            st=E("({on:BP.REACH.on,k:BP.REACH.k,n:BP.REACH.targets.length,h:BP.REACH.help&&BP.REACH.help.k,w:BP.REACH.w,r:BP.REACH.cur&&+BP.REACH.cur.r.toFixed(2),by:BP.REACH.cur&&BP.REACH.cur.by,run:!!BP.RUN})")
            if st['h'] and (not helps or helps[-1]!=st['h']):helps.append(st['h'])
            if not shot and t0>2.2 and name!='both cameras':
                pg.screenshot(path=OUT+'/reach-'+('confused' if conf=='true' else 'aonly')+'.png');fl.screenshot(path=OUT+'/reach-floor-'+('confused' if conf=='true' else 'aonly')+'.png');shot=True
            if st['k']>=st['n'] or not st['run'] or t0>info['dur']+6:break
        log('reach practice, '+name,{'zeroed first':info['zero'],'zero':E('BP.REACH.zinfo'),'targets':info['targets'],'reached':E("BP.REACH.res"),'help shown, in order':helps,'band at end':st['w']})
    E("BP.RUN=null;BP.REACH.on=false");pg.wait_for_timeout(200)
    # whole rows while carrying with only the laptop camera: a still hand; how often the raw row and the placed row change
    E(SETUP%fB);E("""(()=>{const W=.15,D=.075,CW=W/16,CD=D/8,H0=BP.SIM.H0,P=[(10+2)*CW,(4+.5)*CD,H0],M=[W/2,D/2,H0];BP.GEO.L=.09;BP.reset();BP.RUN={sc:{dur:14,occl:{B:[[0,999]]},hands:[[{t:0,P:M,closed:false},{t:1.6,P:M,closed:false},{t:2.6,P,closed:false},{t:3,P,closed:true},{t:8,P,closed:true},{t:10,P:[P[0],(6+.5)*CD,H0],closed:true},{t:14,P:[P[0],(6+.5)*CD,H0],closed:true}]]},t0:performance.now(),name:'carry',next:[],last:null};setTimeout(()=>{const t=BP.TR.find(x=>!x.ptr&&x.X);window._z=t&&BP.zeroDepth(t);},1300);window._rows=[];window._ri=setInterval(()=>{const t=BP.TR.find(x=>x.grasp);if(t&&t.grasp.pv)window._rows.push([Math.floor(t.X.V/(D/8)),t.grasp.pv.j,+(t.X.V/(D/8)-.5).toFixed(2),+(t.sd.V*1000).toFixed(0)]);},50);})()""")
    pg.wait_for_timeout(6500);pg.screenshot(path=OUT+'/plan-carry-aonly.png');pg.wait_for_timeout(8000)
    rows=E("(clearInterval(window._ri),window._rows)")
    def changes(a):return sum(1 for i in range(1,len(a)) if a[i]!=a[i-1])
    still=[r for r in rows[:int(len(rows)*.45)]];moved=rows[-20:]
    log('whole-row stepping, laptop camera only, hand held still then moved two rows toward the laptop',{'samples':len(rows),'raw row changes while still':changes([r[0] for r in still]),'placed row changes while still':changes([r[1] for r in still]),'placed row after the move':moved[-1][1]+1 if moved else None,'raw row values seen while still':sorted(set(r[0]+1 for r in still)),'depth sd mm':rows[len(rows)//2][3] if rows else None,'zero':E('window._z'),'placed':E("BP.SCENE.bricks.find(b=>b.id==='butter')")})
    E("BP.RUN=null;BP.cancelAll&&BP.cancelAll()");pg.wait_for_timeout(300)
    # the plan's move: a hand 5 cm above the phone (too close for the Floor camera to see whole) and one far toward the laptop
    for nm,P in [('hand 5 cm above the phone','[W/2,D/2,.05]'),('hand high and toward the laptop','[W/2,D+.03,.36]'),('hand in the middle','[W/2,D/2,.24]')]:
        E(SETUP%fB);E("(()=>{const W=.15,D=.075,P=%s;BP.RUN={sc:{dur:6,hands:[[{t:0,P,closed:false},{t:6,P,closed:false}]]},t0:performance.now(),name:'pt',next:[],last:null};})()"%P);pg.wait_for_timeout(1500)
        a=E("(()=>{const a=BP.planAction(performance.now()),t=BP.TR.find(x=>!x.ptr&&x.X);return {text:a.text,kind:a.kind,seen_by:t&&t.live,canSee:{A:BP.canSee('A',%s),B:BP.canSee('B',%s)}}})()"%(P.replace('W','.15').replace('D','.075'),P.replace('W','.15').replace('D','.075')))
        log('plan, '+nm,a)
        if nm.startswith('hand 5'):pg.screenshot(path=OUT+'/plan-low.png')
    # blind spots on the bed at three heights
    cov=E("""(()=>{const out={};for(const z of [.06,.24,.45]){let a=0,b=0,n=0,none=0;for(let i=0;i<16;i++)for(let j=0;j<8;j++){const P=[(i+.5)*.15/16,(j+.5)*.075/8,z],sa=BP.canSee('A',P)>0,sb=BP.canSee('B',P)>0;if(sa&&sb)n++;else if(sa)a++;else if(sb)b++;else none++;}out[Math.round(z*100)+' cm']={both:n,only_A:a,only_B:b,neither:none};}return out;})()""")
    log('blind spots over the 128 bed cells (simulated cameras)',cov)
    # the Floor: enlarge its own view
    E("BP.RUN=null");log('errors',errs)
    json.dump(R,open(OUT+'/reach.json','w'),indent=1);b.close()
