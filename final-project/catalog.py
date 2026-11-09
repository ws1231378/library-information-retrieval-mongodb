"""Book and reader CRUD. Unique identifiers are never changed by update."""
from connection import audit

def search(db, collection, query=None, page=1, size=10, sort='title'):
    if page < 1 or not 1 <= size <= 100: raise ValueError('页码须为正数，每页1—100条')
    return list(db[collection].find(query or {}).sort(sort,1).skip((page-1)*size).limit(size))

def create(db, collection, document):
    result=db[collection].insert_one(document.copy())
    audit(db,'create',collection,{'id':str(result.inserted_id)})
    return str(result.inserted_id)

def update(db, collection, key, value, fields):
    if key in fields or '_id' in fields: raise ValueError('不可修改标识字段')
    result=db[collection].update_one({key:value},{'$set':fields})
    audit(db,'update',collection,{'key':value,'matched':result.matched_count})
    return result.modified_count

def delete(db, collection, key, value):
    relation='book_isbn' if collection=='books' else 'reader_card'
    if db.borrow_logs.count_documents({relation:value}): raise ValueError('存在借阅关联，不能删除')
    result=db[collection].delete_one({key:value})
    audit(db,'delete',collection,{'key':value,'deleted':result.deleted_count})
    return result.deleted_count
