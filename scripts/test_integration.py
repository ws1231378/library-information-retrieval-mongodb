"""对真实 MongoDB 的集成验收，使用本次创建的独立库。"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["MONGO_DB"] = "library_integration_test"
from mongodb_connect import get_database, get_client, close_connection
from init_data import initialize
import book_manager as b
import reader_manager as r
import borrow_manager as loan
import stat_manager as stats
from pymongo.errors import DuplicateKeyError


def run():
    checks = []
    def check(name, condition):
        assert condition, name
        checks.append({"test": name, "status": "PASS"})
    def rejected(name, fn, error=ValueError):
        try: fn()
        except error: check(name, True)
        else: raise AssertionError(name)
    initialize()
    db = get_database()
    try:
        check("导入数量20/16/66", [db[x].count_documents({}) for x in ["books","readers","borrow_logs"]] == [20,16,66])
        check("日期确为BSON日期", isinstance(db.books.find_one()["publish_date"], datetime))
        check("特殊集合参数", db.borrow_logs.options()["timeseries"]["granularity"] == "hours" and db.book_logs.options()["max"] == 1000)
        check("在库视图19本", db.book_in_stock.count_documents({}) == 19)
        check("Python关键词1本", b.search_books("Python")["total"] == 1)
        check("正则元字符作为普通文本", b.search_books(".*")["total"] == 0)
        check("无结果", b.search_books("不存在的书籍ABCDEFG")["items"] == [])
        pages = [b.search_books(page=i, page_size=10)["items"] for i in (1,2)]
        check("稳定分页20本无重复", len({x["isbn"] for p in pages for x in p}) == 20)
        check("组合检索", b.search_books(category="计算机", min_price=80.01)["total"] == 3)
        check("五类统计", len(stats.category_statistics(save=True)) == 5)
        check("年度趋势总量66", sum(x["count"] for x in stats.borrow_trend()) == 66)
        check("月度趋势总量66", sum(x["count"] for x in stats.borrow_trend(True)) == 66)
        check("学院与等级统计", sum(x["count"] for x in r.reader_statistics()["college"]) == 16)
        check("拒绝负库存", b.change_stock("9787115428028", -999).modified_count == 0)
    except AssertionError:
        get_client().drop_database("library_integration_test")
        raise
    try:
        original = b.find_book("9787115428028")
        rejected("重复ISBN被唯一索引拒绝",lambda:b.add_book({k:v for k,v in original.items() if k!="_id"}),DuplicateKeyError)
        rejected("未知读者不能借书", lambda:loan.borrow_book("UNKNOWN", original["isbn"]))
        rejected("零库存不能借书", lambda:loan.borrow_book("R20240001","9787302653315"))
        result = loan.borrow_book("R20240001", original["isbn"])
        check("借出库存减一", b.find_book(original["isbn"])["stock"] == original["stock"]-1)
        check("借阅累计加一", b.find_book(original["isbn"])["borrow_count"] == original["borrow_count"]+1)
        check("时间序列新增事件", db.borrow_logs.count_documents({}) == 67)
        rejected("未归还图书禁止删除",lambda:b.delete_book(original["isbn"]))
        check("归还成功", loan.return_book(result["loan_id"])["modified_count"] == 1)
        check("重复归还不重复加库存", loan.return_book(result["loan_id"])["modified_count"] == 0 and b.find_book(original["isbn"])["stock"] == original["stock"])
        check("借阅事件不会被归还覆盖", db.borrow_logs.find_one({"_id":result["loan_id"]})["status"] == "借出")
        reg = db.readers.find_one({"card_no":"R20240001"})["register_date"]
        r.save_reader({"card_no":"R20240001","name":"张明","college":"计算机学院","level":"教师"})
        check("更新读者保留注册时间",db.readers.find_one({"card_no":"R20240001"})["register_date"] == reg)
        rejected("非法等级被拒绝",lambda:r.save_reader({"card_no":"X","name":"X","college":"X","level":"未知"}))
        rejected("价格上下限校验",lambda:b.search_books(min_price=100,max_price=1))
        rejected("非法分页被拒绝",lambda:b.search_books(page=0))
        overdue = loan.mark_overdue()
        check("update_many标记逾期",overdue.modified_count > 0)
        check("逾期查询非空",len(loan.overdue_records()) > 0)
        sample = {k:v for k,v in original.items() if k!="_id"}
        sample.update(isbn="9999999999991",title="单条测试图书",stock=0)
        b.add_book(sample)
        check("新增与删除图书",b.delete_book(sample["isbn"]).deleted_count == 1)
        a=dict(sample,isbn="9999999999992");c=dict(sample,isbn="9999999999993")
        check("批量插入",len(b.add_books([a,c]).inserted_ids) == 2)
        check("批量删除零库存",b.delete_empty_books(a["category"]).deleted_count == 2)
        check("热门与活跃榜可关联",len(stats.popular_from_logs()) == 5 and len(stats.active_readers()) == 5)
        (ROOT/"results"/"tests.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({"passed":len(checks),"failed":0},ensure_ascii=False))
    finally:
        get_client().drop_database("library_integration_test")


if __name__ == "__main__":
    try: run()
    finally: close_connection()
