# Skills Lab

可复用的 Claude Code 技能集合，用于编排智能体工作流。

## 安装

### 从 GitHub 安装

```
/plugin marketplace add https://github.com/Cai-ki/skills-lab
/plugin install easywork@skills-lab
```

### 从本地路径安装

```
/plugin marketplace add path\to\skills-lab
/plugin install easywork@skills-lab
```

安装后运行 `/plugin reload-plugins` 或重启 Claude Code。

## 仓库结构

```
skills/
├── bug-sweep/          # 仓库级 bug 巡查
└── using-easywork/     # 技能路由入口
```

## 技能索引

| 技能 | 用途 | 状态 |
|------|------|------|
| `bug-sweep` | 对仓库执行系统性 bug 巡查，发现已确认缺陷、高置信度风险和测试覆盖缺口 | 可用 |
| `using-easywork` | 帮助智能体选择正确的技能和执行顺序 | 可用 |

## 技能详情

### `bug-sweep`

对整个仓库执行系统性的 bug 巡查。通过并行代码审查发现已确认的缺陷和高置信度风险。

- 查找功能性 bug、行为回归、契约不匹配、缺失验证、错误处理、不安全假设
- 将代码划分为独立区域并行扫描
- 按严重程度分级（Critical > High > Medium > Low）
- 区分已确认问题与假设性风险

### `using-easywork`

技能路由入口。帮助智能体根据任务类型选择正确的技能，避免内联处理本应由专门技能完成的工作。

## 添加新技能

1. 创建 `skills/<skill>/SKILL.md` 及支撑文件
2. 更新本 README 的技能索引表
3. 更新 `skills/using-easywork/SKILL.md` 中的路由表
