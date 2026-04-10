# 子代理上下文打包

主代理给子代理打包时，主代理**不读取**打包内容。

## 依赖

- [repomix](https://github.com/yamadashy/repomix)：`npm install -g repomix` 或 `npx repomix`

## 流程

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

## repomix 参数速查

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
