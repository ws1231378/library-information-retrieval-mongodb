// 初次在本项目的无认证本机实例执行；然后关闭并使用 --auth 重启。
// 两个业务账号的密码均由 passwordPrompt 交互输入，源码不保存密码。
db = db.getSiblingDB("admin");
db.createUser({user:"labAdmin",pwd:passwordPrompt(),roles:[{role:"root",db:"admin"}]});
db = db.getSiblingDB("library");
db.createUser({user:"libReader",pwd:passwordPrompt(),roles:[{role:"read",db:"library"}]});
db.createUser({user:"libWriter",pwd:passwordPrompt(),roles:[
  {role:"readWrite",db:"library"},{role:"dbAdmin",db:"library"}]});
printjson(db.getUsers());
