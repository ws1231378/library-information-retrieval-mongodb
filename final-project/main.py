import json,re
from pathlib import Path
from bson import json_util
from connection import connect,audit
import catalog,statistics_service as stats,file_service,borrow_service

def display(value):print(json_util.dumps(value,ensure_ascii=False,indent=2))

def main():
    db=connect()
    while True:
        print('\n智慧图书馆数字资源平台\n1 图书分页 2 读者分页 3 六项检索 4 分类统计 5 学院前五 6 年月趋势 7 借阅排行\n8 保存分类统计 9 上传文件 10 文件清单 11 按书名下载 12 新增图书 13 新增读者\n14 修改图书 15 修改读者 16 删除图书 17 删除读者 18 借书 19 还书 20 导出统计 21 最近操作 0 退出')
        choice=input('选择：').strip()
        try:
            if choice=='0':break
            elif choice in ('1','2'):
                name='books' if choice=='1' else 'readers';display(catalog.search(db,name,page=int(input('页码：')),sort='title' if name=='books' else 'card_no'))
            elif choice=='3':
                for name,q in stats.queries().items():display({'query':name,'filter':q,'count':db.books.count_documents(q),'rows':list(db.books.find(q))})
                display(list(db.books.find({},{'_id':0,'title':1,'author':1,'rating':1}).sort([('rating',-1),('title',1)]).limit(10)))
            elif choice in ('4','5','6','7'):display(stats.run(db,{'4':'分类统计','5':'学院前五','6':'年月趋势','7':'借阅前十'}[choice]))
            elif choice=='8':display(stats.save_categories(db))
            elif choice=='9':display(file_service.upload(db,Path(__file__).parent/'data/gridfs_files'))
            elif choice=='10':display(file_service.listing(db))
            elif choice=='11':display(file_service.download(db,input('书名关键词：'),input('下载目录：')))
            elif choice in ('12','13'):display(catalog.create(db,'books' if choice=='12' else 'readers',json_util.loads(input('完整文档JSON（日期使用$date）：'))))
            elif choice in ('14','15','16','17'):
                name='books' if choice in ('14','16') else 'readers';key='isbn' if name=='books' else 'card_no';value=input(key+'：')
                display(catalog.update(db,name,key,value,json_util.loads(input('修改字段JSON：'))) if choice in ('14','15') else catalog.delete(db,name,key,value))
            elif choice=='18':display(borrow_service.borrow(db,input('读者证号：'),input('ISBN：')))
            elif choice=='19':display(borrow_service.give_back(db,input('流水_id：')))
            elif choice=='20':
                out=Path(input('导出文件路径：'));out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json_util.dumps(stats.save_categories(db),ensure_ascii=False,indent=2),encoding='utf-8');audit(db,'export','category_stats',{'file':out.name});print('导出成功')
            elif choice=='21':display(list(db.audit_logs.find().sort('at',-1).limit(100)))
            else:print('无效选项')
        except Exception as exc:print('操作失败：',str(exc))

if __name__=='__main__':main()
