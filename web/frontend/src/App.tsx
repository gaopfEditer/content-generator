import { useCallback, useEffect, useMemo, useState } from 'react'
import './App.css'
import {
  api,
  DIRECTION_LABELS,
  type DirectionKey,
  type DraftDetail,
  type DraftListItem,
  type DailyRow,
  STATUS_LABELS,
} from './api'

type Tab = 'pipeline' | 'drafts' | 'stats' | 'settings'

const ALL_DIRECTIONS: DirectionKey[] = ['crypto', 'invest', 'scitech', 'engineering']

const PIPELINE_STEPS = [
  '进料 intake',
  '去重视图 dedup',
  '成稿 generate',
  '机械自检 self_check',
  '品鉴 reviewing',
  '待发 ready',
]

function App() {
  const [tab, setTab] = useState<Tab>('pipeline')
  const [selected, setSelected] = useState<DirectionKey[]>([...ALL_DIRECTIONS])
  const [enabledMap, setEnabledMap] = useState<Record<string, boolean>>({})
  const [drafts, setDrafts] = useState<DraftListItem[]>([])
  const [daily, setDaily] = useState<DailyRow[]>([])
  const [dedup, setDedup] = useState<Record<string, unknown>[]>([])
  const [inboxByDir, setInboxByDir] = useState<Record<string, Record<string, unknown>[]>>({})
  const [stepDone, setStepDone] = useState(0)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [editor, setEditor] = useState<{ direction: string; id: string; detail: DraftDetail } | null>(null)
  const [importForm, setImportForm] = useState({ title: '', summary: '', url: '' })
  const [runtime, setRuntime] = useState<Record<string, unknown>>({})
  const [activeDir, setActiveDir] = useState<DirectionKey>('crypto')

  const loadBase = useCallback(async () => {
    setErr('')
    const [dirCfg, draftList, stats, models] = await Promise.all([
      api.directions(),
      api.drafts(),
      api.dailyStats(),
      api.modelsConfig(),
    ])
    const en: Record<string, boolean> = {}
    ALL_DIRECTIONS.forEach((d) => {
      en[d] = dirCfg.directions?.[d]?.enabled !== false
    })
    setEnabledMap(en)
    setDrafts(draftList)
    setDaily(stats)
    setRuntime(models.runtime)
  }, [])

  useEffect(() => {
    loadBase().catch((e) => setErr(String(e)))
  }, [loadBase])

  const toggleDir = (d: DirectionKey) => {
    setSelected((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]))
  }

  const runForSelected = async (fn: (d: DirectionKey) => Promise<unknown>) => {
    setErr('')
    setMsg('')
    for (const d of selected) {
      if (!enabledMap[d]) continue
      await fn(d)
    }
    await loadBase()
  }

  const doIntake = () =>
    runForSelected(async (d) => {
      await api.intake(d, 2)
      setMsg((m) => m + `${DIRECTION_LABELS[d]} 进料完成；`)
      setStepDone((s) => Math.max(s, 1))
    })

  const doDedup = async () => {
    setErr('')
    const rows = await api.dedup()
    setDedup(rows)
    setStepDone((s) => Math.max(s, 2))
    setMsg('已刷新去重视图')
  }

  const loadInbox = async (d: DirectionKey) => {
    const items = await api.inbox(d)
    setInboxByDir((prev) => ({ ...prev, [d]: items }))
  }

  useEffect(() => {
    if (tab === 'pipeline') {
      selected.forEach((d) => loadInbox(d).catch(() => {}))
    }
  }, [tab, selected])

  const doGenerate = async () => {
    setErr('')
    for (const d of selected) {
      const inbox = inboxByDir[d] || (await api.inbox(d))
      const candidate = inbox.find((x) => x.status === 'inbox')
      if (!candidate?.id) continue
      await api.generate(d, String(candidate.id))
      setMsg((m) => m + `${DIRECTION_LABELS[d]} 已生成草稿；`)
    }
    setStepDone((s) => Math.max(s, 3))
    await loadBase()
  }

  const openDraft = async (d: string, id: string) => {
    const detail = await api.draft(d, id)
    setEditor({ direction: d, id, detail })
  }

  const saveEditor = async () => {
    if (!editor) return
    const detail = await api.saveDraft(editor.direction, editor.id, editor.detail.content)
    setEditor({ ...editor, detail })
    setMsg('草稿已保存')
    await loadBase()
  }

  const filteredDrafts = useMemo(() => {
    if (selected.length === 0) return drafts
    return drafts.filter((d) => selected.includes(d.direction as DirectionKey))
  }, [drafts, selected])

  return (
    <div className="app">
      <header>
        <h1>段子产线控制台</h1>
        <p>控制进料 → 去重 → 成稿 → 自检 → 品鉴 → 待发；不自动发帖，仅标记 ready / 导出。</p>
      </header>

      <nav className="tabs">
        {(
          [
            ['pipeline', '流水线'],
            ['drafts', '草稿列表'],
            ['stats', '日统计'],
            ['settings', '模型设置'],
          ] as const
        ).map(([key, label]) => (
          <button key={key} type="button" className={tab === key ? 'active' : ''} onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </nav>

      <section className="panel">
        <h3>方向选择（可并行）</h3>
        <div className="chips">
          {ALL_DIRECTIONS.map((d) => (
            <button
              key={d}
              type="button"
              className={`chip ${selected.includes(d) ? 'selected' : ''} ${enabledMap[d] === false ? 'disabled' : ''}`}
              onClick={() => toggleDir(d)}
            >
              {DIRECTION_LABELS[d]}
              {enabledMap[d] === false ? '（已暂停）' : ''}
            </button>
          ))}
        </div>
      </section>

      {err && <div className="error">{err}</div>}
      {msg && <div className="notice">{msg}</div>}

      {tab === 'pipeline' && (
        <>
          <section className="panel">
            <h3>流水线步骤</h3>
            <div className="pipeline-steps">
              {PIPELINE_STEPS.map((label, i) => (
                <div key={label} className={`step ${stepDone > i ? 'done' : ''}`}>
                  {i + 1}. {label}
                </div>
              ))}
            </div>
            <div className="actions">
              <button type="button" className="primary" onClick={() => doIntake().catch((e) => setErr(String(e)))}>
                模拟进料（stub）
              </button>
              <button type="button" className="secondary" onClick={() => doDedup().catch((e) => setErr(String(e)))}>
                查看去重
              </button>
              <button type="button" className="secondary" onClick={() => doGenerate().catch((e) => setErr(String(e)))}>
                从进料生成草稿
              </button>
            </div>
            <div className="notice">
              真实 X / Reddit 抓取接口预留于后端 <code>simulate_intake</code>；可用下方「手动导入进料」代替。
            </div>
          </section>

          <section className="panel">
            <h3>手动导入进料</h3>
            <div className="form-grid">
              <label>
                方向
                <select value={activeDir} onChange={(e) => setActiveDir(e.target.value as DirectionKey)}>
                  {ALL_DIRECTIONS.map((d) => (
                    <option key={d} value={d}>
                      {DIRECTION_LABELS[d]}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                标题
                <input
                  value={importForm.title}
                  onChange={(e) => setImportForm({ ...importForm, title: e.target.value })}
                />
              </label>
              <label>
                摘要
                <textarea
                  rows={3}
                  value={importForm.summary}
                  onChange={(e) => setImportForm({ ...importForm, summary: e.target.value })}
                />
              </label>
              <label>
                来源 URL（可选）
                <input value={importForm.url} onChange={(e) => setImportForm({ ...importForm, url: e.target.value })} />
              </label>
              <button
                type="button"
                className="primary"
                onClick={() =>
                  api
                    .importInbox(activeDir, importForm)
                    .then(() => {
                      setImportForm({ title: '', summary: '', url: '' })
                      setMsg('进料已写入 inbox')
                      return loadInbox(activeDir)
                    })
                    .catch((e) => setErr(String(e)))
                }
              >
                导入
              </button>
            </div>
          </section>

          {dedup.length > 0 && (
            <section className="panel">
              <h3>去重视图</h3>
              <table>
                <thead>
                  <tr>
                    <th>方向</th>
                    <th>标题</th>
                    <th>指纹</th>
                    <th>重复?</th>
                  </tr>
                </thead>
                <tbody>
                  {dedup.map((row) => (
                    <tr key={String(row.id)}>
                      <td>{DIRECTION_LABELS[row.direction as DirectionKey] || String(row.direction)}</td>
                      <td>{String(row.title)}</td>
                      <td>{String(row.fingerprint)}</td>
                      <td>{row.is_duplicate ? '是' : '否'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </>
      )}

      {tab === 'drafts' && (
        <section className="panel">
          <h3>草稿列表</h3>
          <table>
            <thead>
              <tr>
                <th>方向</th>
                <th>ID</th>
                <th>标题</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredDrafts.map((d) => (
                <tr key={`${d.direction}-${d.id}`}>
                  <td>{DIRECTION_LABELS[d.direction as DirectionKey] || d.direction}</td>
                  <td>{d.id}</td>
                  <td>{d.title}</td>
                  <td>
                    <span className={`badge ${d.status}`}>{STATUS_LABELS[d.status] || d.status}</span>
                  </td>
                  <td className="actions">
                    <button type="button" className="secondary" onClick={() => openDraft(d.direction, d.id).catch((e) => setErr(String(e)))}>
                      编辑
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() =>
                        api
                          .selfCheck(d.direction, d.id)
                          .then(() => {
                            setStepDone((s) => Math.max(s, 4))
                            setMsg('机械自检完成')
                            return loadBase()
                          })
                          .catch((e) => setErr(String(e)))
                      }
                    >
                      自检
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() =>
                        api
                          .transition(d.direction, d.id, 'advance')
                          .then(() => loadBase())
                          .catch((e) => setErr(String(e)))
                      }
                    >
                      推进一步
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() =>
                        api
                          .transition(d.direction, d.id, 'approve')
                          .then(() => {
                            setStepDone((s) => Math.max(s, 6))
                            setMsg('已标记 ready（仍不自动发帖）')
                            return loadBase()
                          })
                          .catch((e) => setErr(String(e)))
                      }
                    >
                      批准待发
                    </button>
                    <button
                      type="button"
                      className="danger"
                      onClick={() =>
                        api
                          .transition(d.direction, d.id, 'reject')
                          .then(() => loadBase())
                          .catch((e) => setErr(String(e)))
                      }
                    >
                      打回
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() =>
                        api
                          .exportDraft(d.direction, d.id)
                          .then((r) => setMsg(`已导出至 content-os/duanzi/${r.path}`))
                          .catch((e) => setErr(String(e)))
                      }
                    >
                      导出
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() =>
                        api
                          .publish(d.direction, d.id)
                          .then(() => setMsg('已标记 published（本地记录，非社交平台发帖）'))
                          .catch((e) => setErr(String(e)))
                      }
                    >
                      确认发出记录
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'stats' && (
        <section className="panel">
          <h3>日统计（daily.csv）</h3>
          <table>
            <thead>
              <tr>
                <th>日期</th>
                <th>方向</th>
                <th>进料</th>
                <th>打回</th>
                <th>发出</th>
                <th>备注</th>
              </tr>
            </thead>
            <tbody>
              {daily.map((row) => (
                <tr key={`${row.date}-${row.direction}`}>
                  <td>{row.date}</td>
                  <td>{DIRECTION_LABELS[row.direction as DirectionKey] || row.direction}</td>
                  <td>{row.intake}</td>
                  <td>{row.rejected}</td>
                  <td>{row.published}</td>
                  <td>{row.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ fontSize: '0.85rem', color: '#666' }}>进料 / 打回 / 发出会在流水线操作时自动累加，也可在此只读查看。</p>
        </section>
      )}

      {tab === 'settings' && (
        <section className="panel">
          <h3>模型优先级</h3>
          <ol>
            <li>Cursor Pro API — 主力（环境变量 <code>CURSOR_API_KEY</code>）</li>
            <li>Ollama — 备用（本地 URL / 模型名）</li>
          </ol>
          <div className="form-grid">
            <label>
              Ollama 地址
              <input
                value={String(runtime.ollama_base_url || '')}
                onChange={(e) => setRuntime({ ...runtime, ollama_base_url: e.target.value })}
              />
            </label>
            <label>
              Ollama 模型
              <input
                value={String(runtime.ollama_model || '')}
                onChange={(e) => setRuntime({ ...runtime, ollama_model: e.target.value })}
              />
            </label>
            <label>
              超时（秒）
              <input
                type="number"
                value={Number(runtime.timeout_seconds || 120)}
                onChange={(e) => setRuntime({ ...runtime, timeout_seconds: Number(e.target.value) })}
              />
            </label>
            <button
              type="button"
              className="primary"
              onClick={() =>
                api
                  .saveModelsConfig(runtime)
                  .then(() => setMsg('已保存至 content-os/duanzi/config/runtime.json（不含密钥）'))
                  .catch((e) => setErr(String(e)))
              }
            >
              保存配置
            </button>
          </div>
          <div className="notice">请勿在界面或仓库中保存 API 密钥；发布内容须人工确认，本系统不代发社交平台。</div>
        </section>
      )}

      {editor && (
        <section className="panel editor">
          <h3>
            编辑草稿 {editor.id}（{DIRECTION_LABELS[editor.direction as DirectionKey] || editor.direction}）
          </h3>
          <textarea
            value={editor.detail.content}
            onChange={(e) => setEditor({ ...editor, detail: { ...editor.detail, content: e.target.value } })}
          />
          <div className="actions" style={{ marginTop: '0.75rem' }}>
            <button type="button" className="primary" onClick={() => saveEditor().catch((e) => setErr(String(e)))}>
              保存
            </button>
            <button type="button" className="secondary" onClick={() => setEditor(null)}>
              关闭
            </button>
          </div>
        </section>
      )}
    </div>
  )
}

export default App
