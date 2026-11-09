# -*- coding: utf-8 -*-
"""单机认证验证：创建三个账号并验证读写。输出 results/single_auth.txt。

密码来源（按顺序）：环境变量 LIB_ADMIN_PASSWORD → runtime/single_auth_password.txt → 随机生成并落盘。
已存在账号时不会覆盖密码；若密码不匹配会给出明确提示。
"""
import os
import secrets
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import OperationFailure

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "single_auth.txt"
PWD_FILE = ROOT / "runtime" / "single_auth_password.txt"


def resolve_password():
    if os.environ.get("LIB_ADMIN_PASSWORD"):
        return os.environ["LIB_ADMIN_PASSWORD"], "环境变量 LIB_ADMIN_PASSWORD"
    if PWD_FILE.exists():
        return PWD_FILE.read_text(encoding="utf-8").strip(), "runtime/single_auth_password.txt"
    pwd = secrets.token_urlsafe(18)
    PWD_FILE.parent.mkdir(parents=True, exist_ok=True)
    PWD_FILE.write_text(pwd, encoding="utf-8")
    return pwd, "随机生成，已写入 runtime/single_auth_password.txt"


PWD, PWD_SOURCE = resolve_password()
lines = []


def p(s=""):
    print(s)
    lines.append(str(s))


def admin_client(pwd):
    try:
        cli = MongoClient("127.0.0.1", 28117, username="labAdmin", password=pwd,
                          authSource="admin", directConnection=True, serverSelectionTimeoutMS=2000)
        cli.admin.command("ping")
        return cli
    except Exception:
        return None


def main():
    p("=== 单机（28117）认证与权限 ===")
    p("管理员密码来源：%s" % PWD_SOURCE)

    adm = admin_client(PWD)
    if adm is None:
        c = MongoClient("127.0.0.1", 28117, directConnection=True, serverSelectionTimeoutMS=3000)
        try:
            c.admin.command("createUser", "labAdmin", pwd=PWD, roles=["root"])
            p("已创建 labAdmin（root）")
        except OperationFailure as exc:
            raise SystemExit("已存在账号但密码不匹配（%s）。请设置 LIB_ADMIN_PASSWORD 为现有密码后重试。"
                             % str(exc)[:60])
        adm = admin_client(PWD)
        if adm is None:
            raise SystemExit("labAdmin 创建后仍无法认证，请检查 --auth 启动参数")
    else:
        p("labAdmin 已存在，密码校验通过")

    for u, roles in (("libReader", [{"role": "read", "db": "smart_library"}]),
                     ("libWriter", [{"role": "readWrite", "db": "smart_library"}])):
        try:
            adm.smart_library.command("dropUser", u)
        except OperationFailure:
            pass
        adm.smart_library.command("createUser", u, pwd=PWD, roles=roles)
        p("已创建 %s：%s" % (u, roles))

    p("[匿名]")
    try:
        MongoClient("127.0.0.1", 28117, serverSelectionTimeoutMS=3000).smart_library.books.count_documents({})
        raise SystemExit("验收失败：匿名读取成功，说明认证未生效")
    except OperationFailure as exc:
        p("  被拒绝 code=%s" % exc.code)

    p("[libReader]")
    rd = MongoClient("127.0.0.1", 28117, username="libReader", password=PWD,
                     authSource="smart_library", serverSelectionTimeoutMS=3000)
    p("  books 读取：%d 条" % rd.smart_library.books.count_documents({}))
    try:
        rd.smart_library.books.insert_one({"isbn": "x", "title": "越权"})
        raise SystemExit("验收失败：只读用户写入成功，说明权限未生效")
    except OperationFailure as exc:
        p("  写入被拒绝 code=%s" % exc.code)
    rd.close()

    p("[libWriter]")
    wr = MongoClient("127.0.0.1", 28117, username="libWriter", password=PWD,
                     authSource="smart_library", serverSelectionTimeoutMS=3000)
    wr.smart_library.audit_logs.insert_one({"action": "single_auth_probe", "collection": "audit_logs",
                                            "detail": "auth ok"})
    p("  audit_logs 写入成功，当前 %d 条" % wr.smart_library.audit_logs.count_documents({}))
    wr.close()

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
