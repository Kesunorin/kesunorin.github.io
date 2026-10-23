import json, os, base64, io
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "data", "mapdata.json"), encoding="utf-8"))

BOX_COLORS = {
    "ammo": "#ffb74d",
    "attach": "#4fc3f7",
    "gear": "#ab47bc",
    "supply": "#66bb6a",
    "misc": "#b0bec5", "misc1": "#b0bec5", "misc2": "#b0bec5", "misc3": "#b0bec5",
    "parts": "#26c6da",
    "stash": "#ffd54f",
    "material": "#a1887f",
    "otherbox": "#90a4ae",
}
for t in data["boxTypes"]:
    t["color"] = BOX_COLORS.get(t["k"], "#ff9f43")

ICON_DIR = os.path.join(HERE, "assets", "icons")
def icon_uri(name):
    if not name:
        return ""
    p = os.path.join(ICON_DIR, name + ".png")
    if not os.path.exists(p):
        return ""
    return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode("ascii")

for t in data["expTypes"]:
    t["icon"] = icon_uri(t.get("icon", ""))
for t in data["enemyTypes"]:
    t["icon"] = icon_uri(t.get("icon", ""))
data["darkIcon"] = icon_uri("Icon_ESPlayerDetails_Map_Store")

for m in data["maps"].values():
    p = os.path.join(HERE, "assets", m["minimap"] + ".webp")
    m["disp"] = list(m["size"])
    if not os.path.exists(p):
        continue
    raw = open(p, "rb").read()
    rot = m.get("rotate", 0)
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    ow, oh = im.size
    colors = im.getcolors(ow * oh) or []
    opaque = [(n, c) for n, c in colors if c[3] >= 250]
    bg = max(opaque)[1][:3] if opaque else (13, 17, 23)
    m["bgColor"] = "#%02x%02x%02x" % bg
    # Keep the original texture orientation; RawImage has no UV flip.
    # Negative rot = counterclockwise on screen (PIL rotates CCW for positive angles).
    if rot:
        im = im.rotate(-rot, expand=True, resample=Image.Resampling.BICUBIC,
                       fillcolor=bg + (255,))
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=92, method=6)
    m["bg"] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    m["disp"] = [round(m["size"][0] * im.width / ow, 4),
                 round(m["size"][1] * im.height / oh, 4)]

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GF2 危区探遗 · 地图数据</title>
<style>
:root{
  --bg:#0d1117; --panel:#161b22; --panel2:#1c2330; --line:#2b3444;
  --txt:#e6edf3; --dim:#8b949e; --poi:#ffd54a; --enemy:#ff5b5b;
  --iobj:#ffa94d; --npc:#4dd0e1; --spawn:#6ee7a8;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--bg);color:var(--txt);
  font-family:"Segoe UI","Microsoft YaHei",system-ui,sans-serif;font-size:13px}
#app{display:flex;height:100vh;overflow:hidden}
#side{width:270px;flex:0 0 270px;background:var(--panel);border-right:1px solid var(--line);
  display:flex;flex-direction:column;overflow-y:auto;overflow-x:hidden}
#side h1{font-size:15px;margin:0;padding:12px 14px;border-bottom:1px solid var(--line)}
#side h1 small{display:block;color:var(--dim);font-weight:400;font-size:11px;margin-top:3px}
.maps{display:flex;gap:6px;padding:10px 12px;border-bottom:1px solid var(--line)}
.maps button{flex:1;padding:8px 4px;border:1px solid var(--line);background:var(--panel2);
  color:var(--txt);border-radius:6px;cursor:pointer;font-size:12px;line-height:1.3}
.maps button.on{background:#2d6cdf;border-color:#2d6cdf}
.maps button small{display:block;color:#c9d6e6;font-size:10px}
.sec{padding:8px 12px;border-bottom:1px solid var(--line)}
.sec .t{color:var(--dim);font-size:11px;margin-bottom:6px;letter-spacing:.05em}
.sec .t .mini{float:right;background:var(--panel2);border:1px solid var(--line);color:var(--txt);
  border-radius:4px;cursor:pointer;font-size:10px;padding:1px 6px;margin-left:4px}
.lay{display:flex;align-items:center;gap:8px;padding:4px 0;cursor:pointer;user-select:none}
.lay input{accent-color:#2d6cdf}
.sw{width:10px;height:10px;border-radius:3px;flex:0 0 10px}
.lay .n{flex:1}
.lay .c{color:var(--dim);font-size:11px}
.lay .sw.ico{width:15px;height:15px;flex:0 0 15px;border-radius:0;background:none}
.lay .sw.ico img{display:block;width:15px;height:15px;object-fit:contain}
.lay .sw.dot{border-radius:50%}
.lay .sw.diamond{clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%);border-radius:0}
#main{flex:1;position:relative;display:flex;flex-direction:column;min-width:0}
#bar{display:flex;align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid var(--line);
  background:var(--panel)}
#bar .tag{color:var(--dim);font-size:12px}
#bar .sp{flex:1}
#bar button{padding:5px 10px;border:1px solid var(--line);background:var(--panel2);color:var(--txt);
  border-radius:6px;cursor:pointer;font-size:12px}
#wrap{flex:1;position:relative;overflow:hidden;background:#0d1117}
svg{width:100%;height:100%;display:block;cursor:grab}
svg.drag{cursor:grabbing}
.grid{stroke:#9db0cc;stroke-opacity:.08;stroke-width:0.5}
.grid.major{stroke:#9db0cc;stroke-opacity:.17;stroke-width:0.8}
.axis{fill:#55617a;font-size:7px}
.poi-mk{fill:var(--poi);stroke:#7a5c00;stroke-width:0.6}
.poi-bg{fill:#0d1117;fill-opacity:.88}
.poi-tx{fill:#ffe9a8;font-size:7px;paint-order:stroke;stroke:#0d1117;stroke-width:1.6px;
  font-family:"Microsoft YaHei",sans-serif;pointer-events:none}
.enemy{fill:var(--enemy);fill-opacity:.75}
.enemy-normal{fill:#ff5b5b;fill-opacity:.75}
.enemy-elite{fill:#ff9f43;fill-opacity:.9;stroke:#0d1117;stroke-width:.3}
.enemy-boss{filter:drop-shadow(0 0 1.5px #000)}
.enemy-tx{fill:#ffd7a1;font-size:5.5px;paint-order:stroke;stroke:#0d1117;stroke-width:1.3px;
  font-family:"Microsoft YaHei",sans-serif;pointer-events:none}
.enemy-tx.boss{fill:#e9c46a}
.iobj{stroke:#0d1117;stroke-width:.25}
.iobj.loot{fill:#ff9f43;fill-opacity:.86}
.iobj.special{fill:#ffd166;fill-opacity:.9}
.iobj.device{fill:#7aa2ff;fill-opacity:.76}
.iobj.npc{fill:#4dd0e1;fill-opacity:.82}
.iobj.other{fill:#9aa4b2;fill-opacity:.72}
.iobj.box{fill:#ff9f43;fill-opacity:.86}
.iobj.exp{fill:none;stroke:none;filter:drop-shadow(0 0 1px #000)}
.iobj.random{fill-opacity:.2;stroke:#fff;stroke-width:.35;stroke-dasharray:1 .7}
.iobj.grapple{fill:#0d1117;fill-opacity:.55;stroke:#4fc3f7;stroke-width:.9}
.iobj.magnetic{fill:#c084fc;fill-opacity:.82;stroke:#0d1117;stroke-width:.3}
.npc{fill:var(--npc);stroke:#0d1117;stroke-width:.5}
.dark{fill:#4dd0e1;fill-opacity:.9;stroke:#0d1117;stroke-width:.5}
.npc-tx{fill:#9ef5ff;font-size:6px;paint-order:stroke;stroke:#0d1117;stroke-width:1.4px;
  font-family:"Microsoft YaHei",sans-serif;pointer-events:none}
.seg{display:flex;gap:4px;margin:2px 0 6px}
.seg button{flex:1;padding:4px 2px;border:1px solid var(--line);background:var(--panel2);
  color:var(--txt);border-radius:5px;cursor:pointer;font-size:11px}
.seg button.on{background:#2d6cdf;border-color:#2d6cdf}
#boxes .lay,#exps .lay{padding:3px 0}
.hint{color:var(--dim);font-size:10px;margin-top:4px;line-height:1.4}
.spawn{fill:var(--spawn);stroke:#0d1117;stroke-width:.7}
.hidden{display:none}
.mapbg{opacity:1}
.hl{filter:drop-shadow(0 0 4px #fff)}
#svg [data-cat]{transition:opacity .15s;cursor:pointer}
#svg .hl-dim{opacity:.14}
</style>
</head>
<body>
<div id="app">
  <div id="side">
    <h1>危区探遗 · 地图数据<small>Girls' Frontline 2 Exilium · 离线解析</small></h1>
    <div class="maps" id="maps"></div>
    <div class="sec">
      <div class="t">探遗深度</div>
      <div class="seg" id="depths"></div>
    </div>
    <div class="sec">
      <div class="t">数据筛选 <button class="mini" id="allon">全开</button><button class="mini" id="alloff">全关</button></div>
      <div id="layers"></div>
      <div class="t" style="margin-top:8px">精英 / 首领</div>
      <div id="enemies"></div>
      <div class="t" style="margin-top:8px">箱子</div>
      <div id="boxes"></div>
      <div class="t" style="margin-top:8px">图鉴</div>
      <div id="exps"></div>
      <div class="t" style="margin-top:8px">特殊点位</div>
      <div id="utils"></div>
    </div>
  </div>
  <div id="main">
    <div id="bar">
      <span class="sp"></span>
      <button id="zin">放大 +</button>
      <button id="zout">缩小 −</button>
      <button id="zreset">复位</button>
    </div>
    <div id="wrap">
      <svg id="svg"></svg>
    </div>
  </div>
</div>
<script>
const DATA = __DATA__;
const LAYERS = [
  {k:'pois',   n:'地标 POI',   c:'var(--poi)',   on:true},
  {k:'spawns', n:'玩家出生点', c:'var(--spawn)', on:true}
];
const BOX_TYPES = DATA.boxTypes, EXP_TYPES = DATA.expTypes, UTIL_TYPES = DATA.utilTypes,
      ENEMY_TYPES = DATA.enemyTypes, DEPTHS = DATA.depths || [1,2,3,4,5,6];
const EXP_ICON = Object.fromEntries(EXP_TYPES.map(t=>[t.k,t.icon]));
const ENEMY_ICON = Object.fromEntries(ENEMY_TYPES.map(t=>[t.k,t.icon]));
const DARK_ICON = DATA.darkIcon;
const BOX_COLOR = Object.fromEntries(BOX_TYPES.map(t=>[t.k,t.color]));
const NS='http://www.w3.org/2000/svg';
const svg=document.getElementById('svg'), wrap=document.getElementById('wrap'),
      layerBox=document.getElementById('layers'),
      mapBox=document.getElementById('maps'),
      boxBox=document.getElementById('boxes'), expBox=document.getElementById('exps'),
      utilBox=document.getElementById('utils'), enemyBox=document.getElementById('enemies'),
      depthBox=document.getElementById('depths');
let cur=null, curKey=null, curDepth=DATA.defaultDepth||DEPTHS[DEPTHS.length-1], W=0, H=0,
    view={x:0,y:0,w:0,h:0}, show={}, showBox={}, showExp={}, showUtil={},
    showEnemy={}, highlightCat=null;

function el(t,a){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;}
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

/* ---- UI ---- */
LAYERS.forEach(L=>{
  show[L.k]=L.on!==false;
  const row=document.createElement('label');row.className='lay';
  row.innerHTML=`<input type="checkbox"${L.on===false?'':' checked'}><span class="sw" style="background:${L.c}"></span>`+
                `<span class="n">${L.n}</span><span class="c" data-c="${L.k}"></span>`;
  row.querySelector('input').addEventListener('change',e=>{
    show[L.k]=e.target.checked; applyFilters();
  });
  layerBox.appendChild(row);
});
function addChecks(container, items, state, color){
  items.forEach(t=>{
    state[t.k]=true;
    const row=document.createElement('label');row.className='lay';
    const col=t.color||color;
    const sw=t.icon?`<span class="sw ico"><img src="${t.icon}" alt=""></span>`
                    :`<span class="sw ${t.shape||''}" style="background:${col}"></span>`;
    row.innerHTML=`<input type="checkbox" checked>${sw}`+
                  `<span class="n">${esc(t.n)}</span><span class="c" data-c="${t.k}"></span>`;
    const inp=row.querySelector('input');inp.dataset.v=t.k;
    inp.addEventListener('change',e=>{state[t.k]=e.target.checked;applyFilters();});
    container.appendChild(row);
  });
}
addChecks(boxBox,BOX_TYPES,showBox,'#ff9f43');
addChecks(expBox,EXP_TYPES,showExp,'#ffd166');
addChecks(utilBox,UTIL_TYPES,showUtil,'#4dd0e1');
addChecks(enemyBox,ENEMY_TYPES,showEnemy,'#ff5b5b');
DEPTHS.forEach(d=>{
  const b=document.createElement('button');
  b.textContent=d;b.dataset.d=d;b.classList.toggle('on',d===curDepth);
  b.addEventListener('click',()=>{
    curDepth=d;
    [...depthBox.children].forEach(x=>x.classList.toggle('on',Number(x.dataset.d)===curDepth));
    if(curKey) selectMap(curKey, false);
  });
  depthBox.appendChild(b);
});
function setAll(v){
  layerBox.querySelectorAll('input').forEach(i=>i.checked=v);
  LAYERS.forEach(L=>show[L.k]=v);
  boxBox.querySelectorAll('input').forEach(i=>i.checked=v);
  expBox.querySelectorAll('input').forEach(i=>i.checked=v);
  utilBox.querySelectorAll('input').forEach(i=>i.checked=v);
  enemyBox.querySelectorAll('input').forEach(i=>i.checked=v);
  BOX_TYPES.forEach(t=>showBox[t.k]=v);
  EXP_TYPES.forEach(t=>showExp[t.k]=v);
  UTIL_TYPES.forEach(t=>showUtil[t.k]=v);
  ENEMY_TYPES.forEach(t=>showEnemy[t.k]=v);
  applyFilters();
}
document.getElementById('allon').onclick=()=>setAll(true);
document.getElementById('alloff').onclick=()=>setAll(false);
function applyFilters(){
  LAYERS.forEach(L=>{
    const g=document.getElementById('g-'+L.k);
    if(g) g.classList.toggle('hidden', !show[L.k]);
  });
  const gi=document.getElementById('g-iobjs');
  if(gi) gi.querySelectorAll('.iobj').forEach(el=>{
    const b=el.dataset.b, e=el.dataset.e;
    let okType=false;
    if(el.dataset.k!=='npc'){
      if(b) okType=showBox[b]!==false;
      if(e) okType=okType||showExp[e]!==false;
    }
    el.style.display=okType?'':'none';
  });
  const gu=document.getElementById('g-utils');
  if(gu) gu.querySelectorAll('[data-u]').forEach(el=>{
    el.style.display=showUtil[el.dataset.u]===false?'none':'';
  });
  const ge=document.getElementById('g-enemies');
  if(ge) ge.querySelectorAll('[data-t]').forEach(el=>{
    el.style.display=showEnemy[el.dataset.t]===false?'none':'';
  });
}
function applyHighlight(){
  const els=[...svg.querySelectorAll('[data-cat]')];
  if(highlightCat && !els.some(x=>x.dataset.cat===highlightCat)) highlightCat=null;
  els.forEach(x=>x.classList.toggle('hl-dim', !!highlightCat && x.dataset.cat!==highlightCat));
}
Object.keys(DATA.maps).forEach(k=>{
  const m=DATA.maps[k];
  const b=document.createElement('button');
  b.innerHTML=`${m.btn||m.name}<small>${m.sub||m.scene}</small>`;
  b.title=m.name+' · '+m.scene;
  b.dataset.k=k;
  b.addEventListener('click',()=>selectMap(k));
  mapBox.appendChild(b);
});
function iobjActive(o,d){
  return !o.variants || o.variants.some(v=>v===null||v===Number(d));
}
function depthIobjs(d){
  const seen=new Set(), out=[];
  for(const o of cur.iobjs){
    if(!iobjActive(o,d)) continue;
    const k=o.group??o.id;
    if(seen.has(k)) continue;
    seen.add(k); out.push(o);
  }
  return out;
}
function selectMap(k, resetView=true){
  cur=DATA.maps[k];curKey=k;
  const ds=String(curDepth);
  if(cur.enemiesByDepth) cur.enemies=cur.enemiesByDepth[ds]||[];
  if(cur.challengesByDepth) cur.challenges=cur.challengesByDepth[ds]||[];
  if(cur.npcsByDepth) cur.npcs=cur.npcsByDepth[ds]||[];
  if(cur.spawnsByDepth) cur.spawns=cur.spawnsByDepth[ds]||[];
  wrap.style.background=cur.bgColor||'#0d1117';
  [...mapBox.children].forEach(b=>b.classList.toggle('on',b.dataset.k===k));
  [...depthBox.children].forEach(b=>b.classList.toggle('on',Number(b.dataset.d)===curDepth));
  cur.disp=cur.disp||cur.size.slice();
  W=cur.disp[0];H=cur.disp[1];
  const rot=(cur.rotate||0)*Math.PI/180, cr=Math.cos(rot), sr=Math.sin(rot);
  const cx=cur.size[0]/2, cy=cur.size[1]/2, dw=W/2, dh=H/2;
  const tf=p=>{
    if(p.ox===undefined){p.ox=p.x;p.oy=p.y;}
    const py=cur.size[1]-p.oy;
    if(!rot){p.x=p.ox;p.y=py;return;}
    const dx=p.ox-cx, dy=py-cy;
    p.x=dw+cr*dx-sr*dy; p.y=dh+sr*dx+cr*dy;
  };
  ['pois','iobjs','challenges','enemies','npcs','spawns'].forEach(k=>(cur[k]||[]).forEach(tf));
  if(resetView) view={x:0,y:0,w:W,h:H};
  render();
  const activeIobjs=depthIobjs(curDepth);
  const baseVis=activeIobjs.filter(o=>(o.box||o.expCat)&&o.kind!=='npc');
  const challengeVis=(cur.challenges||[]).map(c=>({...c,kind:'challenge',box:'',expCat:'challenge'}));
  const vis=baseVis.concat(challengeVis);
  const utilVis=activeIobjs.filter(o=>o.utilCat);
  LAYERS.forEach(L=>{
    const c=layerBox.querySelector(`[data-c="${L.k}"]`);
    if(c) c.textContent=(cur[L.k]||[]).length;
  });
  BOX_TYPES.forEach(t=>{
    const c=boxBox.querySelector(`[data-c="${t.k}"]`);
    if(c) c.textContent=vis.filter(o=>o.box===t.k).length;
  });
  EXP_TYPES.forEach(t=>{
    const c=expBox.querySelector(`[data-c="${t.k}"]`);
    if(c) c.textContent=vis.filter(o=>o.expCat===t.k).length;
  });
  UTIL_TYPES.forEach(t=>{
    const c=utilBox.querySelector(`[data-c="${t.k}"]`);
    if(c) c.textContent=t.k==='dark'
      ? (cur.npcs||[]).filter(n=>n.ref===1004).length
      : utilVis.filter(o=>o.utilCat===t.k).length;
  });
  ENEMY_TYPES.forEach(t=>{
    const c=enemyBox.querySelector(`[data-c="${t.k}"]`);
    if(c) c.textContent=(cur.enemies||[]).filter(e=>e.rank===t.k).length;
  });
  applyFilters();
}

/* ---- render map ---- */
function render(){
  svg.innerHTML='';
  svg.setAttribute('viewBox',`${view.x} ${view.y} ${view.w} ${view.h}`);
  const defs=el('defs');
  defs.innerHTML=`<pattern id="pat" width="20" height="20" patternUnits="userSpaceOnUse">
    <path class="grid" d="M20 0H0V20" fill="none"/></pattern>`;
  svg.appendChild(defs);
  const bg=el('rect',{x:0,y:0,width:W,height:H,fill:cur.bgColor||'#111722',stroke:'#33415a','stroke-width':1.2});
  svg.appendChild(bg);
  if(cur.bg){
    const im=el('image',{x:0,y:0,width:W,height:H,preserveAspectRatio:'none',class:'mapbg'});
    im.setAttribute('href',cur.bg);
    svg.appendChild(im);
  }
  svg.appendChild(el('rect',{x:0,y:0,width:W,height:H,fill:'url(#pat)'}));
  // major grid + labels
  const g=el('g');
  const fs=Math.max(1.6,Math.min(7,Math.max(W,H)/50));
  for(let v=0;v<=W;v+=50){g.appendChild(el('line',{class:'grid major',x1:v,y1:0,x2:v,y2:H}));}
  for(let v=0;v<=H;v+=50){g.appendChild(el('line',{class:'grid major',x1:0,y1:v,x2:W,y2:v}));}
  for(let v=0;v<=W;v+=50){const t=el('text',{class:'axis',x:v+fs*.25,y:fs*1.15,style:`font-size:${fs}px`});t.textContent=v;g.appendChild(t);}
  for(let v=50;v<=H;v+=50){const t=el('text',{class:'axis',x:fs*.25,y:v-fs*.3,style:`font-size:${fs}px`});t.textContent=v;g.appendChild(t);}
  svg.appendChild(g);

  const mk=(name)=>{const gg=el('g',{id:'g-'+name});svg.appendChild(gg);return gg;};

  const mkScale=Math.min(1,W/330);
  if(cur.enemies.length){
    const ge=mk('enemies');
    cur.enemies.forEach(e=>{
      let r;
      if(e.rank==='boss'&&ENEMY_ICON.boss){
        const s=5.2*mkScale;
        r=el('image',{class:'enemy-boss',x:e.x-s/2,y:e.y-s/2,width:s,height:s,
                      preserveAspectRatio:'xMidYMid meet'});
        r.setAttribute('href',ENEMY_ICON.boss);
      }else if(e.rank==='elite'&&ENEMY_ICON.elite){
        const s=4.8*mkScale;
        r=el('image',{class:'enemy-elite',x:e.x-s/2,y:e.y-s/2,width:s,height:s,
                      preserveAspectRatio:'xMidYMid meet'});
        r.setAttribute('href',ENEMY_ICON.elite);
      }else if(e.rank==='elite'){
        const b=2.1*mkScale;
        r=el('polygon',{class:'enemy-elite',
          points:`${e.x},${e.y-b} ${e.x+b},${e.y} ${e.x},${e.y+b} ${e.x-b},${e.y}`});
      }else{
        r=el('circle',{class:'enemy-normal',cx:e.x,cy:e.y,r:1.4*mkScale});
      }
      r.dataset.t=e.rank;r.dataset.cat='enemy:'+e.rank;
      ge.appendChild(r);
      if((e.name||e.fallback)&&(e.rank==='boss'||e.rank==='elite')){
        const label=e.name||'未知';
        const fsE=4.2*mkScale;
        const txX=e.x+(e.rank==='boss'?3.2:3.0)*mkScale;
        const txY=e.y+fsE*0.35;
        const tx=el('text',{class:`enemy-tx ${e.rank}`,x:txX,y:txY,
                            style:`font-size:${fsE}px`});
        tx.textContent=label;
        tx.dataset.t=e.rank;tx.dataset.cat='enemy:'+e.rank;
        ge.appendChild(tx);
      }
    });
  }
  const iobjItems=depthIobjs(curDepth).filter(o=>(o.box||o.expCat)&&o.kind!=='npc')
    .concat((cur.challenges||[]).map(c=>({...c,kind:'challenge',box:'',expCat:'challenge'})));
  if(iobjItems.length){
    const gi=mk('iobjs');
    iobjItems.forEach(o=>{
      const cls=`iobj ${o.kind}${o.box?' box':''}${o.expCat?' exp':''}${o.random?' random':''}`;
      let r;
      if(o.expCat&&EXP_ICON[o.expCat]){
        const s=6.0*mkScale;
        r=el('image',{class:cls,x:o.x-s/2,y:o.y-s/2,width:s,height:s,
                      preserveAspectRatio:'xMidYMid meet'});
        r.setAttribute('href',EXP_ICON[o.expCat]);
      }else if(o.box){
        const b=2.2*mkScale;
        r=el('rect',{class:cls,x:o.x-b/2,y:o.y-b/2,width:b,height:b});
        r.style.fill=BOX_COLOR[o.box]||'#ff9f43';
      }else if(o.kind==='special'){
        r=el('polygon',{class:cls,points:`${o.x},${o.y-1.7} ${o.x+1.7},${o.y} ${o.x},${o.y+1.7} ${o.x-1.7},${o.y}`});
      }else if(o.kind==='device'){
        r=el('circle',{class:cls,cx:o.x,cy:o.y,r:1.35});
      }else{
        r=el('rect',{class:cls,x:o.x-1.1,y:o.y-1.1,width:2.2,height:2.2});
      }
      r.dataset.k=o.kind;r.dataset.s=o.sub;
      r.dataset.b=o.box||'';r.dataset.e=o.expCat||'';
      r.dataset.cat=o.expCat?'exp:'+o.expCat:
        (o.box?'box:'+(['misc','misc1','misc2','misc3'].includes(o.box)?'misc':o.box):'iobj:'+o.kind);
      gi.appendChild(r);
    });
  }
  const utilItems=depthIobjs(curDepth).filter(o=>o.utilCat);
  const darkNpcs=(cur.npcs||[]).filter(n=>n.ref===1004);
  if(utilItems.length||darkNpcs.length){
    const gu=mk('utils');
    utilItems.forEach(o=>{
      let r;
      if(o.utilCat==='magnetic'){
        r=el('polygon',{class:`iobj magnetic${o.random?' random':''}`,
          points:`${o.x},${o.y-2.0} ${o.x+2.0},${o.y} ${o.x},${o.y+2.0} ${o.x-2.0},${o.y}`});
      }else{
        r=el('circle',{class:`iobj grapple${o.random?' random':''}`,
          cx:o.x,cy:o.y,r:2.0});
      }
      r.dataset.u=o.utilCat;r.dataset.cat='util:'+o.utilCat;
      gu.appendChild(r);
    });
    darkNpcs.forEach(n=>{
      const g=el('g');g.dataset.u='dark';g.dataset.cat='util:dark';
      if(DARK_ICON){
        const s=7.5*Math.min(1,W/330);
        const im=el('image',{class:'dark-icon',x:n.x-s/2,y:n.y-s/2,width:s,height:s,
                             preserveAspectRatio:'xMidYMid meet'});
        im.setAttribute('href',DARK_ICON);g.appendChild(im);
      }else{
        g.appendChild(el('rect',{class:'dark',x:n.x-2.2,y:n.y-2.2,width:4.4,height:4.4,rx:1}));
      }
      const t=el('text',{class:'npc-tx',x:n.x+4.0,y:n.y+2.0});
      t.textContent=n.name||'暗商';g.appendChild(t);
      gu.appendChild(g);
    });
  }
  if(cur.spawns.length){
    const gs=mk('spawns');
    cur.spawns.forEach(s=>{
      const c=el('circle',{class:'spawn',cx:s.x,cy:s.y,r:2.6});
      c.dataset.cat='spawn';
      gs.appendChild(c);
    });
  }
  if(cur.pois.length){
    const gp=mk('pois');
    cur.pois.forEach(p=>{
      const g=el('g');g.dataset.cat='poi';
      const st=el('polygon',{class:'poi-mk',points:star(p.x,p.y,4.2,1.8,5)});
      g.appendChild(st);
      const bw=p.name.length*7.3+5;
      g.appendChild(el('rect',{class:'poi-bg',x:p.x+4.6,y:p.y-4.4,width:bw,height:9.4,rx:1.6}));
      const t=el('text',{class:'poi-tx',x:p.x+5.5,y:p.y+2.5});
      t.textContent=p.name;g.appendChild(t);
      gp.appendChild(g);
    });
  }
  applyFilters();
  applyHighlight();
}
function star(cx,cy,R,r,n){
  let pts=[];for(let i=0;i<n*2;i++){const a=-Math.PI/2+i*Math.PI/n;const rad=i%2?r:R;
    pts.push((cx+rad*Math.cos(a)).toFixed(2)+','+(cy+rad*Math.sin(a)).toFixed(2));}
  return pts.join(' ');
}

/* ---- zoom & pan ---- */
function setView(v){view=v;svg.setAttribute('viewBox',`${v.x} ${v.y} ${v.w} ${v.h}`);}
svg.addEventListener('wheel',ev=>{
  ev.preventDefault();
  const r=svg.getBoundingClientRect();
  const mx=view.x+(ev.clientX-r.left)/r.width*view.w;
  const my=view.y+(ev.clientY-r.top)/r.height*view.h;
  const f=ev.deltaY<0?0.85:1.18;
  const nw=Math.min(W*3,Math.max(W/12,view.w*f)), nh=nw*(H/W);
  setView({x:mx-(mx-view.x)*nw/view.w,y:my-(my-view.y)*nh/view.h,w:nw,h:nh});
},{passive:false});
const drag={on:false,x:0,y:0,vx:0,vy:0,moved:false};
const startDrag=ev=>{drag.on=true;drag.moved=false;drag.x=ev.clientX;drag.y=ev.clientY;
  drag.vx=view.x;drag.vy=view.y;svg.classList.add('drag');};
function doDrag(ev){if(!drag.on)return;
  if(Math.abs(ev.clientX-drag.x)+Math.abs(ev.clientY-drag.y)>4) drag.moved=true;
  const r=svg.getBoundingClientRect();
  const dx=(ev.clientX-drag.x)/r.width*view.w, dy=(ev.clientY-drag.y)/r.height*view.h;
  setView({...view,x:drag.vx-dx,y:drag.vy-dy});}
const endDrag=()=>{drag.on=false;svg.classList.remove('drag');};
svg.addEventListener('mousedown',startDrag);
window.addEventListener('mouseup',endDrag);
svg.addEventListener('mousemove',ev=>{if(drag.on)doDrag(ev);});
svg.addEventListener('click',ev=>{
  if(drag.moved){drag.moved=false;return;}
  const t=ev.target.closest?ev.target.closest('[data-cat]'):null;
  if(!t){if(highlightCat){highlightCat=null;applyHighlight();}return;}
  highlightCat=highlightCat===t.dataset.cat?null:t.dataset.cat;
  applyHighlight();
});
function zoom(f){const cx=view.x+view.w/2,cy=view.y+view.h/2;const nw=Math.min(W*3,Math.max(W/12,view.w*f));
  setView({x:cx-nw/2,y:cy-nw*(H/W)/2,w:nw,h:nw*(H/W)});}
document.getElementById('zin').onclick=()=>zoom(0.8);
document.getElementById('zout').onclick=()=>zoom(1.25);
document.getElementById('zreset').onclick=()=>setView({x:0,y:0,w:W,h:H});
function centerOn(x,y){const w=W/5;setView({x:x-w/2,y:y-w*(H/W)/2,w:w,h:w*(H/W)});}
const params=new URLSearchParams(location.search);
const qd=Number(params.get('depth'));
if(DEPTHS.includes(qd)) curDepth=qd;
[...depthBox.children].forEach(b=>b.classList.toggle('on',Number(b.dataset.d)===curDepth));
function setFromQuery(container,state,raw){
  if(!raw)return;
  const keys=raw.split(',').filter(Boolean);
  Object.keys(state).forEach(k=>state[k]=keys.includes(k));
  container.querySelectorAll('input').forEach(i=>i.checked=state[i.dataset.v]);
}
setFromQuery(boxBox,showBox,params.get('box'));
setFromQuery(expBox,showExp,params.get('exp'));
setFromQuery(utilBox,showUtil,params.get('util'));
setFromQuery(enemyBox,showEnemy,params.get('enemy'));
const start=params.get('map');
selectMap(DATA.maps[start]?start:Object.keys(DATA.maps)[0]);
</script>
</body>
</html>
"""

html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
outp = os.path.join(HERE, "gf2_map.html")
open(outp, "w", encoding="utf-8").write(html)
print("wrote", outp, len(html), "bytes")

