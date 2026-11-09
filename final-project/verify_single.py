"""Run against the isolated coursework database; write actual evidence JSON."""
from pathlib import Path
import hashlib
from bson import json_util
from connection import connect
from initialize import indexes
import statistics_service as stats,file_service

def main():
    db=connect();result={'counts':{n:db[n].count_documents({}) for n in ('books','readers','borrow_logs')}}
    assert list(result['counts'].values())==[50,30,3000]
    result['queries']={n:{'filter':q,'count':db.books.count_documents(q)} for n,q in stats.queries().items()}
    result['top_ratings']=list(db.books.find({},{'_id':0,'title':1,'author':1,'rating':1}).sort([('rating',-1),('title',1)]).limit(10))
    result['statistics']={n:stats.run(db,n) for n in stats.pipelines()}
    result['category_stats']=stats.save_categories(db)
    result['plans']=[]
    tests=[('category_1_price_1',stats.queries()['类别价格']),('publish_date_1',stats.queries()['出版年份'])]
    for index,q in tests:
        if index in db.books.index_information():db.books.drop_index(index)
        before=db.command('explain',{'find':'books','filter':q},verbosity='executionStats')
        indexes(db)
        after=db.command('explain',{'find':'books','filter':q,'hint':index},verbosity='executionStats')
        result['plans'].append({'query':q,'before':before,'after_hinted':after,'note':'after uses explicit index hint; small dataset may naturally favor COLLSCAN'})
    root=Path(__file__).parent
    result['uploads']=file_service.upload(db,root/'data/gridfs_files')
    result['files']=file_service.listing(db)
    result['downloads']=file_service.download(db,'',root/'runtime/downloads')
    import gridfs
    fs=gridfs.GridFS(db);result['all_six_verified']=[]
    for row in result['files']:
        content=fs.get(row['_id']).read();source=(root/'data/gridfs_files'/row['filename']).read_bytes()
        assert content==source
        result['all_six_verified'].append({'filename':row['filename'],'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
    assert len(result['all_six_verified'])==6
    (root/'results/single_node.json').write_text(json_util.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'results/category_stats.json').write_text(json_util.dumps(result['category_stats'],ensure_ascii=False,indent=2),encoding='utf-8')
    print(json_util.dumps({'counts':result['counts'],'queries':{n:r['count'] for n,r in result['queries'].items()},'statistics':{n:len(r) for n,r in result['statistics'].items()},'files_verified':len(result['all_six_verified'])},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
