# 香港基金管理监管与案例简报

用于 briefing 的静态网页，汇集香港基金管理行业的重要监管更新、判例及执法活动。

线上简报：https://hk-fund-regulatory-briefing.hushenglang.chatgpt.site/

## 项目结构

- `dist/index.html`：网站完整页面，包含内容与样式。
- `.openai/hosting.json`：现有 Sites 托管配置。
- `CONTENT_GUIDELINES.md`：后续更新时沿用的内容及版式要求。

## 本地预览

无需安装依赖或构建，可直接打开 `dist/index.html`。也可在项目根目录运行：

```sh
python3 -m http.server 8000 --directory dist
```

随后访问 http://localhost:8000 。

## 更新与发布

编辑 `dist/index.html` 后，核对报告期、规则状态、官方来源及案例措辞，检查桌面、窄屏和 A4 竖向打印效果，再提交到 Git。

GitHub 用于源码和版本管理；现有网站仍由 Sites 托管。推送到 GitHub 不会自动发布到现有网站，网站更新需另行执行 Sites 发布流程。

当前页面为 2026 Q3 版本，包含 13 项监管更新和 17 项判例及执法活动。原始 Word 文件及内部工作文档不属于网站源码。
