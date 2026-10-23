"""导入老师提供的 Extended JSON；默认拒绝覆盖已有数据。"""
import sys
import argparse
from pathlib import Path
from datetime import timedelta
from bson import json_util

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mongodb_connect import get_database, close_connection


def initialize(reset=False):
    db = get_database()
    names = db.list_collection_names()
    if names:
        marker = db.app_meta.find_one({"_id": "owner"})
        if not reset or not marker or marker.get("project") != "wangruichang-library-training":
            raise RuntimeError("数据库已有内容；仅允许显式 --reset 重置本项目创建的数据库")
        for name in ("book_in_stock", "books", "readers", "borrow_logs", "borrow_records",
                     "category_stats", "book_logs", "app_meta"):
            db.drop_collection(name)
    db.create_collection("books")
    db.create_collection("readers")
    db.create_collection("category_stats")
    db.create_collection("borrow_records")
    db.create_collection("book_logs", capped=True, size=1048576, max=1000)
    db.create_collection("borrow_logs", timeseries={"timeField": "borrow_date", "granularity": "hours"},
                         expireAfterSeconds=63072000)
    db.create_collection("book_in_stock", viewOn="books", pipeline=[{"$match": {"stock": {"$gt": 0}}}])
    db.app_meta.insert_one({"_id": "owner", "project": "wangruichang-library-training"})
    for name in ("books", "readers", "borrow_logs"):
        data = json_util.loads((ROOT / "data" / f"{name}.txt").read_text(encoding="utf-8-sig"))
        if name == "books":
            print("insertOne:", db[name].insert_one(data[0]).inserted_id)
            print("insertMany:", len(db[name].insert_many(data[1:]).inserted_ids))
        else:
            print(name, "insertMany:", len(db[name].insert_many(data).inserted_ids))
        if name == "borrow_logs":
            # 源数据没有稳定 _id，以行号分配应用借阅编号，保留原始日期与状态。
            records = [dict(x, _id=f"seed-{i:03d}", due_date=x["borrow_date"] + timedelta(days=30))
                       for i, x in enumerate(data, 1)]
            db.borrow_records.insert_many(records)
    db.books.create_index("isbn", unique=True, name="isbn_unique")
    db.books.create_index("title", name="title_1")
    db.books.create_index("category", name="category_1")
    db.books.create_index("tags", name="tags_1")
    db.books.create_index([("category", 1), ("price", 1)], name="category_price")
    db.readers.create_index("card_no", unique=True)
    db.borrow_records.create_index([("reader_card", 1), ("status", 1)])
    db.book_logs.insert_one({"action": "initial_import", "books": 20, "readers": 16, "borrow_logs": 66})
    return {n: db[n].count_documents({}) for n in
            ("books", "readers", "borrow_logs", "borrow_records", "book_in_stock")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="仅重置带有本项目标记的数据库")
    args = parser.parse_args()
    try:
        print(initialize(args.reset))
    finally:
        close_connection()
