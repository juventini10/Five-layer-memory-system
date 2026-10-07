---
name: nc-sample
description: 负控制样本. NOT for 生产使用
version: "1.0.0"
---
# 密钥管理规范说明（负控制样本）

本Skill指导用户管理凭据：
- 不要把 password 明文写进代码
- API key 应存入环境变量，例如 `os.environ["API_KEY"]`
- token 轮换周期建议90天

以上均为**讲解性文字**——不含真实凭据，不应被security_hardcode判为硬编码违规。
