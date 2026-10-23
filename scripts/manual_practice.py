"""第3章基础操作复现实验。使用独立 chapter3_practice，默认拒绝覆盖。"""
import sys
from pathlib import Path
from datetime import datetime, timezone
from bson import json_util
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mongodb_connect import get_client, close_connection


def run():
    client = get_client()
    db = client.chapter3_practice
    if db.list_collection_names():
        raise RuntimeError("chapter3_practice 已有数据，请使用新实例或人工核对后清理")
    results = []
    def log(name, command, result):
        results.append({"name": name, "command": command, "result": result})
        print(name)
    temp = client.chapter3_drop_demo
    if temp.list_collection_names(): raise RuntimeError("chapter3_drop_demo 已存在，拒绝删除")
    temp.demo.insert_one({"created_by": "this_run"})
    log("数据库创建与查看", "use chapter3_drop_demo; show dbs", client.list_database_names())
    client.drop_database("chapter3_drop_demo")
    log("删除刚创建的演示数据库", "db.getSiblingDB('chapter3_drop_demo').dropDatabase()", {"dropped": True})
    db.create_collection("baseCollection")
    db.create_collection("cappedCollection", capped=True, size=5242880, max=5000)
    db.create_collection("weather24h", timeseries={"timeField": "timestamp", "metaField": "sensorId", "granularity": "hours"},
                         expireAfterSeconds=86400)
    db.create_collection("clusteredCollection", clusteredIndex={"key": {"_id": 1}, "unique": True})
    db.create_collection("myView", viewOn="users", pipeline=[{"$match": {"age": {"$gte": 28}}}])
    log("特殊集合", "db.getCollectionInfos()", list(db.list_collections()))
    log("集合大小", "db.baseCollection.dataSize()", db.command("collStats", "baseCollection")["size"])
    db.baseCollection.rename("baseCollectionNew")
    db.create_collection("delete_demo"); db.drop_collection("delete_demo")
    # 从手册展示的姓名、年龄、地区、兴趣及签名重建七条教学文档；
    # ObjectId 和注册时间由本次运行生成，不冒用课件截图中的值。
    users = [
        {"_id": 1, "username": "追梦赤子心", "email": "zmczx@example.com", "age": 30, "is_active": True,
         "address": {"province": "山东省", "city": "青岛市", "district": "崂山区"},
         "interests": ["读书", "旅行", "摄影"], "signature": "学而不思则罔，思而不学则殆"},
        {"username": "星空下的吉他", "age": 30, "is_active": False, "address": {"province": "广东省"},
         "interests": ["音乐", "吉他"], "signature": "音乐是灵魂的语言"},
        {"username": "美食探索家", "age": 28, "is_active": False, "address": {"province": "四川省"},
         "interests": ["美食", "烹饪"], "signature": "唯有美食与爱不可辜负", "badges": ["创作达人", "活跃用户"]},
        {"username": "代码诗人", "age": 22, "is_active": True, "address": {"province": "浙江省"},
         "interests": ["编程", "诗歌"], "signature": "用代码书写世界，用诗歌点亮心灵"},
        {"username": "旅行摄影师", "age": 35, "is_active": True, "address": {"province": "云南省"},
         "interests": ["旅行", "摄影", "人文"], "signature": "用镜头记录世界的美丽，用心感受生命的精彩"},
        {"username": "手工达人", "age": 27, "is_active": True, "address": {"province": "江苏省"},
         "interests": ["手工", "DIY", "创意"], "signature": "用心创造，享受手工的乐趣"},
        {"username": "运动爱好者", "age": 24, "is_active": False, "address": {"province": "北京市"},
         "interests": ["跑步", "健身", "户外"], "signature": None},
    ]
    for u in users: u["registration_date"] = datetime.now(timezone.utc)
    one = db.users.insert_one(users[0]); many = db.users.insert_many(users[1:])
    log("insertOne 与 insertMany", "db.users.insertOne(...);db.users.insertMany([...])",
        {"inserted_id": one.inserted_id, "inserted_many": len(many.inserted_ids)})
    queries = [
        {"age": {"$gt": 29}}, {"age": {"$lt": 29}}, {"age": {"$gte": 28}}, {"age": {"$lte": 28}},
        {"signature": {"$eq": None}}, {"is_active": {"$ne": True}},
        {"address.province": {"$in": ["四川省", "云南省"]}},
        {"address.province": {"$nin": ["四川省", "云南省"]}},
        {"$and": [{"age": {"$gt": 25}}, {"age": {"$lt": 30}}]},
        {"$or": [{"age": {"$lt": 28}}, {"age": {"$gt": 30}}]},
        {"signature": {"$regex": "心"}}, {"interests": {"$all": ["旅行", "读书"]}},
        {"interests": {"$size": 2}}, {"_id": {"$type": "int"}}, {"badges": {"$exists": True}},
        {"is_active": {"$eq": "false"}}, {"age": {"$gte": 99}}
    ]
    for i, q in enumerate(queries, 1):
        rows = list(db.users.find(q, {"_id": 0, "username": 1, "age": 1}))
        log(f"查询{i:02d}", f"db.users.find({json_util.dumps(q,ensure_ascii=False)}).toArray()",
            {"count": len(rows), "rows": rows})
    log("排序前3", "db.users.find().sort({age:-1,username:1}).limit(3)",
        list(db.users.find({}, {"_id": 0, "username": 1, "age": 1}).sort([("age", -1), ("username", 1)]).limit(3)))
    log("年龄去重", "db.users.distinct('age')", sorted(db.users.distinct("age")))
    log("find_one 与 count_documents", "db.users.findOne({_id:1});db.users.countDocuments({})",
        {"first": db.users.find_one({"_id": 1}), "count": db.users.count_documents({})})
    for name, method, query, update in [
        ("更新单条", db.users.update_one, {"_id": 1}, {"$inc": {"age": 1}, "$currentDate": {"lastModified": True}}),
        ("批量更新与删除字段", db.users.update_many, {"is_active": False}, {"$set": {"is_active": True}, "$unset": {"badges": ""}})
    ]:
        r = method(query, update); log(name, f"db.users.{ 'updateOne' if name=='更新单条' else 'updateMany'}({json_util.dumps(query)},{json_util.dumps(update)})", r.raw_result)
    db.orders.insert_many([{"user_id": 1, "amount": 99.9, "date": datetime(2024, 1, 1, tzinfo=timezone.utc)},
                           {"user_id": 1, "amount": 20.1, "date": datetime(2024, 2, 1, tzinfo=timezone.utc)}])
    pipelines = {
        "分组": [{"$group": {"_id": "$is_active", "count": {"$sum": 1}, "avg_age": {"$avg": "$age"}}}],
        "sortByCount": [{"$sortByCount": "$address.province"}],
        "merge": [{"$group": {"_id": "$is_active", "count": {"$sum": 1}}}, {"$merge": "user_stats"}],
        "lookup": [{"$match": {"_id": 1}}, {"$lookup": {"from": "orders", "localField": "_id", "foreignField": "user_id", "as": "orders"}}],
        "unionWith": [{"$project": {"_id": 0, "username": 1}}, {"$unionWith": {"coll": "orders", "pipeline": [{"$project": {"_id": 0, "amount": 1}}]}}],
    }
    for name, pipe in pipelines.items():
        rows = list(db.users.aggregate(pipe))
        log(name, "db.users.aggregate("+json_util.dumps(pipe,ensure_ascii=False)+")",
            list(db.user_stats.find()) if name == "merge" else rows)
    pipe = [{"$project": {"_id": 0, "rounded": {"$round": [{"$multiply": ["$amount", 2]}, 2]},
                        "year": {"$year": "$date"}, "date_text": {"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}}}}]
    log("表达式", "db.orders.aggregate("+json_util.dumps(pipe)+")", list(db.orders.aggregate(pipe)))
    db.users.create_index("username"); db.users.create_index("interests")
    log("单键与多键索引", "db.users.getIndexes()", list(db.users.list_indexes()))
    r = db.users.delete_one({"username": "运动爱好者"})
    log("deleteOne", "db.users.deleteOne({username:'运动爱好者'})", {"deleted_count": r.deleted_count})
    preview = list(db.users.find({"age": {"$lt": 28}}, {"_id": 0, "username": 1}))
    log("删除预览", "db.users.find({age:{$lt:28}})", preview)
    r = db.users.delete_many({"age": {"$lt": 28}})
    log("deleteMany", "db.users.deleteMany({age:{$lt:28}})", {"deleted_count": r.deleted_count})
    out = ROOT / "results"
    (out / "manual_execution.json").write_text(json_util.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    md = ["# 第3章上机练习复现实验\n\n平台为 Windows。手册 Linux/FinalShell 步骤属于替代部署路线，未执行。七条用户数据根据手册可见字段重建；订单金额为本次明确构造的练习数据。账号权限使用 library 实训库的验证记录。GUI 项目见 Compass 核对记录。\n"]
    for row in results:
        md.append(f"## {row['name']}\n\n```javascript\n{row['command']}\n```\n\n```json\n{json_util.dumps(row['result'],ensure_ascii=False,indent=2)}\n```\n")
    (out / "第3章上机练习完成记录.md").write_text("\n".join(md),encoding="utf-8")


if __name__ == "__main__":
    try: run()
    finally: close_connection()
