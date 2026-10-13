# API配置依据与当前故障

核查日期：2026-10-13。用户明确授权 DeepSeek，整个基础题最多64次模型请求。

- 依据 [DeepSeek官方Chat Completions文档](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)，选择模型标识 deepseek-flash，thinking.type=disabled，temperature=0，max_tokens=512，response_format.type=json_object。系统提示已要求JSON。stream=false。请求最长等待90秒，无自动重试。
- [官方错误码](https://api-docs.deepseek.com/zh-cn/quick_start/error_codes/)定义HTTP402为余额不足。
- 真实开发记录 9dcb99b7-85c5-4c73-99c9-469c739badc2 返回402，耗时约0.541秒，call_count=1，usage不可得，未产生模型答案。这是服务错误返回的证据；不能把它当作已验证参数兼容或成功模型执行。
- 保留状态码与安全错误类别，不保留可能包含私人内容的服务错误页面；成功时会保存原始响应全文。记录中无Endpoint或凭据。
- 密钥仅从用户指定的本地.env读取所选字段并放入进程环境；原文件不复制、不改动。用户未授权更换其他服务，因此没有尝试Gemini。
