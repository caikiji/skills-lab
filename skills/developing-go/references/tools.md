# 工具能力速查

## gopls MCP 工具（稳定可用，推荐优先）

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

## gopls LSP 操作（需精确定位）

| 操作 | 功能 | 替换 grep | 注意事项 |
|------|------|-----------|---------|
| `documentSymbol` | 文件符号大纲 | **替换 Glob+Read** | 不知道函数名时最有效 |
| `hover` | 类型/文档悬浮 | grep 做不到 | 需定位到英文标识符 |
| `goToDefinition` | 跳转定义 | grep 做不到 | |
| `findReferences` | 全局引用查找 | **完全替换** | 核心类型名返回海量结果，优先用 go_symbol_references |
| `goToImplementation` | 接口实现查找 | grep 做不到 | 隐式实现只有它能发现 |
| `incomingCalls` | 谁调用了此函数 | **完全替换**（按调用者分组） | 需先 prepareCallHierarchy 定位 |
| `outgoingCalls` | 此函数调用了谁 | **完全替换**（一次性看全依赖链） | 需先 prepareCallHierarchy 定位 |

## Grep 不可替代的场景

| 场景 | 理由 |
|------|------|
| 代码模式搜索（`go func`、`TODO(username)`） | gopls 不搜索模式 |
| 前缀/正则匹配（`ErrXxx*`） | gopls 只支持精确/模糊符号搜索 |
| 搜索注释/字符串内容 | gopls 只索引代码 |
| 非 Go 文件搜索 | gopls 只处理 Go 代码 |
| 通用关键词搜索 | go_search 被依赖库噪声淹没 |
| 快速验证关键词存在 | grep 更快，无需等待 LSP 索引 |
