# 智慧图书馆数字资源平台

本目录为期末项目公开版；作者姓名、学号、班级及文档作者元数据已隐去，实名报告单独线下提交。

## 提交内容

- `deliverables/实验报告-公开版.docx`：18 页完整合并实验报告，保留实验报告模板，含全部项目正文、8 张表格和 6 张图片；同名 PDF 用于预览。
- `deliverables/智慧图书馆数字资源平台项目文档（含补充验收）.docx`：14 页项目技术文档；同名 PDF 用于预览。第 13—14 页为“8 补充验收”，子节编号为 8.1—8.5。完整实验报告中的相同内容位于第 16—17 页。
- `data/`：学生包原始数据与 6 个电子资源样例。
- `results/`：原始实测记录、截图、图形化导出文件及 SHA256 校验清单。
- `deploy/`：部署、重启、补充验收与截图脚本，以及截图工具专用的 Node.js 依赖清单。

本包不包含答辩大纲或演示文稿。根目录文件仅保留 Python 源码、README、requirements.txt 和 .gitignore。

## 环境与运行

实测环境：Windows、Python 3.12、MongoDB Community 8.0.26、PyMongo 4.19.0。数据库程序需自行安装。通过环境变量 `MONGOD_BIN` 指定 mongod 路径，分片另需 `MONGOS_BIN`。在项目根目录安装 Python 依赖：

```powershell
python -m pip install -r requirements.txt
```

单机初始导入阶段使用独立空目录启动：

```powershell
mongod --dbpath <数据目录> --port 28117 --bind_ip 127.0.0.1
python initialize.py
python main.py
```

初始化拒绝覆盖非空集合。单机适合检索、维护、统计与 GridFS；借还事务需要副本集或 mongos 连接。程序通过 `MONGODB_URI` 和 `MONGODB_DATABASE` 读取连接配置。

首次部署认证副本集时，在独立教学环境的空 runtime/replica 目录执行：

```powershell
python deploy/replica_lab.py
$env:MONGODB_URI = (Get-Content runtime/replica/connection.txt -Raw).Trim()
python verify_replica.py
python main.py
```

脚本创建 28217、28218、28219 三节点并演练停止主节点。`verify_replica.py` 导入基线、创建角色和验证事务，账号已存在时不要重复创建。首次部署分片执行 `python deploy/sharding_lab.py`：配置服务器 28300、两个分片 28301/28302、mongos 28417。初始化需要空运行目录；已初始化环境可执行 `python deploy/restart_lab.py` 重启。重启验收记录见 `results/restart_check.txt`。

单机最终认证阶段以相同数据目录、28117 端口及 `--auth` 启动，再执行 `python deploy/single_auth.py`。管理员密码优先读取 `LIB_ADMIN_PASSWORD`，否则生成并保存于 `runtime/single_auth_password.txt`。凭据、运行数据和 keyFile 均不随包提交；部署时按脚本生成，不在源码中填写密码。

## 图形化验收与截图依赖

验收采用 **Playwright 截图 + Compass 核对（第 8.1 节）**。配置单机连接后运行 `python review_server.py`，访问 `http://127.0.0.1:28780`。页面区分实时查询与历史实测记录，并支持“导出分类统计 JSON”。Compass 集合截图拍摄于无认证导入阶段；最终单机认证另见第 8.4 节。

`deploy/package.json` 和 `deploy/package-lock.json` 仅供截图脚本 `deploy/capture_review.cjs` 使用，不是 Python 应用的运行依赖。需要重新截图时，在项目根目录执行：

```powershell
npm ci --prefix deploy
node deploy/capture_review.cjs
```

截图需要本机 Chrome；默认路径为 `C:/Program Files/Google/Chrome/Application/chrome.exe`，可通过 `CHROME_BIN` 指定实际路径。网页服务需先运行。脚本仍以项目根目录为输出基准，将截图和下载文件写入 `results/`。

图片性质：01—36 为 Playwright 浏览器页面截图，其中实时查询和历史记录在页面上标注；37 为 Compass 窗口截图；38—40 为真实运行输出的日志可视化，不是窗口截屏。

## 模块与结果

`connection.py` 负责连接与审计，`catalog.py` 负责图书和读者维护，`borrow_service.py` 负责事务借还，`statistics_service.py` 负责检索与统计，`file_service.py` 负责 GridFS，`main.py` 提供 21 项菜单。

本批次记录：数据量 50/30/3000；GridFS 六文件逐字节校验通过；只读写入拒绝码 13；事务借还与重复归还验证通过。停止原主 28217 后，28219 升主，约 13.13 秒恢复写入。另一次 stepDown 连续读探针使用 secondaryPreferred，45 次读取全部成功、0 失败，选举约 8.55 秒。两次演练的计时口径不同，不混同。

补充验收对应关系：8.1 Compass 核对；8.2 第四节点加入后成为 SECONDARY，再移除，成员数 3→4→3；8.3 连续读探针；8.4 单机三账号权限；8.5 批次说明。分片分布为 1300/1700 条，即 43.3%/56.7%。

全部节点在同一台主机上，仅验证进程级故障恢复。完整索引执行计划见 `results/single_node.json`，索引后使用 hint；小样本毫秒级耗时不能视为显著提速。普通资料维护与审计仍有独立写入边界，借还已使用事务。运行记录按其生成批次保留，未为文档编号调整重新运行数据库实验。

## 文件校验

`results/SHA256SUMS.txt` 列出包内除清单自身外的全部文件，路径相对于项目根目录。修改文件后应重新生成清单。
