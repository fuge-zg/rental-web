# -*- coding: utf-8 -*-
"""从 index.html（管家版）生成租客版 tenant/index.html

改造规则：
- 楼栋匿名化：盘口内按栋号数字排序分配 A/B/C... 代号（映射固定，不随数据变化漂移）
- 删除来源人名（src 字段）
- note 过滤：房间密码、佣金/红包、已租已定已签剔除记录、价目表/微信群等内部词汇
- 页面文案改租客视角，统一联系入口为房东电话
- 保留视频在线播放：从 filebin registry.json 拉取视频索引（真实栋名通过隐藏映射表对应）
- 删除全部内部功能：视频上传/队列/自检/H盘写入等

用法：python build_tenant.py
之后 git add tenant/index.html && git commit && git push，租客版即同步上线。
"""
import json, re, os, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "index.html")
OUTDIR = os.path.join(BASE, "tenant")
OUT = os.path.join(OUTDIR, "index.html")
PHONE = "19879877953"

html_src = open(SRC, encoding="utf-8").read()
m = re.search(r'const DATA = (\[.*?\]);\s*\nconst state', html_src, re.S)
if not m:
    raise SystemExit("!! 未找到 DATA JSON，请确认 index.html 格式")
data = json.loads(m.group(1))

def park_of(name):
    if name.startswith("共和花园"):
        return "共和花园"
    if "伍屋村" in name:
        return "伍屋村"
    return "其他"

def bld_num(name):
    m2 = re.search(r'(\d+)\s*栋', name)
    return int(m2.group(1)) if m2 else 9999

groups = {}
for b in data:
    groups.setdefault(park_of(b["b"]), []).append(b)

letters = "ABCDEFGHIJKLMNOPQRSTUVWXY"
def anon_code(i):
    L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return L[i] if i < len(L) else "A" + L[i - len(L)]

anon_map = {}
print("== 楼栋匿名映射 ==")
for park in ["共和花园", "伍屋村", "其他"]:
    if park not in groups:
        continue
    for i, b in enumerate(sorted(groups[park], key=lambda x: bld_num(x["b"]))):
        anon = "%s·%s栋" % (park, anon_code(i))
        anon_map[b["b"]] = anon
        print("  %s  ->  %s" % (b["b"], anon))

BAD_KW = ["密码", "佣金", "红包", "已剔除", "已定", "已签", "已租",
          "价目表", "微信群", "管家", "结佣", "招租"]
def clean_note(note):
    if not note:
        return ""
    keep = []
    for p in re.split(r'[；;]', note):
        p = p.strip()
        if not p:
            continue
        if any(k in p for k in BAD_KW):
            continue
        keep.append(p)
    return "；".join(keep)

new_data = []
for b in data:
    nb = {"b": anon_map[b["b"]]}
    if b.get("park"):
        nb["park"] = b["park"]
    if b.get("time"):
        nb["time"] = b["time"]
    nb["note"] = clean_note(b.get("note"))
    nb["rooms"] = b.get("rooms", [])
    if b.get("status"):
        nb["status"] = b["status"]
    new_data.append(nb)

bmap = {anon_map[b["b"]]: b["b"] for b in data}

date_m = re.search(r'更新 <b>([\d\-]+)</b>', html_src)
update_date = date_m.group(1) if date_m else ""

data_js = json.dumps(new_data, ensure_ascii=False, separators=(",", ":"))
bmap_js = json.dumps(bmap, ensure_ascii=False, separators=(",", ":"))

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>富哥房源 · 在租房源</title>
<style>
:root{--teal:#0F8577;--teal-d:#0B6E63;--bg:#F1F5F3;--card:#fff;--ink:#22302C;--sub:#7A8C86;--line:#E2EAE7;--orange:#E8833A;}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{background:var(--bg);color:var(--ink);font-family:"PingFang SC","Microsoft YaHei","Segoe UI",system-ui,sans-serif;font-size:15px;line-height:1.5}
.wrap{max-width:740px;margin:0 auto;padding:0 12px 40px}
header{background:linear-gradient(160deg,#109183,var(--teal-d));border-radius:0 0 18px 18px;padding:18px 16px 16px;color:#fff;box-shadow:0 6px 18px rgba(15,133,119,.25)}
.hrow{display:flex;align-items:center;gap:10px}
.logo{font-size:22px}
h1{font-size:21px;font-weight:700;letter-spacing:.5px}
.btn-book{margin-left:auto;background:rgba(255,255,255,.16);border:1.5px solid rgba(255,255,255,.75);color:#fff;border-radius:10px;padding:7px 14px;font-size:13px;cursor:pointer;white-space:nowrap}
.btn-book:hover{background:rgba(255,255,255,.28)}
.stats{font-size:12.5px;opacity:.92;margin-top:6px}
.stats b{font-size:14px}
.bigbadge{margin-left:10px;background:rgba(255,255,255,.14);border:1.5px solid rgba(255,255,255,.72);border-radius:12px;padding:5px 14px;text-align:center;flex-shrink:0}
.bigbadge b{display:block;font-size:21px;line-height:1.15}
.bigbadge span{font-size:11px;opacity:.92}
.search{margin-top:12px;position:relative}
.search input{width:100%;border:none;border-radius:12px;padding:12px 52px 12px 40px;font-size:14.5px;outline:none;color:var(--ink);background:#fff;box-shadow:0 3px 10px rgba(0,0,0,.12)}
.search .mag{position:absolute;left:13px;top:50%;transform:translateY(-50%);opacity:.5}
.search .clr{position:absolute;right:10px;top:50%;transform:translateY(-50%);border:none;background:#Eef2f1;width:26px;height:26px;border-radius:50%;cursor:pointer;color:#667;font-size:13px;display:none}
.hint{font-size:12px;opacity:.9;margin-top:9px}
.hint .kw{background:rgba(255,255,255,.18);border-radius:6px;padding:1px 7px;margin:0 2px;font-weight:600}
.toggle2{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:12px}
.toggle2 button{background:rgba(255,255,255,.14);border:1.5px solid rgba(255,255,255,.55);color:#fff;border-radius:11px;padding:9px 0;font-size:14px;cursor:pointer}
.toggle2 button.on{background:#fff;color:var(--teal-d);font-weight:700;border-color:#fff}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 4px}
.chip{background:#fff;border:1.5px solid var(--line);border-radius:18px;padding:6px 15px;font-size:13.5px;cursor:pointer;color:var(--ink)}
.chip.on{background:var(--teal);border-color:var(--teal);color:#fff;font-weight:600}
.row2{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 2px;font-size:12.5px}
.row2 .lbl{color:var(--sub);padding:5px 2px}
.row2 select{border:1.5px solid var(--line);background:#fff;border-radius:16px;padding:5px 10px;font-size:12.5px;color:var(--ink);outline:none;cursor:pointer}
.found{color:var(--sub);font-size:13px;margin:10px 2px 12px}
.found b{color:var(--orange);font-size:15px}
.found i{color:var(--teal);font-style:normal;font-weight:700}
.card{background:var(--card);border-radius:14px;padding:14px 14px 12px;margin-bottom:12px;box-shadow:0 2px 10px rgba(30,60,55,.06)}
.chead{display:flex;align-items:center;gap:8px}
.chead h2{font-size:16.5px;font-weight:700}
.cbadge{font-size:12px;color:var(--teal-d);background:#E5F3F0;border-radius:8px;padding:2px 8px;white-space:nowrap}
.copy{margin-left:auto;border:1.5px solid var(--line);background:#fff;border-radius:8px;padding:4px 10px;font-size:12px;color:var(--sub);cursor:pointer}
.copy:hover{color:var(--teal);border-color:var(--teal)}
.cnote{font-size:12px;color:var(--sub);margin-top:6px}
.util{font-size:12px;color:#41615A;margin-top:4px;font-weight:600}
.grp{margin-top:10px}
.glabel{font-size:12px;color:var(--sub);margin-bottom:6px;display:flex;align-items:center;gap:6px}
.glabel::after{content:"";flex:1;height:1px;background:var(--line)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px}
.room{background:#fff;border:1.5px solid var(--line);border-radius:11px;padding:9px 4px 7px;text-align:center;cursor:pointer;transition:.15s;position:relative}
.room:hover{border-color:var(--teal);box-shadow:0 3px 10px rgba(15,133,119,.15);transform:translateY(-1px)}
.room .rn{font-size:16px;font-weight:700;letter-spacing:.5px}
.room .rp{color:var(--orange);font-size:13px;font-weight:700;margin-top:2px}
.room .rp.na{color:#AAB6B2;font-weight:500;font-size:12px}
.room .vplay{position:absolute;top:4px;right:4px;width:22px;height:22px;border-radius:50%;background:#12A594;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.22)}
.room .mgf{font-size:11px;color:var(--sub);margin-top:1px}
.room.hi{background:#FFF8D6;border-color:#EFD98B}
#vplayer{position:fixed;inset:0;background:#000;z-index:120;display:flex;flex-direction:column}
.room .tagdot{position:absolute;top:5px;right:6px;font-size:9px;color:#fff;background:var(--orange);border-radius:6px;padding:0 4px}
.empty{color:var(--sub);font-size:12.5px;background:#F6F9F8;border:1.5px dashed var(--line);border-radius:10px;padding:10px;text-align:center;margin-top:10px}
footer{margin-top:18px;font-size:12px;color:var(--sub)}
footer .card{padding:14px}
footer h3{font-size:13.5px;color:var(--ink);margin-bottom:6px}
footer p{margin:3px 0}
.modal{position:fixed;inset:0;background:rgba(15,40,35,.45);display:none;align-items:flex-end;justify-content:center;z-index:50}
.modal.open{display:flex}
.mcard{background:#fff;width:100%;max-width:460px;border-radius:16px 16px 0 0;padding:18px 18px 22px;max-height:86vh;overflow:auto}
@media(min-width:560px){.modal{align-items:center}.mcard{border-radius:16px}}
.mhead{display:flex;align-items:center;margin-bottom:10px}
.mhead h3{font-size:17px}
.mclose{margin-left:auto;border:none;background:#EEF2F1;width:30px;height:30px;border-radius:50%;font-size:14px;cursor:pointer;color:#567}
.mrow{display:flex;border-bottom:1px dashed var(--line);padding:8px 0;font-size:14px}
.mrow .k{width:78px;color:var(--sub);flex-shrink:0}
.mrow .v{flex:1;font-weight:600}
.mrow .v.price{color:var(--orange);font-size:17px}
.mrow .v.plain{font-weight:400;color:var(--ink)}
.mrow .v.tel{color:var(--teal);font-size:17px}
#toast{position:fixed;left:50%;bottom:36px;transform:translateX(-50%);background:rgba(30,45,42,.92);color:#fff;font-size:13px;border-radius:20px;padding:8px 18px;opacity:0;pointer-events:none;transition:.25s;z-index:99}
#toast.show{opacity:1}
</style>
</head>
<body>
<header>
 <div class="wrap" style="padding-bottom:0">
  <div class="hrow">
   <span class="logo">🏠</span><h1>富哥房源</h1>
   <button class="btn-book" onclick="document.getElementById('about').scrollIntoView({behavior:'smooth'})">📞 联系看房</button>
   <div class="bigbadge"><b id="statRooms2">0</b><span>套房在租</span></div>
  </div>
   <div class="stats">共 <b id="statRooms">0</b> 套在租房源 · <b id="statBld">0</b> 个分组 · 更新 <b>__DATE__</b>　📍 深圳·龙华 · 共和花园 / 伍屋村</div>
  <div class="search">
   <span class="mag">🔍</span>
   <input id="q" type="search" placeholder='搜索房号 / 价格区间，如「01」「1000-1600」' autocomplete="off">
   <button class="clr" id="clr">✕</button>
  </div>
  <div class="hint">💡 预算可直接搜区间：<span class="kw">单间 1000-1600</span> 或 <span class="kw">1000至1600</span></div>
   <div class="toggle2" id="floorBtns">
    <button data-v="all" class="on">（全部房源）</button>
    <button data-v="电梯">（电梯房）</button>
    <button data-v="楼梯">（楼梯房）</button>
   </div>
  </div>
 </header>
 <div class="wrap">
  <div class="chips" id="catChips"></div>
  <div class="row2">
   <span class="lbl">盘口</span>
   <select id="park">
    <option value="all">全部</option>
    <option value="共和花园">共和花园</option>
    <option value="伍屋村">伍屋村</option>
    <option value="其他">其他盘口</option>
   </select>
   <span class="lbl">预算</span>
   <select id="budget">
    <option value="all">不限</option>
    <option value="0-1000">1000以下</option>
    <option value="1000-1500">1000-1500</option>
    <option value="1500-2000">1500-2000</option>
    <option value="2000-99999">2000以上</option>
   </select>
   <span class="lbl">楼型</span>
   <select id="floorSel">
    <option value="all">全部</option>
    <option value="电梯">电梯</option>
    <option value="楼梯">楼梯</option>
   </select>
   <span class="lbl">排序</span>
   <select id="sort">
    <option value="def">默认</option>
    <option value="asc">价格低→高</option>
    <option value="desc">价格高→低</option>
   </select>
  </div>
 <div class="found">找到 <b id="cnt">0</b> 套房源 · 分布在 <i id="cntB">0</i> 个分组</div>
 <div class="legend">🟡 黄色房号 = 高层房源　▶ = 有房间实拍视频（点▶直接看）</div>
 <div id="list"></div>
 <footer id="about">
  <div class="card">
   <h3>📞 联系看房</h3>
   <p>看房请拨打房东电话：<a href="tel:__PHONE__" style="color:var(--teal);font-weight:700;font-size:16px">__PHONE__</a>（手机上点击可直接拨打）</p>
   <p>房态实时变动，来电确认房源在租后即可安排带看。</p>
  </div>
  <div class="card">
   <h3>📌 温馨提示</h3>
   <p>· 房源信息更新于 __DATE__，实时变动，以电话确认为准</p>
   <p>· 部分房源有实拍视频，点房号右上角 ▶ 直接观看</p>
   <p>· 空白字段＝原信息未标注</p>
  </div>
 </footer>
</div>
<div class="modal" id="modal"><div class="mcard" id="mcard"></div></div>
<div id="toast">已复制</div>
<script>
const DATA = __DATA__;
/* 楼栋匿名代号 -> 真实楼栋名（仅用于匹配房间视频索引，不在页面展示） */
const BMAP = __BMAP__;
const UPDATE_DATE = "__DATE__";
const PHONE = "__PHONE__";
const state = {cat:"全部户型", floor:"all", park:"all", budget:"all", sort:"def", q:""};
const CATEGORIES = ["全部户型","单间","大单间","一房一厅","两房一厅","三房一厅","其他"];
function catOf(t){
  if(!t) return "其他";
  if(t.includes("三房")) return "三房一厅";
  if(t.includes("两房")||t.includes("二房")) return "两房一厅";
  if(t.includes("大单")) return "大单间";
  if(t.includes("一房")||t.includes("一室")) return "一房一厅";
  if(t.includes("单")) return "单间";
  return "其他";
}
const ICON={"单间":"🛏️","大单间":"🛌","一房一厅":"🏠","两房一厅":"🏡","三房一厅":"🏘️","其他":"📦"};
function parkOf(b){return b.park||(b.b.startsWith("共和花园")?"共和花园":(b.b.includes("伍屋村")?"伍屋村":"其他"))}
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}
function parseTokens(q){
  return q.trim().split(/\s+/).filter(Boolean).map(tok=>{
    const m=tok.match(/^(\d{3,5})\s*(?:[-~至到]\s*(\d{3,5}))?$/);
    if(m&&m[2]) return {type:"range",lo:+m[1],hi:+m[2]};
    return {type:"text",v:tok.toLowerCase()};
  });
}
function roomMatch(r,bname,toks){
  const price = typeof r.p==="number"?r.p:null;
  for(const tk of toks){
    if(tk.type==="range"){
      if(price===null||price<tk.lo||price>tk.hi) return false;
    }else{
      const v=tk.v;
      const hay=(bname+" "+r.r+" "+r.t+" "+(r.tag||"")).toLowerCase();
      if(!hay.includes(v)) return false;
    }
  }
  return true;
}
function render(){
  const toks=parseTokens(state.q);
  const totalRooms=DATA.reduce((s,b)=>s+b.rooms.length,0);
  const totalB=DATA.filter(b=>b.rooms.length>0).length;
  document.getElementById("statRooms").textContent=totalRooms;
  document.getElementById("statRooms2").textContent=totalRooms;
  document.getElementById("statBld").textContent=totalB;
  let html="",cnt=0,cntB=0;
  for(const b of DATA){
    if(state.park!=="all"&&parkOf(b)!==state.park) continue;
    let rooms=b.rooms.filter(r=>{
      if(state.cat!=="全部户型"&&catOf(r.t)!==state.cat) return false;
      if(state.floor!=="all"&&(r.f||"").indexOf(state.floor)<0) return false;
      if(state.budget!=="all"){const bp=typeof r.p==="number"?r.p:null;if(bp===null)return false;const pr=state.budget.split("-").map(Number);if(bp<pr[0]||bp>=pr[1])return false;}
      if(toks.length&&!roomMatch(r,b.b,toks)) return false;
      return true;
    });
    if(state.sort==="asc") rooms=[...rooms].sort((a,b2)=>(a.p??1e9)-(b2.p??1e9));
    if(state.sort==="desc") rooms=[...rooms].sort((a,b2)=>(b2.p??-1)-(a.p??-1));
    if(b.rooms.length===0){
      if(toks.length) continue;
      const label=b.status==="full"?"🏙️ 满房":"❓ 信息缺失";
      html+=`<div class="card"><div class="chead"><h2>${esc(b.b)}</h2><span class="cbadge">${label}</span></div><div class="cnote">${esc(b.note)}</div><div class="empty">暂无可展示的在租房源</div></div>`;
      continue;
    }
    if(rooms.length===0) continue;
    cnt+=rooms.length;cntB++;
    const uc=b.rooms.find(r=>r.c), uh=b.rooms.find(r=>r.h), ue=b.rooms.find(r=>r.e);
    const uparts=[];
    if(uc) uparts.push("冷水"+uc.c);
    if(uh) uparts.push("热水"+uh.h);
    if(ue) uparts.push("电"+ue.e);
    const util=uparts.length? "💧 水电："+uparts.join(" · ")+"（水/热水：元每吨，电：元每度）" : "💧 水电：未标注";
    const groups={};
    rooms.forEach(r=>{(groups[catOf(r.t)] ||= []).push(r)});
    const roomKey=r=>{const m=String(r.r).match(/^(\d{1,6})/);return m?+m[1]:null};
    Object.values(groups).forEach(arr=>arr.sort((a,b2)=>{
      const ka=roomKey(a),kb=roomKey(b2);
      if(ka!==null&&kb!==null) return ka-kb;
      if(ka!==null) return -1;
      if(kb!==null) return 1;
      return 0;
    }));
    let body="";
    for(const g of Object.keys(groups)){
      body+=`<div class="grp"><div class="glabel">${ICON[g]||"📦"} ${g} · ${groups[g].length}套</div><div class="grid">`;
      for(const r of groups[g]){
        const p = typeof r.p==="number"? r.p+"元" : "价格未标";
        const na = typeof r.p==="number"?"":" na";
        const mg = r.m ? (["已含","包","包管理"].includes(r.m) ? "已含管理费" : (/^[0-9]/.test(r.m) ? "管理费"+r.m : "管理费"+r.m)) : "管理费未标";
        const tag = /特价|已含|包/.test((r.tag||"")+(r.m||""))?'<span class="tagdot">惠</span>':"";
        const rk=roomKey(r);
        const hic=rk!==null&&rk>=1000?" hi":"";
        const hasV=!!VIDEOS[vKey(b.b,r.r)];
        const vtag=hasV?'<span class="vplay" title="播放房间视频">▶</span>':"";
        body+=`<div class="room${hic}" data-b="${esc(b.b)}" data-r="${esc(r.r)}" data-t="${esc(r.t)}" data-p="${r.p??"未标注"}" data-m="${esc(r.m||"未标注")}" data-c="${esc(r.c||"未标注")}" data-h="${esc(r.h||"未标注")}" data-e="${esc(r.e||"未标注")}" data-f="${esc(r.f||"未标注")}" data-tag="${esc(r.tag||"—")}">${tag}${vtag}<div class="rn">${esc(r.r)}</div><div class="rp${na}">${p}</div><div class="mgf">${esc(mg)}</div></div>`;
      }
      body+="</div></div>";
    }
    html+=`<div class="card"><div class="chead"><h2>${esc(b.b)}</h2><span class="cbadge">${rooms.length} 套</span></div><div class="cnote">${esc(b.note)}</div><div class="util">${esc(util)}</div>${body}</div>`;
  }
  document.getElementById("list").innerHTML=html||`<div class="card"><div class="empty">没有匹配的房源，换个关键词试试～</div></div>`;
  document.getElementById("cnt").textContent=cnt;
  document.getElementById("cntB").textContent=cntB;
  document.querySelectorAll(".room").forEach(el=>el.addEventListener("click",()=>openModal(el.dataset)));
  document.querySelectorAll(".room .vplay").forEach(el=>el.addEventListener("click",e=>{e.stopPropagation();const rd=el.closest(".room").dataset;openVideoViewer(rd.b,rd.r)}));
}
function openModal(d){
  const price = d.p==="未标注"?'<span class="v plain">价格未标注（信息缺失）</span>':`<span class="v price">${esc(d.p)} 元/月</span>`;
  const cur=VIDEOS[vKey(d.b,d.r)];
  const vrow=cur?`<div class="mrow"><span class="k">房间视频</span><span class="v"><a href="#" id="playv" style="color:var(--teal);text-decoration:none">▶ 播放房间实拍视频</a></span></div>`:"";
  document.getElementById("mcard").innerHTML=`
   <div class="mhead"><h3>${esc(d.b)}</h3><button class="mclose" onclick="document.getElementById('modal').classList.remove('open')">✕</button></div>
   <div class="mrow"><span class="k">户型</span><span class="v">${esc(d.t)}</span></div>
   <div class="mrow"><span class="k">房号</span><span class="v">${esc(d.r)}</span></div>
   <div class="mrow"><span class="k">月租金</span>${price}</div>
   <div class="mrow"><span class="k">管理费</span><span class="v">${esc(d.m)}</span></div>
   <div class="mrow"><span class="k">冷水</span><span class="v">${esc(d.c)}</span></div>
   <div class="mrow"><span class="k">热水</span><span class="v">${esc(d.h)}</span></div>
   <div class="mrow"><span class="k">电</span><span class="v">${esc(d.e)}</span></div>
   <div class="mrow"><span class="k">电梯/楼梯</span><span class="v">${esc(d.f)}</span></div>
   <div class="mrow"><span class="k">备注</span><span class="v plain">${esc(d.tag)}</span></div>
   <div class="mrow"><span class="k">位置</span><span class="v plain">深圳·龙华 · ${esc(d.b)}</span></div>
   <div class="mrow"><span class="k">看房联系</span><span class="v tel"><a href="tel:${PHONE}" style="color:inherit;text-decoration:none">📞 ${PHONE}</a></span></div>${vrow}`;
  const pv=document.getElementById("playv");
  if(pv)pv.onclick=e=>{e.preventDefault();openVideoViewer(d.b,d.r)};
  document.getElementById("modal").classList.add("open");
}
/* ===== 房间视频：索引来自云端登记表（只读），点 ▶ 在线播放 ===== */
let VIDEOS={};
function realB(n){return BMAP[n]||n}
function vKey(b,r){return realB(b)+"|"+r}
function toastMsg(m){const t=document.getElementById("toast");t.textContent=m;t.classList.add("show");setTimeout(()=>{t.classList.remove("show");t.textContent="已复制"},1800)}
async function loadVideos(){
  try{const c=localStorage.getItem("fuge_tenant_videos");if(c)VIDEOS=JSON.parse(c)||{}}catch(e){}
  render();
  try{
    const r=await fetch("https://filebin.net/fugevideo/registry.json",{cache:"no-store"});
    if(r.ok){
      const reg=await r.json();
      VIDEOS={};
      (reg.videos||[]).forEach(v=>{VIDEOS[vKey(v.bld,v.room)]={num:v.num,file:v.file,bld:v.bld,room:v.room}});
      try{localStorage.setItem("fuge_tenant_videos",JSON.stringify(VIDEOS))}catch(e){}
    }
  }catch(e){}
  render();
}
async function resolveVideoUrl(b,r,cur){
  try{
    const rr=await fetch("https://filebin.net/fugevideo/"+encodeURIComponent(cur.file),{cache:"no-store"});
    if(rr.ok)return rr.redirected&&rr.url?rr.url:rr.url;
  }catch(e){}
  return null;
}
async function openVideoViewer(b,r){
  const key=vKey(b,r);const cur=VIDEOS[key];if(!cur)return;
  const ov=document.createElement("div");ov.id="vplayer";
  ov.innerHTML=`
   <div style="display:flex;align-items:center;gap:10px;padding:10px 14px;flex-shrink:0">
    <button id="vclose" style="border:none;background:rgba(255,255,255,.16);color:#fff;width:36px;height:36px;border-radius:50%;font-size:16px;cursor:pointer">✕</button>
    <div style="color:#fff;font-size:15px;font-weight:700;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(r)} · ${esc(b)}</div>
   </div>
   <div style="flex:1;display:flex;align-items:center;justify-content:center;position:relative;min-height:0">
    <video id="vv" playsinline webkit-playsinline x5-video-player-type="h5" x5-playsinline x5-video-orientation="portrait" controls preload="metadata" style="max-width:100%;max-height:100%;width:100%;object-fit:contain;background:#000"></video>
   </div>`;
  document.body.appendChild(ov);
  document.body.style.overflow="hidden";
  const close=()=>{const v=ov.querySelector("video");if(v){try{v.pause()}catch(e){}if(v.src&&v.src.startsWith("blob:"))URL.revokeObjectURL(v.src)}ov.remove();document.body.style.overflow="";};
  ov.querySelector("#vclose").onclick=close;
  const vv=ov.querySelector("#vv");
  (async()=>{
    const url=await resolveVideoUrl(b,r,cur);
    if(!ov.isConnected)return;
    if(url){
      vv.src=url;
      try{await vv.play()}catch(e){}
    }else{
      vv.outerHTML='<div style="color:#cbd5d1;font-size:13px;text-align:center;padding:24px">视频暂时加载不出来，请稍后再试</div>';
    }
  })();
}
document.getElementById("modal").addEventListener("click",e=>{if(e.target.id==="modal")e.currentTarget.classList.remove("open")});
const chipBox=document.getElementById("catChips");
CATEGORIES.forEach(c=>{
  const s=document.createElement("span");
  s.className="chip"+(c==="全部户型"?" on":"");s.textContent=c;
  s.onclick=()=>{state.cat=c;chipBox.querySelectorAll(".chip").forEach(x=>x.classList.remove("on"));s.classList.add("on");render();};
  chipBox.appendChild(s);
});
function syncFloorUI(){
  document.getElementById("floorSel").value=state.floor;
  document.querySelectorAll("#floorBtns button").forEach(x=>x.classList.toggle("on",x.dataset.v===state.floor));
}
document.getElementById("floorBtns").addEventListener("click",e=>{
  const b=e.target.closest("button");if(!b)return;
  state.floor=b.dataset.v;syncFloorUI();render();
});
document.getElementById("floorSel").addEventListener("change",e=>{state.floor=e.target.value;syncFloorUI();render()});
document.getElementById("park").addEventListener("change",e=>{state.park=e.target.value;render()});
document.getElementById("budget").addEventListener("change",e=>{state.budget=e.target.value;render()});
document.getElementById("sort").addEventListener("change",e=>{state.sort=e.target.value;render()});
const qEl=document.getElementById("q");
qEl.addEventListener("input",()=>{state.q=qEl.value;document.getElementById("clr").style.display=qEl.value?"block":"none";render()});
document.getElementById("clr").onclick=()=>{qEl.value="";state.q="";document.getElementById("clr").style.display="none";render();qEl.focus()};
function fallback(text,done){
  const ta=document.createElement("textarea");ta.value=text;document.body.appendChild(ta);ta.select();
  try{document.execCommand("copy");done()}catch(e){}document.body.removeChild(ta);
}
syncFloorUI();
render();
loadVideos();
</script>
</body>
</html>
'''

out_html = (TEMPLATE
            .replace("__DATA__", data_js)
            .replace("__BMAP__", bmap_js)
            .replace("__DATE__", update_date)
            .replace("__PHONE__", PHONE))

os.makedirs(OUTDIR, exist_ok=True)
open(OUT, "w", encoding="utf-8", newline="\n").write(out_html)

size = os.path.getsize(OUT)
print("== 敏感词残留自检（仅页面可见内容，BMAP 映射表除外）==")
visible = re.sub(r'const BMAP = \{.*?\};', '', out_html, flags=re.S)
bad_words = ["密码", "佣金", "红包", "已剔除", "价目表", "招租", "谢永胜", "宜居", "万佳", "管家"]
found = [w for w in bad_words if w in visible]
print("  残留敏感词: %s" % (found if found else "无 ✅"))
print("== 生成完成 ==")
print("  输出: %s (%.1f KB)" % (OUT, size / 1024))
