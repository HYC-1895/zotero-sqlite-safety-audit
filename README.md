# Zotero SQLite Safety Audit

一个只读的 Zotero SQLite 健康检查工具，以及将旧式“直接改数据库”工作流迁移到安全方案的说明。

> 重要：这个项目**不会**修改 `zotero.sqlite`、同步缓存或附件目录。Zotero 官方明确不建议外部程序直接写数据库；本项目保留旧路线的诊断价值，而不复刻危险的写入行为。

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

## 不做什么

- 不生成或替换 Zotero 内部对象键；
- 不改写 `collections`、`collectionItems`、`syncCache` 或同步日志；
- 不直接移动本地附件目录；
- 不在 Zotero 正在运行时绕过数据库锁。

## 从旧式工具迁移

如果旧脚本曾通过 SQLite 创建收藏夹或归类条目：停止运行该脚本，先执行本项目的审计与完整备份，然后把后续整理改为 Zotero Web API。服务端会生成合法键，并处理同步版本与冲突。

## 给智能体的离线审计顺序

1. 完全退出 Zotero；若数据库被锁，停止而不是绕过锁。
2. 复制整个数据目录作为快照。示例机器的结构是 `D:\Zotero-article\zotero.sqlite` 与同目录的 `storage\`，但换机器时必须从 Zotero 设置中确认真实目录。
3. 只读运行审计工具，保存 JSON 报告。
4. 若 `database_integrity` 不是 `ok`、外键违规不为零、或存在孤立归属，停止后续自动化，改走官方支持或备份恢复。
5. 若只发现异常未同步对象 key，也不要按字符批量替换全库；先确认对象来源、同步状态和云端状态。
6. 日后所有新增或整理操作迁移到 Web API；这个仓库不提供直接 SQLite 写入命令。

完整的低风险复现手册见 [docs/agent-runbook.md](docs/agent-runbook.md)。旧路线的实现逻辑与失败原因归档在 [legacy/unsafe-workflow-archive.md](legacy/unsafe-workflow-archive.md)，它不可执行，不能作为生产方案。

## 官方资料

- [不要直接写 Zotero SQLite 数据库](https://www.zotero.org/support/dev/client_coding/direct_sqlite_database_access)
- [Web API 写入请求](https://www.zotero.org/support/dev/web_api/v3/write_requests)
- [数据库与备份](https://www.zotero.org/support/zotero_data)

