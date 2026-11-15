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

## 三份输出

每期保留汇总版 `dist/archive/<id>.html`，并自动生成 `dist/archive/<id>-regulatory.html`（监管更新）及 `dist/archive/<id>-cases.html`（判例及执法）。`dist/index.html` 仅展示最新汇总版，历史菜单也只列汇总版。两份专版保留完整对应栏目、来源及表格，独立打开/打印，不加入首页导航；法律 AI 与跨栏目摘要留在汇总版。运行原构建命令即可生成全部输出。

## Dashboard

`dist/dashboard.html` 是独立的合规工作台，不替换 `index.html`。每次构建从目录中选择报告期最新的周报，自动提取两栏各前两项简短标题，显示完整栏目条数，并跳转到当期独立专版。季度报告不会取代 dashboard 的周报来源。

`templates/dashboard.html` 管理三个模块的布局；`scripts/build_dashboard.py` 管理数据提取。“合规清单提醒”已接入用户提供的2026年度文档，支持查看只读清单、状态筛选与搜索。

## 合规清单提醒

`data/compliance-2026.json` 保存更新文档的29项事项（18项监管日历及11项定期监控）、原文日期、频率、责任方及原文状态；原始DOCX不进入网站。`scripts/build_compliance.py` 生成 `dist/compliance.html`，`assets/compliance.js` 根据浏览器当前香港日期计算提醒，提供只读筛选与搜索；仪表板模块3链接到清单。

月度FRR不将未注明月份的“已完成”沿用到本月，单列“待确认”；其余年度/半年度状态按文档保留。12月31日起开始的PI确认按启动日显示。涉及财年后若干个月的期限保留原条件，不推定日期。年份变更时提示需要新年度资料，不自动继承完成情况。用户已明确确认将此2026年度清单内容按原文公开发布到现有仓库和Pages；原始DOCX不上传。此授权不扩展到其他内部文档。

## 每日待办

工作台下方直接展示8:30优先级、9:00晨会、10:00处理紧急事项、14:00空白时段、16:00监管更新与任务复盘。四项有内容的待办支持勾选；勾选状态仅保存在当前浏览器localStorage，按香港日期隔日重置，不跨设备同步，不发送提醒通知。

两个内容模块右上角按用户选择显示页面本次生成更新的香港日期，不代表周报新闻已覆盖到当天。工作台顶栏不再显示周报范围。

2026final版本：B节中的11项明确年度、半年、月度或定期监控事项按用户指定的2026-12-31目标日期提醒，保留原频率、监控范围、责任方、输出与升级触发条件。B节未注明完成情况，暂列待确认。5项仅按事件/交易触发的事项不另设年底目标。页面支持监管日历/定期监控分组筛选，默认显示全部待跟进事项。

发布范围：用户已确认新版11项定期监控与监管日历采用一致的展示及公开发布方式。原频率、责任方、监控范围、输出文件和升级条件随清单展示；原始DOCX不上传。

监管更新专版的大标题统一为“监管更新-香港基金管理行业”，官方新闻链接默认在新标签页打开。
