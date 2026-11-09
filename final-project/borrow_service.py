"""Borrow/return operations require a replica set or mongos for transactions."""
from datetime import datetime,timezone
from bson import ObjectId

def borrow(db,card,isbn):
    def operation(session):
        if not db.readers.find_one({'card_no':card},session=session): raise ValueError('读者不存在')
        r=db.books.update_one({'isbn':isbn,'stock':{'$gt':0}},{'$inc':{'stock':-1,'borrow_count':1}},session=session)
        if not r.modified_count: raise ValueError('图书不存在或库存不足')
        now=datetime.now(timezone.utc)
        r=db.borrow_logs.insert_one({'reader_card':card,'book_isbn':isbn,'borrow_date':now,'status':'借出','duration_days':0},session=session)
        db.audit_logs.insert_one({'at':now,'actor':'operator','action':'borrow','collection':'borrow_logs','detail':{'id':str(r.inserted_id)}},session=session)
        return str(r.inserted_id)
    with db.client.start_session() as s:return s.with_transaction(operation)

def give_back(db,ident):
    def operation(session):
        row=db.borrow_logs.find_one({'_id':ObjectId(ident)},session=session)
        if not row or row['status']=='已归还': raise ValueError('记录不存在或已归还')
        now=datetime.now(timezone.utc)
        start=row['borrow_date'].replace(tzinfo=timezone.utc)
        db.borrow_logs.update_one({'_id':row['_id']},{'$set':{'status':'已归还','return_date':now,'duration_days':(now-start).days}},session=session)
        db.books.update_one({'isbn':row['book_isbn']},{'$inc':{'stock':1}},session=session)
        db.audit_logs.insert_one({'at':now,'actor':'operator','action':'return','collection':'borrow_logs','detail':{'id':ident}},session=session)
        return '归还成功'
    with db.client.start_session() as s:return s.with_transaction(operation)
