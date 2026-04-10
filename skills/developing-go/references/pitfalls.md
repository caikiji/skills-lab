# 踩坑清单

## 目录

1. [LSP 定位问题](#lsp-定位问题)
2. [go_search 使用注意](#go_search-使用注意)
3. [符号引用 vs 接口实现](#符号引用-vs-接口实现)
4. [go_rename_symbol](#go_rename_symbol)
5. [go_file_context / go_package_api](#go_file_context--go_package_api)
6. [go doc 限制](#go-doc-限制)
7. [go_diagnostics](#go_diagnostics)
8. [go_vulncheck](#go_vulncheck)
9. [跨服务追踪](#跨服务追踪)
10. [repomix](#repomix)
11. [MCP vs LSP 可用性](#mcp-vs-lsp-可用性)

## LSP 定位问题

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

## go_search 使用注意

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

## 符号引用 vs 接口实现

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

## go_rename_symbol

9. **需要限定名格式**
   - `symbol: "Handle"` → "failed to resolve name"
   - 必须用 `symbol: "Service.Handle"` 格式（含 receiver type）

10. **不自动应用修改**
    - 返回 diff 预览后，尝试立即再 rename 报 "failed to resolve name"
    - rename 只返回 diff 不修改文件，gopls 缓存基于磁盘文件状态
    - 需手动用 Edit 工具应用 diff

## go_file_context / go_package_api

11. **大业务包的 go_file_context 一律跳过**
    - 文件数 >50 的包，输出 150KB+
    - 原因：Go 同包文件共享符号，file_context 会拉入全部包内声明
    - 替代：`Grep` 定位 → `Read` 指定行范围；或 `documentSymbol` 看结构

11b. **go_package_api 对大业务包输出巨大**
    - 大包（如 protobuf 生成代码）输出 1MB+
    - 仅适合小包/子包（输出 <50KB 可接受）
    - 大包替代：`go_search` 搜索具体符号名
    - 部分包返回空结果，用 `go_search` 代替

## go doc 限制

12. **对私有方法完全无效**
    - `go doc Type.method`、`-all`、`-src` 均报 "no method or field"
    - 替代：go_search 定位 → Read 阅读，或 hover 查看签名

13. **对方法需要完整包路径**
    - `go doc handleXxx` → "no symbol"
    - 必须用 `go doc <module_path>/<pkg> Type.Method` 格式

## go_diagnostics

14. **修改后即时反馈，还可能发现预存问题**
    - 故意改名触发编译错误：精确定位到行列号
    - 修复后发现预存 lint 问题（如 unused parameter）

## go_vulncheck

15. **检出依赖漏洞，需人工判断影响**
    - 可检出 30+ 漏洞（crypto/tls、JWT、gRPC 等）
    - 标准库漏洞多为 DoS 类型，需评估是否暴露给外部输入
    - 第三方依赖漏洞需关注是否在关键路径上

## 跨服务追踪

16. **LSP callHierarchy 无法跨越服务边界**
    - 只能追踪同一进程/包内的调用链
    - 每侧独立追踪，用协议 ID 串联两端

17. **路由注册在 map 中，需 Read 路由文件确认**
    - `go_symbol_references` 可找到处理函数定义，但 map 字面量中的注册关系需 Read 确认

## repomix

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

## MCP vs LSP 可用性

23. **MCP 工具稳定，LSP 操作需精确定位**
    - MCP：始终可用，推荐优先
    - LSP：需精确定位到标识符字符位置，定位偏差即失败
    - 定位失败时改用 MCP 工具

24. **go_workspace 是所有 gopls 操作的前提**
    - 首次调用任何 gopls 工具前必须先调 go_workspace
    - 跳过可能导致 "server is starting" 或 "identifier not found"
