# 无限工作模式 · Infinite Work Mode

独立项目（不塞进现有 Grok Bot / Hermes profile）。目标：agent **全自动**跑通一条资讯生产线，跑通后可复用到其他创作类工作。

> 人只管终稿筛选；其余搜索 → 结构化 → 草稿 →（待发）全自动。

## 垂直起点（第 1 条线）

**交易观察员 unlock 解锁线索**（如 APR / GRASS）：

`线索(inbox) → 核验/补料 → 结构化卡 → 资讯草稿 → 机械自检 → 人工终稿筛选 → 发布或弃`

单线优先：足够复杂且有创造性，不并行开多品类。

## 两层评判（必须）

| 层 | 谁做 | 问什么 | 产出 |
|----|------|--------|------|
| **L1 机械自检** | Agent | 格式齐不齐、环节走完没有、有没有编造 | `runs/<id>/self_check.json` |
| **L2 人工口味** | 人 | 值不值得发（只看终稿） | `published/` 或 `drafts/rejected/` |

L1 **不能**替人做「值不值得发」；L2 **不**重跑流水线。

## 反馈回路（跨轮学习）

每轮结束后写入 `memory/`，下一轮 **必须先读** 再开工，禁止从零：

- `memory/lessons.md` — 改进点（人/自检共同沉淀）
- `memory/style_notes.md` — 口味偏好（仅从 L2 决策反推，勿臆造）
- `runs/<id>/report.md` — 本轮摘要 + 自检结论

## 核心循环（单轮）

```text
1. boot     读 memory/ + 取 inbox 一条线索（unlock）
2. gather   搜索/补料（官网、解锁时间、流通、近期涨跌语境）— 无来源不写断言
3. struct   填 templates/unlock_card.md
4. draft    按运营模板出草稿 → drafts/<id>.md
5. L1       跑 templates/self_check.md → 不过则回 2–4（最多 N 次）
6. handoff  终稿放入待审队列；停，等人 L2
7. learn    根据 L2（发/弃/改）追加 memory/；归档 runs/<id>/
```

确定性 vs 不确定性（协作 / 60 分答案）：

- **确定**：环节顺序、字段是否齐全、引用是否有链接、禁止编造、自检清单项
- **不确定**：选题角度、标题钩子、是否值得发、语气轻重 → 交给 L2 或记入 style_notes

## 项目结构

```text
infinite-work-mode/
  README.md                 # 本文件
  AGENT.md                  # 角色边界与禁止项
  prompts/
    boot.md                 # 开轮必读
    draft_unlock.md         # 解锁资讯草稿 prompt
  templates/
    unlock_card.md          # 结构化卡
    self_check.md           # L1 清单
    run_report.md           # 轮次报告壳
  inbox/                    # 观察员丢进来的线索（或脚本同步）
  drafts/                   # 待 L2
  published/                # 已发归档
  runs/<run_id>/            # 每轮证据与自检
  memory/                   # 跨轮学习
  scripts/                  # 可选：从 unlock_tracker / content-os inbox 拉线索
```

## 工具选型建议（第一轮）

| 角色 | 建议 | 理由 |
|------|------|------|
| **编排 / 反问 / 记 memory** | **Grok Bot（本助手）或 Cursor Agent** | 深度与边界清楚；适合定循环与改 prompt |
| **单点执行（读文件、填卡、改稿）** | **Hermes（独立 profile，如 content-line）** | 擅单点与文件；弱深度→只给窄任务 |
| **复现脚本 / 拉线索 / 测差异** | **Cursor（额度富裕时）** | 代码与本地联调；顺带对比 Hermes |
| **不做主路径** | 豆包工作 | 云端成品、个人改不动全程；仅作对标亮点，不绑死流水线 |

**第一轮具体跑法（建议）**

1. 人工或脚本放 1 条 APR/GRASS 线索进 `inbox/`
2. Cursor 或 Grok Bot 按本 README 走完 1→6（不出自动发布）
3. Hermes 只承包「按 `draft_unlock.md` 改一版草稿」或「填 unlock_card」之一
4. 人做 L2；结果写回 `memory/`
5. 第二轮强制先读 `memory/`，验证「不是从零」

发布通道（CDP / 社媒）**第二轮再接**；第一轮验收 = 草稿 + 过 L1 + 人能 1 分钟判发/弃。

## 与现有栈的关系

- **交易观察员**：只提供线索，不写稿
- **资讯创作官**：可复用模板字段，但本项目不改其仓库职责；跑通后可交接
- **task-os**：实验结论记日历实践，不把本目录并进 bot 舰队

## 验收（第 1 条线跑通）

- [ ] 一条 unlock 线索 → 结构化卡 → 草稿，全自动无手写正文
- [ ] L1 清单有落盘；编造项为 fail 时不进入待审
- [ ] L2 只看终稿即可发/弃
- [ ] 第二轮能读到第一轮 lessons，行为有可观察差异
