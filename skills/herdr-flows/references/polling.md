# 轮询验收循环（herdr-flows 附录）

派活后不依赖工具状态机，用短轮询真实检查。两个循环可独立使用，默认 3s 间隔：

## 主 pane 反向消息轮询

子 agent 完成时通过 `herdr pane run <主pane-id> "[<agent名>] 完成"` 注入消息；主控轮询最近的 unwrapped 输出抓 `[<agent名>]` 开头的行：

```bash
for i in 1 2 3 4 5 6 7 8; do
  sleep 3
  MSG=$(herdr pane read <主pane-id> --source recent-unwrapped --lines 60 | grep -E "\[worker-01\]" | tail -1)
  [ -n "$MSG" ] && { echo "收到($((i*3))s): $MSG"; break; }
done
```

## 报告文件轮询

子 agent 承诺写 `.temp/reports/<agent名>.md` 时，轮询文件存在并 cat：

```bash
for i in 1 2 3 4 5 6; do
  sleep 3
  [ -f .temp/reports/worker-01.md ] && { cat .temp/reports/worker-01.md; break; }
done
```

## 超限处置

约 25s 内未命中 = 工具或任务可能出问题：先 `agent get` 看状态、`pane read --source visible` 看现场，再决定重试/打回/上报。禁止在超限后继续无脑延长轮询等待。
