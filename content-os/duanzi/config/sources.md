# 段子产线信息源

## 主源（国外热门实时）

| id | 平台 | 备注 |
|----|------|------|
| SRC-X | Twitter/X | cookie + GraphQL；发布时间用 created_at |
| SRC-RED | Reddit | hot/new JSON 或官方 API；created_utc |

具体 subreddit / X list 由本人确认后再写入下行（未确认不擅自扩源）：

- Reddit 候选（待确认）：待填  
- X list / 关键词（待确认）：待填  

## 筛子源（国内，弱信号）

| id | 平台 | 用法 |
|----|------|------|
| SRC-ZHIHU | 知乎 | 仅标 domestic_echo，不深爬 |
| SRC-JIKE | 即刻 | 同上 |
| SRC-BILI | B站 | 同上 |

原则：国内不当主源；「稳中向好」叙事多，信号弱。
