# agent 生命周期协议（herdr-flows 附录）

## agent start 前置

`agent start` 等待「识别出 kind 且 ready」，识别失败即满超时（名字释放但进程大概率活着）。排查按序：

1. `herdr integration status` 确认目标 agent 已装集成。claude 未装时安装：`herdr integration install claude`（写入 `C:\Users\caikiji\.claude\hooks\herdr-agent-state.ps1`，由钩子向服务端上报 idle/working/blocked）。
2. 装了集成的 agent 钩子是**状态权威**，屏幕清单不再回退——画面再标准也不会被「认出」，此路禁止再排查。
3. 屏幕规则缺口走本地覆盖：配置目录 `%APPDATA%\herdr\agent-detection\<kind>.toml`（改后 `herdr server reload-agent-manifests`，以返回的 `local_override_shadowing_remote: true` 为准）。本地覆盖路径放错会被静默忽略。
4. 都正常仍不 ready → 引擎级兼容问题，带证据提上游 issue，不继续耗在重试上。

claude 可用零钩子识别：远程 `claude.toml` 已有完整屏幕规则（OSC title、prompt box `❯`、spinner、permission prompt）；钩子只补充状态上报精度。

## 启动失败降级（pane 注入模式）

`agent start` 超时 ≠ agent 没起来（名字释放但进程大概率活着）：

1. `pane read --source visible` 确认存活（claude 看底部 prompt box `❯` 或 OSC title `✳ ...`）。
2. 活但不被识别 → 改用 pane 注入模式：
   ```bash
   herdr pane run <pane-id> "<任务描述>。产出写入 .temp/reports/<name>.md；完成后最终回复最后一行单独输出 __WORK_COMPLETE__（除此行外不要提这个标记）。"
   herdr pane wait-output <pane-id> --match "__WORK_COMPLETE__" --timeout 600000
   ```
3. 打回重做：空闲后注入「补充要求：<差异点>。更新同一文件并再次输出同一哨兵行」，验收看文件新增内容。
4. 重试 `agent start` 前必须先把面板收回 shell；占用中重试报 `agent_pane_busy`。

## 生命周期速查

| 场景 | 动作 |
|------|------|
| 判断面板里是否活 agent | `pane read --source visible` 看底部输入框/prompt box；禁止发文字探测（会被当真消耗一轮对话）|
| 退出 agent 归还面板 | 首选 `MSYS_NO_PATHCONV=1 herdr pane run <id> "/exit"`；兜底零间隔连续两次 `send-keys ctrl+c`（两条命令间不 sleep，间隔 ≥0.5s 会被双击判定静默吞掉）；见 shell 提示符回归即成功 |
| worker 卡死 | 先 `send-keys esc` 中断生成，再决定打回（见上）还是终止 |
| 接力复用 | 同一 agent 会话上下文延续，第二份简报可以很短；要全新上下文才另起面板 |

## 注入命令键盘语义对照

| 命令 | 回车 | 用途 |
|------|------|------|
| `pane run <id> "<text>"` | 自动 | 逐条喂语句/派简报（主通道）|
| `pane send-text <id> "<text>"` | 否 | 拼接半行，之后自己 `send-keys enter` |
| `pane send-keys <id> <key>` | - | 只接受键名（enter/esc/ctrl+c/方向键），传文本报 `invalid_key` |

相邻两次注入会拼进同一行（`echo A` + `echo B` → `echo Aecho B`），节奏靠主控显式 sleep 或 enter 控制。

## Git Bash（MSYS）路径转换坑

Git Bash 会把以 `/` 开头的参数改写成本地路径（如 `/exit` 变成 `C:/Program Files/Git/exit`），`pane run`、`send-text`、`send-keys` 全部中招。凡参数以 `/` 开头，命令前缀加 `MSYS_NO_PATHCONV=1`；改写后的参数发给 agent 会被当成消息消耗一轮对话，报错则是 `invalid_key`/语法错。

## 审批链纪律

工具权限审批是**逐条出现**的：批准某条命令的白名单只覆盖该命令（`node *` 只免 node，不含 `echo`/`bash` 等），同任务的后续命令会再弹新审批。处理流程：

1. `pane read --source visible` 读清当前审批是哪条命令、光标停在哪个选项。
2. 用户授权自动批准时，用 `agent send-keys <name> enter` 确认（`down`/`enter` 组合键可能只移动不确认，enter 单独发并重读屏验证）。
3. 每次批准后重新 `pane read`：新审批就继续处理，直到 agent 回到 working。
4. 不可用 esc 当“收尾”键：esc 会取消当前审批（等价拒绝），且会把输入框残留 `/` 置于斜杠菜单态，后续注入前先 ctrl+u 清空。
5. 验收以报告文件为准：`wait-output` 命中只是信号（回显可假阳性），命中与未命中都 `cat` 报告文件二次验证；文件缺失时读 claude 调试日志 `~/.claude/debug/<session-id>.txt` 的 `tool permission denied`/`stop_reason` 定位。

## 并发写入规则

1. **默认分片**：每个 worker 只写自己的报告文件，主控汇总。
2. 共享文件只允许 append 且简报里显式声明（"只能追加，禁止重写整文件"）——读取后整写会互相覆盖。
3. 共享文件结构化修改改回串行派发。
4. 多 worker 改代码必须配 worktree 隔离，同一 checkout 撞 git index.lock。
