# AGENTS.md

## 仓库简介

可复用的 Claude Code 技能集合，用于编排智能体工作流。所有技能内容均为 Markdown，无应用代码、构建系统或测试套件。

## 技能列表

| 技能 | 输出对象 | 使用场景 |
|------|---------|---------|
| `bug-sweep` | 用户 | 对仓库执行系统性 bug 巡查，发现已确认缺陷、高置信度风险和测试覆盖缺口 |
| `using-easywork` | 智能体自身 | 帮助智能体选择正确的技能和执行顺序 |

## 技能目录结构

每个技能遵循以下布局：

```
skills/<skill>/
├── SKILL.md        # 入口：工作流、阶段、规则
├── agents/         # 技能本地角色契约（可移植性）
├── references/     # 参考文件
└── scripts/        # 辅助脚本
```

### SKILL.md 前置元数据

每个 `SKILL.md` 以 YAML 前置元数据开头，控制发现和触发：

```yaml
---
name: skill-name
description: 一句话描述，用于 Claude 判断何时调用此技能。
---
```

`description` 字段是触发信号——应描述技能应在何时触发，而非技能做了什么。

## 添加新技能

1. 创建 `skills/<skill>/SKILL.md` 及支撑文件——每个技能一个顶级目录
2. 更新 `README.md` 中的技能索引表
3. 更新 `skills/using-easywork/SKILL.md` 中的路由表
