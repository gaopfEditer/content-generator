# content-generator

币圈、科技、技术及相关方向的内容生成与模板产线仓库。把「选题规则、写作模板、段子多方向产线、单币决策工具链」和「解锁线索全自动草稿流水线」从本地工作区种子化到此，供 Agent 与人协作扩写。

## 仓库用途

| 模块 | 做什么 |
|------|--------|
| **content-os** | 资讯创作官主系统：分类与筛选、模板、playbook、Python 小工具、段子（duanzi）四方向产线 |
| **infinite-work-mode** | 解锁线索 → 结构化卡 → 草稿 → L1 自检 → 人工 L2 的迭代流水线（prompt + 模板 + memory） |
| **ROLES-交易观察员-资讯创作官.md** | 交易观察员与资讯创作官的职责边界摘要（完整版见 `content-os/roles-boundary.md`） |

**本 seed 刻意未包含：**

- `content-os/topics/` 下全部历史选题成稿（体积大、含大量样稿与素材路径）
- 各方向 `inbox/` 的大体量线索 dump

克隆后请在本机或 CI 环境自行创建 `content-os/topics/`、`content-os/inbox/` 并按 [`content-os/README.md`](content-os/README.md) 的状态机开工。`index.md` / `log.csv` 保留规则与系统文件说明，**不**附带可点击的历史选题目录。

## 目录地图

```text
.
├── README.md                          # 本文件
├── ROLES-交易观察员-资讯创作官.md      # 角色边界（入口）
├── content-os/
│   ├── README.md                      # Content OS 规则、状态机、操作规范
│   ├── index.md                       # 选题索引（seed 版：无历史 topics 行）
│   ├── log.csv                        # 变更流水（历史审计，路径可能指向未打包的 topics）
│   ├── roles-boundary.md              # 角色边界（权威）
│   ├── sources.md / filter.md / categories.md / calendar.md / resources.md
│   ├── topic-taxonomy.md / topic-taxonomy.json
│   ├── templates/                     # brief / research / draft / 决策辅助短讯 等
│   ├── playbooks/                     # 如 单币决策稿.md
│   ├── tools/                         # coin_data.py / coin_news.py / logic_chart.py
│   └── duanzi/                        # 段子产线：crypto / invest / scitech / engineering
│       ├── config/directions.yaml
│       ├── directions/<方向>/{inbox,drafts}/
│       ├── templates/段子成稿.md
│       └── samples/、stats/、scripts/
└── infinite-work-mode/
    ├── README.md                      # 无限工作模式说明
    ├── AGENT.md                       # Agent 边界
    ├── prompts/                       # boot / draft_unlock
    ├── templates/                     # unlock_card / self_check / run_report
    ├── memory/                        # lessons / style_notes（跨轮学习）
    ├── inbox/ drafts/ published/ runs/
    └── scripts/
└── web/                               # 段子产线 Web 控制台（FastAPI + Vite）
    ├── README.md
    ├── backend/
    └── frontend/
```

## 模板工作流（Content OS）

标准选题走 **brief → research → draft → review**，状态机见 [`content-os/README.md`](content-os/README.md)：

```text
inbox → researching → drafting → reviewing → ready → published → archived
```

1. **收线索**：写入 `content-os/inbox/`（需先在 `sources.md` 确认来源平台）。
2. **立项**：建 `topics/C-YYYYMMDD-NN-短标题/`，填 `brief.md`；**没有 brief 不准写 draft**。
3. **研究 / 成稿**：事实进 `research.md`，成稿进 `draft.md`；只使用 [`content-os/templates/README.md`](content-os/templates/README.md) 登记的模板。
4. **登记**：更新 `index.md`，向 `log.csv` **只追加**一行。

**已锁定的成稿形态（节选）：**

- `templates/决策辅助短讯.md` — 单事件方向预期 + 逻辑链 + 验证/失效（禁止买卖建议）
- `templates/事件定价周表.md` — 深度/长文周表
- `templates/解锁异动短讯.md` — 解锁看板异动
- `playbooks/单币决策稿.md` + `tools/coin_data.py` / `coin_news.py` / `logic_chart.py` — 单币快评与逻辑图

**段子产线（duanzi）** 与资讯 `topics/` 分离：四方向配置见 `duanzi/config/directions.yaml`，成稿模板见 `duanzi/templates/段子成稿.md`，各方向示例草稿在 `duanzi/directions/*/drafts/`。**Web 控制台**见仓库根目录 [`web/README.md`](web/README.md)，可在浏览器中推进进料→成稿→自检→待发状态机（发布仍须人工确认，不代发社交平台）。

## Web 控制台（段子流水线）

本地启动步骤摘要：

1. 终端 A：`cd web/backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
2. 终端 B：`cd web/frontend && npm install && npm run dev`
3. 打开 http://127.0.0.1:5173 — 选择方向、跑进料/去重/成稿、编辑草稿、查看/累加 `stats/daily.csv`

模型：**Cursor Pro API** 为主（`CURSOR_API_KEY` 环境变量），**Ollama** 为备（`config/runtime.json`，勿提交密钥）。详见 [`web/README.md`](web/README.md)。

## 无限工作模式（Infinite Work Mode）

面向 **交易观察员 unlock 线索** 的全自动草稿线：核验 → 结构化卡 → 草稿 → L1 机械自检 → 人工 L2 发/弃。循环与验收标准见 [`infinite-work-mode/README.md`](infinite-work-mode/README.md)。

## 角色边界

- **交易观察员**：数据、看板、线索、早报；不写资讯成稿。
- **资讯创作官**：按模板写稿；不维护解锁爬虫/看板。

详见 [`ROLES-交易观察员-资讯创作官.md`](ROLES-交易观察员-资讯创作官.md) 与 [`content-os/roles-boundary.md`](content-os/roles-boundary.md)。

## 快速入口

| 你想… | 打开 |
|--------|------|
| **用浏览器跑段子流水线** | [`web/README.md`](web/README.md)（`npm run dev` + `uvicorn`） |
| 了解全套规则 | [`content-os/README.md`](content-os/README.md) |
| 选模板写稿 | [`content-os/templates/README.md`](content-os/templates/README.md) |
| 跑单币决策稿 | [`content-os/playbooks/单币决策稿.md`](content-os/playbooks/单币决策稿.md) |
| 开段子四方向 | [`content-os/duanzi/IMPLEMENTATION.md`](content-os/duanzi/IMPLEMENTATION.md) |
| 跑 unlock 自动线 | [`infinite-work-mode/AGENT.md`](infinite-work-mode/AGENT.md) |

## 许可与注意

- 仓库内 Markdown / YAML / Python 为工作区规则与工具，**不含** API 密钥；调用外部 API 时请在本地配置环境变量。
- 成稿须标注来源或【待核】；禁止编造阅读量或未发布即标 published。
