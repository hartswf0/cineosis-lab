import sys,json;sys.path.insert(0,'/home/claude/stack/proof');import serve
from playwright.sync_api import sync_playwright
serve.start(8828);U='http://127.0.0.1:8828/cineosis-lab/lab/wg-butter-pair.html?sim'
T128='/tmp/claude-0/-home-claude/5dcbf124-08aa-5357-a87a-ec1f490e8f81/scratchpad/t128/node_modules/three/build/three.min.js'
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context();ctx.route('**/three.min.js',lambda r:r.fulfill(path=T128,content_type='text/javascript'))
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(U);pg.wait_for_timeout(1500)
    r=pg.evaluate("""(()=>{BP.resetModel();BP.calStart();BP.measure('calibrate');BP.resetModel();BP.reset();const sc=BP.SIM.SCRIPTS.palms(),rows=[];const n0=BP.HIST.length;
      for(let t=0;t<=sc.dur;t+=1/30){BP.simStep(sc,t);const truth=BP.SIM.handsAt(sc,t)[0],h=BP.TR.find(x=>x.grasp)||BP.TR.find(x=>!x.ptr);
        rows.push({t:+t.toFixed(2),c:BP.CONSTR&&BP.CONSTR.kind,st:h&&h.state,H:h&&h.X?+(h.X.H*1000).toFixed(1):null,trueH:+((truth.P[2]-.24)*1000).toFixed(1),V:h&&h.X?+(h.X.V*1000).toFixed(1):null,trueV:+(truth.P[1]*1000).toFixed(1),U:h&&h.X?+(h.X.U*1000).toFixed(1):null,trueU:+(truth.P[0]*1000).toFixed(1),j:h&&h.grasp&&h.grasp.pv?h.grasp.pv.j:null,i:h&&h.grasp&&h.grasp.pv?h.grasp.pv.i:null,via:h&&h.via,n:BP.TR.filter(x=>!x.ptr).length});}
      const win=(a,b)=>rows.filter(r=>r.t>=a&&r.t<=b);const span=(a,k)=>{const v=a.map(r=>r[k]).filter(x=>x!=null);return v.length?+(Math.max(...v)-Math.min(...v)).toFixed(1):null;};
      const F=win(2.1,3.6),T=win(4.5,6.2);
      return {floor:{constraint:[...new Set(F.map(r=>r.c))],via:[...new Set(F.map(r=>r.via))],H_range_mm:span(F,'H'),true_H_range_mm:span(F,'trueH'),U_range:span(F,'U'),true_U_range:span(F,'trueU')},
              top:{constraint:[...new Set(T.map(r=>r.c))],via:[...new Set(T.map(r=>r.via))],V_range_mm:span(T,'V'),true_V_range_mm:span(T,'trueV'),rows_j:[...new Set(T.map(r=>r.j))],cols_i:[...new Set(T.map(r=>r.i))],U_range:span(T,'U'),true_U_range:span(T,'trueU')},
              free_between:[...new Set(win(3.9,4.2).map(r=>r.c))],tracks:[...new Set(rows.map(r=>r.n))],commands:BP.HIST.slice(n0).map(h=>h.label),log:BP.LOG.slice(0,8).reverse()};})()""")
    print(json.dumps(r,indent=1),errs);b.close()
