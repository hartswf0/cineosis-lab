# Butter Pair: calibration by touch, lift and two lines of sight. The simulator's cameras differ from what the system assumes; the solve must find them.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8837);U='http://127.0.0.1:8837/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
def log(k,v):R[k]=v;print(k,json.dumps(v)[:800])
SETUP="""(o=>{const W=.15,D=.075,S=BP.SIM,d=Math.PI/180;BP.resetModel();BP.reset();BP.CAL.A=null;BP.CAL.B=null;BP.CAL.rev=0;BP.BPAIRS.length=0;BP.LIFTS.length=0;BP.BCAM.noauto=true;BP.BCAM.on=false;BP.BCAM.p=null;BP.BCAM.report=null;BP.BCAM.prior=null;BP.XF.Bh=BP.XF.Av;
 /* the true Floor camera: lens 3 mm off, tilted 1.5 degrees, turned, field of view as given, perhaps mirrored */
 const tl=1.5*d,yw=(o.byaw||4)*d,pos=[-.007,D/2-.003,0];S.setB(pos,[pos[0]+Math.sin(tl),pos[1],Math.cos(tl)],[Math.sin(yw),Math.cos(yw),0],o.bfov||72,o.mir);
 /* the true laptop camera, and the system's starting belief about it */
 S.setA([W/2,D+.40,.27],[W/2,D*.4,.12],o.afov||62);const t=BP.geoFromImage(S.flash(0),4/3);
 if(o.prior==='rig'){const a=3*d,c=Math.cos(a),s=Math.sin(a),g=JSON.parse(JSON.stringify(t));g.R=g.R.map(r=>[r[0],c*r[1]-s*r[2],s*r[1]+c*r[2]]);g.t=[g.t[0],c*g.t[1]-s*g.t[2],s*g.t[1]+c*g.t[2]];g.C=[0,1,2].map(i=>-(g.R[i][0]*g.t[0]+g.R[i][1]*g.t[1]+g.R[i][2]*g.t[2]));g.C[1]-=.02;g.t=[0,1,2].map(j=>-(g.R[0][j]*g.C[0]+g.R[1][j]*g.C[1]+g.R[2][j]*g.C[2]));if(o.afov&&o.afov!==62)g.f=4/3*.5/Math.tan(31*d);BP.GEO.A=null;BP.rigLoad(g,'test');}
 else{S.reseed(3);BP.setGeo(BP.geoFromImage(S.flash(.0015),4/3),'test');}
 window._truth=t;BP.SIM.SCRIPTS.wobble=o.wobble||0;BP.TCAL.check={U:.47*W,V:D/2};BP.startTcal();BP.measure('tapcal');BP.TCAL.check=null;BP.TCAL.on=false;
 const rep=BP.calibSolve();const g=BP.GEO.A,tr=window._truth,ang=Math.acos(Math.min(1,g.R[0][2]*tr.R[0][2]+g.R[1][2]*tr.R[1][2]+g.R[2][2]*tr.R[2][2]))*180/Math.PI;
 const out={report:rep,used:BP.BCAM.on,A_position_error_mm:Math.round(1000*Math.hypot(g.C[0]-tr.C[0],g.C[1]-tr.C[1],g.C[2]-tr.C[2])),A_axis_error_deg:+ang.toFixed(2),B_lens_true_mm:[-7,Math.round((D/2-.003)*1000)]};
 const run=(s,m)=>{BP.resetModel();BP.reset();const r=BP.measure(s,{mask:m||null});return r.rms_mm;};
 BP.resetModel();BP.reset();const pb=BP.measure('path');out.path_both=pb.rms_mm;out.path_by_view=pb.by_view;out.path_B_only=run('path',{A:false,B:true});out.path_A_only=run('path',{A:true,B:false});
 BP.LOG.length=0;out.handoff=run('handoff');out.gestures=run('gestures');out.isolations=BP.LOG.filter(l=>l.includes('isolated')).length;return out;})"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':860})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(1800);E=lambda s:pg.evaluate(s)
    # the baseline: same cameras, no lift solve (the previous build)
    log('before: rig 3 deg / 2 cm off, Floor camera 72 deg, no lift solve',E("""(()=>{const f=%s;const W=.15,D=.075,S=BP.SIM,d=Math.PI/180;const o={prior:'rig'};
      const save=BP.calibSolve;return (()=>{const r=f(Object.assign(o,{}));return r;})()})()"""%SETUP.replace("const rep=BP.calibSolve();","const rep=null;BP.BCAM.on=false;")))
    log('rig 3 deg / 2 cm off, Floor camera 72 deg, solved from lifts',E("(%s)({prior:'rig'})"%SETUP))
    log('flash, Floor camera 72 deg, solved from lifts',E("(%s)({prior:'flash'})"%SETUP))
    log('rig, wobbly lifts (8 mm sideways)',E("(%s)({prior:'rig',wobble:.008})"%SETUP))
    log('rig, Floor picture turned 90 deg and mirrored',E("(%s)({prior:'rig',byaw:90,mir:true})"%SETUP))
    log('rig, laptop camera 70 deg (system assumes 62), Floor camera 80 deg',E("(%s)({prior:'rig',afov:70,bfov:80})"%SETUP))
    log('errors',errs)
    json.dump(R,open(OUT+'/calib.json','w'),indent=1);b.close()
