# -*- coding: utf-8 -*-
"""重建 filebin 视频登记表 registry.json（事故恢复）

数据源：
1. H:\\富哥房源视频\\_video_group_map.json  视频文件名 -> [盘口, 真实栋名, 户型]
2. H:\\富哥房源视频\\*.mp4                  视频文件本体（文件名 NN_栋名+房号.mp4）
3. index.html 的 DATA                      用于校验 (bld, room) 是否对得上当前在租房源

用法：python restore_registry.py          （只解析+校验，不上传）
      python restore_registry.py --push   （解析+校验+PUT registry.json 到 filebin）
"""
import json, re, os, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
VDIR = r"H:\富哥房源视频"
PUSH = "--push" in sys.argv

# ---------- 读取 DATA ----------
html_src = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
m = re.search(r'const DATA = (\[.*?\]);\s*\nconst state', html_src, re.S)
data = json.loads(m.group(1))

# DATA 里的真实栋名（含括号别名 -> 去括号短名 两套都用于匹配）
real_blds = []
for b in data:
    name = b["b"]
    real_blds.append(name)
    short = re.sub(r'（.*?）', '', name).strip()
    if short != name:
        real_blds.append(short)

# DATA 房号集合（用于校验）
data_rooms = set()
for b in data:
    for r in b["rooms"]:
        data_rooms.add((b["b"], str(r["r"])))

# ---------- 读取视频分组映射 ----------
gmap_path = os.path.join(VDIR, "_video_group_map.json")
gmap = json.load(open(gmap_path, encoding="utf-8")) if os.path.exists(gmap_path) else {}

# ---------- 扫描视频文件 ----------
exts = ('.mp4', '.mov', '.webm', '.avi')
files = [f for f in os.listdir(VDIR) if f.lower().endswith(exts)]
print("H 盘视频文件: %d 支" % len(files))

videos = []
unmatched_room = []
no_bld = []
for fname in files:
    fm = re.match(r'^(\d{1,3})_(.+?)\.(mp4|mov|webm|avi)$', fname, re.I)
    if not fm:
        no_bld.append((fname, "文件名不符合 NN_内容.扩展名 格式"))
        continue
    num = fm.group(1).zfill(2)
    content = fm.group(2)

    # 栋名：优先用 _video_group_map.json
    bld = None
    if fname in gmap and len(gmap[fname]) >= 2:
        mapped = gmap[fname][1]
        # 映射里的栋名对齐 DATA（含/不含括号别名）
        for rb in real_blds:
            if rb == mapped or re.sub(r'（.*?）', '', rb).strip() == mapped:
                bld = rb
                break
        if bld is None:
            bld = mapped
    if bld is None:
        # 回退：用文件名内容匹配 DATA 栋名（取最长匹配）
        cands = [rb for rb in real_blds if content.startswith(re.sub(r'（.*?）', '', rb).strip())]
        if cands:
            bld = max(cands, key=len)
    if bld is None:
        no_bld.append((fname, "无法识别楼栋"))
        continue

    # 房号：去掉栋名短前缀后的剩余部分中，取最后一个数字组；无数字则保留原文
    short_bld = re.sub(r'（.*?）', '', bld).strip()
    rem = content[len(short_bld):] if content.startswith(short_bld) else content
    rem = re.sub(r'^(单间|大单间|一房一厅|两房一厅|三房一厅|二房一厅|特价|带书房|书房|铺面|单房|中单房|大单房)', '', rem)
    nums = re.findall(r'\d+', rem)
    room = nums[-1] if nums else (rem.strip() or "未标注")

    videos.append({"num": num, "file": fname, "bld": bld, "room": room, "status": "已入库"})

    if (bld, room) in data_rooms:
        pass
    else:
        unmatched_room.append((fname, bld, room))

videos.sort(key=lambda v: (len(v["num"]), v["num"]))

print("\n== 解析结果（%d 支）==" % len(videos))
for v in videos:
    ok = "✅" if (v["bld"], v["room"]) in data_rooms else "⚠️"
    print("  %s 编号%s  %s %s  <- %s" % (ok, v["num"], v["bld"], v["room"], v["file"]))

print("\n== 校验 ==")
in_data = sum(1 for v in videos if (v["bld"], v["room"]) in data_rooms)
print("  与当前在租房源匹配: %d / %d" % (in_data, len(videos)))
if unmatched_room:
    print("  房号与当前数据不对应的（可能已下架，登记表仍保留，重上架时自动挂回）:")
    for f, b, r in unmatched_room:
        print("    %s -> %s %s" % (f, b, r))
if no_bld:
    print("  无法识别楼栋的:")
    for f, why in no_bld:
        print("    %s (%s)" % (f, why))

if not PUSH:
    print("\n[dry-run] 未上传。确认无误后运行: python restore_registry.py --push")
    sys.exit(0)

# ---------- 推送 registry.json ----------
registry = {
    "updated": __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "videos": [{"num": v["num"], "file": v["file"], "bld": v["bld"], "room": v["room"], "status": v["status"]} for v in videos],
}
body = json.dumps(registry, ensure_ascii=False, separators=(",", ":"))
print("\n== PUT registry.json（%d 支视频记录）==" % len(videos))
import subprocess
p = subprocess.run(
    ["curl.exe", "-sS", "--max-time", "60",
     "-X", "PUT",
     "-H", "Content-Type: application/json",
     "--data-binary", body.encode("utf-8"),
     "https://filebin.net/fugevideo/registry.json"],
    capture_output=True)
out = p.stdout.decode("utf-8", errors="replace")
print("  filebin 返回: %s" % (out[:200] if out else "(空)"))
if p.returncode == 0:
    print("  ✅ 登记表已恢复")
else:
    print("  ❌ PUT 失败，退出码 %d" % p.returncode)
