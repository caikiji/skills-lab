# skills-lab

可复用的 AI 技能与配置集合：技能/配置经 [git-fetch-file](https://github.com/andrewmcwattersandco/git-fetch-file) 从外部源仓库同步（溯源见 `.git-remote-files`），由 `install.sh` 安装到本机（pi / Claude Code / Codex）。

## 约定

- 新增技能须创建 `skills/<name>/SKILL.md`（含 name/description），并更新 README 技能表
- **写/改 skill 一律在项目 `skills/<name>/` 内进行**：新增、修改、评审都只碰项目副本；用户级目录（`~/.pi/agent/skills/` 等）是 install.sh 的安装产物，禁止手改，同步走 `install.sh`
- `install.sh` / `deploy.yaml` 改动需本地测试（configs 部署用临时目录验证）
- 提交信息用中文

## 边界

- `skills/`、`configs/`：由 `git fetch-file pull` 从外部源覆盖，改动会丢失；变更请走外部源仓库（`.git-remote-files` 记录来源）
- `bin/`、`.temp/`：本地构建产物（go 构建、git clone 缓存），不入库
- `install.sh` / `deploy.yaml`：改动未本地实测前不提交（`configs` 部署会覆盖本机配置）

## 常用命令

```sh
# 同步外部源内容到本仓库（首次配置见 README）
git fetch-file pull
```

```sh
# 一键安装到本机（pi + configs 部署）
curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi configs
```

## 深文档

- `README.md`：技能列表、安装参数、configs 部署格式
- `templates/AGENTS.md`：编码约定（提交/注释语言、代码风格、冲突处理）
