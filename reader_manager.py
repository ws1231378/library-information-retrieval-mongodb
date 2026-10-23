"""读者信息维护与学院、等级统计。"""
from datetime import datetime, timezone
from mongodb_connect import get_database


def list_readers(college=None):
    return list(get_database().readers.find({"college": college} if college else {}, {"_id": 0}).sort("card_no", 1))


def save_reader(reader):
    for key in ("card_no", "name", "college"):
        if not isinstance(reader.get(key), str) or not reader[key].strip():
            raise ValueError(f"{key} 不能为空")
    if reader.get("level", "普通") not in ("普通", "高级", "教师"):
        raise ValueError("等级仅支持普通、高级、教师")
    data = {k: v for k, v in reader.items() if k not in ("_id", "register_date")}
    data.setdefault("level", "普通")
    return get_database().readers.update_one(
        {"card_no": reader["card_no"]},
        {"$set": data, "$setOnInsert": {"register_date": datetime.now(timezone.utc)}},
        upsert=True)


def reader_statistics():
    col = get_database().readers
    return {field: [{"name": value, "count": col.count_documents({field: value})}
                    for value in sorted(col.distinct(field))]
            for field in ("college", "level")}
