# AGENTS.md

## 仓库简介

可复用的 Claude Code 技能和规则集合，用于编排智能体工作流。技能内容为 Markdown，无应用代码、构建系统或测试套件。

## 技能列表

| 技能 | 输出对象 | 使用场景 |
|------|---------|---------|
| `sweeping-bugs` | 用户 | 对仓库执行系统性 bug 巡查，发现已确认缺陷、高置信度风险和测试覆盖缺口 |
| `developing-go` | 智能体自身 | 涉及 Go 代码分析时使用——包括理解代码、调试、bug 定位、重构、代码审查、依赖分析、安全审计等，指导 gopls MCP/LSP、go doc、repomix 工具组合的高效使用 |
| `routing-easywork` | 智能体自身 | 帮助智能体根据任务类型选择正确的技能和执行顺序 |

## 规则列表

| 规则文件 | 内容 |
|---------|------|
| `rules/subagent-rules.md` | 子智能体使用时机、模型选择、中断恢复 |
| `rules/output-style.md` | 输出规范、需求复述、工作摘要、诚实原则 |
| `rules/work-style.md` | 临时文件清理、代码声明基于事实、实现质量、持续性与自主性、长任务执行 |
| `rules/skill-authoring.md` | 技能编写规范：简洁、描述第三人称、自由度、渐进式披露、命名约定、反模式 |

## 仓库结构

```
skills/
├── sweeping-bugs/SKILL.md       # 仓库级 bug 巡查
├── developing-go/SKILL.md       # Go 项目工具使用指南
└── routing-easywork/SKILL.md    # 技能路由入口
rules/
├── subagent-rules.md            # 子智能体规则
├── output-style.md              # 输出规范
├── work-style.md                # 工作规范
└── skill-authoring.md           # 技能编写规范
```

## SKILL.md 前置元数据

每个 `SKILL.md` 以 YAML 前置元数据开头，控制发现和触发：

```yaml
---
name: skill-name
description: 一句话描述，用于 Claude 判断何时调用此技能。
---
```

`description` 字段是触发信号——应描述技能应在何时触发，而非技能做了什么。详见 `rules/skill-authoring.md`。

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
