import json
from datetime import datetime
from pathlib import Path
from connection import connect,audit

def load(db):
    counts={}
    for name in ('books','readers','borrow_logs'):
        if db[name].estimated_document_count(): raise ValueError(f'{name}非空，拒绝覆盖，请使用新数据库')
    for name in ('books','readers','borrow_logs'):
        rows=json.loads((Path(__file__).parent/'data'/f'{name}.txt').read_text(encoding='utf-8'))
        for row in rows:
            for key in ('publish_date','register_date','borrow_date','return_date'):
                if key in row: row[key]=datetime.fromisoformat(row[key])
        db[name].insert_many(rows);counts[name]=db[name].count_documents({})
    db.audit_logs.create_index([('at',-1)])
    audit(db,'import','all',counts)
    return counts

def indexes(db):
    db.books.create_index('isbn',unique=True)
    db.readers.create_index('card_no',unique=True)
    db.books.create_index([('category',1),('price',1)])
    db.books.create_index([('rating',-1),('title',1)])
    db.books.create_index('publish_date')
    db.books.create_index('tags')
    db.borrow_logs.create_index([('reader_card',1),('borrow_date',-1)])
    db.borrow_logs.create_index('book_isbn')
    db.borrow_logs.create_index('borrow_date')

if __name__=='__main__':
    db=connect();print(load(db));indexes(db)
