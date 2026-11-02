# 段子产线 Web 控制台

浏览器内控制段子（duanzi）进料 → 去重 → 成稿 → 机械自检 → 品鉴 → 待发；**不**自动发帖，仅本地标记 `ready` / `published` 与导出 Markdown。

## 结构

| 路径 | 说明 |
|------|------|
| `backend/` | FastAPI，读写 `content-os/duanzi/` 下 inbox、drafts、stats |
| `frontend/` | Vite + React，中文界面 |

运行时数据（不提交密钥）：

- `content-os/duanzi/config/runtime.json` — Ollama 地址等（从 `runtime.example.json` 复制）
- `content-os/duanzi/directions/<方向>/inbox/*.json` — 进料条目
- `content-os/duanzi/exports/` — ready 稿导出

## 启动（两个终端）

### 1. 后端 API

```bash
cd web/backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export CURSOR_API_KEY=   # 可选，主力模型；勿写入仓库
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. 前端

```bash
cd web/frontend
npm install
npm run dev
```

浏览器打开 http://127.0.0.1:5173 ，API 经 Vite 代理到 `8000`。

## 流水线说明

1. **方向**：crypto / invest / scitech / engineering 可多选；与 `config/directions.yaml` 同步。
2. **进料**：「模拟进料」写入 stub 条目；或「手动导入」；真实 X/Reddit 抓取可接 `POST /api/pipeline/{direction}/intake` 背后接口。
3. **去重**：URL 归一化 + 指纹，见 `stats/fingerprints.jsonl`。
4. **成稿**：从 inbox 生成 Markdown 草稿（占位生成，可编辑）。
5. **自检**：字数与结构槽位机械检查，失败计入 `daily.csv` 打回。
6. **品鉴 / 待发**：界面推状态至 `reviewing` → `ready`；「确认发出记录」仅更新本地 `published` 与统计，**不**调用社交平台 API。

契约详见 [`../content-os/duanzi/IMPLEMENTATION.md`](../content-os/duanzi/IMPLEMENTATION.md)。
