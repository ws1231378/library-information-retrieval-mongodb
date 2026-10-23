"""图书管理：所有检索都使用 MongoDB，分页采用稳定次序。"""
import math
import re
from datetime import datetime, timezone
from mongodb_connect import get_database


def validate_book(book):
    required = ("isbn", "title", "author", "publisher", "category")
    if any(not isinstance(book.get(k), str) or not book[k].strip() for k in required):
        raise ValueError("ISBN、书名、作者、出版社、类别必须是非空字符串")
    if not re.fullmatch(r"\d{13}", book["isbn"]):
        raise ValueError("ISBN 必须是 13 位数字")
    for key in ("price", "rating"):
        value = book.get(key)
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            raise ValueError(f"{key} 必须为有限数值")
    if book["price"] < 0 or not 0 <= book["rating"] <= 5:
        raise ValueError("价格不得为负，评分范围为 0—5")
    for key in ("stock", "borrow_count"):
        value = book.get(key, 0)
        if type(value) is not int or value < 0:
            raise ValueError(f"{key} 必须为非负整数")
    if not isinstance(book.get("tags", []), list) or any(not isinstance(x, str) for x in book.get("tags", [])):
        raise ValueError("tags 必须是字符串数组")


def add_book(book):
    validate_book(book)
    book = dict(book)
    book.setdefault("borrow_count", 0)
    book.setdefault("publish_date", datetime.now(timezone.utc))
    return get_database().books.insert_one(book)


def add_books(books):
    if not books:
        raise ValueError("批量数据不能为空")
    for book in books:
        validate_book(book)
    return get_database().books.insert_many([dict(b) for b in books])


def find_book(isbn):
    return get_database().books.find_one({"isbn": isbn})


def search_books(keyword="", category=None, min_price=None, max_price=None,
                 min_rating=None, max_stock=None, tags=None, page=1,
                 page_size=10, sort_field="rating", descending=True):
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError("页码从 1 开始，每页 1—100 条")
    if sort_field not in ("rating", "price", "stock", "title", "borrow_count"):
        raise ValueError("不支持的排序字段")
    query = {}
    if keyword:
        query["$or"] = [{k: {"$regex": re.escape(keyword), "$options": "i"}}
                        for k in ("title", "author", "isbn")]
    if category:
        query["category"] = category
    if min_price is not None or max_price is not None:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValueError("价格下限不能大于上限")
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    if min_rating is not None:
        query["rating"] = {"$gte": min_rating}
    if max_stock is not None:
        query["stock"] = {"$lte": max_stock}
    if tags:
        query["tags"] = {"$all": tags}
    col = get_database().books
    rows = list(col.find(query, {"_id": 0}).sort(
        [(sort_field, -1 if descending else 1), ("isbn", 1)]
    ).skip((page - 1) * page_size).limit(page_size))
    return {"total": col.count_documents(query), "page": page, "items": rows}


def ranking(n=5):
    return search_books(page_size=n)["items"]


def change_stock(isbn, delta):
    if type(delta) is not int:
        raise ValueError("库存增减量必须为整数")
    query = {"isbn": isbn}
    if delta < 0:
        query["stock"] = {"$gte": -delta}
    return get_database().books.update_one(
        query, {"$inc": {"stock": delta}, "$currentDate": {"updated_at": True}})


def delete_book(isbn):
    db = get_database()
    if db.borrow_records.count_documents({"book_isbn": isbn, "status": {"$ne": "已归还"}}):
        raise ValueError("该书仍有未归还借阅，不能删除")
    return db.books.delete_one({"isbn": isbn})


def delete_empty_books(category):
    if not category:
        raise ValueError("批量删除必须指定类别")
    db = get_database()
    active = db.borrow_records.distinct("book_isbn", {"status": {"$ne": "已归还"}})
    return db.books.delete_many({"category": category, "stock": 0, "isbn": {"$nin": active}})
