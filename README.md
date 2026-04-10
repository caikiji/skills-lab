# Skills Lab

可复用的 Claude Code 技能和规则集合，用于编排智能体工作流。

## 安装

### 从 GitHub 安装

```
/plugin marketplace add https://github.com/Cai-ki/skills-lab
/plugin install easywork@skills-lab
```

### 从本地路径安装

```
/plugin marketplace add path/to/skills-lab
/plugin install easywork@skills-lab
```

安装后运行 `/plugin reload-plugins` 或重启 Claude Code。

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

## 技能索引

| 技能 | 用途 | 状态 |
|------|------|------|
| `sweeping-bugs` | 对仓库执行系统性 bug 巡查，发现已确认缺陷、高置信度风险和测试覆盖缺口 | 可用 |
| `developing-go` | 在 Go 项目中指导 gopls MCP/LSP、go doc、repomix 工具组合的高效使用 | 可用 |
| `routing-easywork` | 帮助智能体根据任务类型选择正确的技能和执行顺序 | 可用 |

## 规则索引

| 规则 | 内容 |
|------|------|
| `subagent-rules` | 子智能体使用时机、模型选择（默认 haiku）、中断恢复 |
| `output-style` | 输出客观务实、需求复述、工作摘要、诚实原则 |
| `work-style` | 临时文件清理、代码声明基于事实、实现质量、持续性与自主性、长任务执行 |
| `skill-authoring` | 技能编写规范：简洁、描述第三人称、自由度匹配、渐进式披露、命名约定 |

## 添加新技能

1. 创建 `skills/<skill>/SKILL.md` 及支撑文件
2. 更新本 README 的技能索引表
3. 更新 `skills/routing-easywork/SKILL.md` 中的路由表
