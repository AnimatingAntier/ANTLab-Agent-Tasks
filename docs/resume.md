# 后续从这里继续

工作区：E:/AUniversityStudy/大创/Agent_work/基础；分支 codex/basic-assessment。不要回原题包开发或另造散乱目录。

## 当前实际状态

- 正式basic-main-v1已冻结并完成40首轮；1次正式重试另列。不要重新跑同一轮。
- 总请求57/64，开发16/16，显式重试2/8（含开发1次）。后续默认只做离线审计与复算，不为了回放发请求。
- 44项测试通过；独立代码审查的重要问题已修复。
- 主结果R0 4/8、R1 5/8、R2 4/8、K 1/8、改进3/8。改进没有整体提升。
- 逐例参考与语义核查由助手依原文整理，用户本人未核验；T01参考解释有显式假设。
- T06实际messages相同而输出不同；同题等价变体因锚点并列回退而顺序变化，不能声称普遍稳健。

## 后续顺序

1. 读reports/基础题实验报告.md、docs/本人核验清单.md、docs/decisions.md及git status；python main.py status确认调用数。旧report.md只是入口。
2. python main.py audit --manifest config/basic-main-v1.json --runs runs/main/basic-main-v1。
3. 用户按独立清单核验T01假设、8题标签、逐run语义、实际请求/失败、T06诊断、三项决定与声明。未核验字段保持待填写；修订前保存旧标签/结果并记录依据，不改原始日志、不冒写human。
4. 离线复算先输出.cache/user-review-score；补充用python results/scoring/build_report_supplement.py --output-dir .cache/user-review-supplement。完成核验与版本记录后再发布新的评价结果，不能用旧正式轮次伪装新探索。
5. 如需新算法实验，保存本轮不动，明确探索版本、新ID与新预算；不能在本轮T结果上调参再回填。
6. 进阶与基础需整合到同一最终GitHub仓库和一份报告；已选择公开Fork AnimatingAntier/ANTLab-Agent-Tasks，分支codex/basic-assessment；考核材料SHA见README。收集表未登记。最终本人声明及收集表内容由用户核验。新增进阶/评分修订后需重新确定最终SHA，不沿用旧提交版本。

## 运行与凭据

python main.py serve默认离线，浏览器127.0.0.1:8765。config/local.json不提交，已有凭据位于E:/MyApp/VibeShell/.env，仅读取DEEPSEEK_API_KEY；不要输出密钥。真实调用的旧授权上限不会因重启自动归零，程序以保留日志计数。

冻结代码基点b7274fd0894172e2cfa119a68411ebd6f9bb9743，UTC 2026-10-13 12:07:40。主流程文件受hash保护；报告、评价与独立诊断不属于生成代码。

## 本次材料补充

新增完整配对表、报告补充JSON和离线生成脚本，均在results/既有分类内。历史失败的状态/错误类型/耗时已留档，HTTP错误体与底层异常原因未保存，不能补造。原主结果、运行日志、标签与冻结代码保持原样。模型请求仍57次；新方法只列为后续建议，本次不执行。
