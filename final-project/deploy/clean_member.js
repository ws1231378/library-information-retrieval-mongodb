// 清理重复的 28220 成员配置
let cfg = rs.conf();
print("清理前：" + cfg.members.map(m => m._id + "=" + m.host).join(", "));
cfg.members = cfg.members.filter(m => m.host !== "127.0.0.1:28220");
cfg.version += 1;
rs.reconfig(cfg, { force: true });
sleep(3000);
print("清理后成员数：" + rs.status().members.length);
rs.status().members.forEach(m => print("  " + m.name + "  " + m.stateStr));
