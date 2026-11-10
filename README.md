# 香港基金管理监管与案例简报

用于 briefing 的静态网页，汇集香港基金管理行业的重要监管更新、判例及执法活动。

线上简报：https://hk-fund-regulatory-briefing.hushenglang.chatgpt.site/

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

GitHub 用于源码和版本管理；现有网站仍由 Sites 托管。推送到 GitHub 不会自动发布到现有网站，网站更新需另行执行 Sites 发布流程。

当前收录 2026.10.13–10.19 周报及 2026 Q3 季度简报；季度简报包含 13 项监管更新和 17 项判例及执法活动。原始 Word 文件及内部工作文档不属于网站源码。
