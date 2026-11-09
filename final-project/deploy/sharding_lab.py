"""Local, authenticated config RS + two shard RS + mongos teaching topology."""
import os,sys,secrets,base64,json,time,subprocess
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import json_util
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
RUN=ROOT/'runtime/sharding';RUN.mkdir(parents=True,exist_ok=True)
if (RUN/'credentials.json').exists():raise SystemExit('已初始化目录，拒绝覆盖凭据')
password=secrets.token_urlsafe(24)
KEYFILE=Path(os.environ.get('SHARD_KEYFILE_PATH',r'C:\ProgramData\mongo_lab\keyfile_shard'))
KEYFILE.parent.mkdir(parents=True,exist_ok=True)
KEYFILE.write_text(base64.b64encode(secrets.token_bytes(512)).decode())
(RUN/'credentials.json').write_text(json.dumps({'username':'labAdmin','password':password}))
def direct(port,auth=False):return MongoClient('127.0.0.1',port,directConnection=True,serverSelectionTimeoutMS=2000,**({'username':'labAdmin','password':password,'authSource':'admin'} if auth else {}))
def wait(port,primary=False):
    for _ in range(90):
        try:
            h=direct(port).admin.command('hello')
            if not primary or h.get('isWritablePrimary'):return
        except PyMongoError:pass
        time.sleep(1)
    raise RuntimeError(f'{port}启动超时')
for name,port,role in [('configRS',28300,'--configsvr'),('shardA',28301,'--shardsvr'),('shardB',28302,'--shardsvr')]:
    path=RUN/str(port);path.mkdir(exist_ok=True)
    args=[os.environ['MONGOD_BIN'],'--dbpath',str(path),'--logpath',str(path/'mongod.log'),'--port',str(port),'--bind_ip','127.0.0.1','--replSet',name,role,'--keyFile',str(KEYFILE),'--wiredTigerCacheSizeGB','0.25']
    p=subprocess.Popen(args,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));(path/'pid').write_text(str(p.pid));wait(port)
    config={'_id':name,'members':[{'_id':0,'host':f'127.0.0.1:{port}'}]}
    if role=='--configsvr':config['configsvr']=True
    direct(port).admin.command('replSetInitiate',config);wait(port,True)
    if role=='--configsvr':direct(port).admin.command('createUser','labAdmin',pwd=password,roles=[{'role':'root','db':'admin'}])
args=[os.environ.get('MONGOS_BIN',str(ROOT/'runtime/mongo/mongos.exe')),'--configdb','configRS/127.0.0.1:28300','--port','28417','--bind_ip','127.0.0.1','--keyFile',str(KEYFILE),'--logpath',str(RUN/'mongos.log')]
p=subprocess.Popen(args,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));(RUN/'mongos.pid').write_text(str(p.pid));wait(28417)
uri=f'mongodb://labAdmin:{password}@127.0.0.1:28417/?authSource=admin';(RUN/'connection.txt').write_text(uri)
c=MongoClient(uri,serverSelectionTimeoutMS=10000)
for name,port in [('shardA',28301),('shardB',28302)]:c.admin.command('addShard',f'{name}/127.0.0.1:{port}')
c.admin.command('enableSharding','smart_library')
c.smart_library.create_collection('borrow_logs')
c.smart_library.borrow_logs.create_index([('reader_card','hashed')])
c.admin.command('shardCollection','smart_library.borrow_logs',key={'reader_card':'hashed'},numInitialChunks=4)
from initialize import load,indexes
counts=load(c.smart_library);indexes(c.smart_library)
cross=c.smart_library.command('explain',{'find':'borrow_logs','filter':{'status':'借出'}},verbosity='executionStats')
target=c.smart_library.command('explain',{'find':'borrow_logs','filter':{'reader_card':'R20240001'}},verbosity='executionStats')
distribution=list(c.smart_library.borrow_logs.aggregate([{'$collStats':{'count':{}}}]))
assert len(distribution)==2 and all(x['count']>0 for x in distribution)
evidence={'counts':counts,'shards':c.admin.command('listShards'),'distribution':distribution,'chunks':list(c.config.chunks.find()),'balancer':c.admin.command('balancerStatus'),'cross_shard':cross,'targeted':target}
(ROOT/'results/sharding.json').write_text(json_util.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'counts':counts,'distribution':[{'shard':x['shard'],'count':x['count']} for x in distribution]}))

