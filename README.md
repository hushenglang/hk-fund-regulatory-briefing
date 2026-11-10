# 香港基金管理监管与案例简报

用于 briefing 的静态网页，汇集香港基金管理行业的重要监管更新、判例及执法活动。

GitHub Pages：https://hushenglang.github.io/hk-fund-regulatory-briefing/

原 Sites 地址：https://hk-fund-regulatory-briefing.hushenglang.chatgpt.site/

## 项目结构

- `dist/index.html`：自动生成的主页，默认展示报告期最新的一期全文。
- `dist/archive/`：各期简报的独立永久链接。
- `reports/`：正式简报 HTML 原稿与 `catalog.json` 期刊目录。
- `scripts/build_home.py`：按报告期排序、生成主页和折叠历史导航。
- `.openai/hosting.json`：现有 Sites 托管配置。
- `CONTENT_GUIDELINES.md`：后续更新时沿用的内容及版式要求。

## 本地预览

无需安装依赖或构建，可直接打开 `dist/index.html`。也可在项目根目录运行：

```sh
python3 -m http.server 8000 --directory dist
```

随后访问 http://localhost:8000 。

## 更新与发布

更新时编辑 `reports/` 中的正式 HTML，并在 `reports/catalog.json` 登记唯一 ID、标题、报告期截止日和类型。运行：

```sh
python3 scripts/build_home.py
```

生成器按 `periodEnd` 从新到旧排序，主页与最新一期使用相同正文；各期链接为 `/archive/<id>.html`。ID 发布后保持不变。目录只收录正式版本，不收录重复草稿。核对报告期、规则状态、官方来源及案例措辞，检查桌面、窄屏和 A4 竖向打印效果，再提交源码与生成结果。

每次向 `main` 分支推送，`.github/workflows/pages.yml` 会自动运行生成器、校验目录与页面链接，再将 `dist/` 发布到 GitHub Pages。也可在 Actions 页面手动运行。只需提交正式 HTML 和目录更新，不必手动生成或上传 `dist/`。校验失败时停止发布，保留上一成功版本。

新增一期的步骤：

1. 将完整 HTML 放到 `reports/<id>.html`，沿用现有模板并保留 `<div class="period">` 供导航替换。
2. 在 `reports/catalog.json` 中添加 `id`、`label`、`title`、`type` 和 ISO 日期 `periodEnd`。
3. 将这两项提交到 GitHub 的 `main` 分支，或通过合并 PR 提交。
4. 在 Actions 查看构建与发布结果。主页按报告期自动选最新一期，历史链接继续保留。

上传到本地文件夹而未提交到 GitHub 不会触发发布。本流程自动发布已有文稿，不自动研究或撰写新闻。原 Sites 网站独立托管，不随 GitHub Pages 工作流更新。

当前收录 2026.10.13–10.19 周报及 2026 Q3 季度简报；季度简报包含 13 项监管更新和 17 项判例及执法活动。原始 Word 文件及内部工作文档不属于网站源码。
