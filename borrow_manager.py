"""borrow_logs 留存借出时的时间序列事件，borrow_records 维护当前状态。

课程单机 CLI 使用补偿操作；没有跨集合事务，不适合作为生产并发服务。
不要把不可更新的时间序列事件当作当前借阅状态。
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from pymongo import ReturnDocument
from mongodb_connect import get_database


def borrow_book(card_no, isbn, days=30):
    if type(days) is not int or not 1 <= days <= 365:
        raise ValueError("借阅天数必须为 1—365 的整数")
    db = get_database()
    if not db.readers.find_one({"card_no": card_no}):
        raise ValueError("读者不存在")
    now = datetime.now(timezone.utc)
    record = {"_id": str(uuid4()), "reader_card": card_no, "book_isbn": isbn,
              "borrow_date": now, "due_date": now + timedelta(days=days), "status": "借出"}
    changed = db.books.update_one({"isbn": isbn, "stock": {"$gt": 0}},
                                 {"$inc": {"stock": -1, "borrow_count": 1}})
    if not changed.modified_count:
        raise ValueError("图书不存在或库存不足")
    try:
        db.borrow_records.insert_one(record)
    except Exception:
        db.books.update_one({"isbn": isbn}, {"$inc": {"stock": 1, "borrow_count": -1}})
        raise
    try:
        db.borrow_logs.insert_one(dict(record))
    except Exception as exc:
        # 保留已成功登记的借阅；明确报告归档失败，避免误称整个借阅失败。
        db.borrow_records.update_one({"_id": record["_id"]}, {"$set": {"archive_pending": True}})
        return {"inserted_count": 1, "loan_id": record["_id"], "archive_pending": True,
                "warning": f"借阅已登记，时间序列归档待人工核对：{type(exc).__name__}"}
    return {"inserted_count": 1, "loan_id": record["_id"], "archive_pending": False}


def return_book(loan_id):
    db = get_database()
    # 原子状态变更保证重复归还不会重复增加库存。
    record = db.borrow_records.find_one_and_update(
        {"_id": loan_id, "status": {"$in": ["借出", "逾期"]}},
        {"$set": {"status": "已归还", "return_date": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.BEFORE)
    if record is None:
        return {"modified_count": 0, "message": "借阅不存在或已经归还"}
    try:
        result = db.books.update_one({"isbn": record["book_isbn"]}, {"$inc": {"stock": 1}})
        if result.matched_count != 1:
            raise ValueError("图书记录缺失")
    except Exception:
        db.borrow_records.update_one({"_id": loan_id},
                                     {"$set": {"status": record["status"]}, "$unset": {"return_date": ""}})
        raise
    return {"modified_count": 1, "stock_modified_count": result.modified_count}


def overdue_records(now=None):
    now = now or datetime.now(timezone.utc)
    db = get_database()
    q = {"status": {"$in": ["借出", "逾期"]}, "due_date": {"$lt": now}}
    return list(db.borrow_records.find(q).sort([("due_date", 1), ("_id", 1)]))


def mark_overdue(now=None):
    return get_database().borrow_records.update_many(
        {"status": "借出", "due_date": {"$lt": now or datetime.now(timezone.utc)}},
        {"$set": {"status": "逾期"}})


def list_loans(card_no):
    return list(get_database().borrow_records.find({"reader_card": card_no}).sort("borrow_date", -1))
