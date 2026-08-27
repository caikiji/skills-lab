# 场景速查（herdr-flows 附录）

## 长驻服务（dev server / watcher）

普通进程不用 agent 原语，面板本身就是持久终端。

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
herdr pane run <svc-pane-id> "npm run dev"
curl -fsS -o /dev/null http://localhost:<port>/    # 行为探针优先
```

- 启动判定：行为探针优先（curl），横幅受本地化影响仅兜底（`--regex "英文|中文"` 兼容）；超时 ≠ 失败，先 read 现场。
- 日志 `pane read --source recent-unwrapped`，外部请求实时可见，主控可无侵入验证服务行为。
- 重启：ctrl+c -> 提示符回归 -> 同面板重启。结束必须停掉自起服务；不是你起的只汇报不动手。
- 收尾验证：停止后用同一探针反向验证（curl 连接失败 = 端口已释放），再 close 面板；最后 `pane list` 确认无残留。

## worktree 并行开发流

一条分支一个隔离工作区 + 专属 agent。

```bash
herdr worktree create --workspace "$HERDR_WORKSPACE_ID" --branch feat/x   # 从 JSON 取 path
herdr pane split --current --direction down --cwd <worktree-path> --no-focus
herdr agent start feat-x --kind claude --pane <pane-id> -- --agent herdr-child --permission-mode auto
herdr agent prompt feat-x "<任务>. 测试全绿后把改动摘要写入 REPORT.md。"
```
验收是主控职责：轮询报告文件（见 polling.md）+ 审 diff，不过就打回，不用 `--wait`；`worktree remove --force` 丢未提交改动，先征得用户同意。

## 状态看板

```bash
herdr agent list   # .result.agents[]：agent_status/agent/pane_id/cwd
```

`agent_status`：`idle`=等输入；`done`=完工未查看（focus 标记已见）；`blocked`=卡审批 UI 上报用户；`unknown`=识别不了≠完成。重点对象追加 `agent get`、`pane read --source recent-unwrapped`；汇报表格名称/状态/最近动作。

pane run 手动起的 worker 可能整体 `unknown` 甚至缺席——看板退化为自维护映射表（worker 名 -> pane_id -> 任务 -> 报告路径），派活时建好，它是同步事实唯一来源。

## 驱动交互式程序（REPL / 数据库客户端 / TUI）

exec 工具调不到的需要持续 stdin 的程序都走这里：

```bash
herdr pane run <id> "python"                                # 进入交互态（自带回车）
herdr pane wait-output <id> --match ">>>" --timeout 8000    # 提示符做同步点，命中即返回快照
herdr pane run <id> "print(1+1)"                            # 逐条喂语句
herdr pane read <id> --source recent-unwrapped --lines 40   # 看更长现场
```

- 同步点找稳定提示符（`>>>`、`Password:`、`mysql>`）；wait-output 命中即返回快照。
- 结束交互态还原干净 shell（REPL 发 exit()），同面板可复用；越过 alternate screen 的输出无法找回，重要结论落盘。
- 敏感凭据注入会留在可见区，完成后清理并提醒用户。TUI 选择器传参跳过；vim 类一律绕开直接改文件。

## 组合：服务 + worker 全链路

1. down-split 开服务面板并 rename，起服务，行为探针确认。
2. down-split 起 worker 启动 agent，注入简报（验证服务 + 结论写报告 + 哨兵行）。
3. 同时轮询报告文件和 read 服务日志——worker 报告 200 且日志有对应 GET，**双向证据链**才可信。
4. 收尾：ctrl+c 停服 -> agent 退会话 -> close 自建面板 -> 复测端口已释放。

## 派活前自检

斜杠命令与 TUI 快捷键 agent 执行不了（如 claude 的 `/help` 类内置命令在注入时逐行传递有风险），不能就改写为可执行形式或主控亲自做。
