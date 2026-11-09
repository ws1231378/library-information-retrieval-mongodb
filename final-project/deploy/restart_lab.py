"""Restart existing isolated lab directories, preserving all credentials.

keyFile 路径与初始化脚本保持一致（纯 ASCII 路径），可用环境变量覆盖：
    KEYFILE_PATH        副本集 keyFile，默认 C:\\ProgramData\\mongo_lab\\keyfile_merged
    SHARD_KEYFILE_PATH  分片集群 keyFile，默认 C:\\ProgramData\\mongo_lab\\keyfile_shard
"""
import os, socket, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLICA_KEY = Path(os.environ.get("KEYFILE_PATH", r"C:\ProgramData\mongo_lab\keyfile_merged"))
SHARD_KEY = Path(os.environ.get("SHARD_KEYFILE_PATH", r"C:\ProgramData\mongo_lab\keyfile_shard"))


def launch(args, port):
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            print(f"{port}: already listening; left untouched")
            return
    p = subprocess.Popen(args, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    print(f"{port}: started PID {p.pid}")


binary = os.environ["MONGOD_BIN"]
families = [
    ("replica", "libraryRS", [28217, 28218, 28219], None, REPLICA_KEY),
    ("sharding", "configRS", [28300], "--configsvr", SHARD_KEY),
    ("sharding", "shardA", [28301], "--shardsvr", SHARD_KEY),
    ("sharding", "shardB", [28302], "--shardsvr", SHARD_KEY),
]
for family, name, ports, role, keyfile in families:
    if not keyfile.exists():
        print(f"{keyfile} 不存在，跳过 {family}/{name}")
        continue
    for port in ports:
        directory = ROOT / "runtime" / family / str(port)
        if not directory.exists():
            continue
        args = [binary, "--dbpath", str(directory), "--logpath", str(directory / "mongod.log"),
                "--logappend", "--port", str(port), "--bind_ip", "127.0.0.1",
                "--replSet", name, "--keyFile", str(keyfile), "--wiredTigerCacheSizeGB", "0.25"]
        if role:
            args.append(role)
        launch(args, port)

marker = ROOT / "runtime/sharding/connection.txt"
if SHARD_KEY.exists() and marker.exists():
    launch([os.environ["MONGOS_BIN"], "--configdb", "configRS/127.0.0.1:28300", "--port", "28417",
            "--bind_ip", "127.0.0.1", "--keyFile", str(SHARD_KEY),
            "--logpath", str(ROOT / "runtime/sharding/mongos.log"), "--logappend"], 28417)
