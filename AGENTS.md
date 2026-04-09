# AGENTS.md

## 仓库简介

可复用的 Claude Code 技能集合，用于编排智能体工作流。所有技能内容均为 Markdown，无应用代码、构建系统或测试套件。

## 技能列表

| 技能 | 输出对象 | 使用场景 |
|------|---------|---------|
| `sweeping-bugs` | 用户 | 对仓库执行系统性 bug 巡查，发现已确认缺陷、高置信度风险和测试覆盖缺口 |
| `routing-easywork` | 智能体自身 | 帮助智能体根据任务类型选择正确的技能和执行顺序 |

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
3. 更新 `skills/routing-easywork/SKILL.md` 中的路由表

## 版本管理

- 版本号定义在 `.claude-plugin/plugin.json` 和 `.claude-plugin/marketplace.json` 中，两处必须保持一致。
- **每次提交必须修改版本号**：
  - 小改动（bug 修复、文档修正）：递增 patch 版本 `a.b.(c+1)`
  - 较大改动（新增功能、架构调整）：递增 minor 版本并重置 patch `a.(b+1).0`
  - 重大变更（不兼容的改动）：递增 major 版本并重置 minor 和 patch `(a+1).0.0`
