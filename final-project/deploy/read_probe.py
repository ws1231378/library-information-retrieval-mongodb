# -*- coding: utf-8 -*-
"""故障转移期间读探针（secondaryPreferred），记录中断窗口。输出 results/merged_readprobe.txt。"""
import json
import threading
import time
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import PyMongoError

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runtime" / "replica"
OUT = ROOT / "results" / "merged_readprobe.txt"
creds = json.loads((RUN / "credentials.json").read_text())
PWD = creds["password"]
PORTS = [28217, 28218, 28219]
URI = "mongodb://labAdmin:%s@%s/?authSource=admin&replicaSet=libraryRS&readPreference=secondaryPreferred" % (
    PWD, ",".join("127.0.0.1:%d" % p for p in PORTS))
lines = []


def p(s=""):
    print(s)
    lines.append(str(s))


def primary():
    for port in PORTS:
        try:
            c = MongoClient("127.0.0.1", port, directConnection=True, serverSelectionTimeoutMS=1000)
            if c.admin.command("hello").get("isWritablePrimary"):
                return port
        except PyMongoError:
            pass
    return None


def main():
    p("=== 故障转移期间读探针 ===")
    p("读取偏好：secondaryPreferred，每 0.3 秒执行一次 count_documents")
    state = {"ok": 0, "fail": 0, "first_fail": None, "recover": None}
    stop = threading.Event()

    def probe():
        cli = MongoClient(URI, serverSelectionTimeoutMS=1500)
        t0 = time.monotonic()
        while not stop.is_set():
            try:
                cli.smart_library.probe.count_documents({})
                state["ok"] += 1
                if state["first_fail"] is not None and state["recover"] is None:
                    state["recover"] = time.monotonic() - t0
            except PyMongoError:
                state["fail"] += 1
                if state["first_fail"] is None:
                    state["first_fail"] = time.monotonic() - t0
            time.sleep(0.3)
        cli.close()

    th = threading.Thread(target=probe, daemon=True)
    th.start()
    time.sleep(2)
    port = primary()
    p("当前主节点：%d" % port)
    adm = MongoClient("mongodb://labAdmin:%s@127.0.0.1:%d/?authSource=admin&directConnection=true" % (PWD, port),
                      serverSelectionTimeoutMS=3000)
    try:
        adm.admin.command("replSetStepDown", 60, force=True)
    except PyMongoError as exc:
        p("stepDown 断开连接（正常）：%s" % type(exc).__name__)
    t0 = time.monotonic()
    newp = None
    while time.monotonic() - t0 < 40:
        cand = primary()
        if cand and cand != port:
            newp = cand
            break
        time.sleep(0.3)
    p("新主节点：%s，选举耗时 %.2f 秒" % (newp, time.monotonic() - t0))
    time.sleep(3)
    stop.set()
    th.join(timeout=5)
    p("读探针：成功 %d 次，失败 %d 次" % (state["ok"], state["fail"]))
    if state["fail"]:
        p("首次失败 %.2f 秒，恢复 %.2f 秒，中断窗口约 %.2f 秒" % (
            state["first_fail"], state["recover"] or -1,
            (state["recover"] or 0) - (state["first_fail"] or 0)))
    else:
        p("转移期间读请求全部成功：从节点继续提供服务，读未中断")
    adm.close()
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
