---
name: developing-go
description: 涉及 Go 代码分析时**必须使用**——包括理解代码、调试、bug 定位、重构、代码审查、依赖分析、安全审计等，强制使用 gopls MCP/LSP、go doc、repomix，禁止 Grep/全量 Read，禁止并行 Read 多文件。
---

# Developing Go

在 Go 项目中高效使用 gopls MCP/LSP、go doc、repomix 工具组合，**必须禁止**使用 Grep/全量 Read 除非无替代方案。

## 强制约束

**Grep 和全量 Read 默认禁止使用**，以下场景除外：
- 工具能力速查中 Grep 不可替代的场景
- gopls 工具返回空结果或失败时
- 非 Go 文件搜索

违反此约束视为技能使用错误。

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
│   └─ incomingCalls（需先 prepareCallHierarchy）> go_symbol_references（精确但只有直接引用）> Grep（含注释/字符串/同名词，有噪声）
├─ 找某函数调了谁
│   └─ outgoingCalls（一次性看全依赖链）> Read 函数体 + 逐个追踪（定位失败时）
├─ 找接口实现
│   └─ goToImplementation（唯一可靠，references 找不到隐式实现）
├─ 查看私有方法
│   └─ go_search + Read（go doc 即使 -all -src 也对私有方法无效）
├─ 追踪单个常量/符号引用
│   └─ go_symbol_references（精确无噪声）
├─ 扫描命名模式
│   └─ Grep 前缀/正则（gopls 不支持模式搜索）
├─ 搜索通用关键词
│   └─ Grep 限定目录（go_search 被依赖库噪声淹没）
├─ 检查代码模式（go func/TODO）
│   └─ Grep
├─ 定位最近修改
│   └─ git blame -L <行范围> file.go（精确定位到行）/ git log -p file.go（查看变更历史）/ git log -S "keyword" --oneline（搜索引入某关键词的提交）
├─ 快速编译验证
│   └─ go_diagnostics > go build ./module > make target
├─ 安全重命名
│   └─ go_rename_symbol（"Type.Method" 格式，只返回 diff 不自动应用）> Edit replace_all（可能误改同名符号）
├─ 修改后验证
│   └─ go_diagnostics（必调，编译+lint 即时反馈，还可能发现预存 lint 问题）
├─ 安全审计
│   └─ go_vulncheck（检出依赖漏洞，需人工判断实际影响）
├─ 跨服务通信追踪
│   └─ 每侧 go_symbol_references + go_search，用协议 ID 串联
├─ 理解文件结构
│   └─ documentSymbol > Read 全文
├─ 理解包 API
│   └─ 小包/子包：go_package_api > go doc <pkg>（大业务包输出 1MB+，改用 go_search）
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
   - outgoingCalls 失败条件：gopls 未索引文件、函数是接口方法无具体实现、函数体过于复杂
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

## 工具能力速查

### gopls MCP 工具（稳定可用，推荐优先）

| 工具 | 功能 | 替换 grep | 注意事项 |
|------|------|-----------|---------|
| `go_workspace` | 工作区结构概览 | N/A | 会话初始化必调，触发索引 |
| `go_search` | 模糊符号搜索 | **完全替换**（语义精确） | 通用词噪声大，关键词要具体 |
| `go_file_context` | 文件跨包依赖摘要 | grep 做不到 | 大包输出 150-250KB，慎用 |
| `go_package_api` | 包完整 API 列表 | grep 做不到 | 大包输出 1MB+，仅适合小包/子包 |
| `go_symbol_references` | 精确符号引用 | **完全替换**（无注释/字符串误报） | 可能返回大量结果 |
| `go_diagnostics` | 编译+lint 诊断 | grep 做不到 | 每次编辑后必调 |
| `go_rename_symbol` | 安全重命名 | grep 做不到 | 需 `Type.Method` 格式，只返回 diff |
| `go_vulncheck` | 漏洞扫描 | grep 做不到 | 检出依赖漏洞，需人工判断影响 |

### gopls LSP 操作（需精确定位）

| 操作 | 功能 | 替换 grep | 注意事项 |
|------|------|-----------|---------|
| `documentSymbol` | 文件符号大纲 | **替换 Glob+Read** | 不知道函数名时最有效 |
| `hover` | 类型/文档悬浮 | grep 做不到 | 需定位到英文标识符 |
| `goToDefinition` | 跳转定义 | grep 做不到 | |
| `findReferences` | 全局引用查找 | **完全替换** | 核心类型名返回海量结果，优先用 go_symbol_references |
| `goToImplementation` | 接口实现查找 | grep 做不到 | 隐式实现只有它能发现 |
| `incomingCalls` | 谁调用了此函数 | **完全替换**（按调用者分组，含间接调用） | 需先 prepareCallHierarchy 定位 |
| `outgoingCalls` | 此函数调用了谁 | **完全替换**（一次性看全依赖链） | 需先 prepareCallHierarchy 定位 |

### Grep 不可替代的场景

| 场景 | 理由 |
|------|------|
| 代码模式搜索（`go func`、`TODO(username)`） | gopls 不搜索模式 |
| 前缀/正则匹配（`ErrXxx*`） | gopls 只支持精确/模糊符号搜索 |
| 搜索注释/字符串内容 | gopls 只索引代码 |
| 非 Go 文件搜索 | gopls 只处理 Go 代码 |
| 通用关键词搜索 | go_search 被依赖库噪声淹没 |
| 快速验证关键词存在 | grep 更快，无需等待 LSP 索引 |

## 踩坑清单

### LSP 定位问题

1. **prepareCallHierarchy 必须定位到函数名标识符**
   - 定位到 `func` 关键字 → "identifier not found"
   - 定位到 receiver 名（如 `s`）→ "s is not a function"
   - 正确：定位到函数名首字母。如 `func (s *Service) Handle()` 定位到 `H`

2. **hover 必须定位到英文标识符**
   - 非 ASCII 字符行（如中文注释）报 "rune error"

3. **LSP 首次调用可能 "server is starting"**
   - 先调用 `go_workspace` 或 MCP 工具触发索引

4. **prepareCallHierarchy 对非索引文件可能失败**
   - 报 "identifier not found"
   - 先用 MCP 工具触发索引再重试

### go_search 使用注意

5. **通用关键词噪声极大**
   - 搜索 `Handler`、`Redis`、`Manager` 等通用词，返回大量第三方依赖库符号
   - 用更具体的词（`OrderHandler`、`RedisPool`），或改用 Grep 限定项目目录

5b. **关键词具体度决定搜索质量**
   - 精确业务词（`UserSignIn`）→ 结果精准
   - 模糊业务词（`CheckIn`）→ 大量无关结果
   - 通用词（`DailyReward`）→ 大量噪声
   - 原则：优先用业务领域特有术语

6. **不确定函数名时 go_search 可能找不到**
   - 搜 "CreateOrder" 找到常量但找不到入口函数（实际名为 `handlePlaceOrder`）
   - 改用 `documentSymbol` 扫描文件结构

### 符号引用 vs 接口实现

7. **go_symbol_references 与 goToImplementation 语义不同**
   - `go_symbol_references`：找"代码中写出了这个名字的位置"
   - `goToImplementation`：找"满足该接口的类型"
   - 找接口实现**必须**用 goToImplementation

8. **LSP findReferences 对核心类型名返回海量结果**
   - 用 `go_symbol_references` 指定 `Type.Method` 限定名

8b. **go_symbol_references 可能返回大量结果**
   - 常用方法可能 50-100+ 引用
   - 优先关注当前业务模块，跳过无关模块
   - 大量结果说明函数被广泛使用，修改需格外谨慎

### go_rename_symbol

9. **需要限定名格式**
   - `symbol: "Handle"` → "failed to resolve name"
   - 必须用 `symbol: "Service.Handle"` 格式（含 receiver type）

10. **不自动应用修改**
    - 返回 diff 预览后，尝试立即再 rename 报 "failed to resolve name"
    - rename 只返回 diff 不修改文件，gopls 缓存基于磁盘文件状态
    - 需手动用 Edit 工具应用 diff

### go_file_context / go_package_api

11. **大业务包的 go_file_context 一律跳过**
    - 文件数 >50 的包，输出 150KB+
    - 原因：Go 同包文件共享符号，file_context 会拉入全部包内声明
    - 替代：`Grep` 定位 → `Read` 指定行范围；或 `documentSymbol` 看结构

11b. **go_package_api 对大业务包输出巨大**
    - 大包（如 protobuf 生成代码）输出 1MB+
    - 仅适合小包/子包（输出 <50KB 可接受）
    - 大包替代：`go_search` 搜索具体符号名
    - 部分包返回空结果，用 `go_search` 代替

### go doc 限制

12. **对私有方法完全无效**
    - `go doc Type.method`、`-all`、`-src` 均报 "no method or field"
    - 替代：go_search 定位 → Read 阅读，或 hover 查看签名

13. **对方法需要完整包路径**
    - `go doc handleXxx` → "no symbol"
    - 必须用 `go doc <module_path>/<pkg> Type.Method` 格式

### go_diagnostics

14. **修改后即时反馈，还可能发现预存问题**
    - 故意改名触发编译错误：精确定位到行列号
    - 修复后发现预存 lint 问题（如 unused parameter）

### go_vulncheck

15. **检出依赖漏洞，需人工判断影响**
    - 可检出 30+ 漏洞（crypto/tls、JWT、gRPC 等）
    - 标准库漏洞多为 DoS 类型，需评估是否暴露给外部输入
    - 第三方依赖漏洞需关注是否在关键路径上

### 跨服务追踪

16. **LSP callHierarchy 无法跨越服务边界**
    - 只能追踪同一进程/包内的调用链
    - 每侧独立追踪，用协议 ID 串联两端

17. **路由注册在 map 中，需 Read 路由文件确认**
    - `go_symbol_references` 可找到处理函数定义，但 map 字面量中的注册关系需 Read 确认

### repomix

18. **--include 用 glob 模式，不支持正则**
    - 逗号分隔多个 glob：`"service/handler*.go,model/entity*.go"`

19. **--stdin 期望相对路径**
    - 需在仓库根执行

20. **--include-diffs 无未推送变更时输出为空**
    - 正常行为

21. **--compress 压缩率因文件而异**
    - 小文件 ~72%，大文件 ~59%

22. **主代理不应读取打包内容**
    - `--output` 写临时文件后 Bash 只返回摘要
    - 主代理只传文件路径给子代理

### MCP vs LSP 可用性

23. **MCP 工具稳定，LSP 操作需精确定位**
    - MCP：始终可用，推荐优先
    - LSP：需精确定位到标识符字符位置，定位偏差即失败
    - 定位失败时改用 MCP 工具

24. **go_workspace 是所有 gopls 操作的前提**
    - 首次调用任何 gopls 工具前必须先调 go_workspace
    - 跳过可能导致 "server is starting" 或 "identifier not found"

## 子代理上下文打包

**积极使用 repomix，禁止并行 Read**——需要读取多个文件时，必须用 repomix 打包，禁止并行调用 Read 工具。

### 依赖

- [repomix](https://github.com/yamadashy/repomix)：`npm install -g repomix` 或 `npx repomix`

### 流程

1. **主代理用 gopls 确定相关文件**
   - `outgoingCalls` 提取下游依赖文件列表（最精准）
   - `go_symbol_references` 提取引用文件列表
   - 比通配符更精准，只包含实际依赖的文件

2. **主代理执行 repomix**
   ```bash
   repomix --include "file1.go,file2.go,..." --compress --output .tmp/context.txt --style xml
   ```
   - `--output` 模式下 Bash 只返回摘要（token/文件数），不加载内容到主代理上下文
   - 路径建议：输出到项目临时目录 `.tmp/context.txt`

3. **主代理把文件路径传给子代理**
   > 请读取 .tmp/context.txt 获取完整上下文，然后执行以下任务：...

4. **子代理按需补充**
   - `--compress` 可能丢失细节，子代理可 Read 原文件补充

**实测**：10 文件模块，未压缩 45K tokens → 压缩后 12K tokens（72% 压缩率）

### repomix 参数速查

| 参数 | 说明 |
|------|------|
| `--include "glob1,glob2"` | glob 模式，逗号分隔（不支持正则） |
| `--compress` | Tree-sitter 压缩，小文件 ~72%，大文件 ~59% |
| `--style xml/markdown/json` | xml=AI 友好、markdown=人读、json=程序处理 |
| `--include-logs --include-logs-count N` | 附 git 日志 |
| `--include-diffs` | 附 git diff（需有未推送变更） |
| `--output path` | 指定输出位置 |
| `--stdin` | 管道输入文件列表（期望相对路径，需在仓库根执行） |
| `--remote <url> --remote-branch <name>` | 打包远程仓库 |
