# -*- coding: utf-8 -*-
"""把 H 盘视频批量重新上传到 filebin（事故恢复）

- 逐支 PUT 上传，文件名 URL 编码（支持中文）
- 本地进度文件 _restore_uploaded.json 记录已成功清单，重跑自动跳过
- 每支失败自动重试 2 次
- 用法：python upload_videos.py [本次最多上传支数，默认全部]
"""
import json, os, io, sys, subprocess, time
from urllib.parse import quote

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
VDIR = r"H:\富哥房源视频"
PROG = os.path.join(BASE, "_restore_uploaded.json")
BIN = "fugevideo"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9

done = {}
if os.path.exists(PROG):
    try:
        done = json.load(open(PROG, encoding="utf-8"))
    except Exception:
        done = {}

exts = ('.mp4', '.mov', '.webm', '.avi')
files = sorted([f for f in os.listdir(VDIR) if f.lower().endswith(exts)])
todo = [f for f in files if f not in done]
print("总视频 %d 支 | 已传 %d 支 | 待传 %d 支（本次上限 %s）" % (
    len(files), len(done), len(todo), "全部" if LIMIT > 10 ** 8 else LIMIT))

ok_cnt = fail_cnt = 0
t0 = time.time()
for fname in todo[:LIMIT]:
    path = os.path.join(VDIR, fname)
    size_mb = os.path.getsize(path) / 1024 / 1024
    url = "https://filebin.net/%s/%s" % (BIN, quote(fname))
    ok = False
    for attempt in (1, 2, 3):
        p = subprocess.run(
            ["curl.exe", "-sS", "--max-time", "300", "-o", "NUL", "-w", "%{http_code}",
             "-X", "PUT", "-H", "Content-Type: video/mp4",
             "--data-binary", "@" + path, url],
            capture_output=True)
        code = p.stdout.decode("utf-8", errors="replace").strip()
        if p.returncode == 0 and code in ("200", "201"):
            ok = True
            break
        time.sleep(3)
    if ok:
        done[fname] = {"at": time.strftime("%Y-%m-%d %H:%M:%S")}
        json.dump(done, open(PROG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        ok_cnt += 1
        print("  ✅ %s（%.1fMB）累计 %d/%d" % (fname, size_mb, len(done), len(files)))
    else:
        fail_cnt += 1
        print("  ❌ %s（HTTP %s）" % (fname, code))

print("\n本次: 成功 %d 支, 失败 %d 支, 耗时 %.1f 分钟" % (ok_cnt, fail_cnt, (time.time() - t0) / 60))
print("总进度: %d / %d 支已上传" % (len(done), len(files)))
if len(done) < len(files):
    print("继续上传请再次运行: python upload_videos.py")
