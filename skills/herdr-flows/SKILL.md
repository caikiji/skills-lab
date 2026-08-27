---
name: herdr-flows
description: 在 Herdr 中做多智能体与长任务工作流前必须读取并遵守本 skill。覆盖：并行编排多个 coding agent、dev server/watcher 长驻面板、git worktree 多分支开发、agent 状态看板、在终端驱动 REPL/数据库客户端/ssh 等交互式程序。用户提到"派几个 agent 并行"、"开个服务跑着别停"、"每个分支一个 agent"、"看进度/状态"，或任务含长阻塞命令、需持续输入的交互式程序时，即使没点名 Herdr 也用。仅限 HERDR_ENV=1，依赖 herdr skill。
---

# Herdr Flows

herdr skill 教命令细节，本 skill 定义工作流流程与纪律。要求 HERDR_ENV=1。

## 四条铁律

1. **ID 从 JSON 响应解析**（`.result.pane.pane_id` 等），禁止猜。
2. **后台面板一律 `--no-focus`**；创建用 `--cwd "$PWD"`；`pane move` 后改用新 ID。
3. **权限分级**：自建面板可 send/run/close；用户或来源不明面板绝对只读，上限是"只搞乱自己这条分支"。
4. **说话前确认对象**：read 底部状态栏判断 shell/agent/忙闲（判据见时序纪律）。

## 布局与观感

- 复用优先：干净 shell 面板直接派活；串行任务共用一个面板排队。
- 宽度红线：面板 <100 列即不可读（中文折行、状态栏断行），窄面板禁止再向右拆。
- worker 从主控（或上一个 worker）面板 down-split，全宽下叠、`pane rename` 语义名，不另开 tab。
- 屏幕只做状态判断，正文阅读走报告文件；用完 `pane close` 归还布局。

## A 多 agent 编排（worker squad）

N 个独立子任务并行（评审/调研/批量改造）。

```bash
herdr pane split --current --direction down --cwd "$PWD" --no-focus   # 取 .result.pane.pane_id
herdr agent start worker-01 --kind pi --pane <pane-id> --timeout 120000
herdr agent prompt worker-01 "<任务描述>。完成后把结论写入 .temp/reports/worker-01.md，回复只需该文件路径。" --wait --timeout 600000
```

### 验收协议

- **结论写文件**：简报强制「完整结论写入 .temp/reports/<name>.md」——最终回答可能落在 alternate screen 读不到；文件是唯一验收标准。
- 完成同步三选一：`prompt --wait`；哨兵行（`wait-output --match "__WORK_COMPLETE__"`，不加 `^` 锚——输出常带前导空格；字面量不得在简报它处出现，防回显假阳性）；主控轮询报告文件。
- `wait-output` 超时先验收文件，完好就继续。`blocked`=卡审批 UI：读屏后问用户，不替答。`agent_prompt_stalled`：先 `agent get` 再定 esc/ctrl+c/重发。
- 收尾 `agent list` 确认无残留 working；汇总 read 各报告合并。

### 启动失败降级 / 生命周期 / 并发写入

`agent start` 超时 ≠ pi 没起来；启动降级、pane 注入模式、pi 退出按键序列、并发写入纪律见 [references/worker-protocol.md](references/worker-protocol.md)。

## B 长驻服务（dev server / watcher）

普通进程不用 agent 原语，面板本身就是持久终端。

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
herdr pane run <svc-pane-id> "npm run dev"
curl -fsS -o /dev/null http://localhost:<port>/    # 行为探针优先
```

- 启动判定：行为探针优先（curl），横幅受本地化影响仅兜底（`--regex "英文|中文"` 兼容）；超时 ≠ 失败，先 read 现场。
- 日志 `pane read --source recent-unwrapped`，外部请求实时可见，主控可无侵入验证服务行为。
- 重启：ctrl+c -> 提示符回归 -> 同面板重启。结束必须停掉自起服务；不是你起的只汇报不动手。

## C worktree 并行开发流

一条分支一个隔离工作区 + 专属 agent。

```bash
herdr worktree create --workspace "$HERDR_WORKSPACE_ID" --branch feat/x   # 从 JSON 取 path
herdr pane split --current --direction down --cwd <worktree-path> --no-focus
herdr agent start feat-x --kind pi --pane <pane-id>
herdr agent prompt feat-x "<任务>. 测试全绿后把改动摘要写入 REPORT.md。" --wait --timeout 900000
```

验收是主控职责（read 报告 + 审 diff，不过就打回）；`worktree remove --force` 丢未提交改动，先征得用户同意。

## D 状态看板

```bash
herdr agent list   # .result.agents[]：agent_status/agent/pane_id/cwd
```

`agent_status`：`idle`=等输入；`done`=完工未查看（focus 标记已见）；`blocked`=卡审批 UI 上报用户；`unknown`=识别不了≠完成。重点对象追加 `agent get`、`read --source recent-unwrapped`；汇报表格名称/状态/最近动作。

pane run 手动起的 worker 可能整体 `unknown` 甚至缺席——看板退化为自维护映射表（worker 名 -> pane_id -> 任务 -> 报告路径），派活时建好，它是同步事实唯一来源。

## E 驱动交互式程序（REPL / 数据库客户端 / TUI）

exec 工具调不到的需要持续 stdin 的程序都走这里：

```bash
herdr pane run <id> "python"                                # 进入交互态（自带回车）
herdr pane wait-output <id> --match ">>>" --timeout 8000    # 提示符做同步点，命中即返回快照
herdr pane run <id> "print(1+1)"                            # 逐条喂语句
herdr pane read <id> --source recent-unwrapped --lines 40   # 看更长现场
```

- 文本注入：`pane run`（带回车原子发）、`pane send-text`（不带回车，拼语句后自己 enter）；相邻注入会拼进同一行，节奏主控显式控制。`send-keys` 只吃键名，传文本报 `invalid_key`。
- 同步点找稳定提示符（`>>>`、`Password:`、`mysql>`）；wait-output 命中即返回快照。
- 结束交互态还原干净 shell（REPL 发 exit()），同面板可复用；越过 alternate screen 的输出无法找回，重要结论落盘。
- 敏感凭据注入会留在可见区，完成后清理并提醒用户。TUI 选择器传参跳过；vim 类一律绕开直接改文件。

## 组合：服务 + worker 全链路

1. down-split 开服务面板并 rename，起服务，行为探针确认。
2. down-split 起 worker 启动 pi，注入简报（验证服务 + 结论写报告 + 哨兵行）。
3. 同时轮询报告文件和 read 服务日志——worker 报告 200 且日志有对应 GET，**双向证据链**才可信。
4. 收尾：ctrl+c 停服 -> worker 退会话 -> close 自建面板 -> 复测端口已释放。

## 操作纪律

- **反馈闭环（禁止盲等）**：发后即查退出码/stderr/预期效应；报错（ParserError/ENOENT/`agent_pane_busy`）当场停下修，整批当事务；等 = 判定实现（wait-output/轮询），`sleep N` 仅限物理缓冲且后跟真实检查。
- **忙时不发指令**（生成期注入可能被 TUI 静默吞掉）；多轮意图合并成一条简报。
- **派活前自检**：斜杠命令与 TUI 快捷键 agent 执行不了，不能就改写为可执行形式或主控亲自做。
- **面板白名单**：写操作（send/run/close/resize）前核对 pane_id 在自建登记清单；不在清单 = 不碰（用户面板只读，禁止 backspace/delete"帮清理"）；归属不明先问；误操作用户面板必须如实报告影响并给恢复命令（`pi --session <id>`）。

## 常见坑

- JSON 错误在 stderr 且 exit 1；exit 2 是语法错，先修命令形状。
- `pane move` 后旧 pane ID 只在原调用方上下文有效，全局引用刷新为新 ID。
- 本 skill 未覆盖的问题走 skill-feedback 流程沉淀，不在本文件内私自扩写。
