# worker 生命周期协议（herdr-flows 附录）

## 前置：agent 识别与集成（pi 必查）

`agent start` 等待的是「识别出 kind 且 ready」，识别失败即满超时（名字释放但 pi 进程大概率活着）。排查按序：

1. `herdr integration status` 确认目标 agent 已装集成。pi 未装的典型症状：`agent start` 满超时报 `timeout`、面板状态永远 `unknown`。安装：`herdr integration install pi`（写入 `~/.pi/agent/extensions/herdr-agent-state.ts`，由钩子向服务端上报 idle/working/blocked）。
2. 装了集成的 agent 钩子是**唯一状态权威**，屏幕清单不再回退——画面画得再标准也不会被「认出」，此路禁止再排查。
3. 屏幕规则缺口走本地覆盖：配置目录 `%APPDATA%\herdr\agent-detection\<kind>.toml`（Windows 平台配置目录是 Roaming；改后 `herdr server reload-agent-manifests`，以返回的 `local_override_shadowing_remote: true` 为准）。本地覆盖路径放错（如放进 Local\herder 状态目录或嵌 local/ 子目录）会被静默忽略。
4. 以上都正常仍不 ready → 属引擎级兼容问题，带证据提上游 issue，不要继续耗在重试上。

## 启动失败降级

`agent start` 超时 ≠ pi 没起来（名字释放但进程大概率活着）：

1. `read --source visible` 找 pi 状态栏 `(模型名) • max` 确认存活。
2. 存活但不被识别 -> 改用 **pane 注入模式**：
   ```bash
   herdr pane run <pane-id> "<任务描述>。产出写入 .temp/reports/<name>.md；完成后最终回复最后一行单独输出 __WORK_COMPLETE__（除此行外不要提这个标记）。"
   herdr pane wait-output <pane-id> --match "__WORK_COMPLETE__" --timeout 600000
   cat .temp/reports/<name>.md   # 以文件为准
   ```
3. 打回重做：空闲后注入「补充要求：<差异点>。更新同一文件并再次输出同一哨兵行」，验收看文件新增内容。
4. 重试 `agent start` 前必须先把面板收回 shell；占用中重试报 `agent_pane_busy`。

## 生命周期速查

| 场景 | 动作 |
|------|------|
| 判断面板里是否活 pi | read visible 找 `(模型名) • max` 状态栏；禁止发文字探测（会被当真消耗一轮对话）|
| 退出 pi 归还面板 | 首选注入 `/quit`；或 **零间隔连续两次** `send-keys ctrl+c`（两条命令间不 sleep，间隔 ≥0.5s 会被双击判定静默吞掉）；看到 `To resume this session:` + shell 提示符即成功 |
| worker 卡死 | 先 esc 中断生成，再决定打回还是终止 |
| 接力复用 | 同一 pi 会话上下文延续，第二份简报可以很短；要全新上下文才另起面板 |

## Windows 专属：spawn pi ENOENT

`spawn("pi")` 在 Windows 报 ENOENT——npm shim 是 bash 脚本，无 `pi.exe`。直启 node：

```js
spawn(process.execPath, [
  "C:/Users/<user>/AppData/Roaming/npm/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js",
  "--mode", "rpc",
])
```

## 注入命令键盘语义对照

| 命令 | 回车 | 用途 |
|------|------|------|
| `pane run <id> "<text>"` | 自动 | 逐条喂语句/派简报（主通道）|
| `pane send-text <id> "<text>"` | 否 | 拼接半行，之后自己 `send-keys enter` |
| `pane send-keys <id> <key>` | - | 只接受键名（enter/esc/ctrl+c/方向键），传文本报 `invalid_key` |

相邻两次注入会拼进同一行（`echo A` + `echo B` → `echo Aecho B`），节奏靠主控显式 sleep 或 enter 控制。

## Git Bash（MSYS）路径转换坑

Git Bash 会把以 `/` 开头的参数改写成本地路径（如 `/quit` 变成 `C:/Program Files/Git/quit`），`pane run`、`send-text`、`send-keys` 全部中招。凡参数以 `/` 开头，命令前缀加 `MSYS_NO_PATHCONV=1`；改写后的参数发给 agent 会被当成消息消耗一轮对话，报错则是 `invalid_key`/语法错。

## 并发写入规则

1. **默认分片**：每个 worker 只写自己的报告文件，主控汇总。
2. 共享文件只允许 append 且简报里显式声明（"只能追加，禁止重写整文件"）——读取后整写会互相覆盖。
3. 共享文件结构化修改改回串行派发。
4. 多 worker 改代码必须配 worktree 隔离，同一 checkout 撞 git index.lock。
