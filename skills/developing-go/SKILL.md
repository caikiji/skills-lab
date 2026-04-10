---
name: developing-go
description: 在 Go 项目中开发、调试、重构或审查代码时使用——指导 gopls MCP/LSP、go doc、repomix 工具组合的高效使用，减少对 Grep/全量 Read 的依赖。
---

# Developing Go

在 Go 项目中高效使用 gopls MCP/LSP、go doc、repomix 工具组合，减少对 Grep/全量 Read 的依赖。

## 会话初始化

每次会话开始，先执行：
1. `go_workspace` — 触发 gopls 索引
2. `go_vulncheck` — 检查依赖安全风险

## 决策速查

```
我要做什么？
├─ 找入口/函数
│   └─ documentSymbol 扫描文件 > go_search/grep 猜名字
├─ 找谁调了某函数
│   └─ incomingCalls（需先 prepareCallHierarchy）> go_symbol_references > Grep（有噪声）
├─ 找某函数调了谁
│   └─ outgoingCalls > Read 函数体 + 逐个追踪（定位失败时）
├─ 找接口实现
│   └─ goToImplementation（唯一可靠，references 找不到隐式实现）
├─ 查看私有方法
│   └─ go_search + Read（go doc 对私有方法无效）
├─ 追踪单个符号引用
│   └─ go_symbol_references（精确无噪声）
├─ 扫描命名模式
│   └─ Grep 前缀/正则（gopls 不支持模式搜索）
├─ 搜索通用关键词
│   └─ Grep 限定目录（go_search 被依赖库噪声淹没）
├─ 检查代码模式（go func/TODO）
│   └─ Grep
├─ 定位最近修改
│   └─ git blame -L / git log -p / git log -S
├─ 快速编译验证
│   └─ go_diagnostics > go build ./module > make target
├─ 安全重命名
│   └─ go_rename_symbol（"Type.Method" 格式）> Edit replace_all
├─ 修改后验证
│   └─ go_diagnostics（必调）
├─ 安全审计
│   └─ go_vulncheck
├─ 跨服务通信追踪
│   └─ 每侧 go_symbol_references + go_search，用协议 ID 串联
├─ 理解文件结构
│   └─ documentSymbol > Read 全文
├─ 理解包 API
│   └─ 小包：go_package_api；大包：go_search
├─ 理解文件依赖
│   └─ 小包：go_file_context；大包（>50 文件）：Grep + Read
├─ 理解函数上下文
│   └─ incomingCalls + outgoingCalls + documentSymbol
└─ 给子代理打包上下文
    └─ 见 [子代理打包](references/subagent-packing.md)
```

## 工作流

### 开发新功能

1. `documentSymbol` 或 `go_search` → 定位相关函数
2. `outgoingCalls` / `incomingCalls` → 理解上下游
3. `go_package_api`（仅小包）或 `go_search` → 了解需调用的包 API
4. 编辑代码
5. `go_diagnostics` → 验证（每次编辑后必调）

**incomingCalls/outgoingCalls 步骤**：
1. `go_search` → 目标函数的文件和行号
2. `prepareCallHierarchy` → 定位到函数名标识符（如 `Handle` 的 `H`，不是 `func` 也不是 receiver）
3. `incomingCalls` / `outgoingCalls` → 查询

**编辑后验证优先级**：`go_diagnostics`（最快）> `go build ./module`（更严格）> `make target`（完整流程）

### 修改/重构

1. `go_symbol_references` → 影响范围
2. `incomingCalls` / `outgoingCalls` → 调用链
3. `go_symbol_references` 找文件 → `repomix --include` 精准打包
4. 编辑代码
5. `go_diagnostics` → 验证
6. `go_rename_symbol` → 重命名（只返回 diff，需手动应用）

### 代码审查

1. `go_vulncheck` → 安全扫描
2. `go_diagnostics` → 静态分析
3. `go_symbol_references` → 追踪关键路径
4. `incomingCalls` → 调用链风险

### 跨服务通信追踪

1. 发起侧：`go_search("rpcXxx")` → 找 RPC 封装函数
2. 发起侧：`go_symbol_references("Service.rpcXxx")` → 找调用链
3. 发起侧：`go_symbol_references("Service.CallAsync")` → 找所有 RPC 出口
4. **定位协议 ID**：`go_search("MsgId_Xxx")` → 找协议 ID 定义（根据项目命名规则）
5. 接收侧：`go_search("handleXxx")` → 找处理函数
6. 接收侧：`go_symbol_references` → 找路由注册
7. 接收侧：若路由在 map 中，`Read` 路由注册文件确认
8. 用协议 ID 串联两侧

### 调试

1. `goToDefinition` → 追踪定义
2. `outgoingCalls` → 下游调用链（失败时：Read 函数体 + 逐个 goToDefinition）
3. `hover` → 类型信息
4. `go_symbol_references` → 所有调用点（优先关注当前业务模块）

## 工具优先级原则

1. **语义精确 > 文本匹配**：go_symbol_references > Grep
2. **结构理解 > 全量阅读**：documentSymbol > Read 全文
3. **调用链 > 逐个追踪**：incomingCalls/outgoingCalls > 逐个 Grep
4. **模式搜索归 Grep**：gopls 不搜索模式/正则/注释
5. **主代理不读打包内容**：repomix --output 只看摘要
6. **outgoingCalls 失败有备选**：Read + 逐个 goToDefinition
7. **三者互补**：go_search（语义精确）、go_package_api（接口理解）、Grep（全景/模式搜索）
8. **MCP 优先于 LSP**：MCP 稳定可用，LSP 需精确定位易失败
9. **大包跳过 go_file_context/go_package_api**：文件数 >50 用 Grep + Read
10. **关键词具体度决定搜索质量**：业务特有词 > 模糊词 > 通用词

## 参考文件

- [工具能力速查](references/tools.md) — MCP/LSP/Grep 工具对比与不可替代场景
- [踩坑清单](references/pitfalls.md) — 24 条实战注意事项
- [子代理打包](references/subagent-packing.md) — repomix 上下文打包流程
