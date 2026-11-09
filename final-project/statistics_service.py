from datetime import datetime, timezone

def queries():
    return {
        '类别价格': {'category':'计算机','price':{'$gte':50,'$lte':100}},
        '多标签': {'tags':{'$all':['编程','入门']}},
        '书名模糊': {'title':{'$regex':'Python','$options':'i'}},
        '出版年份': {'publish_date':{'$gte':datetime(2020,1,1,tzinfo=timezone.utc),'$lt':datetime(2024,1,1,tzinfo=timezone.utc)}},
        '缺少标签': {'tags':{'$exists':False}},
    }

def pipelines():
    return {
      '分类统计': [{'$group':{'_id':'$category','count':{'$sum':1},'avg_price':{'$avg':'$price'},'avg_rating':{'$avg':'$rating'}}},{'$sort':{'_id':1}}],
      '学院前五': [{'$lookup':{'from':'readers','localField':'reader_card','foreignField':'card_no','as':'reader'}},{'$unwind':'$reader'},{'$group':{'_id':'$reader.college','count':{'$sum':1}}},{'$sort':{'count':-1,'_id':1}},{'$limit':5}],
      '年月趋势': [{'$group':{'_id':{'$dateToString':{'format':'%Y-%m','date':'$borrow_date','timezone':'Asia/Shanghai'}},'count':{'$sum':1}}},{'$sort':{'_id':1}}],
      '借阅前十': [{'$group':{'_id':'$book_isbn','count':{'$sum':1}}},{'$sort':{'count':-1,'_id':1}},{'$limit':10},{'$lookup':{'from':'books','localField':'_id','foreignField':'isbn','as':'book'}},{'$unwind':'$book'},{'$project':{'count':1,'title':'$book.title','location':'$book.location'}}]
    }

def run(db,name):
    p=pipelines()[name]
    return list(db['books' if name=='分类统计' else 'borrow_logs'].aggregate(p))

def save_categories(db):
    list(db.books.aggregate(pipelines()['分类统计']+[{'$out':'category_stats'}]))
    return list(db.category_stats.find())
