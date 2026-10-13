# 执行记录 — plan: docs/plan.md

## 路径与决定

- 2026-10-13 用户授权开始，并指定 `E:/AUniversityStudy/大创/Agent_work/基础`，强调目录清晰。
- Ruling: 以用户指定的空目录建立独立 Git 仓库，分支 `codex/basic-assessment`，不创建另一个工作树 — 满足明确的输出位置并保持原题包不变 — 代价是通过来源清单而非共享 Git 历史追踪上游。
- Ruling: 原计划的 starter 改为 app，配置集中 config，报告集中 reports，过程文档集中 docs；所有操作从 main.py 进入 — 减少重复目录与入口 — 代价是命令相对原题包改变，README 提供映射。
- Ruling: Windows 下用本文件持续记录任务与验证，替代依赖 shell/英文任务标题的技能记账脚本；保留公开进度 — 便于用户与后续助手恢复 — 代价是进度需人工维护。
- 本机 Git 未配置作者。后续本地提交使用 `Codex <codex@local.invalid>` 标记实际 AI 作者，不冒用用户身份；未配置远程仓库。

## 接口预检

| 关联任务 | 共同契约 | 检查决定 |
|---|---|---|
| 2 → 3 | prepare_messages/improve 只接收问题及本次段落 | 保留函数签名，runner 控制资料范围 |
| 3 → 4/5/6 | schema_version=2 运行记录 | 统一记录结构，不让人工评分回流模型 |
| 4/6 → 8 | 冻结 jobs、主结果分母与重试 | 40 个 job，按首次尝试计分；未知与失败保留 |
| 5 → 3 | 页面预览与实际请求一致 | 传入输入/配置 hash 校验；UI 默认开发/探索 |
| 6 → 9 | 冻结代码与离线变体 | 变体独立运行，不改写主实验或原始数据 |

## 当前状态

| 任务 | 当前状态 | 证据 |
|---|---|---|
| 1 实验约定与来源 | 完成 | reference/source_manifest.json |
| 2 提示词与组织 | 完成 | app/student.py、app/ordering.py |
| 3 运行与检查 | 完成 | runs/dev、tests/test_runtime.py |
| 4 评价 | 完成，本人核验待办 | results/scoring、results/results.csv |
| 5 页面 | 完成 | app/static、真实开发请求与回放 |
| 6 冻结调度 | 完成 | config/basic-main-v1.json |
| 7 开发真实请求 | 完成16次 | runs/dev、development-results.csv |
| 8 正式实验 | 完成40首轮+1重试 | runs/main/basic-main-v1、basic-audit.json |
| 9 诊断与变体 | 完成，负面结果保留 | runs/diagnostics、runs/variants |
| 10 交付材料 | 本地完成，本人/发布待办 | README、reports/report.md、docs/resume.md |

原题包没有现成自动测试。已复制原始数据与代码基点，后续从行为测试开始实现。

## 阶段验证

- Task 1: complete — 来源校验通过，阅读与实验协议已保存。原始数据和 reference 文件哈希一致。
- Task 2: complete — test_student 首轮4项失败，实现后5/5通过；身份重映射和跨段行为验证。
- Task 3: complete（离线）— runtime 9项和 provider 3项先失败再通过；全套17/17通过。真实API尚未调用。
- 验证记录：.cache/runtime-red.txt、provider-red.txt、runtime-green.txt（本地测试日志）；正式证据尚未生成。
- Task 4: complete（离线）— 6项评分用例先失败，模块实现后全套23/23通过。答案正确性与语义支持独立；重试不替换首轮，缺标签保留待核验。
- Task 5: complete（页面与API离线验收）— 5项HTTP测试通过；浏览器预览D01/E、保存输入、真实请求返回402，run_id=9dcb99b7-85c5-4c73-99c9-469c739badc2。成功模型输出待余额恢复。
- Task 6: complete（调度代码）— 6项批次测试通过，临时目录40任务、续跑、重试、漂移、停止条件；全套38/38通过。新增全局64次上限及串行锁。正式清单尚未冻结。
- Task 7: blocked by HTTP 402 — 用户授权DeepSeek最多64次，已尝试1次；依据官方错误码为余额不足。禁止重复自动请求。
- Task 9: partial — D01正文/ID等价变体完成，预测先于执行保存；正式结果诊断待主实验。

- Task 10: partial — 已写README、恢复入口、整合报告草案与统一声明；未伪造正式结果，剩余任务7/8及正式诊断待HTTP402解除。
- Task 6: Ruling: 统一命令采用app/scoring.py及main.py score，评分规则保留results/scoring；结果文件严格使用results/results.csv — 保持用户要求的清楚目录与题包交付位置 — 代价是与旧计划部分文件表名称不同，README为准。
- 修复实际Windows控制台编码故障：--help在cp1252失败，新增回归测试先失败，再将统一入口输出设为UTF-8。

## 最新验收（2026-10-13）

- 当前全套测试39/39通过。CLI帮助在cp1252环境回归通过；freeze → batch --dry-run → audit → score在.cache/cli-verification验证通过：40个预览、0个正式完成、五组分母均8且provisional。
- 原始data/reference与lexical文件哈希校验通过。仅已授权的一次真实请求，1/64；页面已切回默认离线模式，回放不增加调用。
- 真实失败的source_hashes记录的是当时开发代码，后续新增CLI/预算等造成变化属于冻结前开发；不回写历史日志。

## 独立审查与单轮修复

- Final review: fresh reviewer reviewed a3d12d3..2eea3d1，只读且无模型调用；没有Critical，发现两个Important及两项状态问题。
- Final: fixed 混用冻结版本 — test_resume_rejects_existing_primary_from_another_frozen_version、test_score_rejects_mixed_versions_before_publishing RED→GREEN，版本不一致时先拒绝续跑/评分。
- Final: fixed 分阶段预算未执行 — development/retry上限回归RED→GREEN，shared paid lock内计数，started保守计1，限额读取authorization。
- Final: Ruling: 将语义待核验却provisional=false升为Important并修复 — 防止把未完成评价读为已完成；代价是已判对答案但未核语义的汇总仍为临时。
- Final: Ruling: 协议的未授权/无API旧状态会误导后续执行，更新为实际授权及402记录 — 当前状态优先于旧草案措辞；代价是需以Git查看早期假设。
- 全套44/44通过；Minor未留待修项。审查未判断的真实兼容性/正式效果将由后续真实实验验证；未读取T答案；用户本人核验、进阶和GitHub发布仍按原范围待办。评审未运行全套测试，执行者已独立实跑44项。
- 2026-10-13 用户确认余额已处理，授权继续DeepSeek；继续原64次上限，无新增费用授权请求。

- Task 7: complete（助手开发核查）— 页面真实200已验证；开发16次保留全部记录，初版D01拒答促成通用计算提示修订。余额错误与传输错误原样保留，传输错误显式重试有retry_of。
- 测试隔离修复：开发16次额度用尽后3个provider替身用例受真实预算污染，先观察失败；对这些测试隔离预算计数边界，预算自身仍在临时目录真实测试，全套44/44重新通过。未改付费执行逻辑。
- 正式冻结前最后决定：使用deepseek-flash非思考模式、temperature=0、max_tokens=512、JSON输出；baseline/improved共用最终提示，改进只重排。尚未人工阅读T答案/正式输出。

## 本次最终进度

- Task 8: complete — basic-main-v1首轮40/40留档，39条API+格式成功，1条传输失败；1次正式显式重试成功且独立保存。审计无缺失、重复、未知job或版本漂移。
- Task 9: complete — T06实际输入诊断：两次messages完全相同但25%/20%不同；D01变体保持关联，T06并列回退导致顺序不变性失败，报告保留负面结果。均未追加模型调用。
- Task 10: complete（本地基础材料，本人核验待办）— 逐例41行、5组主汇总、8对配对、参考原句与语义判断、报告6栏目、E1–E7、恢复入口、AI声明齐备。评分来源标记assistant_source_review、reviewed_by_user=false。
- 主结果R0=4/8，R1=5/8，R2=4/8，K=1/8，改进=3/8。T04改善，T05首轮技术失败、T06错误输出造成两例退化；不宣称整体改善。
- 总请求57/64；开发16/16、显式重试2/8（开发1、正式1）；54条usage合计92421 Token。未进行额外裁判模型调用。
- 正式冻结以后仅增加记录、评分依据、诊断和文档，未修改受冻结保护的运行/评分代码。
- Final: Ruling: 独立仓库没有上游分叉或远程，按用户指定目录保留本地codex/basic-assessment分支 — 无需为不适用的合并/PR菜单打断用户 — 代价是最终GitHub目标与整合由后续用户决定。
- Final review未判断项的处置：真实兼容性已由成功开发/API记录验证；T参考答案在主请求结束后依据原文推导且留假设；发布/进阶/本人核验按范围待办；全套测试由执行者实跑，未以审查者未执行为通过依据。

- Final verification: 44/44 tests PASS; 40 actual messages/selected passages exactly equal saved preflight; frozen code/config/rubric hashes unchanged; offline re-score byte-identical; original source hashes PASS; git diff --check PASS.
