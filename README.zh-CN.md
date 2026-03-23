# Skills Lab

[English README](./README.md)

这个仓库存放可复用的本地 agent skill 及其配套文档。

## 安装

### 从 GitHub 安装（任意机器）

```
/plugin marketplace add https://github.com/Cai-ki/skills-lab
/plugin install easywork@skills-lab
```

### 从本地路径安装（已经 clone）

```bash
git submodule update --init --recursive
```

```
/plugin marketplace add path\to\skills-lab
/plugin install easywork@skills-lab
```

安装后，运行 `/plugin reload-plugins`，或者重启 Claude Code。
全部 19 个 skill 会自动加载，不需要额外单独安装 superpowers。

## 仓库结构

- `agents/`：多个 skill 共享的子 agent 角色契约
- `skills/context-pack/`：skill 本体及其可复用参考资料
- `skills/batch-refactor/`：skill 本体及其验证场景
- `skills/deepresearch/`：skill 本体及其 references、agents、scripts
- `skills/log-query/`：面向大体量本地日志的自然语言分析 skill，采用分层文本过滤
- `skills/using-easywork/`：用于在核心 skill 之间做选择和路由的入口 skill
- `superpowers/`：git 子模块，提供通用开发流程 skill

## Skill 索引

| Skill | 用途 | 状态 |
| --- | --- | --- |
| `context-pack` | 以证据驱动的代码库研究；产出 `Research Report` 和 `Context Pack`，并带有 `sbro_readiness` 信号供下游 agent 使用 | Active |
| `deepresearch` | 面向用户的代码库研究；产出带 Mermaid 图表的分层 Markdown 报告 | Active |
| `batch-refactor` | 面向大规模语义级批量重构的规范优先编排；当存在 `Context Pack` 时会直接消费它 | Active |
| `log-query` | 针对大体量本地日志，用分层文本过滤、证据支撑统计和可选的后置语义归类来回答自然语言问题 | Active |
| `using-easywork` | 在大日志分析、人类可读研究、面向下游 agent 的上下文打包和语义批量重构之间选择合适的核心 skill 和执行顺序 | Active |
| `brainstorming` | 在任何创造性工作前使用；用于澄清意图、提出方案并拿到设计确认 | Active |
| `writing-plans` | 把 spec 转成精确的分步实现计划 | Active |
| `writing-skills` | 用 TDD 方法创建和校验 skill 文档 | Active |
| `subagent-driven-development` | 在当前会话里按任务拆分，用子 agent 执行并做两阶段 review | Active |
| `executing-plans` | 没有子 agent 时的顺序执行兜底方案 | Active |
| `dispatching-parallel-agents` | 并行运行 2 个及以上相互独立的任务 | Active |
| `using-git-worktrees` | 在功能开发前创建隔离的 git worktree | Active |
| `test-driven-development` | 先写失败测试，再做最小实现 | Active |
| `systematic-debugging` | 修复前先做四阶段根因调试 | Active |
| `verification-before-completion` | 在宣称完成前先运行验证命令并检查输出 | Active |
| `requesting-code-review` | 用精确的 git SHA 范围派发 reviewer 子 agent | Active |
| `receiving-code-review` | 在采纳 review 意见前先做技术性核验 | Active |
| `finishing-a-development-branch` | 实现完成后验证测试，并提供 merge/PR/保留/丢弃等收尾选项 | Active |
| `using-superpowers` | 会话启动时使用；用于建立 skill 发现与调用规则 | Active |

## Skill 关系

三个 orchestration skill 在明确的交接点上相连：

```
deepresearch ----------------------------------> human reader
                (if codebase-wide change found)
                       suggests running context-pack --> (user decides)

context-pack
  + Context Pack
        + sbro_readiness: ready_to_freeze | needs_verification | blocked
        + SBRO Handoff Block (facts / inferences / blockers / shared-file risks)
              v
batch-refactor
  + step 3: checks sbro_readiness; gates execution on blocked/needs_verification
  + step 12: writes corrections.md in Context Pack schema -> future context-pack runs can read it
```

**什么时候在 `batch-refactor` 前先跑 `context-pack`：**

| 场景 | 动作 |
|-----------|--------|
| 任务跨越 3 个及以上模块 | 先运行 `context-pack` |
| 共享文件 / 类型 / 事件定义还没定位清楚 | 先运行 `context-pack` |
| 主 agent 在不读源码的情况下无法写出规则 | 先运行 `context-pack` |
| 任务只涉及 1 到 2 个边界清晰的模块 | 在 `batch-refactor` 内联探索 |
| 已存在可直接复用的新鲜 Context Pack | 直接消费，跳过 `context-pack` |

**`deepresearch` 和 `context-pack` 的区别：**
两者都研究代码库，但服务对象不同。
当输出是给人阅读的文档时，用 `deepresearch`。
当输出要提供给下游 agent 或 `batch-refactor` 时，用 `context-pack`。
当 agent 需要先在 `log-query`、`deepresearch`、`context-pack`、`batch-refactor` 之间做选择并编排交接顺序时，用 `using-easywork`。

## Orchestration 与分析类 Skills（`agents/`、`skills/context-pack/`、`skills/deepresearch/`、`skills/batch-refactor/`、`skills/log-query/`）

### `using-easywork`

这是仓库里核心 skill 层的入口路由，帮助 agent 判断：

- 什么时候大体量本地日志问题应该使用 `log-query`
- 什么时候用户可读报告应该使用 `deepresearch`
- 什么时候需要可复用、可溯源的上下文打包，应该使用 `context-pack`
- 什么时候大规模语义级代码变更应该使用 `batch-refactor`
- 什么时候正确路径是 `context-pack -> batch-refactor`

- `skills/using-easywork/SKILL.md`

### `context-pack`

以证据驱动的代码库研究与上下文打包。它会产出一份给人看的 `Research Report`，
再产出一份给下游 agent 使用的 `Context Pack`。当下游很可能进入语义批量执行阶段时，
还会额外给出 `sbro_readiness` 字段和 `SBRO Handoff Block`。

- `skills/context-pack/SKILL.md`
- `skills/context-pack/references/output-templates.md`
- `skills/context-pack/references/delegation-guidance.md`
- `skills/context-pack/pressure-scenarios.md`

### `deepresearch`

面向用户的代码库研究 skill。它会输出带 Mermaid 图表的分层 Markdown 文档。
它支持并行子 agent 和持久化多轮状态，因此适合在大型代码库上跨上下文重置持续研究。
支持 `depth: quick | standard | deep`。

如果你需要的是结构化、可被 agent 消费的输出，不要用它替代 `context-pack`。

- `skills/deepresearch/SKILL.md`
- `skills/deepresearch/agents/exploration-agent.md`
- `skills/deepresearch/references/subagent-scaling.md`
- `skills/deepresearch/references/plan-template.md`
- `skills/deepresearch/references/output-document-template.md`

### `batch-refactor`

面向大规模语义级代码修改的规范优先 orchestration skill。它会在存在 `Context Pack` 时优先消费它，
在冻结规则前检查 `sbro_readiness`，并在执行后写出 `corrections.md`，方便未来的 `context-pack`
把这些更正当作已有研究结果使用。

- `skills/batch-refactor/SKILL.md`
- `skills/batch-refactor/pressure-scenarios.md`

### `log-query`

面向大体量本地日志的自然语言分析 skill。它是 workflow-only 的：
先做小样本探测，再把问题翻译为显式的包含/排除条件，优先使用 `rg`、`grep`
或兼容 PowerShell 的搜索方式做分层文本过滤，只有在候选集足够小之后才做语义归类。

- `skills/log-query/SKILL.md`
- `skills/log-query/pressure-scenarios.md`

## Superpowers Skills（`superpowers/skills/`）

通用开发流程 skill，会和 orchestration skills 一起自动加载，不需要单独安装。

| Skill | 适用场景 |
|-------|-------------|
| `using-superpowers` | 会话启动时使用；建立 skill 发现和调用规则 |
| `brainstorming` | 在任何创造性工作前使用：功能、组件、行为改动 |
| `writing-plans` | 已有 spec，需要生成分步实现计划时使用 |
| `writing-skills` | 创建或编辑 skill 文档时使用（把 TDD 应用到文档） |
| `subagent-driven-development` | 在当前会话里按任务拆分，用子 agent 执行并做两阶段 review |
| `executing-plans` | 没有子 agent 时的顺序执行兜底方案 |
| `dispatching-parallel-agents` | 当 2 个及以上相互独立的任务可以并行推进时使用 |
| `using-git-worktrees` | 在需要隔离工作空间的功能开发前使用 |
| `test-driven-development` | 开始写实现前先写失败测试 |
| `systematic-debugging` | 遇到 bug 或异常行为时，先找根因再修 |
| `verification-before-completion` | 宣称完成前先运行验证命令并检查输出 |
| `requesting-code-review` | 任务或功能完成后，派发 reviewer 子 agent |
| `receiving-code-review` | 准备采纳 review 反馈时先做核验 |
| `finishing-a-development-branch` | 实现完成后，验证测试并选择 merge/PR/保留/丢弃 |

## 新增 Skill

1. 创建 `<skill>/SKILL.md` 以及需要的配套文件
2. 更新本 README 的 Skill 索引表

## 维护说明

- 添加或重命名 skill 时，保持 Skill Index 表同步更新
- 每次提交都要更新插件版本
- 小提交按 `a.b.(c+1)` 升 patch 版本
- 非 patch 的较大变更按 `a.(b+1).0` 升 minor 并把 patch 归零
- 尽量保持一个 skill 一个顶层目录
- 如果修改了 `agents/` 下的 canonical agent 文件，要同步到各个 skill 私有 `agents/` 目录中的副本
