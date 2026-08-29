# Zotero Local Desktop Organizer

一个面向本机、离线 AI 和本地资料库维护者的 Zotero 整理项目。它提供三部分协同能力：

1. 通过 Zotero Desktop 的本地 Connector 导入 BibTeX/RIS；整个过程只访问 `127.0.0.1`，不需要 Zotero Web API Key 或互联网。
2. 对关闭状态下的本地 `zotero.sqlite` 执行结构审计，输出可保存的 JSON 健康报告。
3. 提供一套可复现的离线批量整理工作流，用于建立收藏夹层级、补全元数据、归类父条目和登记已获授权的附件。

它适合希望把文献整理留在电脑本地、让本地 AI 处理 RIS/BibTeX、或需要对资料库进行离线维护和审计的用户。

## 项目结构

```text
zotero_local_connector.py      本地 Connector 导入器：BibTeX/RIS → 当前 Zotero 目标
zotero_sqlite_audit.py         关闭 Zotero 后的只读 SQLite 健康检查
examples/example.bib           可直接用于预演的 BibTeX 样例
examples/example.ris           可直接用于预演的 RIS 样例
docs/agent-runbook.md          本地 AI 的完整执行手册
legacy/controlled-offline-direct-write.md
                                离线批量整理的操作契约、验证与回退
```

## 5 分钟开始：本地导入题录

### 第一步：准备 Zotero

1. 打开 Zotero Desktop。
2. 在左侧选择目标资料库或目标收藏夹。
3. 保持 Zotero 打开；本项目会将题录交给 Zotero 自己的 Connector 导入。

### 第二步：运行检查

本项目仅依赖 Python 标准库。下载或克隆项目后，在 PowerShell 中运行：

```powershell
cd <项目下载目录>\zotero-sqlite-safety-audit
python .\zotero_local_connector.py status
python .\zotero_local_connector.py selected-target
```

第一条命令确认本机 Connector 可用；第二条命令显示当前会接收导入内容的资料库/收藏夹。若目标不对，回到 Zotero 左侧栏重新选择，再重复该命令。

### 第三步：预演导入

```powershell
# BibTeX 样例：只输出计划，不写入
python .\zotero_local_connector.py import --format bibtex --file .\examples\example.bib

# RIS 样例：只输出计划，不写入
python .\zotero_local_connector.py import --format ris --file .\examples\example.ris
```

预演会显示源文件、格式、字符数和当前目标收藏夹。确认目标正确后才执行：

```powershell
python .\zotero_local_connector.py import --format bibtex --file .\examples\example.bib --apply
```

导入完成后切回 Zotero，核对新条目的题名、作者、年份、DOI/URL 和收藏夹归属。实际使用时，把样例文件换成你的 RIS 或 BibTeX 导出文件即可。

## 本地 AI 的完整工作顺序

```text
启动 Zotero Desktop
  ↓
用户在界面选择目标收藏夹
  ↓
AI 运行 selected-target，复述目标供用户确认
  ↓
AI 运行 import（不带 --apply）并展示计划
  ↓
用户确认 → AI 以相同参数加 --apply
  ↓
AI 在 Zotero 中检查导入结果、补全缺失元数据、下载已授权 PDF
```

本地导入不要求 Key。若 AI 还需要创建新的收藏夹：先在 Zotero 界面用“新建收藏夹/新建子收藏夹”建立目标并选中它，再运行上述本地导入流程。这样每次导入的落点都由用户在界面上直观看到。

## 离线资料库审计

大规模整理前，或怀疑本地资料库状态异常时，可运行只读审计。先完全退出 Zotero，再创建完整数据目录备份，然后执行：

```powershell
python .\zotero_sqlite_audit.py --database 'D:\Zotero-article\zotero.sqlite'
```

报告包括数据库完整性、外键关系、收藏夹成员关系、活跃条目/收藏夹/附件计数，以及未同步对象 key 的复核清单。将输出保存为 JSON，作为整理前后的对照依据。

## 离线批量整理工作流

本项目同时保留本地批量维护的完整方法，适用于已有明确输入计划的场景：

```text
计划文件（条目、元数据、分类和附件）
  ↓
完整备份与只读基线审计
  ↓
dry-run：逐条输出拟建收藏夹、拟更新题录、拟归类条目和拟登记附件
  ↓
单批执行与完整性检查
  ↓
打开 Zotero 抽检 → 一次普通同步
```

详细的范围定义、幂等性、输入绑定、对象 key、验证矩阵和回退流程见 [受控离线操作契约](legacy/controlled-offline-direct-write.md)。这份文档可直接交给本地 AI，用于生成和审阅每一批的执行计划。

## 使用注意事项

- 本地导入时必须先确认当前选中的收藏夹；Connector 会将条目交给这个目标。
- BibTeX/RIS 是题录交换格式，不应包含受版权保护的论文正文或 PDF 内容。
- 离线审计时 Zotero 必须完全退出；数据目录备份应包含 `zotero.sqlite` 和 `storage`。
- 批量维护始终采用“小批次、预演、确认、验证、备份”的节奏；首次来源建议从 1–3 条记录开始。
- 已获授权的 PDF 应通过 Zotero 界面附到正确父条目；导入题录与附件获取是两个独立步骤。

## 与联网整理项目的关系

本仓库服务于本机 Connector、离线导入和本地维护；配套的 [Zotero Web API Organizer](https://github.com/HYC-1895/zotero-web-api-organizer) 适合需要跨设备同步、通过 API 创建收藏夹、为指定条目增加归属和由服务端生成对象 key 的自动整理任务。

## 参考资料

- [Zotero 数据目录、备份与恢复](https://www.zotero.org/support/zotero_data)
- [添加文献条目](https://www.zotero.org/support/adding_items_to_zotero)
- [高级设置与数据库完整性检查](https://www.zotero.org/support/preferences/advanced)

