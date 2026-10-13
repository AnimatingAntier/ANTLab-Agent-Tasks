# 基础题 · 文档证据核验实验

本目录是基础题的独立实现工作区。原题包保留在 ANTLab-Agent-Tasks，不在原仓库开发。

## 目录

```text
基础/
  main.py             统一命令入口（实施中）
  app/                程序代码；static/ 为页面
  config/             示例配置、冻结清单；local.json 不提交
  data/               题包原始数据，不修改
  reference/          原始要求与来源校验清单
  tests/              自动测试
  docs/               计划、协议、阅读、决策与进度
  runs/               原始运行证据：dev、main、variants、diagnostics
  results/            逐例评价、配对表、scoring 人工依据
  reports/            报告与 AI 声明
```

当前实施进度见 [docs/progress.md](docs/progress.md)，详细任务见 [docs/plan.md](docs/plan.md)。可用命令将随实现更新，不把未来命令当成已完成能力。

## 来源

复用 ANTLab 题包，源码基点 `b028d90f43f44585cf085a3f607516a94f485e88`，数据版本 `basic-context-v1.2`。原始路径及 SHA256 见 [reference/source_manifest.json](reference/source_manifest.json)。本地 Git 首次提交保存移入后的原始骨架，后续提交为实际修改。

基础题需 40 个正式任务；进阶不在本目录本轮实施范围。真实模型配置和预算尚未确定，目前无正式实测结果。
