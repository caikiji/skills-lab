# 子 agent 简报模板（herdr-flows 附录）

`--agent herdr-child` 已自带身份/协议/安全红线（[agents/herdr-child.md](../../herdr-chat/agents/herdr-child.md)），简报**只需**告知动态值，协议段不再重复：

```
【本机信息】我（主控）的 pane id 是 <主控pane-id>，你的名字是 <agent名>，消息前缀 [<agent名>]。
任务：<任务描述>。完整结论写入 .temp/reports/<agent名>.md，回复只需该路径。
```

## 动态值来源

- `<主控pane-id>`：`herdr pane current --current` 取 `.result.pane.pane_id`（当前 pane 即主 pane）。
- `<agent名>`：`agent start` 指定的名字，与消息前缀一致。

## 长文交换目录（协议已由 subagent 模板定义，此处仅记路径）

- 子 agent 长文：`.temp/msg/<agent名>.md`，子写、主控读。
- 主控长文：`.temp/msg/主控.md`，主写、子读；在后续简报里告知文件路径。
- 双方各自只写自己的文件（并发安全），读对方文件只读。

## 收尾清理

任务结束、确认子 agent 退出后，删除其 `.temp/msg/<agent名>.md` 与 `.temp/reports/` 下报告；`.temp/` 本身不入库（AGENTS.md 约定）。
