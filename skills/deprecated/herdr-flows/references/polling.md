# 轮询验收循环（herdr-flows 附录）

派活后不依赖工具状态机，用短轮询真实检查。两个循环可独立使用，默认 3s 间隔：

## 主 pane 反向消息轮询

子 agent 完成时通过 `herdr pane run <主pane-id> "[<agent名>] 完成"` 注入消息；主控轮询最近的 unwrapped 输出抓 `[<agent名>]` 注入行（可能带 `Steering:` 等前缀、前后空格，故不锚定行首）：

```bash
for i in 1 2 3 4 5 6 7 8; do
  sleep 3
  MSG=$(herdr pane read <主pane-id> --source recent-unwrapped --lines 60 | grep -E "\[worker-01\]" | tail -1)
  [ -n "$MSG" ] && { echo "收到($((i*3))s): $MSG"; break; }
done
```

## 假阳性防线

两条规则必须同时成立：

- **哨兵字面量不出现在任务简报里**：简报涉及"发消息说 xxx"时，不要照抄会说出的那行字（否则 prompt 回显先匹配，未干完就误报完成）。用变化措辞或只写"发一条完成消息"，不写具体内容。
- **匹配用无锚 grep**（实测：注入消息可能带 `Steering:` 前缀，行首锚会漏）；命中后人工验一下行内容是否为真实注入（含 `[<agent名>]` 且前缀是提示符类文本）。

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
