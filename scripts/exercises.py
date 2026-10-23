"""实测 Q1—Q16、U1—U4、D1—D3、A1—A9、I1—I5；生成命令与结果附录。"""
import sys
from pathlib import Path
from copy import deepcopy
from bson import json_util
from pymongo.errors import OperationFailure, DuplicateKeyError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mongodb_connect import get_database, close_connection

QUERIES = [
    ("Q1", "books", {"price": {"$gt": 80}}),
    ("Q2", "books", {"stock": {"$lt": 10}}),
    ("Q3", "books", {"isbn": {"$eq": "9787115428028"}}),
    ("Q4", "readers", {"email": {"$eq": None}}),
    ("Q5", "books", {"publisher": {"$ne": "人民邮电出版社"}}),
    ("Q6", "books", {"category": {"$in": ["计算机", "经济管理"]}}),
    ("Q7", "books", {"$and": [{"rating": {"$gt": 4.0}}, {"category": "计算机"}]}),
    ("Q8", "books", {"$or": [{"rating": {"$lt": 3.5}}, {"stock": 0}]}),
    ("Q9", "books", {"title": {"$regex": "Python"}}),
    ("Q10", "books", {"tags": {"$all": ["编程", "入门"]}}),
    ("Q11", "books", {"tags": {"$size": 3}}),
    ("Q12", "books", {"tags": {"$exists": True}}),
    ("Q13", "books", {"_id": {"$type": "string"}}),
]
A1 = [{"$group": {"_id": "$category", "count": {"$sum": 1}, "avg_rating": {"$avg": "$rating"},
                  "max_stock": {"$max": "$stock"}, "min_stock": {"$min": "$stock"}}},
      {"$sort": {"_id": 1}}]
AGGREGATIONS = {
    "A1": ("books", A1),
    "A2": ("books", [{"$group": {"_id": "$publisher", "count": {"$sum": 1}}},
                     {"$group": {"_id": None, "top5": {"$topN": {
                         "n": 5, "sortBy": {"count": -1, "_id": 1},
                         "output": {"publisher": "$_id", "count": "$count"}}}}}]),
    "A3": ("books", [{"$sortByCount": "$category"}, {"$sort": {"count": -1, "_id": 1}}, {"$limit": 1}]),
    "A4": ("books", [{"$sort": {"rating": -1, "isbn": 1}}, {"$limit": 3},
                     {"$project": {"_id": 0, "title": 1, "borrow_count": 1}}]),
    "A5": ("books", [{"$project": {"_id": 0, "title": 1,
                    "sales_amount": {"$round": [{"$multiply": ["$price", "$borrow_count"]}, 2]}}}]),
    "A6": ("borrow_logs", [{"$group": {"_id": {"$year": {"date": "$borrow_date", "timezone": "Asia/Shanghai"}},
                            "count": {"$sum": 1}, "sample_date": {"$min": "$borrow_date"}}},
                           {"$project": {"_id": 0, "count": 1, "year": {"$dateToString": {
                               "date": "$sample_date", "format": "%Y年", "timezone": "Asia/Shanghai"}}}},
                           {"$sort": {"year": 1}}]),
    "A7": ("borrow_logs", [{"$group": {"_id": "$reader_card", "count": {"$sum": 1}}},
                           {"$sort": {"count": -1, "_id": 1}}, {"$limit": 5}]),
    "A8": ("borrow_logs", [{"$lookup": {"from": "readers", "localField": "reader_card",
                                      "foreignField": "card_no", "as": "reader"}},
                           {"$unwind": "$reader"}, {"$group": {"_id": "$reader.college", "count": {"$sum": 1}}},
                           {"$sort": {"count": -1, "_id": 1}}]),
    "A9": ("books", A1 + [{"$merge": {"into": "category_stats",
                     "whenMatched": "replace", "whenNotMatched": "insert"}}])
}


def js(value):
    return json_util.dumps(value, ensure_ascii=False)


def execute():
    db = get_database()
    out = ROOT / "results"; out.mkdir(exist_ok=True)
    records = []
    def record(label, command, result):
        records.append({"id": label, "command": command, "result": result})
        print(label, "OK", f"{len(result)} rows" if isinstance(result, list) else js(result)[:130])
    record("ENV", 'db.version(); db.getCollectionInfos()', {
        "version": db.client.server_info()["version"], "collections": list(db.list_collections()),
        "counts": {n: db[n].count_documents({}) for n in ["books", "readers", "borrow_logs", "book_in_stock"]}})
    for label, col, query in QUERIES:
        rows = list(db[col].find(query, {"_id": 0}))
        record(label, f"db.{col}.find({js(query)}).toArray()", {"count": len(rows), "rows": rows})
    rows = list(db.books.find({}, {"_id": 0}).sort([("rating", -1), ("isbn", 1)]).limit(5))
    record("Q14", 'db.books.find().sort({rating:-1,isbn:1}).limit(5).toArray()', rows)
    record("Q15", 'db.books.find({},{_id:0,title:1,price:1,rating:1}).toArray()',
           list(db.books.find({}, {"_id": 0, "title": 1, "price": 1, "rating": 1})))
    record("Q16", 'db.books.distinct("category")', sorted(db.books.distinct("category")))
    # A 系列在原始数据基线执行，不混用打折、删除后的数据。
    for label, (col, pipeline) in AGGREGATIONS.items():
        rows = list(db[col].aggregate(pipeline))
        if label == "A9": rows = list(db.category_stats.find().sort("_id", 1))
        record(label, f"db.{col}.aggregate({js(pipeline)}).toArray()", rows)
    record("I1-I5", 'db.books.getIndexes()', list(db.books.list_indexes()))
    try:
        duplicate = dict(db.books.find_one()); duplicate.pop("_id")
        db.books.insert_one(duplicate)
        raise AssertionError("唯一索引未拒绝重复 ISBN")
    except DuplicateKeyError as exc:
        record("I1-duplicate", "db.books.insertOne(重复ISBN的文档)", {"code": exc.code, "expected": "DuplicateKey"})
    for name, hint in [("COLLSCAN", {"$natural": 1}), ("IXSCAN", "category_price")]:
        explain = db.command("explain", {"find": "books", "filter": {"category": "计算机", "price": {"$gt": 80}},
                                       "hint": hint}, verbosity="executionStats")
        record("explain-" + name, f'db.books.find({{category:"计算机",price:{{$gt:80}}}}).hint({js(hint)}).explain("executionStats")',
               explain["executionStats"])
    originals = list(db.books.find())
    original_reader = db.readers.find_one({"card_no": "R20240001"})
    original_logs = list(db.borrow_logs.find())
    try:
        ops = [
            ("U1", {"isbn": "9787115428028"}, {"$inc": {"stock": -5}}, False),
            ("U2", {"category": "计算机"}, {"$mul": {"price": 0.9}}, True),
            ("U3", {"isbn": "9787115428028"}, {"$set": {"source": "实训"}, "$currentDate": {"updated_at": True}}, False),
            ("U4", {"isbn": "9787115428028"}, {"$unset": {"tags": ""}}, False)]
        for label, q, update, many in ops:
            method = "updateMany" if many else "updateOne"
            result = (db.books.update_many if many else db.books.update_one)(q, update)
            record(label, f"db.books.{method}({js(q)},{js(update)})",
                   {"matched_count": result.matched_count, "modified_count": result.modified_count,
                    "after": list(db.books.find(q, {"_id": 0}))})
        returned = db.borrow_logs.find_one({"status": {"$eq": "已归还"}})
        try:
            d = db.borrow_logs.delete_one({"_id": returned["_id"], "status": {"$eq": "已归还"}})
            record("D1", 'db.borrow_logs.deleteOne({_id:指定ID,status:{$eq:"已归还"}})', {"deleted_count": d.deleted_count})
        except OperationFailure as exc:
            record("D1-limit", 'db.borrow_logs.deleteOne({status:{$eq:"已归还"}})',
                   {"code": exc.code, "error": str(exc)})
            d = db.borrow_logs.delete_many({"_id": returned["_id"]})
            record("D1-compatible", "db.borrow_logs.deleteMany({_id:指定ID})",
                   {"deleted_count": d.deleted_count, "note": "来源数据的自动生成_id不重复，精确筛选仅删除此条"})
            db.borrow_records.insert_one({"_id": "D1-demo", "status": "已归还"})
            d = db.borrow_records.delete_one({"_id": "D1-demo", "status": {"$eq": "已归还"}})
            record("D1-method", 'db.borrow_records.deleteOne({_id:"D1-demo",status:{$eq:"已归还"}})',
                   {"deleted_count": d.deleted_count})
        preview = list(db.borrow_logs.find({"status": "逾期"}))
        record("D2-preview", 'db.borrow_logs.find({status:"逾期"}).toArray()', preview)
        d = db.borrow_logs.delete_many({"status": "逾期"})
        record("D2", 'db.borrow_logs.deleteMany({status:"逾期"})', {"deleted_count": d.deleted_count})
        replacement = deepcopy(original_reader); replacement["level"] = "教师"
        r = db.readers.replace_one({"card_no": "R20240001"}, replacement)
        record("D3", f"db.readers.replaceOne({{card_no:'R20240001'}},{js({k:v for k,v in replacement.items() if k!='_id'})})",
               {"modified_count": r.modified_count, "id_preserved": db.readers.find_one({"card_no": "R20240001"})["_id"] == original_reader["_id"]})
        try:
            db.borrow_logs.update_many({"status": "借出"}, {"$set": {"status": "已归还"}})
        except OperationFailure as exc:
            record("TS-update-limit", 'db.borrow_logs.updateMany({status:"借出"},{$set:{status:"已归还"}})',
                   {"code": exc.code, "error": str(exc)})
    finally:
        for row in originals: db.books.replace_one({"_id": row["_id"]}, row)
        db.readers.replace_one({"_id": original_reader["_id"]}, original_reader)
        db.borrow_logs.delete_many({})
        db.borrow_logs.insert_many(original_logs)
    record("RESTORED", "更新删除演示结束后恢复原始数据基线",
           {n: db[n].count_documents({}) for n in ["books", "readers", "borrow_logs", "book_in_stock"]})
    for col in ("books", "readers", "borrow_logs", "category_stats"):
        (out / f"{col}.json").write_text(json_util.dumps(list(db[col].find()), ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "execution.json").write_text(json_util.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# 图书平台命令与实测结果\n\n所有结果由真实 MongoDB 实例运行获得。Q/A 使用导入后的原始基线；U/D 单独演示后恢复。金额 A5 是题目指定的单价×借阅次数指标，不代表真实销售收入。\n"]
    for row in records:
        md += [f"## {row['id']}\n\n```javascript\n{row['command']}\n```\n",
               f"```json\n{json_util.dumps(row['result'], ensure_ascii=False, indent=2)}\n```\n"]
    (out / "完整命令与实测结果.md").write_text("\n".join(md), encoding="utf-8")
    # 可执行的查询与聚合 mongosh 文件。
    shell = ['// 从项目根目录运行 mongosh --file scripts/queries.js',
             'db = db.getSiblingDB("library");', 'function emit(id, result){print(id);printjson(result);}']
    for row in records:
        if row["id"].startswith(("Q", "A")) and row["id"] != "ENV":
            shell.append(f'emit("{row["id"]}", {row["command"]});')
    (ROOT / "scripts" / "queries.js").write_text("\n".join(shell), encoding="utf-8")
    return records


if __name__ == "__main__":
    try: execute()
    finally: close_connection()
