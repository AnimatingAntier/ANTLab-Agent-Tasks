# 后续从这里继续

工作区：E:/AUniversityStudy/大创/Agent_work/基础；分支 codex/basic-assessment。不要回原题包开发，不创建第二套散落目录。

1. 查看 git status、docs/progress.md、config/authorization.json；运行 python main.py status。当前真实尝试1/64，全部在开发阶段，HTTP402。
2. 等用户确认DeepSeek余额可用。已授权最多64次，不必重新索取同一预算，也不要打印密钥。配置 config/local.json；凭据路径 E:/MyApp/VibeShell/.env，字段 DEEPSEEK_API_KEY。
3. 先在页面重做开发题D01/E联通。先前失败run_id为9dcb99b7-85c5-4c73-99c9-469c739badc2；新尝试要保留失败并注明关联。再次402立即停止。
4. 在剩余开发预算内覆盖D01–D04 R0/K/improved，检查JSON、引用、计算和输入。只有开发题可用于调整。阅读 docs/plan.md 任务7。
5. 全套测试与Git保存后正式冻结；按README运行40任务、审计。当前没有basic-main-v1正式清单，也没有主实验请求，不能把离线preflight清单当正式冻结。
6. 主实验结束后才独立推导T01–T08标签和逐例语义核查，不让标签进入推理。保存判断来源，用户未亲自确认不得写human。
7. score、配对表、正式结果诊断、报告六个栏目、E1–E7索引、决策与声明；清楚标注未核验项。基础与未来进阶在同一最终仓库整合。

已有证据：
- runs/dev/e50a4843-9299-4a6e-9b98-354eec26547e.json：页面dry输入。
- runs/dev/9dcb99b7-85c5-4c73-99c9-469c739badc2.json：页面真实HTTP402。
- runs/variants/D01-both-20261006/：先保存预测后执行的0调用等价变体。
- runs/diagnostics/development-coverage.json：开发参考证据与K可见范围检查。

没有模型输出之前，不补填正确率、改进收益或正式诊断。总耗时不等同TTFT或Prefill，也不能反推GPU型号。
