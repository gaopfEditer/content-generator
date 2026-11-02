# 统计与去重字段

## daily.csv 列

`date,direction,intake,rejected,published,notes`

示例：

```csv
date,direction,intake,rejected,published,notes
2026-11-02,crypto,12,8,1,首日试跑
```

## fingerprints.jsonl 一行一例

```json
{"fp":"a1b2c3d4e5f60718","norm_url":"https://x.com/user/status/123","canonical_id":"crypto/I-20261102-01","sources":[{"platform":"x","url":"https://twitter.com/user/status/123","published_at":"2026-11-02T08:00:00+08:00"},{"platform":"reddit","url":"https://reddit.com/r/...","published_at":"2026-11-02T08:05:00+08:00"}],"created_at":"2026-11-02T21:00:00+08:00"}
```

## inbox 条目建议字段

`id, direction, title, summary, published_at, sources[], fingerprint, norm_url, domestic_echo, status`
