# Zotero SQLite Safety Audit

一个可直接运行的 Zotero SQLite **只读健康检查工具**，配套记录一套真实可用的离线整理流程：建立收藏夹层级、补全题录、归类条目和登记已有 PDF 附件。

> 这不是把旧路线简单判定为“不能用”的项目。离线 SQLite 整理在固定 Zotero 版本、完全退出应用、先备份、范围明确且由维护者掌握数据模型的前提下，确实能够高效完成批量工作。本项目如实保留这条路线的工程步骤、优点和验证方法；同时也说明它为何不适合作为跨版本、跨机器、无人值守或直接面对同步服务的通用写入方案。

本仓库的可执行代码保持**只读**：它帮助你先确认离线库是否处于适合处理的状态。直接写入流程只作为受控维护方法文档化，不提供可对任意资料库直接执行的写入器。

## 它检查什么

- SQLite 完整性检查与外键检查；
- 孤立的收藏夹成员关系；
- 未同步收藏夹或条目中是否存在容易导致同步拒绝的无效键字符；
- 活跃（未删除）的条目、收藏夹、附件记录数量。

## 使用方法

1. 完全退出 Zotero，包括后台进程。
2. 先复制整个 Zotero 数据目录作为可恢复备份。
3. 指定数据库文件运行只读审计：

```powershell
python zotero_sqlite_audit.py --database 'X:\path\to\zotero.sqlite'
```

4. 保存 JSON 输出；只有在确认问题范围、拥有完整备份并遵循官方恢复流程时，才考虑下一步修复。

### 下载后最快可运行的检查

本项目仅依赖 Python 标准库。下载或克隆后，在 PowerShell 中运行：

```powershell
cd <项目下载目录>\zotero-sqlite-safety-audit
python --version
python .\zotero_sqlite_audit.py --database 'D:\Zotero-article\zotero.sqlite'
```

上例的目录是本机示例。换电脑时，先在 Zotero 中打开“设置 → 高级 → 显示数据目录”，然后把输出的真实 `zotero.sqlite` 路径填入命令。工具以 SQLite 只读模式打开数据库，不会生成、修改或删除文件。

## 不做什么

- 不生成或替换 Zotero 内部对象键；
- 不改写 `collections`、`collectionItems`、`syncCache` 或同步日志；
- 不直接移动本地附件目录；
- 不在 Zotero 正在运行时绕过数据库锁。

## 既有离线 SQLite 工作流：它做对了什么

一套成熟的旧式整理脚本通常不是“只插入一行 SQL”。它会先读取一份计划（例如 JSON），然后在 Zotero 完全退出时完成以下工作：

1. 为一个明确的批次建立顶层收藏夹和日期/主题子收藏夹；已存在时跳过，保证重复执行不会重复建树。
2. 通过 DOI、Crossref 或人工核验补全题名、作者、期刊、卷期页和摘要等题录字段。
3. 只把**父文献条目**加入对应收藏夹，避免把 PDF 子附件当作独立论文归类。
4. 检查重复记录，先输出保留/删除计划，再在明确范围内处理本批次未同步的重复项。
5. 对已经合法下载的 PDF 计算校验值、建立附件记录并放入 Zotero 管理的存储结构。
6. 提交前后运行完整性检查，并把每一次输入、输出和备份保留下来。

这些设计——计划文件、dry-run、幂等性、范围收窄、备份和回读——都是正确且值得继续使用的。更详细的受控流程见 [legacy/controlled-offline-direct-write.md](legacy/controlled-offline-direct-write.md)。

## 这条路线的适用边界

| 场景 | 离线 SQLite 流程 | Web API 流程 |
|---|---|---|
| 同一台已验证版本的电脑、一次性处理明确批次 | 可行，但必须完整备份与离线验证 | 可行，需网络与 API Key |
| 建立/归类收藏夹、补全题录 | 可行，但需自行掌握内部关系 | 推荐；服务端生成 key、处理版本 |
| 上传或同步 PDF 附件 | 本机可登记存储附件，但不等于云端上传 | 需官方多阶段上传协议 |
| 跨设备、长期自动化、多人协作 | 不适合做唯一写入通道 | 推荐 |
| Zotero 正在运行、版本不明或同步状态不明 | 不应使用 | 等正常同步后再用 |

真正的风险不是“SQLite 天生不可用”，而是外部工具必须与 Zotero 的内部对象键、版本、删除状态、附件与同步缓存保持一致；这些内部实现可能随版本变化，且服务端会额外校验。若无法验证这些条件，就不要把直接写入当作默认方案。

## 给智能体的离线审计顺序

1. 完全退出 Zotero；若数据库被锁，停止而不是绕过锁。
2. 复制整个数据目录作为快照。示例机器的结构是 `D:\Zotero-article\zotero.sqlite` 与同目录的 `storage\`，但换机器时必须从 Zotero 设置中确认真实目录。
3. 只读运行审计工具，保存 JSON 报告。
4. 若 `database_integrity` 不是 `ok`、外键违规不为零、或存在孤立归属，停止后续自动化，改走官方支持或备份恢复。
5. 若只发现异常未同步对象 key，也不要按字符批量替换全库；先确认对象来源、同步状态和云端状态。
6. 日后所有新增或整理操作迁移到 Web API；这个仓库不提供直接 SQLite 写入命令。

完整的低风险审计手册见 [docs/agent-runbook.md](docs/agent-runbook.md)。历史实现与此次同步问题的边界说明见 [legacy/unsafe-workflow-archive.md](legacy/unsafe-workflow-archive.md)；受控离线操作的完整检查表见 [legacy/controlled-offline-direct-write.md](legacy/controlled-offline-direct-write.md)。

## 官方资料

- [不要直接写 Zotero SQLite 数据库](https://www.zotero.org/support/dev/client_coding/direct_sqlite_database_access)
- [Web API 写入请求](https://www.zotero.org/support/dev/web_api/v3/write_requests)
- [数据库与备份](https://www.zotero.org/support/zotero_data)

