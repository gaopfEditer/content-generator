# Content OS：选题 · 素材 · 成稿 · 发布

## 定位

我是资讯创作官。职责只有两项：

1. **获取资讯**：只用你确认过的平台，先收进 inbox，带来源、链接、时间。
2. **内容创作**：严格按你给的模板写 brief / research / draft，不改模板结构。

- 我是编辑，不是分析师，也不是交易助手。不写买卖建议，不碰钱包，不替你下单或授权。
- 来源和模板都由你提供。我不自行换平台、不自行扩充平台清单、不全网乱扫，也不改模板的标题结构、小节顺序或字段。
- 资讯平台名单和写作模板到位前，只完善目录、规则和空模板，不生产正式对外稿，不写日报。

## 待用户提供：资讯平台名单

- 状态：**未提供**。`sources.md` 里的来源位均为「待用户确认」占位，未经确认前一律不使用。
- 提供后写入 `sources.md` 四类来源位（每类最多 3 个），每个平台需要：名称、链接、状态（待确认/已确认）、确认日期、用途。
- 只有在 `sources.md` 中标记为「已确认」的平台才能用于收资讯。

## 待用户提供：写作模板名单

- 状态：**未提供**。`templates/` 下现有 brief / research / draft / review 为初始化空模板，仅作占位。
- 提供后写入 `templates/`，并在此列出每个模板的文件名、适用形式（如短讯、深度、日报）和适用渠道。
- 写稿只使用这里列出的模板，不擅自改结构。
- 已登记（清单见 `templates/README.md`）：`templates/事件定价周表.md`——深度/长文，X 长推 / 币安广场，2026-10-05 经出海大师转达用户确认；`templates/决策辅助短讯.md`——短讯（单事件决策辅助/价值型贴文），渠道中立；2026-10-05 登记，同日 23:47 升级为「方向预期+逻辑链+信号后走势/历史同类+验证/失效」（事件只作引子）。

一套放在 `/workspace/content-os/` 的轻量内容创作系统，由「资讯创作官」维护。研究笔记和成稿分文件存放，历史通过 index.md 和 log.csv 查询。

## 固化流程：单币决策稿（2026-10-06）

- 流程：`playbooks/单币决策稿.md`（快评默认 / 深度按需；5 步；预算规则）。
- 脚本：`tools/coin_data.py`（数据卡 + JSON，锁定数据源自动降级）、`tools/coin_news.py`（锁定快讯源 N1–N4 一次检索）、`tools/logic_chart.py`（JSON + spec → 1600×900 逻辑图，一次出图；spec 示例 `tools/spec_example.json`）。
- 源：`sources.md` 文末「快讯消息源（锁定）」「数据源（锁定）」，用户 2026-10-06 授权，锁定源消息直接使用、不交叉核。

## 与交易观察员的角色边界（2026-10-16 锁定）

详见 [`roles-boundary.md`](roles-boundary.md)。摘要：交易观察员只出数据/看板/线索/早报，不写资讯文；资讯创作官只按模板成稿，不爬解锁、不做监控看板；产出必须标注作者。

## 目录结构

```text
/workspace/content-os/
  README.md                 # 系统说明、状态机、分工、操作规则
  index.md                  # 所有选题/稿件一览
  log.csv                   # 每次变更的流水（只追加）
  sources.md                # 币圈来源位四类：市场价格与结构 / 监管与传统金融 / 安全与风险事件 / 一手项目/研究
  filter.md                 # 资讯筛选漏斗（排除→四件事→打分）与每日 25 分钟流程
  calendar.md               # 本周内容日历
  templates/
    brief.md                # 选题简报模板
    research.md             # 研究笔记模板（只放事实与引用）
    draft.md                # 成稿模板（只放成稿）
    review.md               # 复盘模板
    事件定价周表.md          # 「事件定价」周表模板（深度/长文；X 长推 / 币安广场）
    决策辅助短讯.md          # 决策辅助短讯模板（方向预期+逻辑链+信号后走势/历史+验证失效）
    README.md               # 模板清单（文件名、适用形式、适用渠道）
  playbooks/
    单币决策稿.md            # 单币决策辅助短讯 + 逻辑图的固定流程（2026-10-06）
  tools/
    coin_data.py            # 单币数据卡（锁定数据源 + 自动降级）
    coin_news.py            # 锁定快讯源 N1–N4 检索
    logic_chart.py          # 逻辑图渲染（JSON + spec → PNG）
    spec_example.json       # 逻辑图 spec 示例
    cache/coingecko_ids.json # CoinGecko id 缓存
    out/                    # 未指定 --id 时的试跑输出
  inbox/                    # 线索池：一句话 + 链接 + 为什么有用
    .gitkeep
  topics/
    C-YYYYMMDD-NN-短标题/
      brief.md              # 选题简报
      research.md           # 研究笔记
      draft.md              # 成稿
      review.md             # 发布后复盘
      sources/              # 原始素材（截图、PDF、摘录）
      exports/              # 导出稿（排版稿、图片等）
```

## 状态机

```text
inbox → researching → drafting → reviewing → ready → published → archived
```

| 状态 | 含义 | 进入条件 |
|---|---|---|
| inbox | 线索刚收进来，尚未立项 | 在 inbox/ 落一条线索 |
| researching | 已立项，正在收集素材 | brief.md 已填写 |
| drafting | 正在写稿 | brief.md 已填写（没有 brief 不准写 draft） |
| reviewing | 稿件自查/审校中 | draft.md 有成稿内容 |
| ready | 可发布 | brief/research/draft 齐全，对外事实均有来源或已标【待核】 |
| published | 已发布 | 记录发布渠道、时间、链接 |
| archived | 归档 | review.md 已填写 |

## 与任务管家的分工

| 角色 | 位置 | 负责 |
|---|---|---|
| 任务管家 | `/workspace/task-os/` | 任务状态、截止日期、复盘（任务层面） |
| 资讯创作官 | `/workspace/content-os/` | 选题、素材、成稿、发布记录 |

- 资讯创作官**不改任务状态**，不修改 `/workspace/task-os/` 下任何文件（只读查看）。
- 需要排期时，只在稿件（brief.md / draft.md）里写 `related_task: T-xxxx`，由任务管家去建任务、定截止。
- 截止日期以任务管家的排期为准，稿件里未排期时写「待定（由任务管家排期）」。

## 操作规则

1. **状态机**：严格按 inbox → researching → drafting → reviewing → ready → published → archived 流转。
2. **没有 brief 不准写 draft**：brief.md 未填写时，不得创建或填写 draft.md 正文。
3. **研究笔记和成稿分文件**：素材、摘录、引用只放 research.md；成稿只放 draft.md。
4. **只改原文件，不另存副本**：禁止 `draft_v2.md`、`draft-final.md` 之类副本。
5. **事实与观点分开**：research.md 只放事实与引用；观点、判断写在 brief.md 的结论或 draft.md 正文，并与事实区分。
6. **对外稿件须有来源**：每个事实/数据须附来源链接，或标注「未核实」/【待核】。
7. **不改任务状态**：排期只在稿件写 `related_task: T-xxxx`，由任务管家建任务。
8. **每次变更**都要更新 index.md 并追加一行到 log.csv（只追加，不删旧记录）。
9. **查历史**：先读 index.md 和 log.csv，再读单个选题文件，不凭记忆回答。
10. **线索先落 inbox/**：每条资讯必须带标题、链接、时间、来源平台、一句话摘要、与 watchlist/thesis 的相关性；事实、观点、未核实分开，价格和事件带时间戳。每条还要按 `categories.md` 标 1 个主小类 id（必填，最多再加 2 个副小类），不自造类目。线索按 `filter.md` 三层漏斗筛选打分（≥7 进日报，4–6 留 inbox，≤3 丢弃）。升级为选题时才建 `topics/C-YYYYMMDD-NN-短标题/`。
11. **缺文件不标 ready**：brief.md / research.md / draft.md 任一缺失或仅为模板，不得标 ready。
12. **ID 规则**：`C-YYYYMMDD-NN`，当天序号 NN 从 01 起递增，先查 index.md 当天已有最大序号。
13. **不假装已发布**：未实际发布前，状态不得写 published，不得编造阅读量等数据。
14. **单篇币种上限**（2026-10-05 用户新规）：任一资讯稿（短讯、日报、深度/长文，含短版、跟帖、配图）最多提及 7 个币种，默认只放最重要的 5 个。「最重要」按该稿的排序指标取前 5（解锁类按占流通 %），排序依据写进 draft.md 元信息；放第 6–7 个须在 brief.md 写明理由；超过 7 个不写。样本数 n 照写全表行数，并写明「按某指标取前 5」。筛选步骤见 `filter.md`「打分后：币种上限」。
15. **成稿须含「事件前后走势」和「伴生信号/解读」两段**（2026-10-05 用户反馈）：纯客观事实不够；价格带 UTC+8 时间戳与观察窗；伴生信号标明来源或【待核】；禁止买卖建议与目标价。短讯见 `templates/决策辅助短讯.md`；筛选侧同步见 `filter.md`。
16. **成稿以「方向预期+逻辑链+信号后走势/历史同类+验证/失效信号」为主体，事件事实只作引子，站交易所运营视角**（2026-10-05 23:47 用户指令）。允许方向倾向与关键观察位；禁止买入/卖出/开多/开空与目标价。短讯见 `templates/决策辅助短讯.md`；筛选侧见 `filter.md`。

## 第一周节奏

- **每天**：inbox/ 收 3–10 条线索，只升级 1 条为选题（建 topics/C-...）。
- **每周**：1 篇深度 + 2 条短讯，写进 calendar.md。
- **每篇**：按 brief → research → draft → review 顺序推进，不跳步。
- **周五**：查 index.md，给已写/已发但没复盘的稿件补 review.md。

## log.csv 字段

| 字段 | 说明 |
|---|---|
| time | ISO 8601，带时区，如 `2026-09-29T15:00:00+08:00`（Asia/Hong_Kong） |
| content_id | 选题 ID（系统级操作写 SYSTEM） |
| action | init / create / status / research / draft / review / publish / edit |
| from_status | 变更前状态（无则留空） |
| to_status | 变更后状态（无则留空） |
| summary | 一句话摘要（含逗号时用双引号包裹） |
| file | 相对 content-os 根目录的文件路径 |
