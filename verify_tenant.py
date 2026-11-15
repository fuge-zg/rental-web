# -*- coding: utf-8 -*-
"""校验租客版页面：JS 引用的元素 id 是否都存在于 HTML 中"""
import re, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

c = open(r"H:\富哥Loomy房源资料\共和花园房源网页\tenant\index.html", encoding="utf-8").read()

ids_needed = ["statRooms", "statRooms2", "statBld", "q", "clr", "catChips",
              "park", "budget", "floorSel", "sort", "floorBtns", "cnt", "cntB",
              "list", "about", "modal", "mcard", "toast"]
missing = [i for i in ids_needed if ('id="%s"' % i) not in c]
print("JS 引用元素检查:", ("缺失 " + str(missing)) if missing else "全部齐备 OK")

# DATA JSON 合法性
m = re.search(r'const DATA = (\[.*?\]);\s*\n/\*', c, re.S) or re.search(r'const DATA = (\[.*?\]);', c, re.S)
try:
    import json
    data = json.loads(m.group(1))
    rooms = sum(len(b["rooms"]) for b in data)
    print("DATA JSON 合法: OK（%d 个楼栋块，%d 条房号）" % (len(data), rooms))
except Exception as e:
    print("DATA JSON 异常:", e)

# 花括号配对粗检（script 段）
script = re.search(r'<script>(.*)</script>', c, re.S).group(1)
print("script 段花括号: { %d 个 vs } %d 个" % (script.count("{"), script.count("}")))
