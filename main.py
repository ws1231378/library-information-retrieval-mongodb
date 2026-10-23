"""运行 python main.py；功能菜单覆盖检索、统计、更新、删除与借还。"""
import json
from bson import json_util
from pymongo.errors import PyMongoError
from mongodb_connect import get_database, close_connection
import book_manager as books
import reader_manager as readers
import borrow_manager as loans
import stat_manager as stats

MENU = """
=== 图书情报检索与统计平台 ===
1 图书关键词检索与分页   2 ISBN 精确检索    3 评分前五
4 分类统计并落库         5 年度借阅趋势     6 累计借阅榜
7 调整库存               8 删除指定图书     9 新增图书
10 读者列表              11 读者统计       12 登记借阅
13 归还图书              14 逾期查询       15 读者借阅记录
16 维护读者              17 多条件检索     18 月度借阅趋势
19 流水热门榜            20 活跃读者榜     21 标记逾期
22 批量导入图书          23 删除指定类别零库存图书
0 退出
"""


def show(data):
    if data is None or data == [] or isinstance(data, dict) and data.get("items") == []:
        print("查询无结果")
    print(json_util.dumps(data, ensure_ascii=False, indent=2))


def affected(result):
    for key in ("modified_count", "matched_count", "deleted_count"):
        if hasattr(result, key):
            print(f"{key} = {getattr(result, key)}")
    if hasattr(result, "inserted_id"):
        print(f"inserted_count = 1, inserted_id = {result.inserted_id}")
    if hasattr(result, "inserted_ids"):
        print(f"inserted_count = {len(result.inserted_ids)}")
    if getattr(result, "upserted_id", None) is not None:
        print("inserted_count = 1")


def main():
    try:
        db = get_database()
        print("数据库连接成功")
        for name in sorted(db.list_collection_names()):
            if not name.startswith("system."):
                print(f"{name}: {db[name].count_documents({})}")
        while True:
            print(MENU)
            try:
                choice = input("选择功能：").strip()
                if choice == "0":
                    break
                if choice == "1":
                    show(books.search_books(input("关键词："), page=int(input("页码：") or "1")))
                elif choice == "2": show(books.find_book(input("ISBN：")))
                elif choice == "3": show(books.ranking())
                elif choice == "4":
                    rows = stats.category_statistics(save=True)
                    print(f"统计结果写入 {len(rows)} 个类别")
                    show(rows)
                elif choice == "5": show(stats.borrow_trend())
                elif choice == "6": show(stats.best_sellers())
                elif choice == "7": affected(books.change_stock(input("ISBN："), int(input("库存增减量："))))
                elif choice == "8":
                    isbn = input("待删除 ISBN："); show(books.find_book(isbn))
                    if input("输入 DELETE 确认：") == "DELETE": affected(books.delete_book(isbn))
                elif choice == "9": affected(books.add_book(json.loads(input("完整图书 JSON："))))
                elif choice == "10": show(readers.list_readers(input("学院（空为全部）：") or None))
                elif choice == "11": show(readers.reader_statistics())
                elif choice == "12": show(loans.borrow_book(input("借阅证号："), input("ISBN：")))
                elif choice == "13": show(loans.return_book(input("借阅记录 _id：")))
                elif choice == "14": show(loans.overdue_records())
                elif choice == "15": show(loans.list_loans(input("借阅证号：")))
                elif choice == "16": affected(readers.save_reader(json.loads(input("读者 JSON："))))
                elif choice == "17": show(books.search_books(**json.loads(input('条件 JSON（如 {"category":"计算机","min_price":50}）：'))))
                elif choice == "18": show(stats.borrow_trend(monthly=True))
                elif choice == "19": show(stats.popular_from_logs())
                elif choice == "20": show(stats.active_readers())
                elif choice == "21": affected(loans.mark_overdue())
                elif choice == "22":
                    from pathlib import Path
                    affected(books.add_books(json_util.loads(Path(input("JSON 文件路径：")).read_text(encoding="utf-8-sig"))))
                elif choice == "23":
                    category = input("类别：")
                    show(list(db.books.find({"category": category, "stock": 0}, {"_id": 0, "isbn": 1, "title": 1})))
                    if input("输入 DELETE 确认（未归还图书会跳过）：") == "DELETE":
                        affected(books.delete_empty_books(category))
                else: print("无效选项，请重新输入")
            except (ValueError, TypeError, OSError, PyMongoError) as exc:
                print(f"操作未完成：{exc}")
    except PyMongoError as exc:
        print(f"数据库连接失败，请检查服务与认证参数：{exc}")
    except (EOFError, KeyboardInterrupt):
        print("\n退出")
    finally:
        close_connection()
        print("数据库连接已关闭")


if __name__ == "__main__":
    main()
