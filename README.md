# 基础题 · 文档证据核验

本目录是用户指定的独立工作区。**基础代码、40次主实验和报告已完成；评分依据由助手整理，待用户本人复核。** 原ANTLab-Agent-Tasks题包不变，当前未推送GitHub。

主结果：R0 **4/8**、R1 **5/8**、R2 **4/8**、K **1/8**、改进 **3/8**；改进没有整体提升。全项目共 **57/64** 次模型请求，含3次技术失败。先看[报告](reports/report.md)和[后续入口](docs/resume.md)。

## 清晰的目录

```text
基础/
  main.py               日常操作唯一入口
  app/                  Python代码；static/页面
  config/               示例、公开配置、授权与冻结清单
  data/                 原始题包数据，字节不变
  reference/            原要求与来源校验
  tests/                离线自动测试
  docs/                 计划、协议、阅读、决策、诊断、进度
  runs/                 原始记录：dev / main / variants / diagnostics
  results/              逐例CSV、汇总与配对；scoring/判分依据
  reports/              一份报告、声明；assets/截图
```

config/local.json及.env不提交；密钥不复制进项目。缓存统一.cache/并被Git忽略。正式结果在runs/main/basic-main-v1根下；其preflight/子目录仅为40条无API输入预览。

## 启动和查看（不产生模型费用）

Python3.10+，只用标准库，无需安装依赖。实际验证Windows/Python3.13.5。

```powershell
Set-Location "E:\AUniversityStudy\大创\Agent_work\基础"
python main.py serve
```

打开 http://127.0.0.1:8765 。页面可预览输入、保存dry记录、模拟和只读回放；默认禁用真实API。左右记录框可选同题基线与改进。切换/查看记录不会重新调用模型。

```powershell
python -m unittest discover -s tests -v
python main.py status
python main.py audit --manifest config/basic-main-v1.json --runs runs/main/basic-main-v1
python main.py score --runs runs/main/basic-main-v1 --manifest config/basic-main-v1.json --output-dir results
```

44项测试通过。审计应为40首轮完成、1首轮技术失败、1正式重试、0缺失/重复/版本漂移。离线score生成results/results.csv、basic-summary.json、basic-pairs.csv；原始日志不修改。

等价变体已有D01和T06两组，预测先于检查保存，均0模型调用。如需重复检查，用新目录：

```powershell
python main.py robustness --case D01 --kind both --seed 17 --outdir runs/variants/D01-both-17
```

D01保持内容顺序；T06由于并列锚点回退不保持顺序，局限已报告。

## 数据、判分和重要边界

- 首次失败留在各条件8题分母；重试独立UUID、retry_of，不替换主结果。
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
| 报告、阅读、三项决策、AI声明 | 已整理，待本人核验 |
| 进阶、最终GitHub整合/登记 | 未完成 |

原题包源码基点b028d90f43f44585cf085a3f607516a94f485e88，数据basic-context-v1.2；来源与SHA256见reference/source_manifest.json。初始提交a3d12d3保存移入基点；`git diff a3d12d3 HEAD -- app tests`查看主要改动。数据和app/lexical.py保留原字节，新增模块均有独立职责。

正式代码冻结基点b7274fd0894172e2cfa119a68411ebd6f9bb9743。本地Git作者为Codex，未冒用用户身份。基础与进阶最终须在同一GitHub仓库、一份整合报告中提交，截止北京时间2026-10-16 23:59；用户尚未指定远程，未推送或登记。
