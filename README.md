# skills-lab

可复用的 AI 技能和规则集合，用于编排智能体工作流。从 GitHub 源码仓库随所有修改保持同步，支持安装到多个 agent harness（pi、Claude Code、Codex）。

## 技能列表

| 技能 | 使用场景 |
|------|---------|
| `html-card` | 生成网页卡片/可视化 HTML |
| `mcp-builder` | MCP server 开发（Python/Node） |
| `skill-creator` | 创建新技能 |
| `xlsx` | Excel 文档处理 |
| `zhihu-search` | 知乎内容搜索 |

## 一键安装

先决条件：已安装 git。

```sh
curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi
```

`pi` 表示安装到 pi 的全局技能目录 `~/.pi/agent/skills/`，重启 pi 后用 `/skill:<技能名>` 验证。

### 安装到其它 harness

| 参数 | 安装目录 | 说明 |
|------|---------|------|
| `pi` | `~/.pi/agent/skills` | pi（默认支持，传参生效） |
| `claude` | `~/.claude/skills` | Claude Code |
| `codex` | `~/.codex/skills` | OpenAI Codex |
| `--list` | - | 列出支持的 harness 及目录 |

可同时安装多个：

```sh
curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi claude
```

## 行为说明

- **更新**：重复执行同一命令即同步最新技能，旧技能自动备份到 `<安装目录>.backup/<时间戳>/`，可回滚。
- **覆盖与备份**：安装前若目标目录已有同名技能，先备份再替换，不影响无关文件。
- **自定义仓库/目录**：环境变量 `SKILLS_LAB_REPO`、`SKILLS_LAB_BRANCH` 覆盖仓库；`PI_SKILLS_DIR`、`CLAUDE_SKILLS_DIR`、`CODEX_SKILLS_DIR` 覆盖对应安装目录。
- **安全**：`curl \| sh` 会执行远程代码，请确认来源仓库可信。

## 手动安装

```sh
git clone --depth 1 https://github.com/caikiji/skills-lab.git
cp -R skills/* ~/.pi/agent/skills/
```

## 规则

`rules/` 目录存放子智能体规则、输出规范、工作规范等，供技能内部引用。
