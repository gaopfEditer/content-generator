# L1 机械自检清单

对 `drafts/<id>.md` + `runs/<id>/` 逐项：`pass` / `fail` / `na`。任一 **fail** → 不得进入人工终稿队列。

## 环节完整性
- [ ] 本轮有 `inbox` 线索原文快照
- [ ] 有结构化卡（unlock_card 字段）
- [ ] 有草稿文件
- [ ] 有本轮 `report.md`

## 格式
- [ ] 标题、导语、要点、风险提示区块齐全（按运营模板）
- [ ] 关键数字/日期有来源链接或标注 unknown
- [ ] 无「据传/可能」冒充确定事实

## 反编造
- [ ] 解锁时间、数量、归属未凭空填写
- [ ] 涨跌归因未捏造「主力/内幕」
- [ ] 引用句能回链到 gather 证据

## 流程纪律
- [ ] 开轮前已读 `memory/lessons.md`（若存在）
- [ ] 未同时处理第二条线索
- [ ] 未调用发布 API（第一轮）

## 输出

写入 `runs/<id>/self_check.json`：

```json
{
  "run_id": "",
  "verdict": "pass|fail",
  "items": [{"id": "", "result": "pass|fail|na", "note": ""}],
  "fix_hints": []
}
```
