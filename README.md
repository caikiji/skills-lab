# skills-lab

可复用的 AI 技能和规则集合，用于编排智能体工作流。从 GitHub 源码仓库随所有修改保持同步，支持安装到多个 agent harness（pi、Claude Code、Codex）。

## 配置

本仓库使用 [git-fetch-file](https://github.com/andrewmcwattersandco/git-fetch-file) 从其他仓库同步单个文件（见 `.git-remote-files`）。首次配置：

```bash
cd .temp
git clone https://github.com/andrewmcwattersandco/git-fetch-file.git
cd ./git-fetch-file
go build -o ../../bin/git-fetch-file.exe
cd ../../
git config --global alias.fetch-file '!bin/git-fetch-file.exe'
```

## 技能列表

| 技能 | 使用场景 |
|------|---------|
| `agents-md` | 生成/诊断仓库根级 AGENTS.md |
| `html-card` | 生成网页卡片/可视化 HTML |
| `mcp-builder` | MCP server 开发（Python/Node） |
| `readme-md` | 生成/精简仓库根级 README.md |
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
| `configs` | 按 `deploy.yaml` | 部署 `configs/` 内容到机器目录 |
| `--list` | - | 列出支持的 harness 及目录 |

```sh
curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi claude
curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi configs
```

## configs 部署

`deploy.yaml`（仓库根）定义 `configs/` 里每个条目要搬到哪里：

```yaml
# configs/rpiv-web-tools 目录 -> ~/.config/rpiv-web-tools
deployments:
  - src: rpiv-web-tools
    dest: ~/.config/rpiv-web-tools
    mode: copy      # copy 默认;link 暂不支持
```

- `src`：`configs/` 下的相对路径（文件或目录）
- `dest`：目标路径，支持 `~` 和 `$HOME` / `$XDG_CONFIG_HOME` 等变量
- `mode`：`copy` 复制并备份（默认）；`link` 暂不支持
- 部署依赖 python3 + PyYAML（脚本自动探测 `python3` / `python` / `py -3`）
- 目标已存在时先备份到 `<目标>.backup/<时间戳>/`，轮转策略同技能安装

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
