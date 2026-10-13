# 基础题实施计划（Basic Assessment Implementation Plan）

> 2026-10-13 路径修订：用户指定在 Agent_work/基础 独立实施；最终路径及命令以本目录 README 和 docs/progress.md 为准，原题包仓库只读。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 默认由当前助手顺序执行；用户若另行选择委派，再使用 superpowers:subagent-driven-development。本文件是后续执行依据，不表示任何程序或真实实验已经完成。

**Goal:** 完成基础题的真实请求链、40 个主实验任务、逐例评价、配对比较、一次诊断、一次离线等价变体和三项决策记录，并交付可离线复查的基础部分材料。

**Architecture:** 继续扩展题包的 Python 标准库骨架。基线逐字保留输入段落及顺序；主要改进根据当前问题和段落内容关联主体记录与补页，把相关证据相邻前置，同时保留全部可见原文。请求、运行记录、自动格式检查、人工语义复核和汇总分别处理，所有正式结果从原始记录复算。

**Tech Stack:** Python 3.10+、标准库 unittest/http.server/urllib/json/csv/hashlib、原生 HTML/CSS/JavaScript、Git。当前机器已确认 Python 3.13.5；这不代替后续在 README 中声明实际验证的版本。

**Spec:** [基础题](../reference/01_考核题目.md)、[阅读材料](../reference/02_阅读材料.md)、[基础提交要求](../reference/03_提交要求.md)、[最终提交格式](../reference/05_提交与报告格式.md)。题包要求优先于本计划的实现建议；发生冲突时先记录，再修订计划。

## Global Constraints

- 原题：“用D01–D04调试和选择方案，记录冻结时的代码、数据与配置版本。”
- 原题：“对T01–T08各执行R0、R1、R2、K，共32次基线请求；在R0上执行你的改进，共8次。”
- 原题：“统一模型、提示词、生成参数和判分口径；无法统一的差异写明。”
- 原题：“`prepare_messages`及`improve`只能读取问题与本次可见段落，不能按题号、已知答案、其他条件或固定ID生成结果。”
- 原题：“开发答案不得进入正式模型输入。”
- 原题：“首次技术失败、格式错误和无答案均保留在分母；另列技术成功后的结果。”
- 原题：“不要把引用ID存在当成语义支持，也不要用另一个模型作唯一裁判。”
- 原题：“至少做一次不调用模型的段落顺序或ID重映射检查：先预测，再确认你的方法依然按内容工作。”
- 默认接口只重排或选择原段落，不改写 `id/source/text`；本计划主改进保留所有可见段落。
- `data/`、`app/lexical.py`、原始题目及校验文件保持为题包基点；新增实验材料另存。
- 不把本计划中的预测当成实际结果，不冒称用户已经核验、作出判断或批准费用；没有事前记录的内容明确标为事后整理。
- 记录北京时间与 UTC 的对应关系；提交截止为北京时间 2026-10-16 23:59。本计划只覆盖基础题，不代表“基础＋进阶”整套考核完成。

## Review Focus

1. **输入隔离：** `runner.prepare` 当前按整题七段验证改进结果，可能让越过本次可见范围的段落通过；任务 3 的测试必须拒绝从 K 之外引入段落。
2. **跨段与等价性：** 补页只出现批次号、输入被打乱或 ID 被替换时，仍应按内容关联；任务 2、9 覆盖。不要假定所有项目名恰好两个汉字。
3. **响应分层：** HTTP 成功、服务商 JSON 合法、模型输出 JSON 合法是三件事；任务 3 覆盖缺字段、错误类型、无内容及响应格式错误。
4. **失败与重复调用：** 超时、进程中断、人工重试不能覆盖第一次尝试，也不能在续跑时自动重复已发请求；任务 3、6 覆盖。
5. **判分与拒答：** 相同数值来自错误批次、仅部分引用支持、K 漏证据后的合理拒答，都必须分别呈现；任务 4 覆盖，不能靠空引用或全拒答获得虚假的满分。

---

## 1. 当前状态与后续启动方式

- 计划创建于 2026-10-13；检查时分支为 `main`，题包基点为 `b028d90f43f44585cf085a3f607516a94f485e88`，创建本计划前工作区干净。
- 数据版本：`basic-context-v1.2`；题包声明的 `cases.json` SHA256 为 `c37cda40ada89a18630dd7be098672f7e942e6f57e6199fe1aa2d6046e2b4961`。执行前仍须实际核算。
- `prepare_messages` 尚未实现，`improve` 为恒等映射；尚未为本项目运行真实模型实验。
- 目前已阅读题目、骨架、开发答案和开发题内容，核对过开发题 K 的证据缺失；没有人工解答 T01–T08 或进行正式模型调参。继续接触评测数据时追加记录，不宣称真正盲测。
- 默认继续使用当前本地仓库；最终 GitHub 目标由用户指定。不要自行覆盖 remote、向原题包仓库推送，或代填收集表。
- 后续收到“按计划开始”时，先读本文件和 Spec，检查 `git status`，从第一个未完成任务继续；若已有产物，先核验再勾选，不重新跑已存在的付费实验。
- 当前请求仅建立计划。后续默认顺序执行，每个阶段记录实际命令、结果路径和下一步；使用 Git 保存真实阶段，不补造提交或决策时间。

### 执行前尚缺的信息

| 信息 | 什么时候需要 | 处理方式 |
|---|---|---|
| 实际模型、服务协议、Endpoint | 首次真实 API 前 | 用户提供本地配置；优先兼容现有 Chat Completions 接口 |
| API 凭据 | 首次真实 API 前 | 本机环境变量 `ASSESSMENT_API_KEY`，不写入代码、报告或对话示例 |
| 调用及费用预算 | 首次真实 API 前 | 建议 40 主请求＋最多 16 开发请求＋最多 8 次人工触发重试，总上限建议 64；这是预算建议，尚非费用授权 |
| 用户自己的 GitHub 仓库 | 最终推送前 | 可先完成本地代码和证据，目标未明确时不推送 |
| 用户对关键判断的核验 | 决策记录与最终声明 | 助手先给出可检查证据，用户未核验则明确记为未核验 |

缺少模型和预算时可完成任务 1–6 的离线部分及开发题变体；真实调用只在已有明确授权和可用配置范围内执行，不重复索要同一项已给出的授权。

## 2. 方案、假设与评价边界

### 已选择的计划默认方案

| 方案 | 收益与代价 | 本计划用途 |
|---|---|---|
| 原顺序全文 | 无选段遗漏，可能存在干扰和顺序敏感性 | R0/R1/R2 固定基线 |
| 题包词法前两段 | 输入少，可能漏掉跨段证据 | K 固定对照，不修改算法或条件清单 |
| 关联证据相邻前置，保留全文 | 不增加模型调用或删除资料，需要检验关联规则能否泛化 | 唯一主要改进 |

**待验证主假设 H1：** 在相同模型、提示词和七段原文下，按内容关联并前置主体记录与补页，可减少跨段计算或规则选择中的证据遗漏。没有提升、出现退化或基线天花板均须报告。

**竞争解释 H2：** 结果差异来自模型随机性或服务变化，或者只是一般相关性排序带来的变化，尚不足以说明“关联补页”机制有效。主实验只比较整个组织方法；仅凭这 8 题不能证明某个机制或总体显著性。

**K 的独立疑点：** 部分失败可能在生成前就已缺失必要证据。正式结果出来后优先检查实际 messages 是否覆盖必要原句，再考虑模型没有使用证据、输出截断或判分错误。

**代价预期：** 主改进保留全文、仍只调用一次，不预设 Token 或延迟下降；记录原始段落集合、输入字符数、可得 usage、客户端完整 API 请求耗时和调用数。

**主指标：** 每条件 8 题的任务答案正确数/8；辅助报告格式成功、引用定位、逐主张支持、可回答覆盖及失败类型。另报首次技术成功后的条件结果，不能替代主分母。

**判断“保留/修改/停止”：** 先看逐题净变化和有依据的完成情况，再看实现负担与代价；不预设一定提升。0 净变化时报告天花板或无收益，不能通过删除困难题、只保留成功样例或事后换指标制造提升。

## 3. 文件与接口规划

以下未存在的文件都是后续待创建项，不能把文件表当成已实现清单。

| 路径 | 操作 | 职责 |
|---|---|---|
| `.gitignore` | 新增 | 忽略本地配置、凭据、缓存和临时文件；允许根目录 `runs/` 进入提交 |
| `app/student.py` | 修改 | 统一提示词；`prepare_messages(question, passages) -> list[dict]`；`improve(question, passages) -> list[dict]` |
| `app/ordering.py` | 新增 | `order_passages(question: str, passages: list[dict]) -> list[dict]`，纯函数、无文件或网络依赖 |
| `app/output_checks.py` | 新增 | `parse_output(response: dict \| str \| None) -> dict`；`check_citations(citations: list[str], passages: list[dict]) -> dict` |
| `app/run_records.py` | 新增 | `public_config(config: dict) -> dict`；运行记录的创建、终态写入与读取 |
| `app/runner.py` | 修改 | 保持 `prepare` 和 `execute` 的兼容入口；验证可见范围；加入日志元信息与输出检查 |
| `app/provider.py` | 修改 | 保留默认协议和显式付费开关；规范错误状态；保留成功响应原文 |
| `app/experiment.py` | 新增 | `freeze/run/audit` 命令；冻结配置、调度 40 个任务、续跑与完整性检查 |
| `app/robustness.py` | 新增 | 离线重排和 ID 映射，保存输入、映射、事前预测与实际结果 |
| `app/server.py`、`index.html` | 修改 | 输入预览、实际运行、单条证据查看与已保存结果对照 |
| `app/export_runs.py` | 原工具保留 | 原始运行索引；必要时兼容新增字段，语义判分另由 `score.py` 完成 |
| `tests/test_*.py` | 新增 | 有意义的内容、隔离、失败留痕、汇总和请求链测试 |
| `config/basic-public.json` | 新增 | 不含 Endpoint/凭据的有效模型和生成参数 |
| `config/basic-main-v1.json` | 新增 | 正式冻结清单、代码/数据/配置哈希、40 个计划任务、预算与顺序 |
| `runs/dev/`、`main/basic-main-v1/`、`diagnostics/`、`variants/`、`exploratory/` | 新增 | 按用途存放运行证据，文件名采用 UUID，不用后续重试覆盖首轮 |
| `results/scoring/rubric.md`、`score.py` | 新增 | 人工判分口径与离线复算入口 |
| `results/scoring/labels.json`、`reviews.jsonl` | 新增 | 独立参考判断与逐运行复核；只允许评价端读取 |
| `results/results.csv`、`basic-summary.json`、`basic-pairs.csv` | 生成 | 全部逐次记录、条件汇总与 R0 配对结果 |
| `docs/reading.md`、`protocol.md`、`diagnosis.md` | 新增 | 阅读依据、实验预注册、诊断证据 |
| `README.md`、`reports/report.md`、`docs/decisions.md`、`reports/declaration.md` | 新增或更新 | 运行入口、基础报告、真实决策和统一声明；后续进阶复用同一报告 |

### 运行记录契约

保留原骨架字段，新增字段集中于记录层，不传入模型：

- 身份：`schema_version=2`、`run_id`、`experiment_id`、`case_id`、`split`、`condition`、`variant`、`purpose`、`attempt_index`、`retry_of`、`is_primary`、`utc`。
- 输入：`question`、`original_passages`、`selected_passages`（含完整 id/source/text）、`messages`、`input_sha256`、`input_characters`。
- 版本：`config`（公开配置）、`config_sha256`、`data_sha256`、`dataset_version`、`source_hashes`；覆盖新增助手模块，不能只散列 student.py。
- 输出：原始响应文本 `response_raw`、解析后 `response`、`parsed_output`、`api_status`、`format_status`、`locator_status`、`unknown_citations`。
- 语义：自动过程没有真正做语义检查时，`support_status=not_checked`、`judgment_source=unverified`；人工评价保存在独立 reviews 文件，界面明确标注来源。
- 代价：`elapsed_seconds`、`preparation_ms`、`usage`、`usage_source`、`call_count`、`run_kind`。`elapsed_seconds` 从发起 API 请求计到读取完整响应，不冒称浏览器端到端、首 Token 或服务端 Prefill/Decode 耗时。
- 类别：真实 API 为 `live_api`；预览为 `dry_run`；假响应/回放为 `offline_replay`；不调用模型的变体为 `local_rule`。保留原 `mode` 便于兼容。
- 原始文件以一次尝试为单位。允许初始 `started` 更新为同一尝试的终态，但终态不覆盖；重试建立新 run_id 并关联旧记录。

### 评价字段与特殊情况

- `format_status`：`valid / invalid / absent`；严格检查答案为非空字符串、引用为字符串数组。主结果不通过隐式再调用或自动修复伪装格式成功；如另做容错解析，结果单列。
- `locator_status`：非空且全部引用来自 `selected_passages` 为 `valid`；未知引用为 `invalid`；空引用为 `absent`。定位不等于支持。
- `labels.json` 按题号存 `answer_type`、`expected_answer`、`reference_passages`、`reason`、`provenance`、`reviewed_by_user`；正式标签标为自行核对，不能冒称评委金标准。
- `reviews.jsonl` 每行按 run_id 存 `task_correct`、`semantic_support`、`evidence_coverage`、`abstention_reasonable`、原句/计算依据和核验来源；修订另记，不无痕覆盖。
- 数值答案按事前约定进行单位和表示规范化，使用 Decimal 精确比较或明确的题目舍入规则，不事后放宽容差；不让“答案包含某个数字”代替完整判定。
- D02 参考 evidence_ids 为空，不要求模型也必须空引用；按题意核对“证据不足”的检查来源。
- K 缺必要证据后的合理拒答分别记录为输入约束下的合理行为和任务覆盖下降；对于完整资料可回答的题，不把该拒答计为完整任务答对。完整资料本就不足的题，正确拒答可计为答案正确。
- 暂未复核的结果保持 `pending/not_checked`；汇总不能把未知当成正确，也不能悄悄删除未知行。最终报告披露剩余未核验项。

## 4. 逐任务执行清单

所有命令均从仓库根目录执行，命令中使用正斜杠兼容当前 PowerShell。下列新命令的参数是任务要求，须先实现才能运行；未创建的路径不表示现有能力。

### 任务 1：建立实验约定、来源和记录入口

**Files:** 新增 `.gitignore`、`docs/reading.md`、`docs/protocol.md`、`decisions.md`、`declaration.md`；保留题包原文。  
**Interfaces:** 输出后续任务共同遵守的主假设、指标、冻结范围、预算和判分约定。

- [ ] 检查工作区和题包校验值，记录源码基点、数据版本、实际 Python 版本。开发隔离由执行时的工作区规则决定，不能重置用户已有改动。
- [ ] 阅读 Lost in the Middle 第 2、4、5 节与结论，以及 ALCE 的答案/引用评价定义；记录准确原文位置、访问日期、原实验与本题条件差异。基础选 ALCE 作为公开系统/评价框架；最终整合报告还需第二项系统比较时再补 Semantic Reader。
- [ ] 在 protocol 中记录本计划 H1/H2、预计不变/可能变化的指标、任务分母、停止条件和预算；将尚未发生的结果全部写为预测。
- [ ] 建立三项决策条目：实验设置、诊断优先级、改进保留/修改/停止。此时只填写已有依据和真实 AI 影响，后续结果栏保持明确的待执行状态。
- [ ] 添加根目录忽略规则，保持根目录 `runs/` 可提交。用 `git check-ignore` 检查本地配置被忽略、正式运行文件不被忽略；注意原 `基础/.gitignore` 已忽略 `基础/runs/`。
- [ ] 将 AI 辅助分析与用户尚未核验的事实写入声明草稿，不代写“本人已核验”。为本任务建立一次真实文档提交。

**验收：** 后续执行者能从 protocol 确定何时冻结、如何计分和停止；没有伪造 API 结果或决策时间。

### 任务 2：实现统一提示词和内容驱动的全文重排

**Files:** 修改 `app/student.py`；新增 `ordering.py`、`tests/test_messages.py`、`test_ordering.py`。  
**Interfaces:** 保留原 `prepare_messages(question, passages)` 与 `improve(question, passages)`；后者只调用 `order_passages`。

- [ ] 先写行为测试：`test_baseline_preserves_supplied_order` 逐字比较包含 ID、source、text 的段落顺序；R0/R1/R2 不被统一排序；题目元数据和答案文件不进入消息。
- [ ] 写跨段测试：使用自造项目、版本、日期和批次，补页不重复项目名称；预期主体与补页相邻前置，七段原文集合完全不变。
- [ ] 写负例与变体测试：另一个批次的数值不能使其成为目标补页；替换所有 ID 和来源标识、打乱输入后，内容关联不变；证据不足和模糊主体保持所有段落，不生成答案。
- [ ] 运行 `python -m unittest discover -s tests -p 'test_messages.py' -v` 和对应 ordering 测试，确认新增行为尚未实现时失败；仅因路径或导入配置错误失败不算有效红灯。
- [ ] 实现固定系统提示：仅依当前资料、核对范围/口径、允许跨段关联、证据不足不猜测、只返回约定 JSON。按传入顺序序列化完整原文；正文中的“只输出数值”约束作用于 answer 字段，不删除 citations。
- [ ] 实现纯函数重排：从问题识别范围和任务条件，按内容匹配主体，再沿正文批次标识关联补页。先匹配范围、再任务条件、再一般词法相关性；所有并列和无法识别的回退规则明确记录。运行时不读取磁盘、答案、题号或其他条件。
- [ ] 关联规则扫描完整正文，不依赖固定第几段/第几页/首句位置；不把某个批次值写死。不强行给模糊样例建立唯一关联，保留全文并记录局限。
- [ ] 运行上述测试及全套离线测试，通过后记录一个实现提交。若开发题导致规则修改，更新 protocol，正式评测前统一冻结。

**验收：** 任意合法输入都能产生消息；基线条件顺序不被破坏；改进只组织本次材料，无额外模型调用。

### 任务 3：补齐输出检查、可见范围验证和失败留痕

**Files:** 修改 `runner.py`、`provider.py`；新增 `output_checks.py`、`run_records.py`、`tests/test_output_checks.py`、`test_run_records.py`。  
**Interfaces:** `parse_output` 返回原始内容及格式状态；`check_citations` 返回定位状态及未知 ID；`execute` 新增可选关键字 `metadata=None`，原调用兼容；CLI 新增 `--outdir`。

记录层统一使用 `start_record(record: dict, outdir: Path) -> Path` 和 `finish_record(path: Path, updates: dict) -> dict`：前者以独占创建生成 started 文件，后者原子更新同一尝试并拒绝覆盖已终态文件。解析结果键固定为 `content_raw/answer/citations/format_status/error_code`；定位结果键固定为 `locator_status/unknown_citations`。

- [ ] 写输出测试：合法 JSON；代码围栏包裹；缺 answer；非字符串引用；服务商返回 JSON 但 choices 为空；单个未知引用；空引用。断言原始内容保留且分类正确，不能把 citation 合法直接标 supported。
- [ ] 写隔离测试：通过替身 improve 返回整题中存在、但本次 K 输入没有的段落，必须在调用 provider 前拒绝；修改原文和重复段落同样拒绝。
- [ ] 写留痕测试：HTTP 错误、超时、缺少凭据、prepare 异常仍产生适当错误记录；两次同任务调用产生不同 run_id；重试带 retry_of；记录和服务响应中不包含配置 Endpoint 或凭据。
- [ ] 按上述顺序运行新增测试确认失败，再实现格式解析、对 selected_passages 的引用验证，以及原题可见范围验证。验证对象必须是 `original`，不能只用整题 `by_id`。
- [ ] API 成功时保留服务商响应原文和解析对象；失败记录状态码、错误类别和可安全保留的诊断信息。禁止原样记录 Authorization、凭据或可能包含凭据的完整请求对象。
- [ ] 在 API 发送前持久化 started 记录，正常或可捕获异常时写终态；进程被杀后留下 started，续跑检查将其标为结果未知而非重新自动请求。
- [ ] 用公开配置替换日志中完整 config：去掉 Endpoint 和凭据，保留模型、参数、超时及服务商标识；哈希针对公开配置。记录 source_hashes 覆盖新增运行代码。
- [ ] 明确计时点；预览和模拟不伪装真实耗时或 usage。provider 内部不自动重试，所有重试由上层显式建立新记录。
- [ ] 运行离线测试，以 fake provider 和临时目录验证 dry/mock/错误路径。任何假响应都只作为测试证据，不能计入 40 次正式结果；通过后提交。

**验收：** API、格式、定位、语义状态分开；原始输入和失败可追踪；正式日志可安全提交。

### 任务 4：建立独立判分与配对复算

**Files:** 新增 `results/scoring/rubric.md`、`score.py`、`labels.json`、`reviews.jsonl`、`tests/test_scoring.py`。  
**Interfaces:** `score_record(record: dict, label: dict | None, review: dict | None) -> dict`；`summarize(rows: list[dict], manifest: dict) -> dict`；CLI 参数见步骤。

- [ ] 先写 rubric，确定数值/百分数/配置名/证据不足的判分、引用支持和覆盖标准。此时 labels 仅建立开发参考；正式标签在冻结后独立核对，不回流推理代码。
- [ ] 写测试：D01 风格“数值相同但错批次”必须能表示答案正确、语义不支持；K 漏证据的合理拒答与完整任务成功分开；格式错误/技术失败仍在分母；未知人工判断保持 pending。
- [ ] 写汇总测试：构造每条件 8 个主任务、其中 1 个失败、其余 7 个正确以及若干重试；主结果必须是 7/8，重试不得替换首轮。缺失记录被审计报告，不把 7 条记录自动当成 7 题满分。
- [ ] 运行 `python -m unittest discover -s tests -p 'test_scoring.py' -v` 确认有效失败，再实现独立评价及规范化；推理入口不导入这个模块。
- [ ] score CLI 实现 `--runs`、`--manifest`、`--labels`、`--reviews`、`--output-dir`，生成 `results.csv`、`basic-summary.json`、`basic-pairs.csv`。每行保留原始文件路径、run_id、首次/重试、模型输出、理由、API 状态、usage 来源。
- [ ] 五组条件各分母 8；R0 对 improved 的 8 个配对逐项显示错→对、对→错、不变、失败和待复核。耗时区分成功与失败；不将 40 行当成 40 个独立问题，不默认做显著性宣称。
- [ ] 在临时目录用合成记录复算并核对预期，再运行全套离线测试和提交。真实结果出现前不生成冒充实测的正式汇总表。

**验收：** 同一份原始日志、标签和复核文件能确定性复算；任何数字能追到具体运行与原文依据。

### 任务 5：补充最小可检查页面

**Files:** 修改 `server.py`、`index.html`；新增 `tests/test_server.py`。  
**Interfaces:** 保留 `/api/cases`、`POST /api/run`；新增 `POST /api/preview`、`GET /api/runs` 和 `GET /api/runs/<run_id>`。运行列表只返回配置好的结果目录内记录，不能接受任意文件路径。

- [ ] 先写 API 测试：预览不调用 provider；paid 在未启用时拒绝；未知题目/条件明确失败；读取结果只允许合法 run_id；返回字段不含凭据/Endpoint。
- [ ] preview 请求包含 case_id/condition/variant，返回规范问题、可见段落、组织后顺序、messages、公开配置及 input_sha256；不返回参考答案或评价标签。
- [ ] run 保留 `case_id/condition/variant/mode`，新版页面另传 `question/visible_passages/input_sha256/public_config_sha256`；逐项与后端规范输入及配置核对，发生变化则拒绝并要求重新预览。兼容旧请求时由后端解析规范材料，日志注明未提供预览校验。Endpoint 和凭据仍由服务端本地配置管理。
- [ ] 页面展示真实问题、原文、配置摘要、运行类型、状态、答案和引用来源；引用点击定位到当前材料块。用 textContent 等安全方式呈现材料，避免将正文当 HTML 执行。
- [ ] 从已保存记录选择同题 R0 与改进并排比较；人工核查与系统自动状态分开。查看、切换或回放不自动重新发付费请求。
- [ ] 默认页面执行进入 dev/exploratory 记录，不进入主实验；正式 40 任务统一由任务 6 的清单执行，避免页面点击产生重复主结果。
- [ ] 运行 API 测试，再启动本地服务，用 dry/mock 手动核查预览、运行、失败和对照。保存操作步骤；真实请求的 UI 验收留到任务 7。通过后提交。

**验收：** 页面能把所见输入送往后端，并从一个结果追到同一个 run_id 的真实材料和日志；预览/模拟标识清楚。

### 任务 6：实现冻结清单、正式调度和续跑审计

**Files:** 新增 `app/experiment.py`、`tests/test_experiment.py`；完善 runner 元信息；创建公开配置及清单时遵循下述契约。  
**Interfaces:** `build_jobs(cases: list[dict], seed: int) -> list[dict]` 输出 40 个唯一 job；`freeze_manifest(config_path: Path, output_path: Path) -> dict`；`audit_manifest(manifest_path: Path, runs_dir: Path) -> dict`。

- [ ] 写清单测试：8×4 基线＋8×1 改进恰好 40 个唯一任务，均为 evaluation；无 E；improved 仅 R0。seed 默认 `20261006`，顺序写入清单。
- [ ] 写续跑测试：已终态任务被跳过；started/结果未知不自动重发；同 job 第二次运行只能作为显式重试；冻结后修改一个运行模块或参数会在发送前阻止正式执行。
- [ ] 运行对应测试确认失败，然后实现 freeze/run/audit。把 40 个任务统一排序并固定，适度交错基线与改进，避免把两种方案固定分成不同服务时段；记录真实调用顺序，串行执行。
- [ ] 冻结内容包括：代码基点与运行模块哈希、数据哈希、提示词版本、公开模型配置、rubric 哈希、完整 jobs、主轮次、预算上限、失败分母、停止条件及 dev 接触说明。
- [ ] source_hashes 使用明确文件清单，覆盖主请求实际导入的运行模块和计分脚本；报告、人工 reviews、独立诊断和不被主流程导入的 robustness 脚本不纳入推理代码冻结。主流程新增依赖必须更新清单并建立新实验版本，不能借排除文档规则漏掉运行代码。
- [ ] run 支持 `--manifest`、`--config`、`--paid`、`--dry-run`、`--resume`；默认不联网。dry-run 输出到 dev/preflight，不占正式 job；live 执行前校验冻结文件与本地配置的公开部分。
- [ ] 主实验禁止自动重试。显式重试使用 `--retry-of RUN_ID`，写入新 UUID，`is_primary=false`；不能把第一次失败从结果集移除。
- [ ] 达到预算上限、遇到冻结内容漂移、持续认证/配额故障时停止后续付费调用，保存剩余未执行任务；审计输出 expected/completed/failed/pending/interrupted/retries，不假装完成 40 次。
- [ ] 在测试临时目录用 fake provider 跑完整 40 任务，验证不会联网、预算准确、续跑不重复；mock 证据留在测试临时目录。通过后提交。

**验收：** 主实验身份固定、失败保留、恢复可控；一个审计命令能指出缺失、重复和版本漂移。

### 任务 7：开发集真实联通、用户核验与正式冻结

**Files:** 更新 protocol、decisions、declaration；生成 `runs/dev/`、`config/basic-public.json`、`config/basic-main-v1.json`。

- [ ] 收集尚缺的真实模型、兼容参数和费用上限；优先读取用户已经提供的本地配置，禁止打印凭据。先用提供方当前官方文档确认参数，不猜测支持 temperature/max_tokens 的情况。
- [ ] 用 D01/E 执行 dry-run，人工检查实际 messages、段落 ID、原文和顺序；确认无答案泄漏。正确参数示例：

```powershell
python main.py run --case D01 --condition E --dry-run --config config/local.json --outdir runs/dev
```

- [ ] 在已授权预算内先做一次真实开发请求，再覆盖 D01–D04 的全文、关键 K 缺证据和改进情况。开发请求上限以用户授权为准，不无限调参。
- [ ] 至少一次真实请求经页面发起，核对页面、后端 messages、原始响应和 run_id 一致；保存证据。用户未亲自查看时只记录助手核查。
- [ ] 依据开发题修正真正的格式、关联或计算问题，运行受影响测试；记录每个关键改动及其理由。若无法在开发集可靠建立关联，说明退化策略，保留可解释且内容驱动的改进，不装成已提升。
- [ ] 完成 rubric、H1/H2 与停止条件，给用户核验关键设定和实际样例的入口；未获本人核验的判断继续如实标注。正式轮次前不再改变方案。
- [ ] 执行所有离线测试并保存代码提交；生成正式清单：

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
python main.py freeze --config config/local.json --output config/basic-main-v1.json
python main.py batch --manifest config/basic-main-v1.json --config config/local.json --dry-run
```

**验收：** 实际模型已联通、预算已明确、代码/数据/配置/判分已冻结，正式清单预览为 40 任务。预览日志不算正式输出。

### 任务 8：执行正式 40 任务并逐题核对

**Files:** 生成 `runs/main/basic-main-v1/`；填写正式 labels/reviews；生成根目录 results 文件。

- [ ] 复核授权余额与冻结清单，执行唯一主轮次：

```powershell
python main.py batch --manifest config/basic-main-v1.json --config config/local.json --paid
python main.py audit --manifest config/basic-main-v1.json --runs runs/main/basic-main-v1
```

- [ ] 中断时先 audit 再 `--resume`；timeout 或 started 记录不因“不知道是否完成”而自动重发。所有技术失败、格式错误、空回答保留。
- [ ] 冻结后独立核对 T01–T08 的完整原文，建立答案、必要原句、计算与条件依据；评估文件与运行逻辑隔离。如参考标注有误，保存修订理由并对全部条件统一重算。
- [ ] 逐条核查实际可见范围与引用原文，记录正确答案来自错误证据、部分支持、合理拒答和未核验情况；不把模型自评作为唯一依据。
- [ ] 执行离线复算：

```powershell
python main.py score --runs runs/main/basic-main-v1 --manifest config/basic-main-v1.json --labels results/scoring/labels.json --reviews results/scoring/reviews.jsonl --output-dir results
```

- [ ] 人工抽查一个汇总数和一个配对变化，沿 run_id 追到原始输入、响应与评价。主结果按每条件 8 题；成功后的结果另表，不能替换主表。
- [ ] 任何根据正式结果做的代码/参数修改使用新版本与 `runs/exploratory/`；不得覆盖 v1、回填旧日志或混合计算主结果。保存原始结果提交。

**验收：** 40 个计划任务均有可解释状态，首轮与重试分开；不能执行的部分明确标未完成。主汇总、配对表与原始证据一致。

### 任务 9：完成一次区分原因的诊断和一次离线等价变体

**Files:** 新增 `app/robustness.py`；生成 `runs/diagnostics/`、`runs/variants/`、`docs/diagnosis.md`；复用 ordering 的变体测试。

- [ ] 从正式结果选一个有价值的疑点，先记录两个仍与已知证据相容的解释及各自预测。若已有源码证据排除某原因，不把它当竞争解释凑数；事后构想须明说。
- [ ] 首选离线证据覆盖检查：对该题必要事实逐项核查 original、selected、messages、引用；区分检索缺失、输入构造丢失、生成未使用或评价错误。保存涉及的 run_id、原句、检查步骤及剩余未知。
- [ ] 若没有失败，检查“全文已足够/任务太短导致天花板”等疑点，使用输入与逐例支持核查，不伪造失败或必然的位置效应。额外模型检查只在预算允许时单独记为 diagnostic。
- [ ] 等价变体在运行前保存输入、预测及映射：选至少一题，建议一个开发题及一个评测题；做 ID 重映射和固定种子重排，原文事实不变。
- [ ] robustness CLI 实现 `--case`、`--kind ids|order|both`、`--seed`、`--outdir`。只调用组织函数和消息构造，不调用 provider；记录 `run_kind=local_rule`、`call_count=0`。
- [ ] 映射还原后比较关键证据关联、内容顺序及集合；并列不相关段落允许等价差异，但不能只验证“七段都还在”就宣称算法稳健。无可靠关联的回退行为必须按事前规则解释。
- [ ] 记录变体检验覆盖的是组织/输入组件，不是完整模型回答稳定性。将发现与是否保留改进写回 decisions；完成本阶段提交。

**验收：** 一项诊断有实际检查证据；至少一次符合题意的不调用模型变体有事前预测、映射、结果与解释。

### 任务 10：基础报告、复现与交付核查

**Files:** 更新 `README.md`、`reports/report.md`、`docs/decisions.md`、`reports/declaration.md`；生成 `results/basic-audit.json`（来自 audit）；保留本计划勾选状态。

- [ ] README 写明环境、题包来源、本人改动、启动/测试/离线复算命令、付费命令及完成/未完成状态；清楚区分原题包与实现入口，不改写原题要求。
- [ ] 将基础内容写入唯一整合 report：阅读命题、实验设计、请求链、逐题结果与失败、诊断/变体、保留或修改决定及后续问题。此时进阶仍标未完成，不另造第二份“最终整合报告”。
- [ ] 每张表注明输入文件、复算命令和 run_id 范围；至少三个关键结论链接到实际证据。说明 8 题小样本、公开评测接触、计时范围和未排除解释。
- [ ] 完成统一五项 AI 声明：真实 API 模型名称、可选 Token 量级、AI 工具与用途、本人核验判断及方法、未实现/未运行/未验证内容。助手不能代用户声称“已理解全部模块”。
- [ ] 形成基础 E1–E7 索引；基础记录可供未来进阶引用，区分同一证据的不同作用，不重复宣称新成果。
- [ ] 最后一次运行离线测试、audit、score，并从干净环境或明确记录的当前环境按 README 验证启动及回放；这些验证不产生付费请求。
- [ ] 执行 `git diff --check`；检查将提交文件中无密钥、Endpoint、本地配置和私密信息，`runs/` 的正式记录确实被跟踪。密钥扫描只输出文件与问题类型，不把疑似密钥值回显。
- [ ] 保存真实提交，并向用户提供基础完成情况、证据入口、剩余未核验事项。GitHub 推送和表单登记遵循用户给定目标及已有授权；不要把本计划完成等同整套考核已经提交。

**验收：** 能离线追溯一个数字、一条请求和一项关键决定；基础材料齐全且边界诚实。

## 5. 总验收与暂停后恢复

| 阶段 | 任务 | 可交付成果 | 当前状态 |
|---|---|---|---|
| A | 1–4 | 阅读/实验约定、内容组织、日志、判分及离线测试 | 待执行 |
| B | 5–6 | 可检查页面、40 任务调度/冻结/审计 | 待执行 |
| C | 7 | 开发集真实联通、正式冻结 | 待模型与预算并待执行 |
| D | 8 | 40 主任务状态、逐例核查与配对结果 | 待执行 |
| E | 9–10 | 诊断、变体、报告与复现 | 待执行 |

- [ ] **基础代码完成：** 请求、证据、状态、记录闭环与离线测试通过。
- [ ] **基础实验完成：** 40 个主任务实际执行情况可查，失败/重试保留；缺失主任务就不勾选此项。
- [ ] **基础评价完成：** 逐例表、配对表、诊断、变体和三项决定均有依据；人工未核验部分单列。
- [ ] **基础交付完成：** README、整合报告基础章节、声明、来源和证据索引可离线复查。

每次续接先检查这里的状态及真实产物，再读取最近的 decisions 条目。对已冻结或已付费执行的阶段，优先审计与回放，不能为了“继续”而重新建立一轮同名主实验。

## 6. 计划自检

本节只记录计划审查，不代表实施验收。

- 已逐项覆盖题目的阅读、请求链、40 次比较、逐题核查、诊断、改进、离线变体、三项决定和提交要求。
- 已将首次/重试、未知结果、K 缺证据、D02 空参考引用、跨段关联与输入隔离分配给具体任务和测试。
- 新增模块、CLI 参数和记录字段均在本计划定义；仍待执行的用户信息集中列出，不以虚构默认模型或价格补齐。
- 主改进与基线共用提示词与模型；主实验前冻结，正式结果不回流调参；未执行输出均不填为成功。
- 文档自检方式：检查计划链接、任务和验收映射、命令参数一致性及 Git diff；不为计划文件新增无意义的软件测试。
