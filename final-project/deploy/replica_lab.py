"""Isolated local replica lab. MONGOD_BIN must point to installed mongod."""
import os,json,secrets,subprocess,time,base64
from pathlib import Path
from datetime import datetime,timezone
from pymongo import MongoClient,ReadPreference
from pymongo.errors import PyMongoError
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runtime/replica';RUN.mkdir(parents=True,exist_ok=True)
# keyFile 放在纯 ASCII 路径：MongoDB 读取中文路径下的密钥文件会报 Illegal byte sequence
KEYFILE=Path(os.environ.get('KEYFILE_PATH',r'C:\ProgramData\mongo_lab\keyfile_merged'))
KEYFILE.parent.mkdir(parents=True,exist_ok=True)
BIN=os.environ['MONGOD_BIN']
ports=[28217,28218,28219]
def client(p,auth=False):
    return MongoClient('127.0.0.1',p,directConnection=True,serverSelectionTimeoutMS=2000,**({'username':'labAdmin','password':password,'authSource':'admin'} if auth else {}))
def start(p):
    path=RUN/str(p);path.mkdir(exist_ok=True)
    args=[BIN,'--dbpath',str(path),'--logpath',str(path/'mongod.log'),'--port',str(p),'--bind_ip','127.0.0.1','--replSet','libraryRS','--keyFile',str(KEYFILE),'--wiredTigerCacheSizeGB','0.25']
    process=subprocess.Popen(args,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    (path/'pid').write_text(str(process.pid));return process
def wait_primary(auth=False):
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        for p in ports:
            try:
                if client(p,auth).admin.command('hello').get('isWritablePrimary'):return p
            except PyMongoError:pass
        time.sleep(.5)
    raise RuntimeError('主节点选举超时')
if (RUN/'credentials.json').exists():raise SystemExit('目录已初始化，拒绝覆盖密钥；重启请使用 restart_lab.py')
password=secrets.token_urlsafe(24)
KEYFILE.write_text(base64.b64encode(secrets.token_bytes(512)).decode('ascii'))
(RUN/'credentials.json').write_text(json.dumps({'username':'labAdmin','password':password}))
processes={p:start(p) for p in ports}
# 等待三个节点都能接受连接再初始化（首次启动 + keyFile 校验需要几秒）
import socket
deadline=time.time()+90
for p in ports:
    while time.time()<deadline:
        try:
            with socket.create_connection(("127.0.0.1",p),timeout=1): break
        except OSError: time.sleep(.5)
    else: raise RuntimeError(f"端口 {p} 启动超时")
client(ports[0]).admin.command('replSetInitiate',{'_id':'libraryRS','members':[{'_id':i,'host':f'127.0.0.1:{p}'} for i,p in enumerate(ports)]})
primary=wait_primary()
client(primary).admin.command('createUser','labAdmin',pwd=password,roles=[{'role':'root','db':'admin'}])
uri='mongodb://labAdmin:'+password+'@'+','.join('127.0.0.1:'+str(p) for p in ports)+'/?authSource=admin&replicaSet=libraryRS'
(RUN/'connection.txt').write_text(uri)
c=MongoClient(uri,serverSelectionTimeoutMS=15000)
db=c.smart_library
db.probe.insert_one({'stage':'before','at':datetime.now(timezone.utc)})
time.sleep(2)
evidence={'initial':c.admin.command('replSetGetStatus'),'preferences':{}}
for name,pref in [('primary',ReadPreference.PRIMARY),('secondaryPreferred',ReadPreference.SECONDARY_PREFERRED)]:
    evidence['preferences'][name]=db.get_collection('probe',read_preference=pref).count_documents({})
evidence['failure_started']=datetime.now(timezone.utc)
started=time.monotonic();processes[primary].terminate();processes[primary].wait(timeout=30)
evidence['attempts']=[]
while time.monotonic()-started<90:
    t=time.monotonic()
    try:
        db.probe.insert_one({'stage':'during','at':datetime.now(timezone.utc)})
        evidence['attempts'].append({'elapsed':time.monotonic()-started,'write':'success','latency':time.monotonic()-t});break
    except PyMongoError as exc:evidence['attempts'].append({'elapsed':time.monotonic()-started,'error':type(exc).__name__})
else:raise RuntimeError('故障后写入未恢复')
evidence['recovery_seconds']=time.monotonic()-started
evidence['new_primary']=wait_primary(True)
assert evidence['new_primary']!=primary
processes[primary]=start(primary);time.sleep(8)
evidence['rejoined']=c.admin.command('replSetGetStatus')
from bson import json_util
(ROOT/'results/replica.json').write_text(json_util.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'old_primary':primary,'new_primary':evidence['new_primary'],'recovery_seconds':evidence['recovery_seconds']}))
