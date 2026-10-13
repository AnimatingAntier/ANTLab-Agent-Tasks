# 诊断记录

## 正式结果：T06同输入不同输出

主实验结束后发现基线25%、改进20%，两者均引用主体P873502与补页P721388。先保存[检查方案](../runs/diagnostics/T06-input-check-plan.json)，再核对实际记录。方案是已见结果后的诊断假设，不冒称实验开始前的预测。

检查原始段落、组织后段落、实际messages和引用，必要事实与规则逐字保留：60任务，8超时、7格式不合法，两类均计技术失败。因此(8+7)/60=25%。配置、系统提示、正文集合均一致。

进一步发现两条完整messages与输入hash也完全相同。主体和压力组的锚点评分同为(3,21)，组织函数按冻结规则回退保留输入；所以T06根本没有改变顺序。不能把20%归咎于本次重排漏证据、改原文或改参数。单次配对仍无法区分模型/服务随机性、数值执行波动等剩余因素，也不能反推模型具体内部计算路径。

证据：[T06-input-check.json](../runs/diagnostics/T06-input-check.json)，基线4e8e207e…、改进77d12b21…；[八题输入变化](../runs/diagnostics/paired-input-comparison.json)。共6题真正改变顺序，T06/T08没有改变。

## 等价变体

D01的ID+顺序变体保持正文集合、正文顺序、前两段关联。T06变体只保持集合，顺序和前缀变化；原因是并列锚点回退依赖输入顺序。这在事前预测的条件分支内，却也揭示实用局限，不算全方法通过稳健性考核。两次检查均先保存预测、0模型调用，不能据此证明生成回答稳定。[变体目录](../runs/variants/)

## 开发故障与覆盖检查（历史）

开发请求9dcb99b7…返回402，按官方文档属于余额不足；停止后用户确认处理，后续成功。83bc354d…发生URLError，保留首次失败；只读模型列表查询200后显式重试f1b39eae…成功。模型列表GET不属于生成请求，未传送题目内容。

开发覆盖检查属于事后整理：[development-coverage.json](../runs/diagnostics/development-coverage.json)。D01/D03/D04的K缺一个公开参考所需段落；actual messages保持K清单，缺失发生在固定选段阶段。D02没有GPU信息，空参考ID不代表覆盖满分。

复算覆盖：读取data/dev_answers.json的evidence_ids，对开发题调用app.runner.prepare(id,'K','baseline')，比较original与json.loads(messages[-1]['content'])['passages']。不把开发诊断规则导入推理。

## 失败留档范围补充（2026-10-13事后核查）

402只保存HTTP状态和错误码；两条URLError只保存异常类型与完整请求耗时，未保存HTTP错误响应体或底层reason。因此能复核失败发生及首轮/重试关系，不能复原详细故障，也不能仅凭URLError判断DNS、TLS、连接或服务端原因。失败详情清单见[离线补充](../results/report-supplement.json)的failure_evidence。后续版本可增加脱敏错误详情；本轮不改冻结代码、不回写原始日志、不追加调用。
