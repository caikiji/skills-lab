---
name: herdr-flows
description: 在 Herdr 中做多智能体与长任务工作流前必须读取并遵守本 skill。覆盖：agent start 调用 subagent（默认 claude）、pane 新建与 split、把长命令放 Herdr 面板当后台任务、长驻服务与交互式程序。用户提到"派几个 agent 并行"、"开个服务跑着别停"、"每个分支一个 agent"、"看进度/状态"，或任务含长阻塞命令、需持续输入的交互式程序时，即使没点名 Herdr 也用。仅限 HERDR_ENV=1，依赖 herdr skill。
---

# Herdr Flows

herdr skill 教命令细节，本 skill 定义工作流与纪律。要求 HERDR_ENV=1。

## 调 subagent（agent start）

1. **准备 pane**：`herdr pane split --current --direction down --cwd "$PWD" --no-focus`，从 `.result.pane.pane_id` 取 ID；面板须停在交互 shell 提示符、无前台命令。
2. **启动**：`herdr agent start worker-01 --kind claude --pane <pane-id> --timeout 30000 -- --agent herdr-child --permission-mode auto`
  `--agent herdr-child` 加载 [agents/herdr-child.md](../herdr-chat/agents/herdr-child.md) subagent 定义（身份/安全红线/协议全文），禁止裸启动；`--permission-mode auto` 必须显式传（frontmatter 的 permissionMode 实测不生效，省略会回到 manual 模式逐条审批）。
  返回成功 = 识别且 ready；启动失败先 `herdr integration status`，未装集成则 `herdr integration install claude`，仍不 ready 走 [references/agent-lifecycle.md](references/agent-lifecycle.md) 的 pane 注入降级。
3. **派活**：`herdr agent prompt worker-01 "<任务>。完整结论写入 .temp/reports/worker-01.md，回复只需该路径。"`；简报含动态值（主控 pane id、agent 名），模板见 [references/chat-briefing.md](references/chat-briefing.md)；**不用 `--wait`**——等待交给工具状态机，一旦工具卡死就永远等；派活后进入轮询验收（见下）。
4. **验收（轮询，不依赖工具状态机）**：先看主 pane 反向消息，再看报告文件，都是短间隔真实检查；循环模板与超限处置见 [references/polling.md](references/polling.md)。
5. **收尾**：`agent get` 确认回到 idle/done（不阻塞），仍在 working/blocked 先 esc/ctrl+c 处理，禁止带阻塞子 agent 关闭或复用面板；`agent list` 确认无残留；退出 agent 归还面板（注入 `/exit`，前缀 `MSYS_NO_PATHCONV=1`）。

**双向通信**：子 agent 可反向给主 pane 发消息（`herdr pane run <主控pane-id> "[名字] 内容"`），派活简报必须告知主控 pane id（从 `herdr pane current --current` 取），协议全文见 [herdr-chat](../herdr-chat/SKILL.md)。

打回重做 / 卡死中断 / 接力复用 / 并发写入见 [references/agent-lifecycle.md](references/agent-lifecycle.md)。

## pane 操作

新建/拆分三决策：

- 方向：宽面板向右拆，窄或高面板向下拆；禁止重复同向拆出窄列（<100 列不可读）。
- 参数：`--direction right|down --cwd "$PWD" --no-focus`；后台活一律 `--no-focus` 保主 pane 焦点，比率用 `--ratio`。
- 命名归还：`pane rename <id> 语义名`；用完 `pane close` 还布局；串行任务共用一个 pane 排队，不另开 tab。

其它常用：`pane run`（命令+回车原子发）、`pane read --source recent-unwrapped`（日志/现场）、`pane wait-output --match`（等文本，必带 `--timeout`）、`pane zoom --toggle`（临时放大）、`pane move`（搬 pane 后改用新 ID）。

## 长命令进面板（当后台任务）

耗时命令、服务、REPL 放其它 pane，主 pane 只做乐观检查 + timeout：

- 面板是交互式后台：`pane read` 看实时输出、`pane run` 随时追加输入、`send-keys ctrl+c` 可中断、close 即清理。
- 同步点用 `pane wait-output <id> --match "触发文本" --timeout <ms>`，命中即返回快照。
- 服务启动判定用行为探针：`curl -fsS -o /dev/null http://localhost:<port>/`，横幅只作兜底。

长驻服务 / worktree 多分支 / 状态看板 / REPL 驱动速查见 [references/scenarios.md](references/scenarios.md)。

## 推荐习惯

1. 乐观检查：先查再等——read 看现场、看结果文件、看反向消息；查不到才进入等待。
2. 等待用短轮询不用等待命令：`sleep 3` 一轮 + 真实检查，循环上限 6-8 轮（约 25s），超限先看现场再定；禁止把等待交给工具状态机（`--wait` 等）和长睡盲等。
3. 确需物理缓冲也先短后长：1s → 5s → 30s，每次醒来必须真实检查。
4. 锁死防呆：发现 working 超长（>60s 无进展）先读屏，暴露问题优先于等待结果。
5. 阻塞下沉：耗时或需持续输入的命令放其它 pane；主 pane 保持轻快，绝不干等。
6. 忙时不发指令：agent 生成期注入可能被吞；多轮意图合并成一条简报。
7. 白名单：写操作（send/run/close/resize）前核对 pane_id 在自建登记清单；用户面板只读；误操作用户面板如实报告并给恢复命令。

## 常见坑

- JSON 错误在 stderr 且 exit 1；exit 2 是语法错，先修命令形状。
- `pane move` 后旧 pane ID 只在原调用方上下文有效，全局刷新为新 ID。
- 免审批会话（permissionMode: auto）仍会拦截高危命令；若出现审批属预期安全行为，读屏后按 blocked 流程处理，不要试图绕过。
- 本 skill 未覆盖的问题走 skill-feedback 流程沉淀，不在本文件内私自扩写。
