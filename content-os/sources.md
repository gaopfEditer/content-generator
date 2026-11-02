# 来源清单（币圈资讯）

> 只保留 4 类来源，每类最多 3 个来源位，共 12 个。全部为「待用户确认」占位：名称、链接由用户提供后填写，不编造 URL。
> **只有状态为「已确认」的来源才可用于日常收资讯。** 状态为「待确认」的来源位一律不用；候选示例也一律视为未确认。
> 筛选规则见 `filter.md`；每日流程第 5–15 分钟按本表四格各扫一遍。
> 2026-10-06 新增文末两节：「快讯消息源（锁定）」N1–N4 与「数据源（锁定）」（用户授权锁定，单币决策稿直接使用，见 `playbooks/单币决策稿.md`）。

## 通用规则

- 每天每格（每一类）按已确认来源**扫一遍就停**，不追刷、不翻旧页、不因为「还不够」去扩充来源。
- 收进 inbox 的每条须带：标题、链接、发布时间（换算 HKT）、来源平台、一句话摘要、事实/观点/未核实分类。
- 价格与事件必须带时间戳和来源链接；拿不到就不写数字。
- 不收买卖建议、喊单、目标价；分析师观点可以收，但标「观点」。
- 字段说明：名称、链接、状态（待确认 / 已确认）、确认日期（用户确认的日期，YYYY-MM-DD）、用途。

## 一、市场价格与结构（价格、资金费率、清算、成交量）

- 收什么：BTC/ETH 及稳定币价格与市值变化、资金费率、未平仓量、清算量、成交量、ETF 资金流等**有时间戳的数据**。
- 不收什么：K 线形态「预测」、目标价、喊单、无来源的「涨跌原因」、单个小币的拉盘截图。
- 扫描：每天扫一遍就停；数据必须记录读取时间（HKT）和页面链接。
- 候选示例（未确认）：无（待用户提供）。

### MKT-01
- 名称：交易观察员已核事件表（trading-watch）
- 链接：/workspace/trading-watch（本地目录；以 *_YYYY-MM-DD.csv 已核表、各 tracker 的 output 和 SOURCES.md 为准）
- 类型：本地数据目录 / 交易观察员整理的已核事件表（二手汇总：解锁数据来自 PANews 转载的 Token Unlocks/Tokenomist、DefiLlama 等；价格来自 Binance 现货 1h K 线、CoinGecko 小时数据，出处见该目录 SOURCES.md）
- 更新频率：不定期（按交易观察员出表；截至 2026-10-05 已核表只有 2026-10-01 一期：unlocks、delistings、perp_listings、burns 各 1 张及对应 pre7d_daily 表；固定频率待确认）
- 状态：已确认
- 确认日期：2026-10-05（经出海大师转达用户确认）
- 用途：解锁、下架、永续上线、销毁事件的事后数据（前 7 天、事后、相对 BTC），作「事件定价」栏目的唯一数字来源
- 可信度：中（人工核对的二手汇总，每行带 unlock_source / price_source；同一事件各平台口径可能不同，如 XPL 2026-09-25，写稿时须注明采用的口径）
- 规则：只用表里已有的数字，不改价位，不补样本，不做推算；near_research 等没有已核表的原始 JSON 不算这个来源
- 读取方式：只读本地文件，不修改 /workspace/trading-watch/ 下任何内容

### MKT-02
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

### MKT-03
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

## 二、监管与传统金融（官方公告、ETF 发行人、主流财经社）

- 收什么：监管机构官方公告/文件、ETF 发行人公告与申报文件、交易所上市/合规动态、主流财经社对上述事实的报道。
- 不收什么：「知情人士称」且无第二来源的传闻、议员/官员的个人口水表态（除非附官方文件）、营销软文。
- 扫描：每天扫一遍就停；优先引用官方原文，媒体报道作第二来源。
- 候选示例（未确认）：CoinDesk、The Block、Cointelegraph、Decrypt（用户提到的名字，未确认前不作为日常来源）。

### REG-01
- 名称：Foresight News（快讯）
- 链接：https://foresightnews.pro/news
- 类型：中文加密媒体 / 快讯聚合（二手来源）
- 更新频率：全天滚动
- 状态：已确认
- 确认日期：2026-09-29
- 用途：综合快讯线索，覆盖四类（市场、监管、安全、项目）；每条需追到一手出处（官方公告、监管文件、链上数据、安全公司披露）才能给可信度 2 分，追不到最高 1 分，只留 inbox
- 可信度：中（转述为主，作线索用，不作唯一出处）
- 抓取方式：网页有腾讯云 EdgeOne 防护，直接请求和浏览器都被拦（403）；改用站点公开只读接口 `https://api.foresightnews.pro/v1/dayNews?date=YYYYMMDD`（返回 base64+zlib 压缩的 JSON，含 is_important、source_link、published_at 字段）

### REG-02
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

### REG-03
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

## 三、安全与风险事件（安全公司、交易所状态页、项目官方）

- 收什么：黑客/漏洞事件、交易所停提/恢复、稳定币脱锚、预言机故障、大额解锁；以安全公司披露、交易所状态页、项目官方公告为准。
- 不收什么：未经安全公司或项目方确认的「疑似被盗」截图、钓鱼链接、借事件引流的推广帖。
- 扫描：每天扫一遍就停；金额、地址、时间必须来自可核链接。
- 候选示例（未确认）：无（待用户提供）。

### RSK-01
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

### RSK-02
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

### RSK-03
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

## 四、一手项目/研究（项目博客、治理论坛、研究者）

- 收什么：项目官方博客/发布说明、治理论坛提案与投票结果、研究者带数据的报告，且与 watchlist/thesis 相关。
- 不收什么：空投攻略、代币「潜力币」推荐、无数据的叙事鼓吹、与 watchlist/thesis 无关的山寨故事。
- 扫描：每天扫一遍就停；只看 watchlist/thesis 覆盖的项目（`watchlist.md`、`thesis.md` 待用户提供）。
- 候选示例（未确认）：无（待用户提供）。

### PRJ-01
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

### PRJ-02
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

### PRJ-03
- 名称：待用户确认
- 链接：待用户确认
- 状态：待确认
- 确认日期：
- 用途：待用户确认

## 快讯消息源（锁定）

> 用户 2026-10-06 原话：「锁定 3–4 个消息源，不需要反复验证」。以下 4 个已于 2026-10-06 22:58–23:06 UTC+8 在本机实测可抓取。
> **规则**：来自 N1–N4 的消息**直接使用**，正文写「来源 + 时间（UTC+8）」即可，**不交叉验证、不追第二链接**；只有当消息**仅来自单一非锁定来源**时才标【待核】。
> 检索命令：`python3 tools/coin_news.py SYMBOL [--hours 72]`（一次跑完 N1–N4，按币种符号/币名过滤，失败只记一行，不重试第二次）。

| ID | 名称 | 链接 | 类型 | 抓取方式 | 更新频率 | 用途 | 可信度 | 确认日期 | 状态 | 抓取实测（2026-10-06） |
|---|---|---|---|---|---|---|---|---|---|---|
| N1 | crypto-news 看板 data.json | https://raw.githubusercontent.com/gaopfEditer/crypto-news/gh-pages/data.json | 聚合看板（PANews / Odaily / CoinDesk / The Block，自带币种、事件、利多利空标签） | GET JSON；`stories[]` 按 `coins`/`title` 过滤 | 滚动（以 `updated_utc8` 为准；实测 22:47 更新），留存 48h | 首查：单币近 48h 快讯 + 事件时间 | 中高（媒体转述，带原文链接） | 2026-10-06 | 已确认（用户 2026-10-06 授权锁定） | 200，725 KB，412 条，4 个子源 health=ok |
| N2 | PANews 快讯 | https://www.panewslab.com/zh/rss/newsflash.xml | 中文加密媒体快讯（RSS） | GET RSS（XML）；标题+摘要按符号过滤 | 全天滚动；RSS 约 100 条 ≈ 近 22h | 中文快讯原文链接、事件时间 | 中高 | 2026-10-06 | 已确认（用户 2026-10-06 授权锁定） | 200，178 KB，100 条 |
| N3 | Odaily 星球日报快讯 | https://rss.odaily.news/rss/newsflash | 中文加密媒体快讯（RSS） | GET RSS（XML） | 全天滚动；RSS 仅最近 10 条（更早的看 N1） | 补最新 1–2 小时快讯 | 中高 | 2026-10-06 | 已确认（用户 2026-10-06 授权锁定） | 200，10 条 |
| N4 | 交易所官方公告（Binance / OKX / Bitget / Upbit） | Binance：https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20 ；OKX：https://www.okx.com/api/v5/support/announcements?page=1 ；Bitget：https://api.bitget.com/api/v2/public/annoucements?language=zh_CN ；Upbit：https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=20&category=trade | 一手官方公告（上币/下架/合约/维护） | GET JSON（公开接口，无需登录） | 不定期，官方发布即更新 | 上所、下架、永续上线等一手事件与时间 | 高（一手） | 2026-10-06 | 已确认（用户 2026-10-06 授权锁定） | 四个接口均 200（Binance 7 个目录×20 条；OKX 20 条；Bitget 10 条；Upbit 20 条） |

- 不用（本机实测被拦，不重试）：Bithumb 公告页 feed.bithumb.com（403）、Gate 公告页 gate.com/announcements（403）、Foresight News 网页与 api.foresightnews.pro（403）。Bithumb/Gate 上币消息以 N1–N3 转述为准。
- 可达但未锁定（需要时作补充，单独使用须标【待核】）：ChainCatcher、BlockBeats 网页、Cointelegraph RSS（CoinDesk、The Block 已由 N1 覆盖，不单独抓）。

## 数据源（锁定）

> 用户 2026-10-06 授权：数据源按下表固定优先级自动降级，不再逐次试探。已写入 `tools/coin_data.py`（短超时 8s；仅网络错误/5xx/429 重试 1 次；4xx 直接降级）。
> 确认日期：2026-10-06｜状态：已确认（用户 2026-10-06 授权锁定）

| 数据 | 优先级（左→右自动降级） | 接口要点 |
|---|---|---|
| K 线 15m / 1h / 4h（+1m 事件精度） | Bitget USDT 永续 → OKX USDT 永续 → Gate USDT 永续 → Binance 现货（data-api.binance.vision） | Bitget `/api/v2/mix/market/candles` limit 1000；OKX `/api/v5/market/history-candles` 3×300；Gate `/api/v4/futures/usdt/candlesticks` limit 1000；binance.vision `/api/v3/klines` limit 1000 |
| BTC 基准 | Binance 现货 BTCUSDT（data-api.binance.vision）→ Bitget BTCUSDT 永续 | 同上 |
| 资金费率 | Bitget（当期 + 近 3 次结算）+ Gate + MEXC + OKX（若上线）+ CoinGecko 衍生品快照中的 Binance | Bitget `current-fund-rate`/`history-fund-rate`；Gate `/futures/usdt/contracts/{X}_USDT`；MEXC `contract.mexc.com/api/v1/contract/funding_rate/{X}_USDT`；OKX `/api/v5/public/funding-rate` |
| OI | OKX rubik（若上线，USD）否则 Gate contract_stats（张数）；+ CoinGecko 全市场合计（仅量级） | OKX `/api/v5/rubik/stat/contracts/open-interest-volume?ccy=X&period=1H`；Gate `/api/v4/futures/usdt/contract_stats?interval=1h` |
| 标的识别 / 市值 | CoinGecko search（结果缓存 `tools/cache/coingecko_ids.json`，同币只查一次）+ coins/markets | 认错币时用 `--cg-id` 覆盖 |
| ETH ETF 流向（仅 ETH 稿需要） | Farside https://farside.co.uk/eth/ | 网页，手动读一次 |

- **已知封锁（不要再请求）**：api.binance.com、fapi.binance.com（HTTP 451）；api.bybit.com（403 CloudFront）；Foresight News（403）；Bithumb 公告页（403）。Binance 合约费率/OI 一律取 CoinGecko 衍生品快照。
- **已知缺口**：OKX 无部分山寨永续（如 BR），脚本自动跳过；Gate contract_stats 有约 1h 延迟；Bitget 无 OI 历史接口。

