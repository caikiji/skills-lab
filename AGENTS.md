# AGENTS.md

可复用的 AI 技能与配置集合：技能/配置由 [git-fetch-file](https://github.com/andrewmcwattersandco/git-fetch-file) 从外部仓库同步（溯源见
`.git-remote-files`），经 `install.sh` 安装到本机（pi / Claude Code / Codex）。

## 常用命令

```sh
# 一键安装(技能 + 按 deploy.yaml 部署配置)
curl -fsSL https://raw.githubusercontent.com/caikiji/skills-lab/main/install.sh | sh -s -- pi configs

# 同步外部仓库内容到本仓库
cd .temp
git clone https://github.com/andrewmcwattersandco/git-fetch-file.git
cd ./git-fetch-file
go build -o ../../bin/git-fetch-file.exe
cd ../../
git config --global alias.fetch-file '!bin/git-fetch-file.exe'
git fetch-file pull
```

## 约定

- 修改 `skills/`、`configs/` 内容会被 `git fetch-file pull` 覆盖，变更请走外部源仓库
- 新增技能须创建 `skills/<name>/SKILL.md`（含 name/description），并更新 README 技能表
- `install.sh` / `deploy.yaml` 改动需本地测试（configs 部署用临时目录验证）
- 提交信息用中文；编码约定见 `templates/AGENTS.md`
