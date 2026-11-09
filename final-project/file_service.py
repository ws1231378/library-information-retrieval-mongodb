import hashlib,json,re
from pathlib import Path
import gridfs
from connection import audit

def upload(db, directory):
    directory=Path(directory); fs=gridfs.GridFS(db)
    manifest=json.loads((directory/'files_manifest.txt').read_text(encoding='utf-8'))
    results=[]
    for row in manifest['ebooks']+manifest['covers']:
        source=directory/row['filename']; content=source.read_bytes()
        sha=hashlib.sha256(content).hexdigest()
        previous=fs.find_one({'filename':source.name,'metadata.sha256':sha})
        ident=previous._id if previous else fs.put(content,filename=source.name,metadata={'isbn':row['related_isbn'],'type':source.suffix[1:],'original_name':source.name,'sha256':sha})
        audit(db,'upload','fs.files',{'id':str(ident),'filename':source.name})
        results.append({'filename':source.name,'bytes':len(content),'sha256':sha})
    return results

def listing(db):
    return list(db.fs.files.find({}, {'filename':1,'length':1,'uploadDate':1,'metadata':1}))

def download(db,title,directory):
    fs=gridfs.GridFS(db); out=Path(directory);out.mkdir(parents=True,exist_ok=True); results=[]
    for book in db.books.find({'title':{'$regex':re.escape(title),'$options':'i'},'ebook_name':{'$exists':True}}):
        f=fs.get_last_version(book['ebook_name']);data=f.read()
        sha=hashlib.sha256(data).hexdigest()
        if len(data)!=f.length or sha!=f.metadata['sha256']: raise ValueError('文件校验失败')
        (out/Path(f.filename).name).write_bytes(data)
        audit(db,'export','fs.files',{'filename':f.filename,'bytes':len(data)})
        results.append({'filename':f.filename,'bytes':len(data),'sha256':sha,'verified':True})
    return results
