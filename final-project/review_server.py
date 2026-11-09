"""Read-only local graphical verification client. Never exposes credentials."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import html,json
from urllib.parse import urlparse,parse_qs
from bson import json_util
from connection import connect,audit
import statistics_service as stats,file_service
ROOT=Path(__file__).parent
TOPICS=['项目验收','数据模型','图书数量','读者数量','借阅数量','类别价格','多标签','书名模糊','出版年份','缺少标签','评分前十','分类统计','学院前五','年月趋势','借阅前十','分类结果导出','索引对比一','索引对比二','文件上传记录','GridFS文件清单','文件校验1','文件校验2','文件校验3','文件校验4','文件校验5','文件校验6','权限事务','副本集初始状态','故障转移','重加入状态','分片分布','跨分片查询','定向查询','程序菜单']
TOPICS += ['技术选型论证','架构拓扑']
def evidence(name):return json_util.loads((ROOT/'results'/name).read_text(encoding='utf-8'))
def content(i):
    db=connect()
    if i==34:return '设计论证',{'选型':'文档数据库适应可选字段、嵌套位置、数组与聚合','对比':{'键值':'适合缓存；组合检索需额外结构','文档':'馆藏建模及检索聚合','宽列':'高吞吐预定义查询','图':'多跳关系推荐'},'CAP':{'借阅写入':'分区时优先一致性，失去多数派时等待或拒绝','馆藏浏览':'可接受复制延迟，但读取偏好不保证任意分区可用'},'风险':['类型漂移：入口验证及日期转换','运维复杂：认证、监控、备份恢复']}
    if i==35:return '部署设计及已验证端口',{'standalone':'28117','replica':'libraryRS: 28217 ↔ 28218 ↔ 28219','sharding':'客户端 → mongos:28417 → shardA:28301 / shardB:28302；配置元数据 configRS:28300','limitations':'同机教学部署；分片及配置服务器为单成员副本集'}
    if i==0:return '实时数据库查询',{'counts':{n:db[n].count_documents({}) for n in ['books','readers','borrow_logs']},'features':TOPICS}
    if i==1:return '模型设计',{'database':'smart_library','collections':{'books':'馆藏 普通集合 location嵌套 tags数组','readers':'读者 普通集合 card_no唯一','borrow_logs':'流水 普通集合 BSON日期 可事务更新','audit_logs':'操作日志 普通集合 at倒序索引','fs.files':'文件元信息','fs.chunks':'文件分块','category_stats':'分类聚合结果'}}
    if i in (2,3,4):
        n=['books','readers','borrow_logs'][i-2];return '实时数据库查询',{'collection':n,'count':db[n].count_documents({}),'sample':list(db[n].find().limit(3))}
    if 5<=i<=9:
        q=stats.queries()[TOPICS[i]];return '实时数据库查询',{'filter':q,'count':db.books.count_documents(q),'rows':list(db.books.find(q))}
    if i==10:return '实时数据库查询',list(db.books.find({},{'_id':0,'title':1,'author':1,'rating':1}).sort([('rating',-1),('title',1)]).limit(10))
    if 11<=i<=14:return '实时数据库聚合',{'pipeline':stats.pipelines()[TOPICS[i]],'result':stats.run(db,TOPICS[i])}
    if i==15:return '实时数据库查询',list(db.category_stats.find())
    s=evidence('single_node.json')
    if i in (16,17):
        p=s['plans'][i-16];return '原始执行计划实测记录',{'query':p['query'],'before':p['before']['executionStats'],'after_hinted':p['after_hinted']['executionStats'],'note':p['note']}
    if i==18:return '上传实测记录',s['uploads']
    if i==19:return '实时GridFS查询',file_service.listing(db)
    if 20<=i<=25:return '文件逐字节校验实测记录',s['all_six_verified'][i-20]
    if i==26:return '权限与事务实测记录',evidence('security_transactions.json')
    if 27<=i<=29:
        r=evidence('replica.json')
        if i in (27,29):return '副本集实测状态快照',r['initial' if i==27 else 'rejoined']['members']
        return '故障转移实测记录',{k:v for k,v in r.items() if k not in ('initial','rejoined')}
    if 30<=i<=32:
        r=evidence('sharding.json');return '分片实测记录',r[['distribution','cross_shard','targeted'][i-30]]
    return '命令行程序实际运行输出',(ROOT/'results/menu.txt').read_text(encoding='utf-8')
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if urlparse(self.path).path=='/export':
                db=connect();body=json_util.dumps(list(db.category_stats.find()),ensure_ascii=False,indent=2).encode();audit(db,'export','category_stats',{'client':'local verification web'})
                self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Disposition','attachment; filename=category_stats.json');self.end_headers();self.wfile.write(body);return
            i=int(parse_qs(urlparse(self.path).query).get('page',['0'])[0]);kind,value=content(i)
            links=' '.join(f'<a href="/?page={j}">{j+1}. {html.escape(n)}</a>' for j,n in enumerate(TOPICS))
            body=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{TOPICS[i]}</title><style>body{{font:18px "Microsoft YaHei",sans-serif;margin:36px;color:#172a3a;background:#f4f7fa}}header{{border-bottom:3px solid #20677c}}nav{{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}}a{{color:#155d75;font-size:14px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:24px;font:16px Consolas,"Microsoft YaHei";line-height:1.6}}.kind{{color:#455e70}}</style><header><h1>智慧图书馆数字资源平台</h1><p>本机图形化验收客户端</p></header><nav>{links}</nav><h2>{i+1:02d} {TOPICS[i]}</h2><p class="kind">证据类型：{kind} · <a href="/export">导出分类统计 JSON</a></p><pre>{html.escape(json_util.dumps(value,ensure_ascii=False,indent=2))}</pre></html>'''.encode()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(body)
        except Exception as e:self.send_error(500,str(e))
    def log_message(self,*args):pass
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',28780),Handler).serve_forever()
