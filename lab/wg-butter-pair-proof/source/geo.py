# Butter Pair, geometry: the Floor flashes, camera A finds it; touches teach hand size; lifts teach B; the Floor moves and is found again.
import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8821);U='http://127.0.0.1:8821/cineosis-lab/lab/wg-butter-pair.html';OUT='/home/claude/stack/proof/out9'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
R={};errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);ctx=b.new_context(viewport={'width':1280,'height':800})
    ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U+'?sim');pg.wait_for_timeout(2000)
    E=lambda s:pg.evaluate(s)
    def fresh(): E("(()=>{BP.resetModel();BP.reset();BP.CAL.A=null;BP.CAL.B=null;BP.CAL.rev=0;BP.GEO={A:null,rev:BP.GEO.rev+1,L:.09,Ln:0,Lsum:0};BP.BPAIRS.length=0;BP.XF.Bh=(()=>{const o=BP.XF.Bh.constructor;return BP.XF.Bh})();})()")
    def run(name,mask=None):
        return E(f"(()=>{{BP.resetModel();BP.reset();return BP.measure('{name}',{{mask:{json.dumps(mask) if mask else 'null'}}});}})()")
    # 1. the flash: pose of camera A recovered from five dots (image noise 0.15% of the frame, about 1 px at 640x480)
    R['flash']=E("""(()=>{BP.resetModel();BP.SIM.reseed(3);const pts=BP.SIM.flash(.0015),g=BP.geoFromImage(pts,4/3);BP.setGeo(g,'test');const c=BP.SIM.CAMS.A.pos;
      return {dots_found:pts.filter(Boolean).length,residual_mm:g.res,camera_true_cm:c.map(x=>+(x*100).toFixed(1)),camera_found_cm:g.C.map(x=>+(x*100).toFixed(1)),position_error_mm:+(1000*Math.hypot(g.C[0]-c[0],g.C[1]-c[1],g.C[2]-c[2])).toFixed(1),focal_found:+g.f.toFixed(3),focal_true:+(BP.SIM.CAMS.A.fx*4/3).toFixed(3)}})()""")
    # 2. A alone, with the pose and the assumed hand size, before any touch
    R['path_A_only_pose_assumed_hand']=run('path',{'A':True,'B':False})
    # 3. touch and lift three dots
    R['tapcal']=E("(()=>{BP.resetModel();BP.reset();BP.startTcal();const r=BP.measure('tapcal');return {commands:r.commands,hand_size_mm:+(BP.GEO.L*1000).toFixed(1),touches:BP.GEO.Ln,B_map:BP.CAL.B&&BP.CAL.B.src,B_pairs:BP.BPAIRS.length,tcal_on:BP.TCAL.on,log:BP.LOG.slice(0,6)}})()")
    R['path_A_only_after_touches']=run('path',{'A':True,'B':False})
    R['path_B_only_after_touches']=run('path',{'A':False,'B':True})
    R['path_both']=run('path')
    R['path_B_only_after_both']=run('path',{'A':False,'B':True})
    R['learned']=E("({B_height_from_A:BP.XF.Bh.ok,A_depth_from_B:BP.XF.Ag.ok,B_map:BP.CAL.B&&BP.CAL.B.src})")
    R['path_A_only_after_both']=run('path',{'A':True,'B':False})
    for s in ['handoff','blackout','crossing','gestures','palms']: R[s]=run(s)
    R['gestures_scene']=E("BP.SCENE.bricks.map(b=>[b.id,b.i,b.j,b.l,b.rot])")
    # 4. B learns its map from A alone (no touches)
    R['B_from_A']=E("""(()=>{const keep=BP.CAL.B;BP.CAL.B=null;BP.BPAIRS.length=0;BP.resetModel();BP.measure('path');const src=BP.CAL.B&&BP.CAL.B.src;BP.resetModel();const r=BP.measure('path',{mask:{A:false,B:true}});return {B_map:src,path_B_only:r.rms_mm}})()""")
    # 5. the Floor is picked up and put down 6 cm to the left and turned 10 degrees: equivalently camera A moves in the bed's frame
    R['floor_moved']=E("""(()=>{const W=.15,D=.075,old=BP.SIM.CAMS.A.pos.slice();const a=10*Math.PI/180,rot=(p)=>{const x=p[0]-W/2,y=p[1]-D/2;return [W/2+Math.cos(a)*x-Math.sin(a)*y+.06,D/2+Math.sin(a)*x+Math.cos(a)*y,p[2]];};
      BP.SIM.setA(rot(old),rot([W/2,D*.4,.12]));const now=performance.now();BP.imuIn({mov:true,b:20,g:5},now);BP.imuIn({mov:true,b:20,g:5},now+400);BP.imuIn({mov:false,b:0,g:0},now+500);BP.imuIn({mov:false,b:0,g:0},now+1300);
      const stale=BP.GEO.A.stale;BP.resetModel();const before=BP.measure('path',{mask:{A:true,B:false}}).rms_mm;BP.SIM.reseed(5);BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'test re-flash');BP.resetModel();const after=BP.measure('path',{mask:{A:true,B:false}}).rms_mm;BP.resetModel();const both=BP.measure('path').rms_mm;
      BP.SIM.setA(old,[W/2,D*.4,.12]);BP.setGeo(BP.geoFromImage(BP.SIM.flash(.0015),4/3),'back');return {marked_stale_on_set_down:stale,A_only_with_old_registration:before,A_only_after_reflash:after,both_after_reflash:both}})()""")
    # 6. dot finding on a synthetic frame pair: a dim noisy room, one lit dot at (0.62, 0.71)
    R['find_dot']=E("""(()=>{const w=200,h=150,off=new Float32Array(w*h),on=new Float32Array(w*h);let s=9;const r=()=>{s=(s*16807)%2147483647;return s/2147483647;};
      for(let i=0;i<w*h;i++){off[i]=60+20*r();on[i]=off[i]+6*(r()-.5);}for(let y=0;y<h;y++)for(let x=0;x<w;x++){const d=Math.hypot(x+.5-.62*w,y+.5-.71*h);if(d<3.2)on[y*w+x]+=90;}
      const dot=BP.findDot(on,off,w,h);const glare=new Float32Array(w*h);for(let i=0;i<w*h;i++)glare[i]=off[i]+60;return {dot,whole_frame_change:BP.findDot(glare,off,w,h)}})()""")
    # 7. a recorded session replays through the same model: record the path from the simulator as events, play them back
    R['replay']=E("""(()=>{const sc=BP.SIM.SCRIPTS.path(),ev=[];BP.SIM.reseed(7);for(let t=0;t<=sc.dur;t+=1/30){for(const cam of ['A','B']){const hs=[];for(const h of BP.SIM.handsAt(sc,t)){const o=BP.SIM.observe(cam,h);if(o)hs.push({id:o.id,pose:o.pose,lm:BP.packLm(o.lm)});}ev.push({k:'obs',cam,t:Math.round(t*1000),asp:4/3,hands:hs});}}
      const data=JSON.parse(JSON.stringify({v:1,cal:{CAL:BP.CAL,GEO:BP.GEO},ev}));const n=BP.replay(data,true);const t=BP.TR.find(x=>!x.ptr);return {events:n,bytes:JSON.stringify(data).length,track:t&&{id:t.id,live:t.live,X_mm:t.X&&[t.X.U,t.X.V,t.X.H].map(x=>Math.round(x*1000))}}})()""")
    R['reg_text']=E("BP.regText(performance.now())")
    # 8. the corner-pinch route still works without a Floor
    R['corner_pinch_fallback']=E("(()=>{BP.GEO={A:null,rev:BP.GEO.rev+1,L:.09,Ln:0,Lsum:0};BP.CAL.B=null;BP.resetModel();BP.calStart();BP.measure('calibrate');BP.resetModel();return {residual:BP.CAL.res,centre:BP.CAL.check,path_both:BP.measure('path').rms_mm}})()")
    R['errors']=errs
    json.dump(R,open(OUT+'/geo.json','w'),indent=1)
    for k,v in R.items(): print(k,json.dumps(v)[:400])
    b.close()
