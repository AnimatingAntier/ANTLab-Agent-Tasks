# 诊断与边界

## 当前真实故障：开发请求HTTP402

页面预览输入与实际运行messages一致，已发送请求，服务返回402；格式 absent、引用 absent，原因位于API层，尚未进入模型内容评价。官方错误码将402定义为余额不足。记录：[9dcb99b7](../runs/dev/9dcb99b7-85c5-4c73-99c9-469c739badc2.json)。动作：停止后续模型调用，等待账户可用；不通过改提示词、换正式题或连续重试处理此错误。

## 开发阶段覆盖检查（事后整理，非主实验诊断）

早先阅读开发题已知道K存在遗漏，以下是可复查的输入检查，不冒称未知预测。核查两种可能路径：必要材料在固定K阶段缺失，或材料在后续消息构造阶段丢失。

结果保存于 [development-coverage.json](../runs/diagnostics/development-coverage.json)。D01/D03/D04的K少一个公开参考所需段落；actual messages的passages与K清单相同。因此这三例缺失发生在固定选段，不能归咎于本次prepare_messages丢段。D02公开参考为“证据不足”，没有必要引用ID；空参考列表不能用于宣称覆盖完美。

这不证明模型在K下必然答错，也不等同正式8题结果诊断。正式主请求之后仍需从实际结果选一个疑点，检查竞争解释及剩余未知。

复算：读取 data/dev_answers.json 的 evidence_ids，对每个开发题调用 app.runner.prepare(id,'K','baseline')，比较 original 与 json.loads(messages[-1]['content'])['passages']；不要把该诊断导入推理路径。
