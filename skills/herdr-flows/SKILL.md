---
name: herdr-flows
description: 在 Herdr 中执行多智能体与长任务工作流前必须读取并遵守本 skill。覆盖五类场景：并行编排多个 coding agent 干活、dev server/watcher 等长驻进程的面板管理、基于 git worktree 的多分支并行开发、轮询各 agent 的状态看板，以及在真实终端里驱动 REPL、数据库客户端、ssh、fzf 等需要持续 stdin 的交互式程序。凡用户提到"派几个 agent 并行"、"开个服务跑着别停"、"每个分支一个 agent"、"看看它们的进度/状态"，或任务包含会长时间阻塞的命令、需要对交互式程序持续输入时，即使用户没点名 Herdr 也应使用。仅在 Herdr 环境（HERDR_ENV=1）下可用，前置依赖 herdr skill。
---

# Herdr Flows

herdr skill 教的是命令细节；本 skill 定义把这些命令组装成工作流的流程与纪律。

## 前提与五条铁律

要求 `${HERDR_ENV:-}` = 1，不在 Herdr 内立即停下说明。

1. **ID 一律从 JSON 响应里解析**（`.result.tab.tab_id` / `.result.pane.pane_id` / `.agents[].pane_id`），禁止猜。
2. **后台面板一律 `--no-focus`**；用户明确要看才 focus。
3. **创建面板用 `--cwd "$PWD"`** 保住调用方工作目录；面板移动后改用新 ID。
4. **不关闭自己创建之外的面板/tab/workspace**；杀服务、`worktree remove --force` 先问用户。
5. **说话前确认对象状态**：面板当前是 shell 还是活 agent、忙闲与否；判据与发消息时序规则见「时序纪律」。

## 布局与观感

用户实时看着这些面板：

- **复用优先**：已有干净 shell 面板直接派活；串行子任务共用一个面板排队跑。
- **宽度红线**：面板宽度不足 100 列时中文逐字折行、pi 状态栏断行，不可读。主控自身已是窄列就禁止再向右拆；并行 worker 首选向下叠（拿满全宽），其次单开专用 tab 安放区：

```bash
herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$PWD" --label "workers"
# 取 .result.tab.tab_id 与 .result.root_pane.pane_id；tab 默认不抢焦点
herdr pane rename <root-pane-id> "worker-review"   # 给用户看得懂的标签
# 更多 worker 在同 tab 内 down-split 叠加；收工 `tab close <tab_id>` 一次回收
```

- **屏幕只做状态判断，正文阅读一律走报告文件**。
- **用完归还**：agent 结束会话退回 shell；自开的面板 `pane close <id>` 关掉，恢复用户初始布局。

## A 多 agent 编排（worker squad）

适用于 N 个相互独立的子任务可并行完成（评审、调研、批量改造）。

```bash
herdr pane split --current --direction down --cwd "$PWD" --no-focus   # 取 .result.pane.pane_id
herdr agent start worker-01 --kind pi --pane <pane-id> --timeout 120000
herdr agent prompt worker-01 "<任务描述>。完成后把结论写入 .temp/reports/worker-01.md，回复只需该文件路径。" \
  --wait --timeout 600000
```

### 结果与验收协议

- **结论写文件，屏幕只参考**：简报必须强制「完整结论写入 `<repo>/.temp/reports/<name>.md`」——最终回答可能落在 alternate screen 上读不到；文件才是验收标准。
- 完成同步三选一：`prompt --wait`（等第一个 settled 态）；哨兵行（简报约定最终回复最后一行输出 `__WORK_COMPLETE__`，然后 `wait-output --match "__WORK_COMPLETE__"`）；主控轮询报告文件（`test -f` + 内容 grep）。用哨兵时注意两点：**不加 `^` 行首锚**（worker 输出常带前导空格导致白等超时）、**字面量不得在简报其它位置出现**（否则匹配到回显造成假阳性）。
- `wait-output` 超时后第一步永远是验收文件，文件完好就继续。
- `blocked`（卡在审批/提问 UI）：读屏后**问用户**，不替 worker 回答审批。
- `agent_prompt_stalled`：5 秒内未见状态变化，先 `agent get` 再决定 esc / ctrl+c / 重发。
- 收尾清点 `agent list` 确认无残留 working 状态再向用户汇报；汇总时 read 各报告文件合并。

### 启动失败降级（Windows 上 pi 冷启动检测可超过 120s）

`agent start` 超时不代表 pi 没起来——名字被释放但进程大概率活着：

1. `read <pane-id> --source visible` 找 pi 状态栏（`(模型名) • max` 一行）确认进程是否存活。
2. 存活但不被识别 -> 改用 **pane 注入模式**：把简报当普通文本注入，pi 输入框会接收为用户消息：
   ```bash
   herdr pane run <pane-id> "<任务描述>。产出写入 .temp/reports/<name>.md；完成后最终回复最后一行单独输出 __WORK_COMPLETE__（除此行外不要提这个标记）。"
   herdr pane wait-output <pane-id> --match "__WORK_COMPLETE__" --timeout 600000
   cat .temp/reports/<name>.md   # 以文件为准
   ```
3. 打回重做：空闲后再注入一轮"补充要求：<差异点>。更新同一文件并再次输出同一哨兵行"，验收以文件新增内容为准。
4. 重试 `agent start` 前必须先把面板收回成可用 shell，占用中重试报 `agent_pane_busy`。

### 生命周期速查

| 场景 | 动作 |
|------|------|
| 判断面板里是否活 pi | read visible 找底部 `(模型名) • max` 状态栏；禁止发文字探测（会被当真消耗一轮对话）|
| 退出 pi 归还面板 | esc 中断生成 -> ctrl+c ctrl+c，看到 `To resume this session:` + shell 提示符即成功 |
| worker 卡死 | 先 esc 中断生成，再决定打回还是终止 |
| 接力复用 | 同一 pi 会话上下文延续，第二份简报可以很短；需要全新上下文才另起面板 |

### 并发写入规则

多个 worker 同时写同一仓库时的分工纪律：

1. **默认分片**：每个 worker 只写自己的报告文件，主控负责汇总合并。
2. 共享文件只允许 append 且必须在简报里显式声明（"只能追加，禁止重写整文件"）——读取后整写的并发编辑会互相覆盖。
3. 需要对共享文件做结构化修改时改回串行派发。
4. 多 worker 同时改代码必须配合 Recipe C 的 worktree 隔离，同一个 checkout 会撞 git index.lock。

## B 长驻服务（dev server / watcher）

普通进程不用 agent 原语，面板本身就是持久终端。

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
herdr pane run <svc-pane-id> "npm run dev"
curl -fsS -o /dev/null http://localhost:<port>/    # 行为探针优先
```

- 启动判定两层：行为探针优先（curl 探端口等），日志横幅只是兜底（受本地化/版本影响，可用 `--regex "英文写法|中文写法"` 兼容）。横幅超时不等于失败，先 read 现场。
- 日志统一 `pane read --source recent-unwrapped`；外部请求实时进日志，主控可无侵入观察服务行为。
- 重启：ctrl+c -> 提示符回归 -> 同面板 `pane run` 重启，不必关面板重开。
- 任务结束必须停掉自己起的服务再汇报完成；不是你起的服务只汇报不动手。

## C worktree 并行开发流

一条分支一个隔离工作区 + 一个专属 agent。

```bash
herdr worktree create --workspace "$HERDR_WORKSPACE_ID" --branch feat/x   # 从 JSON 取 path
herdr pane split --current --direction down --cwd <worktree-path> --no-focus
herdr agent start feat-x --kind pi --pane <pane-id>
herdr agent prompt feat-x "<任务>. 测试全绿后把改动摘要写入 REPORT.md。" --wait --timeout 900000
```

- 验收是主控职责：read 报告 + 审 diff，不过就打回。
- `worktree remove --force` 会丢未提交改动，先征得用户同意。

## D 状态看板

```bash
herdr agent list                                    # .result.agents[]：agent_status/agent/pane_id/cwd
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
```

`agent_status` 解读：`idle`=等输入；`done`=完工未被查看（focus 即标记已见）；`blocked`=卡审批 UI，上报用户；`unknown`=识别不了，不代表完成。重点对象追加 `agent get` 与 `read --source recent-unwrapped`。汇报表格：名称/状态/最近动作摘要。

经 pane run 手动启动的 worker 可能整体显示 `unknown` 甚至不在列表里——此时看板退化为主控自维护映射表：worker 名 -> pane_id -> 任务 -> 报告路径，派活时就建好，它是同步事实的唯一来源。

## E 驱动交互式程序（REPL / 数据库客户端 / TUI）

exec 工具调不到的需要持续 stdin 的程序都走这里：

```bash
herdr pane run <id> "python"                                # 进入交互态（自带回车）
herdr pane wait-output <id> --match ">>>" --timeout 8000    # 提示符做同步点，命中即返回快照
herdr pane run <id> "print(1+1)"                            # 逐条喂语句
herdr pane read <id> --source recent-unwrapped --lines 40   # 看更长现场
```

- 文本注入两条路：`pane run`（文本+回车原子发送）、`pane send-text`（纯文本不带回车，适合拼接长语句后再自己 enter）。相邻两次注入会拼进同一行，节奏靠主控显式 sleep 或 enter 控制。
- `send-keys` 只接受键名（enter/esc/ctrl+c/方向键），传普通文本报 `invalid_key`。
- 同步点找稳定提示符（`>>>`、`Password:`、`mysql>`）；`wait-output` 命中即返回快照不必再 read。
- 结束交互态把面板还原成干净 shell（REPL 发 exit()），不留僵尸进程；提示符回归后同面板可直接复用。
- 越过 alternate screen 的输出无法从 scrollback 找回，重要结论让对端落盘成文件。
- 敏感凭据终端注入虽不进 history 但留在可见区，完成后清理并提醒用户。
- TUI 选择器能传参跳过就跳过；vim 类编辑器尽量绕开直接改文件。

## 组合：服务 + worker 全链路

各 recipe 叠加时的标准时序（以「起服务 -> worker 验证服务 -> 主控汇总」为例）：

1. down-split 开服务面板并 rename，起服务，行为探针确认（横幅仅参考）。
2. 开 workers 安放区 tab，启动 pi，rename 后注入简报：任务=向服务发请求验证行为，结论写报告文件，末尾哨兵行。
3. 主控同时轮询报告文件和 read 服务日志——worker 报告说返回 200，服务日志里有对应的 GET 记录，**双向证据链**才是可信的验收。
4. 收尾顺序：先 ctrl+c 停服 -> worker 退会话 -> tab close 安放区 -> 关剩余自建面板 -> 复测端口已释放。

## 经验沉淀

若使用中遇到本 skill 未覆盖的问题，靠自主试错（多步摸索、非标准用法）才解决：

1. 问题闭环后**主动提醒用户**：「这次问题 X 的解法是 Y，要把它固化进 herdr-flows 吗？」——一句话即可，不要附长篇分析。
2. 用户同意后，把经验提炼成一条**可执行规则**（触发条件 + 动作），插入对应章节；而不是把踩坑过程记流水账。同一问题已收录则更新而非重复。
3. 用户拒绝则不动文件。

## 时序纪律

worker 生成期间注入的新指令可能被 TUI 静默吞掉（无回显、无报错、不进对话历史）。因此：

1. 说话前等空闲判据：提示符回归 / idle / 哨兵命中 / 文件验收完毕，不确定就先 read。
2. 多轮意图合并成一条简报，比连发短消息可靠。

## 常见坑

- 错误码：JSON 错误在 stderr 且 exit 1（如 `{"error":{"code":"timeout"}}`）；exit 2 是语法错，先修命令形状。
- `pane move` 之后旧 pane ID 只在原调用方上下文有效，全局引用刷新为新 ID。
