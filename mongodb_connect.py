"""统一 MongoDB 连接。支持环境变量；认证密码以交互方式输入。"""
import os
from getpass import getpass
from pymongo import MongoClient

_client = None


def get_client():
    global _client
    if _client is None:
        options = {"serverSelectionTimeoutMS": 5000, "tz_aware": True}
        user = os.getenv("MONGO_USER")
        if user:
            options.update(username=user,
                           password=os.getenv("MONGO_PASSWORD") or getpass("MongoDB 密码："),
                           authSource=os.getenv("MONGO_AUTH_DB", "library"))
        _client = MongoClient(os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017"), **options)
        _client.admin.command("ping")
    return _client


def get_database():
    return get_client()[os.getenv("MONGO_DB", "library")]


def close_connection():
    global _client
    if _client is not None:
        _client.close()
        _client = None
