# ANTLab · Agent方向考核作品

本仓库提交方向为 **Agent**，当前完成 **基础题**。工作分支为 **codex/basic-assessment**；进阶尚未完成，本人核验仍待进行。

根目录按提交要求提供[报告](report.md)、[决定](decisions.md)、[声明](declaration.md)入口；正文及附件仍按原分类维护，避免重复版本。

本目录是用户指定的独立工作区。**基础代码、40次主实验和报告已完成；评分依据由助手整理，待用户本人复核。** 原ANTLab-Agent-Tasks题包不变，发布目标为上方公开Fork的考核分支。

主结果：R0 **4/8**、R1 **5/8**、R2 **4/8**、K **1/8**、改进 **3/8**；改进没有整体提升。全项目共 **57/64** 次模型请求，含3次技术失败。先看[报告正文](reports/基础题实验报告.md)、[本人核验清单](docs/本人核验清单.md)和[后续入口](docs/resume.md)。report.md只作导航，正文只维护一份。

## 提交定位

- 所选方向：**Agent**；当前完成基础题，进阶尚未完成。
- 最终分支（本次基础题提交）：**codex/basic-assessment**。
- 考核材料 commit SHA：**64da400b09dbd42b119b622e4b4b4cc1ac378358**（[固定版本](https://github.com/AnimatingAntier/ANTLab-Agent-Tasks/tree/64da400b09dbd42b119b622e4b4b4cc1ac378358)）。
- 项目链接：[AnimatingAntier/ANTLab-Agent-Tasks](https://github.com/AnimatingAntier/ANTLab-Agent-Tasks)，为Shiina413/ANTLab-Agent-Tasks的公开Fork。
- 本人核验清单：[待本人完成](docs/本人核验清单.md)；收集表尚未提交。
- 此SHA固定已通过独立检出验证的代码、数据、报告和记录。之后的发布登记提交仅更新README和发布状态，实验结果与冻结代码不变。进阶或本人核验产生修订后，应重新确定并登记新的最终SHA。

考核材料源于独立工作区，保留真实开发Git历史；Fork原main分支保留原题包。源码基点、数据校验值及查看改动的命令见文末。当前发布不表示基础与进阶的全部要求均已验收。

## 清晰的目录

```text
基础/
  main.py               日常操作唯一入口
  app/                  Python代码；static/页面
  config/               示例、公开配置、授权与冻结清单
  data/                 原始题包数据，字节不变
  reference/            原要求与来源校验
  tests/                离线自动测试
  docs/                 计划、协议、阅读、决策、诊断、进度、本人核验
  runs/                 原始记录：dev / main / variants / diagnostics
  results/              原主结果、完整配对、离线补充；scoring/规则与复算
  reports/              一份报告、声明；assets/截图
```

config/local.json及.env不提交；密钥不复制进项目。缓存统一.cache/并被Git忽略。正式结果在runs/main/basic-main-v1根下；其preflight/子目录仅为40条无API输入预览。

## 启动和查看（不产生模型费用）

Python3.10+，只用标准库，无需安装依赖。实际验证Windows/Python3.13.5。

```powershell
git clone --branch codex/basic-assessment https://github.com/AnimatingAntier/ANTLab-Agent-Tasks.git
Set-Location ANTLab-Agent-Tasks
python main.py serve
```

打开 http://127.0.0.1:8765 。页面可预览输入、保存dry记录、模拟和只读回放；默认禁用真实API。左右记录框可选同题基线与改进。切换/查看记录不会重新调用模型。

```powershell
python -m unittest discover -s tests -v
python main.py status
python main.py audit --manifest config/basic-main-v1.json --runs runs/main/basic-main-v1
python main.py score --runs runs/main/basic-main-v1 --manifest config/basic-main-v1.json --output-dir results
python results/scoring/build_report_supplement.py
```

44项测试通过。审计应为40首轮完成、1首轮技术失败、1正式重试、0缺失/重复/版本漂移。离线score生成results/results.csv、basic-summary.json、basic-pairs.csv；原始日志不修改。补充脚本只读取现有记录，生成basic-pairs-detailed.csv和report-supplement.json，不导入provider、不读取凭据、不调用网络；其事后统计定义与T01敏感性场景不改变冻结主评分。

等价变体已有D01和T06两组，预测先于检查保存，均0模型调用。如需重复检查，用新目录：

```powershell
python main.py robustness --case D01 --kind both --seed 17 --outdir runs/variants/D01-both-17
```

D01保持内容顺序；T06由于并列锚点回退不保持顺序，局限已报告。

## 数据、判分和重要边界

- 首次失败留在各条件8题分母；重试独立UUID、retry_of，不替换主结果。
- 成功响应原文已保存；失败仅保留状态、HTTP码或异常类型与耗时。HTTP错误体/底层异常原因未完整保存，无法补回；不能声称所有原始错误详情齐全。
- 完整配对表分开列输入参考覆盖、引用参考覆盖与语义支持。T05覆盖不适用，T01参考解释及敏感性分析待本人核验。
- API成功、JSON格式、引用ID定位、答案正确和语义支持分别记录。K合理拒答可以有语义支持，却未完成完整任务。
- labels.json包含原句、推导与标注来源；reviews.jsonl逐run_id保存单一结论的语义判断。用户复核修订应追加理由和历史，不冒写已人工确认。T01有显式参考解释假设。
- T06基线与改进messages实际相同而答案不同，因此该例退化不能归因于重排。
- 全文顺序比较只是8题配对观察；没有证明统计显著性、内部机制或GPU/TTFT。
- 原始日志与评分分开，推理入口不读取标签。冻结代码、数据、配置、规则发生变化会拒绝正式执行；旧版本记录也不能混入。

## 真实调用：已完成，不要重复主实验

用户授权DeepSeek最多64次。实际已用57次，其中开发16/16、显式重试2/8（开发1、正式1）。开发额度已满，后续默认离线复核。扩大开发预算或新一轮实验需要明确新范围，不能将现有日志清空来重置额度。

当前本地config/local.json选deepseek-flash非思考、temperature=0、max_tokens=512、JSON输出、90秒超时；公开部分见config/basic-public.json。原凭据文件路径在docs/resume.md，仅按需读取DEEPSEEK_API_KEY字段。

以下是**本轮已执行命令的复现说明，含付费命令，勿为了查看结果重跑**：

```powershell
python main.py freeze --config config/local.json --output config/basic-main-v1.json --max-calls 48
python main.py batch --manifest config/basic-main-v1.json --config config/local.json --dry-run
python main.py batch --manifest config/basic-main-v1.json --config config/local.json --env-file "E:\MyApp\VibeShell\.env" --paid
```

冻结清单已经存在，程序拒绝覆盖。主批次已完成，默认拒绝重复；--resume仅补没有记录的任务，started不自动重发。显式重试通过--retry-of RUN_ID另存。401/402/403/429停止批次；无自动重试。全局64、开发16、重试8在共享锁内强制检查。

若进程被杀留下.paid.lock/.batch.lock，先确认无对应进程并审计started记录，再人工移除确实失效的锁。不能因结果未知就自动重发。

从新克隆真实复现时，需自行建立不提交的local.json并提供凭据；不要复制别人的私人Endpoint。配置依据见docs/api-notes.md。新版本使用新实验ID并保留旧轮次；T题结果后的改动标为探索。

## 完成状态与交付

| 项目 | 状态 |
|---|---|
| 前后端真实链路、内容组织、日志、测试 | 完成 |
| 冻结、40首轮、1正式重试、逐例/配对表 | 完成，失败保留 |
| 正式输入诊断、两次等价变体 | 完成，负面结果与回退局限已披露 |
| 报告、阅读、三项决策、AI声明 | 已补充，待本人核验，详见独立清单 |
| 离线配对/覆盖/敏感性与失败证据说明 | 已整理；0新增调用，历史错误详情无法追回 |
| GitHub考核材料 | 发布到本页所列公开Fork与分支 |
| 进阶、本人核验、收集表登记 | 未完成 |

原题包源码基点b028d90f43f44585cf085a3f607516a94f485e88，数据basic-context-v1.2；来源与SHA256见reference/source_manifest.json。初始提交a3d12d3保存移入基点；`git diff a3d12d3 HEAD -- app tests`查看主要改动。数据和app/lexical.py保留原字节，新增模块均有独立职责。

正式代码冻结基点b7274fd0894172e2cfa119a68411ebd6f9bb9743。本地Git作者为Codex，未冒用用户身份。基础与进阶最终须在同一GitHub仓库、一份整合报告中提交，截止北京时间2026-10-16 23:59；已按群通知选择公开Fork及上方考核分支；GitHub上传与收集表登记是两件事，收集表仍待本人提交。
