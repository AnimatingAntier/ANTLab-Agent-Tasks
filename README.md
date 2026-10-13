# 基础题 · 文档证据核验

本目录是用户指定的独立实现工作区。代码、数据、运行证据、评价和报告分开放置；原 ANTLab-Agent-Tasks 题包保持不变。

**当前状态：代码及离线链路已实现；正式实验尚未开始。** 已从页面发出 1 次 DeepSeek 开发请求，返回 HTTP 402（余额不足），失败原样留档。用户授权总上限 64 次，当前已尝试 1 次；没有成功模型输出，不能报告准确率提升。

## 目录

```text
基础/
  main.py               唯一日常命令入口
  app/                  Python 程序；static/ 为页面
  config/               示例配置、授权上限、后续冻结清单
  data/                 题包原始数据，保持字节不变
  reference/            原始要求与来源校验
  tests/                自动测试，合成响应只留在临时目录
  docs/                 计划、协议、阅读、决策、诊断和进度
  runs/                 原始记录：dev / main / variants / diagnostics
  results/              逐例评价与汇总；scoring/ 保存判分依据
  reports/              一份整合报告草案、声明、assets/ 截图
```

config/local.json 仅存本地服务配置，不提交；密钥从已有环境或 --env-file 加载，文件不复制进项目。.cache/、Python缓存被 Git 忽略。后续新增输出放在以上对应目录，不另建零散入口。

## 快速启动（不调用模型）

Python 3.10+、标准库，无需 pip 安装。实际验证：Windows、Python 3.13.5。

```powershell
Set-Location "E:\AUniversityStudy\大创\Agent_work\基础"
python main.py serve
```

浏览器打开 http://127.0.0.1:8765 。默认仅预览、保存输入、模拟和回放；页面“真实 API”禁用。先预览输入才能运行。两侧记录下拉框可并排查看同题基线与改进，回放不会重发请求。

```powershell
python -m unittest discover -s tests -v
python main.py status
python main.py run --case D01 --condition E --dry-run
python main.py robustness --case D01 --kind both --seed 17 --outdir runs/variants/D01-both-17
```

已有等价变体位于 runs/variants/D01-both-20261006；复现应使用新输出目录，避免覆盖事前预测。运行日志使用 UUID，终态记录不可覆盖。中断后留下 started，不能当作未发送自动重试。

## 真实调用与后续恢复

**以下 --paid / --allow-paid 命令会向模型服务发送请求，并可能产生费用。** 本地配置已选 DeepSeek deepseek-flash、非思考模式、temperature=0、max_tokens=512、JSON模式。当前 402 只验证到服务错误返回，尚未证明模型与参数能成功生成。参数依据及错误说明见 docs/api-notes.md。

余额恢复后先做开发联通，不直接跑评测。凭据可通过 ASSESSMENT_API_KEY 环境变量，或通过下面已有文件读取 DEEPSEEK_API_KEY；不会加载文件中其他服务的密钥。

```powershell
python main.py serve --config config/local.json --env-file "E:\MyApp\VibeShell\.env" --allow-paid
```

开发题至少核对 D01–D04 的 R0、K、improved（最多 16 次开发请求，含先前失败；不无限调参）。当前 1 次失败关联记录见 docs/resume.md。全部成功/失败均保留，正式题不用于调参。

开发稳定、完成关键判断核验并保存代码后，冻结正式轮次：

```powershell
python main.py freeze --config config/local.json --output config/basic-main-v1.json --max-calls 48
python main.py batch --manifest config/basic-main-v1.json --config config/local.json --dry-run
python main.py batch --manifest config/basic-main-v1.json --config config/local.json --env-file "E:\MyApp\VibeShell\.env" --paid
```

正式清单为 32 个基线 + 8 个 R0 改进，固定随机顺序、串行执行。48 为正式阶段最多40首轮+8重试；全项目共享64次硬上限（含开发与失败，started保守计1）。首次技术失败仍在主分母。401/402/403/429 等错误会停止当前批次。

中断后先审计，再续跑；--resume 只补没有记录的任务。人工决定需要重试时使用 --retry-of RUN_ID，产生新记录，不替换首轮：

```powershell
python main.py audit --manifest config/basic-main-v1.json --runs runs/main/basic-main-v1
python main.py batch --manifest config/basic-main-v1.json --config config/local.json --env-file "E:\MyApp\VibeShell\.env" --paid --resume
```

进程异常退出可能留下 .paid.lock / .batch.lock。先核实无对应进程、审计 started 记录，再人工移除确实失效的锁；程序不会猜测或自动重发。

## 离线复算

正式任务运行后，在 results/scoring/labels.json 建立独立参考，在 reviews.jsonl 逐条追加语义判断。推理程序不会读取它们。标注来源、依据和用户未核验状态必须保留。

```powershell
python main.py score --runs runs/main/basic-main-v1 --manifest config/basic-main-v1.json --output-dir results
```

输出 results/results.csv、basic-summary.json、basic-pairs.csv。答案正确、引用定位和语义支持分别记录；未知标签保持待核验。原始输出、usage来源、模型、run_id 和文件路径可追溯。重试另列；未完成批次汇总是 provisional，不能冒充正式结果。

## 完成与未完成

| 项目 | 状态 |
|---|---|
| 提示词、内容关联、真实请求代码、失败留档 | 已实现并离线测试 |
| 页面预览、输入一致性检查、回放与对比 | 已实现；真实开发请求到达服务但返回402 |
| 40任务清单、冻结、续跑、重试、审计、评分 | 已通过临时目录合成测试 |
| D01 ID/顺序等价变体 | 已执行，0模型调用，见 runs/variants |
| 开发题证据覆盖检查 | 已执行，非正式实验结论 |
| 开发成功联通、正式冻结、40主结果、评测标注 | 未完成，等待余额恢复 |
| 用户本人关键判断核验、最终整合、进阶、GitHub提交 | 未完成 |

后续助手先读 [docs/resume.md](docs/resume.md) 和 [docs/progress.md](docs/progress.md)。报告见 [reports/report.md](reports/report.md)，AI声明见 [reports/declaration.md](reports/declaration.md)。

## 来源与提交

复用 ANTLab 题包骨架，源码基点 b028d90f43f44585cf085a3f607516a94f485e88，数据 basic-context-v1.2。原文件与SHA256见 reference/source_manifest.json。本项目初始提交 a3d12d3 保存移入版本；`git diff a3d12d3 HEAD -- app tests` 可查看主要修改。

原 data 与 app/lexical.py 保持不变；主要新增内容在 ordering、运行记录、校验、评分、实验调度与页面。只有 Python 标准库依赖。未设置远程，未推送原题包仓库。本地 Git 作者使用 Codex，不冒用用户身份。

最终基础与进阶需整合到同一个 GitHub 仓库和一份报告；本目录当前仅基础部分。截止为北京时间 2026-10-16 23:59，最终SHA与链接由用户登记到题包收集表。
