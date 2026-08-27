# worker 生命周期协议（herdr-flows 附录）

## 启动失败降级（pi 冷启动检测可超 120s）

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
| 退出 pi 归还面板 | esc -> ctrl+c ctrl+c，看到 `To resume this session:` + shell 提示符即成功 |
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

## 并发写入规则

1. **默认分片**：每个 worker 只写自己的报告文件，主控汇总。
2. 共享文件只允许 append 且简报里显式声明（"只能追加，禁止重写整文件"）——读取后整写会互相覆盖。
3. 共享文件结构化修改改回串行派发。
4. 多 worker 改代码必须配 worktree 隔离，同一 checkout 撞 git index.lock。
