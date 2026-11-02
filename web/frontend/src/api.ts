const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<T>
}

export type DirectionKey = 'crypto' | 'invest' | 'scitech' | 'engineering'

export interface DraftListItem {
  id: string
  filename: string
  direction: string
  title: string
  status: string
  topic_tags: string[]
  path: string
}

export interface DraftDetail {
  meta: Record<string, unknown>
  content: string
  path: string
  sections: { structure: string; body: string; self_check: string }
}

export interface DailyRow {
  date: string
  direction: string
  intake: string
  rejected: string
  published: string
  notes: string
}

export const api = {
  directions: () => request<{ directions: Record<string, { name: string; enabled: boolean }> }>('/directions'),
  drafts: (direction?: string) =>
    request<DraftListItem[]>(direction ? `/drafts?direction=${direction}` : '/drafts'),
  draft: (direction: string, id: string) => request<DraftDetail>(`/drafts/${direction}/${id}`),
  saveDraft: (direction: string, id: string, content: string) =>
    request<DraftDetail>(`/drafts/${direction}/${id}`, { method: 'PUT', body: JSON.stringify({ content }) }),
  transition: (direction: string, id: string, action: string) =>
    request<DraftDetail>(`/drafts/${direction}/${id}/transition`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    }),
  selfCheck: (direction: string, id: string) =>
    request<DraftDetail & { check?: { chars: number; passed: boolean } }>(
      `/drafts/${direction}/${id}/self-check`,
      { method: 'POST' },
    ),
  publish: (direction: string, id: string) =>
    request<DraftDetail>(`/drafts/${direction}/${id}/publish`, {
      method: 'POST',
      body: JSON.stringify({ confirm: true }),
    }),
  exportDraft: (direction: string, id: string) =>
    request<{ path: string; filename: string }>(`/drafts/${direction}/${id}/export`, { method: 'POST' }),
  dailyStats: () => request<DailyRow[]>('/stats/daily'),
  saveDailyRow: (row: DailyRow) =>
    request<DailyRow[]>('/stats/daily/row', { method: 'POST', body: JSON.stringify(row) }),
  inbox: (direction: string) => request<Record<string, unknown>[]>(`/inbox/${direction}`),
  importInbox: (direction: string, body: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/inbox/${direction}/import`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  intake: (direction: string, count = 3) =>
    request<Record<string, unknown>[]>(`/pipeline/${direction}/intake`, {
      method: 'POST',
      body: JSON.stringify({ count }),
    }),
  dedup: (direction?: string) =>
    request<Record<string, unknown>[]>(direction ? `/pipeline/dedup?direction=${direction}` : '/pipeline/dedup'),
  generate: (direction: string, inboxId: string) =>
    request<DraftDetail>(`/pipeline/${direction}/generate`, {
      method: 'POST',
      body: JSON.stringify({ inbox_id: inboxId }),
    }),
  modelsConfig: () =>
    request<{ runtime: Record<string, unknown>; priority: { rank: number; id: string; label: string }[] }>(
      '/config/models',
    ),
  saveModelsConfig: (runtime: Record<string, unknown>) =>
    request<{ runtime: Record<string, unknown> }>('/config/models', {
      method: 'PUT',
      body: JSON.stringify(runtime),
    }),
}

export const DIRECTION_LABELS: Record<DirectionKey, string> = {
  crypto: '币圈',
  invest: '投资',
  scitech: '科技',
  engineering: '技术',
}

export const STATUS_LABELS: Record<string, string> = {
  inbox: '进料',
  drafting: '成稿中',
  self_check: '自检',
  reviewing: '品鉴中',
  ready: '待发',
  published: '已标记发出',
  archived: '归档',
  rejected: '打回',
  draft_failed: '生成失败',
  duplicate: '重复',
}
