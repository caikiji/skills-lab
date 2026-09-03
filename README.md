# skills-lab

可复用的 AI 技能与配置集合：技能经 [git-fetch-file](https://github.com/andrewmcwattersandco/git-fetch-file) 从上游源仓库同步（溯源见 `.git-remote-files`），zip 直链分发的用 `fetch-zip.sh`（溯源见 `.git-remote-zips`）；`install.sh` 一键安装到本机 pi / Claude Code / Codex。

## 特性

- **多 harness 安装**：一套技能装到 pi、Claude Code、Codex，也可按 `deploy.yaml` 部署 `configs/` 到任意目录
- **源头可溯**：技能/配置来自上游仓库（Anthropic skills、pi-setup 等），提交锁定在 `.git-remote-files`，不手改
- **可重复更新**：重复执行安装命令即同步最新技能，旧版本自动备份到 `.backup/<时间戳>/`，可回滚
- **可定制覆盖**：`SKILLS_LAB_REPO` / `PI_SKILLS_DIR` 等环境变量覆盖仓库与安装目录
- **备份轮转**：每个目标保留最近 5 份备份（`SKILLS_BACKUP_KEEP` 可调）

## 快速开始

先决条件：git；`configs` 部署附加 python3 + PyYAML（脚本自动探测 `python3` / `python` / `py -3`）。

```sh
# 一键安装到 pi 的全局技能目录
curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi

# 重启 pi 后用 /skill:<技能名> 验证，例如 /skill:xlsx
```

安装到其它 harness 或部署 configs：

```sh
curl -fsSL .../install.sh | sh -s -- pi claude       # pi + Claude Code
curl -fsSL .../install.sh | sh -s -- pi configs      # pi + 按 deploy.yaml 部署配置
```

支持的 harness 参数：`pi`（`~/.pi/agent/skills`）、`claude`（`~/.claude/skills`）、`codex`（`~/.codex/skills`）、`configs`（按 `deploy.yaml`），`--list` 查看全部。configs 部署目标已存在时默认跳过，加 `--force` 才备份后覆盖。

## 技能列表

| 技能 | 使用场景 |
|------|---------|
| `agents-style` | 生成/诊断仓库根级 AGENTS.md |
| `code-style` | 约束 agent 生成代码的可维护性（体量/结构/信息三抓手 + 变更导航） |
| `commit-style` | 按 Conventional Commits 规范生成/校验提交信息 |
| `engineering` | 编码工作流技能包（Matt Pocock）：ask-matt/tdd/implement/code-review/to-spec 等 18 个，清单见包内 README |
| `herdr` | 控制 Herdr 终端多路复用器（面板/标签页/工作区） |
| `jupyter-attach` | 长驻 Jupyter 会话管理（tmux 式 attach，跨调用持久状态） |
| `productivity` | 通用效率技能包（Matt Pocock）：grilling/handoff/teach 等 7 个，清单见包内 README |
| `qq-send` | 通过 QQ 官方机器人向个人用户发消息/文件/图片（一次性 CLI，agent 经 bash 调用） |
| `readme-style` | 生成/精简仓库根级 README.md |
| `xlsx` | Excel 文档处理 |
| `zhihu-search` | 知乎内容搜索 |

## 文档

- **同步上游**：`git fetch-file pull`；首次配置 git-fetch-file 见下方“源码同步”
- **同步 zip 分发技能**：`./fetch-zip.sh <url> <target> [--strip]` 添加并登记清单；`./fetch-zip.sh pull` 重放更新；`list` 查看，详见脚本头部注释
- **configs 部署格式**：`deploy.yaml`（`src` / `dest` / `mode`；目标已存在默认跳过，`--force` 才覆盖并先备份到 `<dest>.backup/<时间戳>/`）
- **行为说明**：覆盖与备份策略、自定义仓库/目录的环境变量、安全提示（`curl \| sh` 会执行远程代码，请确认来源可信）
- **贡献**：新增技能须含 `skills/<name>/SKILL.md`（name/description）并更新本表；`install.sh` / `deploy.yaml` 改动需本地实测后提交；提交信息用中文。详见 [AGENTS.md](AGENTS.md)

### 源码同步（首次配置 git-fetch-file）

```bash
cd .temp
git clone https://github.com/andrewmcwattersandco/git-fetch-file.git
cd ./git-fetch-file
go build -o ../../bin/git-fetch-file.exe
cd ../../
git config --global alias.fetch-file '!bin/git-fetch-file.exe'
```

## 手动安装

```sh
git clone --depth 1 https://github.com/caikiji/skills-lab.git
cp -R skills/* ~/.pi/agent/skills/
```
