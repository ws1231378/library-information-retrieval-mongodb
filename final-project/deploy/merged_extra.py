# -*- coding: utf-8 -*-
"""合并版补充验证：副本集账号、第四节点增删、故障期间读探针。

在已由 deploy/replica_lab.py 初始化的 libraryRS（28217-28219，keyFile 认证）上执行。
输出：results/merged_replica.txt
"""
import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import PyMongoError

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runtime" / "replica"
OUT = ROOT / "results" / "merged_replica.txt"
BIN = os.environ.get("MONGOD_BIN", r"D:\文档\New project 2\library_training\runtime\mongo\mongod.exe")
PORTS = [28217, 28218, 28219]
creds = json.loads((RUN / "credentials.json").read_text())
PWD = creds["password"]
KEYFILE = str(Path(os.environ.get("KEYFILE_PATH", r"C:\ProgramData\mongo_lab\keyfile_merged")))
lines = []


def p(s=""):
    print(s)
    lines.append(str(s))


def find_primary():
    for port in PORTS:
        try:
            c = MongoClient("127.0.0.1", port, directConnection=True, serverSelectionTimeoutMS=2000)
            if c.admin.command("hello").get("isWritablePrimary"):
                return port
        except PyMongoError:
            pass
    return None


def main():
    port = find_primary()
    p("=== 合并版补充验证：副本集 ===")
    p("当前主节点：%d" % port)

    # 1. localhost 例外创建管理员
    c = MongoClient("127.0.0.1", port, directConnection=True, serverSelectionTimeoutMS=3000)
    try:
        c.admin.command("createUser", "labAdmin", pwd=PWD, roles=["root"])
        p("已通过 localhost 例外创建 labAdmin")
    except PyMongoError as exc:
        p("labAdmin 创建：%s" % str(exc)[:80])

    uri = "mongodb://labAdmin:%s@%s/?authSource=admin&replicaSet=libraryRS" % (
        PWD, ",".join("127.0.0.1:%d" % x for x in PORTS))
    adm = MongoClient(uri, serverSelectionTimeoutMS=8000)
    lib = adm.smart_library
    for user, roles in (("libReader", [{"role": "read", "db": "smart_library"}]),
                        ("libWriter", [{"role": "readWrite", "db": "smart_library"}])):
        try:
            lib.command("dropUser", user)
        except PyMongoError:
            pass
        lib.command("createUser", user, pwd=PWD, roles=roles)
        p("已创建 %s" % user)

    # 2. 导入基线（空集合时）
    if lib.books.count_documents({}) == 0:
        for name in ("books", "readers", "borrow_logs"):
            rows = json.loads((ROOT / "data" / ("%s.txt" % name)).read_text(encoding="utf-8"))
            for row in rows:
                for k in ("publish_date", "register_date", "borrow_date", "return_date"):
                    if k in row:
                        row[k] = datetime.fromisoformat(row[k])
            lib[name].insert_many(rows)
        p("导入基线：%d / %d / %d" % (lib.books.count_documents({}), lib.readers.count_documents({}),
                                    lib.borrow_logs.count_documents({})))

    # 3. 第四节点增删
    p("\n=== 第四节点增删 ===")
    p4 = 28220
    db4 = RUN / str(p4)
    db4.mkdir(exist_ok=True)
    proc = subprocess.Popen([BIN, "--dbpath", str(db4), "--logpath", str(db4 / "mongod.log"),
                             "--port", str(p4), "--bind_ip", "127.0.0.1", "--replSet", "libraryRS",
                             "--keyFile", KEYFILE, "--wiredTigerCacheSizeGB", "0.25"],
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    time.sleep(5)
    cfg = adm.admin.command("replSetGetConfig")["config"]
    cfg["members"].append({"_id": max(m["_id"] for m in cfg["members"]) + 1,
                           "host": "127.0.0.1:%d" % p4})
    cfg["version"] += 1
    adm.admin.command("replSetReconfig", cfg, force=True)
    p("加入 127.0.0.1:%d（replSetReconfig）" % p4)
    for _ in range(60):
        time.sleep(0.5)
        st = adm.admin.command("replSetGetStatus")
        m = [x for x in st["members"] if x["name"].endswith(":28220")]
        if m and m[0]["stateStr"] == "SECONDARY":
            break
    st = adm.admin.command("replSetGetStatus")
    p("添加后成员数：%d" % len(st["members"]))
    for m in st["members"]:
        p("  %-20s %s" % (m["name"], m["stateStr"]))
    cfg = adm.admin.command("replSetGetConfig")["config"]
    cfg["members"] = [m for m in cfg["members"] if not m["host"].endswith(":28220")]
    cfg["version"] += 1
    adm.admin.command("replSetReconfig", cfg, force=True)
    time.sleep(3)
    proc.terminate()
    st = adm.admin.command("replSetGetStatus")
    p("移除后成员数：%d" % len(st["members"]))

    # 4. 故障期间读探针（secondaryPreferred）
    p("\n=== 故障转移期间读探针（每 0.3 秒一次）===")
    probe_uri = "mongodb://labAdmin:%s@%s/?authSource=admin&replicaSet=libraryRS&readPreference=secondaryPreferred" % (
        PWD, ",".join("127.0.0.1:%d" % x for x in PORTS))
    stop = threading.Event()
    result = {"ok": 0, "fail": 0, "first_fail": None, "recover": None, "fail_span": 0.0}

    def probe():
        cli = MongoClient(probe_uri, serverSelectionTimeoutMS=1500)
        t0 = time.monotonic()
        while not stop.is_set():
            try:
                cli.smart_library.probe.count_documents({})
                result["ok"] += 1
                if result["first_fail"] is not None and result["recover"] is None:
                    result["recover"] = time.monotonic() - t0
            except PyMongoError:
                result["fail"] += 1
                if result["first_fail"] is None:
                    result["first_fail"] = time.monotonic() - t0
            time.sleep(0.3)
        cli.close()

    th = threading.Thread(target=probe, daemon=True)
    th.start()
    time.sleep(2)
    prim = find_primary()
    p("对主节点 %d 执行 replSetStepDown(60, force)" % prim)
    try:
        adm.admin.command("replSetStepDown", 60, force=True)
    except PyMongoError as exc:
        p("stepDown 连接断开：%s" % type(exc).__name__)
    t0 = time.monotonic()
    newp = None
    while time.monotonic() - t0 < 40:
        cand = find_primary()
        if cand and cand != prim:
            newp = cand
            break
        time.sleep(0.3)
    p("新主节点：%s，选举耗时 %.2f 秒" % (newp, time.monotonic() - t0))
    time.sleep(3)
    stop.set()
    th.join(timeout=5)
    p("读探针统计：成功 %d 次，失败 %d 次" % (result["ok"], result["fail"]))
    if result["fail"]:
        p("  首次失败在 %.2fs，恢复读在 %.2fs，受影响窗口约 %.2fs" % (
            result["first_fail"], result["recover"] or -1, (result["recover"] or 0) - (result["first_fail"] or 0)))
    else:
        p("  故障转移期间读请求全部成功（secondaryPreferred 由从节点继续服务）")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    adm.close()
    print("\n保存到", OUT)


if __name__ == "__main__":
    main()
