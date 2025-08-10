# poker-assets 数据仓库

用于存放（或分发）德州扑克项目的数据资产：截图、录屏视频、打包 ZIP 等。建议优先使用 GitHub Releases 上传大文件（简便、配额友好），如需版本化大文件再考虑 Git LFS。

## 方式A：使用 Releases（推荐）
1. 打开仓库 → Releases → Draft a new release
2. Tag（如 v0.1）与标题（如 "dataset v0.1"）
3. 将您的大文件（例如 poker_dataset_full.zip、*.mp4）拖拽到附件区
4. Publish release 后，把下载链接发给协作者

命令行（可选，需安装 gh CLI 并已登录：`gh auth login`）
```bash
# 创建或更新发布并上传资产
# 注意替换文件名
gh release create v0.1 -t "dataset v0.1" -n "initial dataset" \
  poker_dataset_full.zip your_video.mp4 \
  -R tengfei1688/poker-assets

# 追加上传到已有发布
gh release upload v0.1 poker_dataset_full.zip -R tengfei1688/poker-assets
```

优点：
- 支持单文件 > 100MB（上限远高于 LFS 免费配额）
- 不占用 Git LFS 带宽配额；下载直链便于脚本化

## 方式B：使用 Git LFS（可选）
仅当你希望将大文件纳入 Git 版本历史时使用。注意 Git LFS 有带宽/存储配额，可能产生限流。

```bash
# 一次性安装 LFS（全局）
git lfs install

# 初始化或克隆仓库
git clone https://github.com/tengfei1688/poker-assets.git
cd poker-assets

# 跟踪大文件类型（按需调整）
git lfs track "*.mp4" "*.mov" "*.mkv" "*.avi" "*.zip"

echo "*.mp4 filter=lfs diff=lfs merge=lfs -text" >> .gitattributes
echo "*.mov filter=lfs diff=lfs merge=lfs -text" >> .gitattributes
echo "*.mkv filter=lfs diff=lfs merge=lfs -text" >> .gitattributes
echo "*.avi filter=lfs diff=lfs merge=lfs -text" >> .gitattributes
echo "*.zip filter=lfs diff=lfs merge=lfs -text" >> .gitattributes

# 添加并推送
git add .gitattributes poker_dataset_full.zip your_video.mp4
git commit -m "add dataset"
git push origin main
```

## 文件命名建议
- 统一前缀区分来源：`mobile_*.mp4`（手机录屏）、`pc_*.png`（PC H5 截图）
- 数据包命名：`poker_dataset_YYYYMMDD.zip`

## 隐私与合规
仅用于学习/线下复盘；上传前请确保无敏感信息，遵守平台条款与当地法律。

---

如需我自动拉取你上传的文件进行抽帧、伪标注和训练，请发布 Release 后把链接发我。也可以把该仓库权限设置为私有并邀请我协作，我可直接在 CI 里跑处理管线.