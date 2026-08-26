## 配置

```bash
cd .temp
git clone https://github.com/andrewmcwattersandco/git-fetch-file.git
cd ./git-fetch-file
go build -o ../../bin/git-fetch-file.exe
cd ../../
git config --global alias.fetch-file '!bin/git-fetch-file.exe'
```
