# 图书情报检索与统计平台

《数据库管理系统》课程作业仓库。期末项目放在 `final-project/`，上次实训的程序和材料保留在根目录。

## 期末项目：智慧图书馆数字资源平台

班级：24数科3班　学号：202414870324　姓名：王睿昌

- [完整实验报告 Word](final-project/deliverables/24数科3班-202414870324-王睿昌.docx)
- [项目技术文档 Word](final-project/deliverables/智慧图书馆数字资源平台项目文档（含补充验收）.docx)
- [项目说明与运行步骤](final-project/README.md)
- [源代码](final-project/) · [原始数据](final-project/data/) · [运行记录与截图](final-project/results/)

## 上次实训：图书情报检索与统计平台

上次实训从 2026 年 10 月 20 日开始，完成了任务书的六项任务和第 3 章上机练习。以下材料与运行步骤均对应上次实训，期末项目请查看上方链接。

### 材料入口

- [实验报告 Word](deliverables/实验报告-公开版.docx)
- [技术文档 Word（4 页）](deliverables/图书情报检索与统计平台技术文档.docx)
- [三份原始数据 TXT](data/)
- 六个主程序：[连接](mongodb_connect.py)、[图书管理](book_manager.py)、[读者管理](reader_manager.py)、[借还管理](borrow_manager.py)、[统计](stat_manager.py)、[主菜单](main.py)
- [截图说明](results/截图与证据索引.md) · [14 张运行截图](results/screenshots/)
- [实验命令与运行结果](results/完整命令与实测结果.md)

### 测试结果

- 原始数据为 20 本图书、16 位读者、66 条借阅记录；在库视图返回 19 本图书，分类统计返回 5 组。
- 已执行 Q1 至 Q16、U1 至 U4、D1 至 D3、A1 至 A9。更新和删除练习结束后恢复了原始数据。
- 34 项集成检查通过，包括零库存、重复 ISBN、读者不存在和重复归还等情况。
- 启用 `--auth` 后，匿名访问被拒绝；只读账号可读取 20 本图书，写入返回错误码 13；读写账号写入成功。
- 在 Compass 中检查了 Q1、Q2、Q7、Q14、A1 和在库视图，结果与脚本一致。

### 文件说明

| 路径 | 内容 |
| --- | --- |
| 根目录六个 `.py` 文件 | 连接、图书、读者、借还、统计和主菜单 |
| `data/*.txt` | 三份原始 Extended JSON 数据 |
| `scripts/init_data.py` | 建库、导入数据、创建索引和视图 |
| `scripts/exercises.py` | 查询、更新、删除、聚合和索引练习 |
| `scripts/queries.js`、`scripts/mutations.js` | mongosh 命令，其中 mutations.js 会修改数据 |
| `scripts/create_users.js` | 创建三个账号，密码由交互输入 |
| `scripts/manual_practice.py` | 第 3 章上机练习，使用独立数据库 |
| `scripts/test_integration.py` | 集成检查，使用独立测试库 |
| `results/完整命令与实测结果.md` | 实验命令及返回结果 |
| `results/第3章上机练习完成记录.md` | 上机练习完成情况 |
| `results/menu_session.txt`、`results/tests.json`、`results/security.json` | 菜单运行、集成检查和权限测试记录 |
| `results/*.json` | 数据导出及其他运行记录 |
| `results/screenshots/` | 运行截图，具体内容见截图说明 |
| `deliverables/` | 模板实验报告和 4 页技术文档 |

### 在原实验电脑上运行

原实验目录的 `runtime/` 中保留了 MongoDB 8.0.26、Compass 1.50.0、数据库文件和本地凭据。这些文件没有上传到仓库。新下载项目请按下一节配置环境。

在原实验目录打开 PowerShell，启动数据库：

```powershell
.\start_server.ps1 -Auth
```

保持这个窗口运行，再开一个 PowerShell 窗口启动菜单：

```powershell
.\run_local.ps1
```

如果本项目的数据库已在 27017 端口运行，就不必再次启动。`run_local.ps1` 读取本地凭据后使用 libWriter 连接，不会在终端显示密码。

### 在新电脑上运行

1. 安装 Python 3.9 或更高版本、MongoDB Community 8.0 和 mongosh。实验使用的是 Python 3.12。需要图形化查看数据时，另外安装 Compass。也可以用 PyCharm 打开项目，选择装有 PyMongo 的解释器。
2. 在项目根目录安装依赖：

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. 启动数据库。脚本会使用独立数据目录，只监听本机 27017 端口。首次导入时不加 `-Auth`：

   ```powershell
   .\start_server.ps1 -MongoBin 'mongod.exe的完整路径'
   ```

4. 在另一个 PowerShell 窗口依次运行：

   ```powershell
   python scripts/init_data.py
   python scripts/exercises.py
   python scripts/manual_practice.py
   python scripts/test_integration.py
   mongosh --host 127.0.0.1 --port 27017 --file scripts/create_users.js
   ```

   首次导入要求目标库为空。`--reset` 仅用于带有本项目标记的实训库；已有需要保留的数据时，先备份再操作。

5. 用 Ctrl+C 停止数据库，再启用认证：

   ```powershell
   .\start_server.ps1 -Auth -MongoBin 'mongod.exe的完整路径'
   ```

6. 在菜单窗口设置账号并运行程序，密码按提示输入：

   ```powershell
   $env:MONGO_USER='libWriter'
   $env:MONGO_AUTH_DB='library'
   python main.py
   ```

7. 在 Compass 中连接 `mongodb://127.0.0.1:27017/library`，填写账号、密码，认证库选择 `library`。只读测试使用 libReader，连接收藏和导出操作见截图说明。

启用认证后，如果需要重跑练习和测试，应使用有建库权限的维护账号：将 `MONGO_USER` 设为 `labAdmin`，`MONGO_AUTH_DB` 设为 `admin`。更新和删除练习会改动数据，运行前先备份自己的新增内容。

### 实现说明

日期保存为 BSON Date，统计使用 Asia/Shanghai 时区。样例借阅记录来自 2023 至 2025 年，TTL 设为 63072000 秒。为保留这些历史样例，启动脚本默认暂停 TTL 清理；使用 `-EnableTTL` 后，过期记录可能被删除。

时间序列集合 `borrow_logs` 的状态更新遇到了错误码 72，因此另建普通集合 `borrow_records` 保存当前借还状态。MongoDB 8.0.26 下，时间序列集合的 `delete_one` 测试成功。

借还功能采用条件更新和失败补偿，防止库存变成负数或重复归还增加库存。这个实训版本没有跨集合事务，进程突然退出时仍可能留下不一致的数据。

源数据中的 `borrow_count` 是历史累计值，66 条借阅流水只代表给定样本，因此程序分别提供累计借阅榜和样本流水热门榜。手册中未完整给出的用户字段和订单样例，在练习脚本中标明了补充内容。

本次实验在 Windows 命令行下完成，使用项目目录内的便携软件，没有修改系统全局 PATH。手册中的 Linux 和 FinalShell 路线未在本次实验中执行。

### 提交与校验

上次实训保留匿名报告文件名，实验序号按模板留空。期末项目的两份文档已填写姓名、学号和班级。

数据库运行目录、软件安装包、密码、缓存和排版中间文件不在提交包中。根目录的 `SHA256SUMS.txt` 用于核对上次实训材料；期末项目的校验清单位于 `final-project/results/SHA256SUMS.txt`。
