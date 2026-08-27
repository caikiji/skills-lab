# 子 agent 通信简报模板（herdr-flows 附录）

派活时注入的首条简报，除任务外必须附带以下协议段（发任何 subagent 都带上）：

```
【通信协议】你可以主动联系我（主控）：
1. 简短消息：herdr pane run <主控pane-id> "[<agent名>] 消息内容"
2. 长文：完整内容写入 .temp/msg/<agent名>.md，然后发 "[<agent名>] 长文已写入 .temp/msg/<agent名>.md"
3. 消息前缀固定 "[发送方名字] "，你我消息可区分
4. 我的名字是 [主控]，你的名字是 <agent名>；我的 pane id 是 <主控pane-id>，别用你自己的 $HERDR_PANE_ID
```

## 主控侧取值

- `<主控pane-id>`：`herdr pane current --current` 取 `.result.pane.pane_id`（当前 pane 即主 pane）。
- `<agent名>`：`agent start` 的名字，与消息前缀一致。

## 长文交换目录

- 子 agent 长文：`.temp/msg/<agent名>.md`，子写、主控读。
- 主控长文：`.temp/msg/主控.md`，主写、子读；在后续简报里告知文件路径。
- 双方各自只写自己的文件（并发安全），读对方文件只读。

## 收尾清理

任务结束、确认子 agent 退出后，删除其 `.temp/msg/<agent名>.md` 与 `.temp/reports/` 下报告；`.temp/` 本身不入库（AGENTS.md 约定）。
