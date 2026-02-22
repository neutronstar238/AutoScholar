# GitHub 仓库设置指南

## 当前状态
- 本地 Git 仓库：已初始化
- 分支：main
- 最新提交：V0.1.1
- 文件数：19 个

## 推送步骤

1. 在 GitHub 创建仓库：https://github.com/new
   - 名称：AutoScholar
   - 可见性：Public

2. 推送代码：
```bash
cd /AstrBot/AutoScholar
git remote add origin https://github.com/YOUR_USERNAME/AutoScholar.git
git push -u origin main
git push origin --tags
```

3. 版本标签：
```bash
git tag -a v0.1.1 -m "V0.1.1 初始化项目"
git push origin --tags
```

## 版本规范
格式：V<大>.<中>.<小> <内容>
- 大版本：内测为 0
- 中版本：新增功能
- 小版本：每次提交 +1
