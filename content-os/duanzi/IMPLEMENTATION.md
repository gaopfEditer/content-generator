# 段子产线实现方案

> 更新：2026-11-02 Asia/Shanghai  
> 配套：`AGENT-PLAN.md`（深度与四步写作）、本文件（抓取/去重/统计/模型/四方向并行）  
> 根目录：`/workspace/content-os/duanzi/`  
> 独立于资讯产线；不改 `/workspace/task-os/`。

## 1. 目标一句话

国外热帖进料 → 多平台去重 → 按四方向并行写成「铺垫→反转→余味」短叙事 → 机械自检 + 本人品鉴 → 日统计判方向去留。

## 2. 目录落地

```
duanzi/
  AGENT-PLAN.md              # 深度标准与写作四步
  IMPLEMENTATION.md          # 本文件
  checklist.md
  templates/段子成稿.md
  config/
    sources.md               # 主源/筛子源
    models.md                # Cursor Pro 主力 / Ollama 备用
    directions.yaml          # 四方向开关与标签
  directions/
    crypto/                  # 币圈
    invest/                  # 投资（传统+宏观叙事，非喊单）
    scitech/                 # 科技（产品/AI 应用/消费电子）
    engineering/             # 技术（工程/爬虫/开发者日常）
      inbox/                 # 方向进料
      drafts/                # 方向成稿
  stats/
    schema.md
    daily.csv                # 日汇总（进料/打回/发出）
    fingerprints.jsonl       # 内容指纹索引（可旋转归档）
  scripts/                   # 抓取与去重占位（实现时代码进此或独立仓库）
  samples/                   # 跨方向示意样稿（S-01～S-03 保留）
```

四方向**独立建目录、配置可同时 `enabled: true`**，抓取任务互不阻塞；爬取成本近零指：优先 API/列表接口，避免 CDP 深滚。

## 3. 流水线（端到端）

```
[定时调度]
   │
   ├─ fetch_x (cookie+API / GraphQL)     ──┐
   ├─ fetch_reddit (官方/公开 JSON)        ├──► normalize_item
   └─ fetch_domestic_light (可选筛子)    ──┘
                │
         dedup (URL 归一化 + 指纹)
                │
         route_by_direction (四方向并行队列)
                │
         draft_gen (Cursor Pro API → 失败切 Ollama)
                │
         mechanical_checklist
                │
         reviewing（本人品鉴）→ ready → published（须本人明确「发」）
                │
         stats_daily_append
```

状态机（单稿）：`inbox → drafting → self_check → reviewing → ready → published → archived`  
打回：任意阶段回 `inbox` 或标 `rejected`，计入当日打回。

## 4. 信息源策略

### 4.1 主源（国外热门实时）

| 源 | 用途 | 接入思路 |
|----|------|----------|
| Twitter/X 热帖/列表 | 主进料 | 一次登录导会话 → cookie+GraphQL 长期拉；对齐 python-ai-operate 的 `x_api` 思路，**不**以 CDP 滑动为主 |
| Reddit（相关 sub） | 主进料 | 公开 `.json` 或官方 API；按 hot/new 分页，遇已见 id 即停（实时增量） |

时间字段：**一律以帖子发布时间**为准（X `created_at`、Reddit `created_utc`），不用相对文案。

### 4.2 筛子源（国内，不当主源）

知乎 / 即刻 / B站 等仅作「话题是否在中文语境有共鸣」的弱信号：可降权、可打标签 `domestic_echo=true`，**不单独开深抓**。国内「稳中向好」叙事偏多，信号弱，故不进主路径。

详见 `config/sources.md`。

## 5. 多平台去重

落盘前必跑：

1. **URL 归一化**  
   - 去 tracking 参数（`utm_*`、`s`、`t` 等）  
   - 统一 host（`mobile.` / `www.` / `x.com`↔`twitter.com`）  
   - 小写 path；去掉末尾 `/`

2. **内容指纹**  
   - 正文规范化（去空白、小写拉丁字符、去常见表情噪声）后 `sha256` 前 16 位  
   - 可选：标题+正文前 80 字指纹，防同文换链

3. **合并策略**  
   - 同一新闻/同一梗多平台 → **只留一份** canonical  
   - `sources: [{platform, url, published_at}]` 数组挂来源标签  
   - 指纹库：`stats/fingerprints.jsonl`（一行一个）

伪字段见 `stats/schema.md`。

## 6. 定时抓取

- 建议 cron（Asia/Shanghai）：每方向可错峰，例如整点 :05 crypto、:10 invest、:15 scitech、:20 engineering；或同一调度内并行协程。  
- 登录：bootstrap 会话脚本写入 `output/`（gitignore），勿提交 cookie。  
- 实时增量：**碰到本地已存在 id/指纹即停止该时间线翻页**（历史回填另开 mode）。  
- 实现可挂例行或本机脚本；本方案先定契约，代码进 `scripts/` 或复用 operate 仓库客户端。

## 7. 模型优先级

| 优先级 | 用途 | 说明 |
|--------|------|------|
| 1 | Cursor Pro API | 主力生成（结构槽位 + 正文） |
| 2 | Ollama 本地 | 断供 / 额度见底 / 超时后顶上 |

`config/models.md`：超时、重试、降级开关。生成 prompt 必须注入：字数窗、铺垫反转余味、禁止一句话冷笑话、禁止交易建议。

## 8. 日统计与方向去留

每日（建议 23:00 Asia/Shanghai）写一行 `stats/daily.csv`：

| 字段 | 含义 |
|------|------|
| date | YYYY-MM-DD |
| direction | crypto / invest / scitech / engineering |
| intake | 进料条数（去重后） |
| rejected | 打回条数（机械+品鉴） |
| published | 最终发出条数（本人点「发」） |
| notes | 可选 |

**连续约三天**看：`published≈0` 且 `rejected/intake` 高 → 方向建议暂停或改源；三天有稳定发出 → 保留。决策由本人拍，管家可汇总表。

## 9. 厚度（继承 AGENT-PLAN）

- 结构：铺垫 → 反转 → 余味  
- 正文 180～450 字；**< 120 硬失败**  
- 禁短平快一句话冷笑话  

## 10. 样稿交付

| 路径 | 说明 |
|------|------|
| `samples/S-01.md`～`S-03.md` | 保留（职场/亲情/AI 职场） |
| `directions/crypto/drafts/S-crypto-01.md` | 币圈示意 |
| `directions/invest/drafts/S-invest-01.md` | 投资示意 |
| `directions/scitech/drafts/S-scitech-01.md` | 科技示意 |
| `directions/engineering/drafts/S-engineering-01.md` | 技术示意 |

## 11. 不做清单

- 不写买卖建议、不碰钱包、不代发（须本人明确「发」）  
- 不改 task-os 任务状态；排期只写 `related_task`  
- 不把国内源当主爬  
- 不以 CDP 深滚为默认抓取  

## 12. Web 控制台

本地浏览器操作见仓库 [`web/README.md`](../../web/README.md)（与本文件状态机一致，发布须人工确认）。

## 13. 落地顺序（建议）

1. 配置与统计空表（本包已含）  
2. 去重库 + 单测指纹  
3. Reddit 公开拉取 → X cookie+API  
4. 接 Cursor Pro / Ollama 生成器  
5. 开四方向并行例行，跑满约三天后复盘  
