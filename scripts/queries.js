// 从项目根目录运行 mongosh --file scripts/queries.js
db = db.getSiblingDB("library");
function emit(id, result){print(id);printjson(result);}
emit("Q1", db.books.find({"price": {"$gt": 80}}).toArray());
emit("Q2", db.books.find({"stock": {"$lt": 10}}).toArray());
emit("Q3", db.books.find({"isbn": {"$eq": "9787115428028"}}).toArray());
emit("Q4", db.readers.find({"email": {"$eq": null}}).toArray());
emit("Q5", db.books.find({"publisher": {"$ne": "人民邮电出版社"}}).toArray());
emit("Q6", db.books.find({"category": {"$in": ["计算机", "经济管理"]}}).toArray());
emit("Q7", db.books.find({"$and": [{"rating": {"$gt": 4.0}}, {"category": "计算机"}]}).toArray());
emit("Q8", db.books.find({"$or": [{"rating": {"$lt": 3.5}}, {"stock": 0}]}).toArray());
emit("Q9", db.books.find({"title": {"$regex": "Python"}}).toArray());
emit("Q10", db.books.find({"tags": {"$all": ["编程", "入门"]}}).toArray());
emit("Q11", db.books.find({"tags": {"$size": 3}}).toArray());
emit("Q12", db.books.find({"tags": {"$exists": true}}).toArray());
emit("Q13", db.books.find({"_id": {"$type": "string"}}).toArray());
emit("Q14", db.books.find().sort({rating:-1,isbn:1}).limit(5).toArray());
emit("Q15", db.books.find({},{_id:0,title:1,price:1,rating:1}).toArray());
emit("Q16", db.books.distinct("category"));
emit("A1", db.books.aggregate([{"$group": {"_id": "$category", "count": {"$sum": 1}, "avg_rating": {"$avg": "$rating"}, "max_stock": {"$max": "$stock"}, "min_stock": {"$min": "$stock"}}}, {"$sort": {"_id": 1}}]).toArray());
emit("A2", db.books.aggregate([{"$group": {"_id": "$publisher", "count": {"$sum": 1}}}, {"$group": {"_id": null, "top5": {"$topN": {"n": 5, "sortBy": {"count": -1, "_id": 1}, "output": {"publisher": "$_id", "count": "$count"}}}}}]).toArray());
emit("A3", db.books.aggregate([{"$sortByCount": "$category"}, {"$sort": {"count": -1, "_id": 1}}, {"$limit": 1}]).toArray());
emit("A4", db.books.aggregate([{"$sort": {"rating": -1, "isbn": 1}}, {"$limit": 3}, {"$project": {"_id": 0, "title": 1, "borrow_count": 1}}]).toArray());
emit("A5", db.books.aggregate([{"$project": {"_id": 0, "title": 1, "sales_amount": {"$round": [{"$multiply": ["$price", "$borrow_count"]}, 2]}}}]).toArray());
emit("A6", db.borrow_logs.aggregate([{"$group": {"_id": {"$year": {"date": "$borrow_date", "timezone": "Asia/Shanghai"}}, "count": {"$sum": 1}, "sample_date": {"$min": "$borrow_date"}}}, {"$project": {"_id": 0, "count": 1, "year": {"$dateToString": {"date": "$sample_date", "format": "%Y年", "timezone": "Asia/Shanghai"}}}}, {"$sort": {"year": 1}}]).toArray());
emit("A7", db.borrow_logs.aggregate([{"$group": {"_id": "$reader_card", "count": {"$sum": 1}}}, {"$sort": {"count": -1, "_id": 1}}, {"$limit": 5}]).toArray());
emit("A8", db.borrow_logs.aggregate([{"$lookup": {"from": "readers", "localField": "reader_card", "foreignField": "card_no", "as": "reader"}}, {"$unwind": "$reader"}, {"$group": {"_id": "$reader.college", "count": {"$sum": 1}}}, {"$sort": {"count": -1, "_id": 1}}]).toArray());
emit("A9", db.books.aggregate([{"$group": {"_id": "$category", "count": {"$sum": 1}, "avg_rating": {"$avg": "$rating"}, "max_stock": {"$max": "$stock"}, "min_stock": {"$min": "$stock"}}}, {"$sort": {"_id": 1}}, {"$merge": {"into": "category_stats", "whenMatched": "replace", "whenNotMatched": "insert"}}]).toArray());