"""聚合统计；流水排行使用事件，实时归还状态使用 borrow_records。"""
from mongodb_connect import get_database


def category_statistics(save=False):
    db = get_database()
    stages = [{"$group": {"_id": "$category", "book_count": {"$sum": 1},
                          "total_stock": {"$sum": "$stock"}, "avg_price": {"$avg": "$price"},
                          "avg_rating": {"$avg": "$rating"}, "max_stock": {"$max": "$stock"},
                          "min_stock": {"$min": "$stock"}}},
              {"$sort": {"total_stock": -1, "_id": 1}}]
    if save:
        list(db.books.aggregate(stages + [{"$merge": {"into": "category_stats",
              "whenMatched": "replace", "whenNotMatched": "insert"}}]))
        # $merge 不会自动清除已消失的类别。
        db.category_stats.delete_many({"_id": {"$nin": db.books.distinct("category")}})
    return list(db.books.aggregate(stages))


def borrow_trend(monthly=False):
    return list(get_database().borrow_logs.aggregate([
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m" if monthly else "%Y年",
                       "date": "$borrow_date", "timezone": "Asia/Shanghai"}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}]))


def best_sellers(n=5):
    if not 1 <= n <= 100:
        raise ValueError("榜单数量范围 1—100")
    return list(get_database().books.aggregate([
        {"$sort": {"borrow_count": -1, "isbn": 1}}, {"$limit": n},
        {"$project": {"_id": 0, "title": 1, "isbn": 1, "borrow_count": 1}}]))


def popular_from_logs(n=5):
    if not 1 <= n <= 100:
        raise ValueError("榜单数量范围 1—100")
    return list(get_database().borrow_logs.aggregate([
        {"$group": {"_id": "$book_isbn", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}}, {"$limit": n},
        {"$lookup": {"from": "books", "localField": "_id", "foreignField": "isbn", "as": "book"}},
        {"$project": {"count": 1, "title": {"$arrayElemAt": ["$book.title", 0]}}}]))


def active_readers(n=5):
    return list(get_database().borrow_logs.aggregate([
        {"$group": {"_id": "$reader_card", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}}, {"$limit": n},
        {"$lookup": {"from": "readers", "localField": "_id", "foreignField": "card_no", "as": "reader"}},
        {"$project": {"count": 1, "name": {"$arrayElemAt": ["$reader.name", 0]}}}]))
