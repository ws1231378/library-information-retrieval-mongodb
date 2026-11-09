// 第四节点增删（在已认证的副本集连接上执行）
print("添加前成员数：" + rs.status().members.length);
rs.add("127.0.0.1:28220");
sleep(9000);
let st = rs.status();
print("添加后成员数：" + st.members.length);
st.members.forEach(m => print("  " + m.name + "  " + m.stateStr));
rs.remove("127.0.0.1:28220");
sleep(3000);
st = rs.status();
print("移除后成员数：" + st.members.length);
st.members.forEach(m => print("  " + m.name + "  " + m.stateStr));
