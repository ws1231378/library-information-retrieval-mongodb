import json,secrets
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from bson import json_util,ObjectId
from initialize import load,indexes
import borrow_service,catalog
ROOT=Path(__file__).parent
c=MongoClient((ROOT/'runtime/replica/connection.txt').read_text());db=c.smart_library
if not db.books.estimated_document_count():load(db)
indexes(db)
users={name:secrets.token_urlsafe(24) for name in ('libraryReader','libraryWriter','libraryManager')}
for name,role in zip(users,('read','readWrite','dbOwner')):
    db.command('createUser',name,pwd=users[name],roles=[{'role':role,'db':'smart_library'}])
(ROOT/'runtime/replica/app_users.json').write_text(json.dumps(users))
reader=MongoClient('mongodb://127.0.0.1:28217,127.0.0.1:28218,127.0.0.1:28219/?replicaSet=libraryRS',username='libraryReader',password=users['libraryReader'],authSource='smart_library')
result={'reader_count':reader.smart_library.books.count_documents({})}
try:reader.smart_library.books.insert_one({'unauthorized':True});raise AssertionError('只读用户意外写入成功')
except OperationFailure as e:assert e.code==13;result['read_only_write_denied']=e.code
row=db.books.find_one();stock=row['stock'];ident=borrow_service.borrow(db,'R20240001',row['isbn'])
assert db.books.find_one({'isbn':row['isbn']})['stock']==stock-1
borrow_service.give_back(db,ident)
assert db.books.find_one({'isbn':row['isbn']})['stock']==stock
try:borrow_service.give_back(db,ident);raise AssertionError('重复归还未拒绝')
except ValueError:result['double_return_rejected']=True
db.borrow_logs.delete_one({'_id':ObjectId(ident)})
db.books.update_one({'isbn':row['isbn']},{'$inc':{'borrow_count':-1}})
result['transaction_borrow_return']='passed; baseline restored'
catalog.create(db,'readers',{'card_no':'TESTONLY','name':'验收测试'})
assert catalog.update(db,'readers','card_no','TESTONLY',{'name':'修改测试'})==1
assert catalog.delete(db,'readers','card_no','TESTONLY')==1
result['reader_crud']='passed'
result['counts']={n:db[n].count_documents({}) for n in ('books','readers','borrow_logs')}
(ROOT/'results/security_transactions.json').write_text(json_util.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result))
