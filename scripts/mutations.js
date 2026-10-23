// U/D 会修改本项目数据；请先用 init_data.py 创建专用实训库。
// 实测及自动恢复版本见 exercises.py；本文件供逐条操作、截图。
db = db.getSiblingDB("library");
printjson(db.books.updateOne({isbn:"9787115428028"},{$inc:{stock:-5}}));
printjson(db.books.updateMany({category:"计算机"},{$mul:{price:0.9}}));
printjson(db.books.updateOne({isbn:"9787115428028"},{$set:{source:"实训"},$currentDate:{updated_at:true}}));
printjson(db.books.updateOne({isbn:"9787115428028"},{$unset:{tags:""}}));
const returned = db.borrow_logs.findOne({status:{$eq:"已归还"}});
if (returned) {
  try { printjson(db.borrow_logs.deleteOne({_id:returned._id,status:{$eq:"已归还"}})); }
  catch (e) {
    print("时间序列 deleteOne 限制："+e.message);
    printjson(db.borrow_logs.deleteMany({_id:returned._id}));
  }
}
print("D2 删除预览");
printjson(db.borrow_logs.find({status:"逾期"}).toArray());
printjson(db.borrow_logs.deleteMany({status:"逾期"}));
const oldReader = db.readers.findOne({card_no:"R20240001"});
if (oldReader) printjson(db.readers.replaceOne({_id:oldReader._id},{...oldReader,level:"教师"}));
