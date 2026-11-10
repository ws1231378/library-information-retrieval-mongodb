# 图书情报检索与统计平台

## 期末项目 智慧图书馆数字资源平台

本次期末项目交付物已放入 [final-project](final-project/README.md)。

- [完整实验报告 Word](final-project/deliverables/24数科3班-202414870324-王睿昌.docx)
- [项目技术文档 Word](final-project/deliverables/智慧图书馆数字资源平台项目文档（含补充验收）.docx)
- [源码及运行说明](final-project/) · [原始数据](final-project/data/) · [运行记录与截图](final-project/results/)

下方保留上次实训作业内容。


下方为上次实训作业的公开版本，保留原有匿名报告；本次期末项目的两份文档已填写班级、学号、姓名，见上方入口。

本项目包含任务书六项任务的程序、数据、实测记录、Compass 核对截图，以及第3章上机练习的独立脚本和完成记录。报告在 `deliverables`，截图说明在 `results/截图与证据索引.md`。实验于2026年10月20日开始，后续补齐图形化核对与交付材料。

## 提交材料入口

- [实验报告 Word](deliverables/实验报告-公开版.docx)
- [技术文档 Word（4页）](deliverables/图书情报检索与统计平台技术文档.docx)
- [三份原始数据 TXT](data/)
- 六个主程序：[连接](mongodb_connect.py)、[图书管理](book_manager.py)、[读者管理](reader_manager.py)、[借还管理](borrow_manager.py)、[统计](stat_manager.py)、[主菜单](main.py)
- [覆盖六项任务的截图索引](results/截图与证据索引.md) · [14张运行截图](results/screenshots/)
- [全部实测命令与结果](results/完整命令与实测结果.md)

课程：《数据库管理系统》；项目：图书情报检索与统计平台。六个主程序配合运行，初始化与验收辅助脚本位于 `scripts/`。

## 已验证结果

- 原始基线：books 20、readers 16、borrow_logs 66；在库视图19，分类统计5组。
- Q1—Q16、U1—U4、D1—D3、A1—A9 均有真实数据库返回值；修改性练习执行后恢复原始数据。
- 34项真实数据库集成检查全部通过，包括零库存、重复ISBN、重复归还、读者不存在等边界。
- --auth 已启用：匿名读被拒绝，只读用户可读20本图书但写入被拒绝，错误码13；读写用户写入成功。
- Compass 独立核对 Q1、Q2、Q7、Q14、A1 和在库视图，全部一致。

## 文件说明

|路径|内容|
|---|---|
|根目录六个 `.py`|连接、图书、读者、借还、统计、主菜单|
|`data/*.txt`|用户提供的三份原始 Extended JSON 数据|
|`scripts/init_data.py`|创建集合、导入数据、索引与视图|
|`scripts/exercises.py`|项目全部查询、更新删除、聚合与索引实测|
|`scripts/queries.js`、`mutations.js`|对应 mongosh 命令；后者会修改数据|
|`scripts/create_users.js`|交互输入密码创建三个账号|
|`scripts/manual_practice.py`|第3章上机练习，独立练习库|
|`scripts/test_integration.py`|独立测试库的集成验收|
|`results/完整命令与实测结果.md`|完整命令及实际返回值|
|`results/第3章上机练习完成记录.md`|手册逐项练习与说明|
|`results/menu_session.txt`、`tests.json`、`security.json`|真实程序输出、检查和权限结果|
|`results/*.json`|数据导出与机器可读结果|
|`results/screenshots`|真实窗口截图；以索引说明来源|
|`deliverables`|模板版实验报告、4页技术文档|

## 原实验电脑继续运行（不适用于新下载的仓库）

原实验电脑的工作目录保留了专用 MongoDB 8.0.26、Compass 1.50.0、数据库文件和本地随机凭据。它们放在 `runtime`，不进入提交压缩包或公开仓库。新下载本仓库请使用下方“在新电脑复现”步骤。原实验电脑关闭服务后，可在项目目录的 PowerShell 窗口运行：

```powershell
.\start_server.ps1 -Auth
```

保持该窗口运行，在另一窗口启动菜单：

```powershell
.\run_local.ps1
```

如果端口27017已有本项目实例运行，不重复启动。`run_local.ps1` 只在存在本地凭据文件时自动使用 libWriter；不在屏幕输出密码。

## 在新电脑复现

1. 安装 Python 3.9以上（本次实际3.12）、MongoDB Community 8.0和 mongosh。Compass用于图形化核对。PyCharm可直接打开本目录并选择已安装 PyMongo 的解释器；本次代码通过命令行执行，没有把 PyCharm 安装过程当作实测。
2. 进入解压后的项目目录，运行 `python -m pip install -r requirements.txt`。
3. 在新建的专用实例启动数据库：`./start_server.ps1 -MongoBin '实际的mongod.exe完整路径'`。该脚本自定义数据目录并仅监听本机27017。初次建库阶段不带 `-Auth`。
4. 在另一个窗口运行以下命令。初次导入要求目标库为空；`--reset` 只能重置已有本项目标记的库，不要对有需保留改动的库使用。

```powershell
python scripts/init_data.py
python scripts/exercises.py
python scripts/manual_practice.py
python scripts/test_integration.py
mongosh --host 127.0.0.1 --port 27017 --file scripts/create_users.js
```

5. 用 Ctrl+C 正常停止刚才启动的专用实例，然后运行 `./start_server.ps1 -Auth -MongoBin '实际的mongod.exe完整路径'`。
6. 在应用窗口设置账号，密码由程序提示输入，不写在命令行中：

```powershell
$env:MONGO_USER='libWriter'
$env:MONGO_AUTH_DB='library'
python main.py
```

7. Compass连接 `mongodb://127.0.0.1:27017/library`，Authentication填写用户及其密码，认证库为library。只读验证使用libReader。连接收藏和导出方法见截图索引。

已启用认证后重跑练习和测试，需要具有创建练习库权限的维护账号：设置 `MONGO_USER=labAdmin`、`MONGO_AUTH_DB=admin`，再按提示输入密码。重跑更新删除练习前应先备份自己的新增数据。

## 数据与实现说明

- 原始日期保留为 BSON Date。统计明确使用 Asia/Shanghai。样例跨2023—2025年，专用实训实例默认暂停 TTL 线程，集合仍配置63072000秒过期；加 `-EnableTTL` 会重新启用清理并可能删掉历史样例。
- 时间序列集合 borrow_logs 的 status 更新实测受到限制（code72），所以新增普通集合 borrow_records 保存实时借还状态。MongoDB 8.0.26 的时间序列 delete_one 实测成功。
- 借还采取条件原子更新和异常补偿，防止负库存与重复归还；跨集合不是完整事务，进程突然终止仍可能造成不一致，适用于本课程单机演示。
- 源数据累计 borrow_count 与66条样例流水统计口径不同；程序分别提供累计借阅榜和流水热门榜。
- 手册未完整提供部分样例时，练习脚本明确标注重建的用户字段及自构造订单数据，不把它们声称为原始附件。
- Windows是实际部署路线；Linux/FinalShell是手册替代路线，未虚构相应安装截图。软件使用项目内便携环境，没有更改系统全局 PATH。

## 提交与核验

上次实训报告保留匿名文件名。模板未提供本次实验序号，保持该项空白。提交压缩包不包含数据库运行目录、软件安装包、密码、缓存或排版中间文件；在新机器复现按上文安装依赖。`SHA256SUMS.txt` 提供每份交付文件的校验值。
