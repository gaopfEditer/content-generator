#!/usr/bin/env python3
"""逻辑图：coin_data.py 的 JSON + 小 spec（JSON；装了 PyYAML 也可用 YAML）→ 1600×900 深色 PNG，一次出图。

用法：python3 tools/logic_chart.py <SYMBOL-data.json> <spec.json> [-o out.png]

spec 字段（只有 title/punchline/cards/levels 必填）：
{
  "title": "BR 中性偏多：……",            # 超宽自动缩字号
  "punchline": "上所点火，空头添柴；……",   # 底部横幅
  "cards": [{"title": "为什么涨", "lines": ["……", "……"]}, {...}, {...}],  # 3 张；lines 或 text，自动换行/截断
  "levels": {"确认线": {"price": 0.6177, "label": "21:44 次高"},
             "失效线": {"price": 0.48245, "label": "19:50 回撤低点"},
             "refs": [{"price": 0.50755, "label": "前高"}]},
  "events": [{"time": "2026-10-06 15:52", "label": "Bithumb 公告"}],
  "interval": "1h",            # 或 "15m"（数据里 15m 只有近 48h）
  "info": "……",                # 可选，价格区左上信息框；缺省自动用费率/OI；"" 关闭
  "notes": [{"time": "2026-10-06 18:00", "price": 0.6756, "text": "开盘即顶"}],  # 可选，≤4 条
  "subtitle": "……", "footer": "……", "out": "exports/BR-逻辑图.png"   # 可选，缺省自动
}
"""
import argparse, datetime as dt, json, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.gridspec import GridSpec

FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
fontManager.addfont(FR); fontManager.addfont(FB)
TZ = dt.timezone(dt.timedelta(hours=8))
BG = "#0b0e11"; PANEL = "#12161c"; GRID = "#1e2329"; UP = "#0ecb81"; DOWN = "#f6465d"
TEXT = "#eaecef"; MUTED = "#848e9c"; ACCENT = "#f0b90b"; BLUE = "#5dade2"; BLUE2 = "#2e86c1"; PURPLE = "#b388ff"
CARD_COLORS = [ACCENT, BLUE, UP]; EVENT_COLORS = [ACCENT, PURPLE, BLUE, "#ff8a65"]

def F(size, bold=False):
    return FontProperties(fname=FB if bold else FR, size=size)

def fmtp(x):
    a = abs(x)
    return f"{x:,.0f}" if a >= 10000 else f"{x:,.1f}" if a >= 1000 else f"{x:.2f}" if a >= 10 else f"{x:.4g}" if a >= 1 else f"{x:.5g}"

def load(p):
    txt = open(p, encoding="utf-8").read()
    if p.endswith((".yml", ".yaml")):
        import yaml  # 可选依赖
        return yaml.safe_load(txt)
    return json.loads(txt)

def to_ms(s):
    return int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=TZ).timestamp() * 1000)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("spec"); ap.add_argument("-o", "--out")
    a = ap.parse_args()
    D = load(a.data); S = load(a.spec)
    iv = S.get("interval", "1h"); ivms = {"1h": 3_600_000, "15m": 900_000}[iv]
    ch = D["chart"][iv]; bars = ch["bars"]; e144 = ch["ema144"]; e169 = ch["ema169"]
    if S.get("hours"):
        cut = bars[-1][0] - int(S["hours"]) * 3_600_000
        keep = [i for i, b in enumerate(bars) if b[0] >= cut]
        bars = [bars[i] for i in keep]; e144 = [e144[i] for i in keep]; e169 = [e169[i] for i in keep]
    n = len(bars); x = list(range(n)); t0 = bars[0][0]
    T = [dt.datetime.fromtimestamp(b[0] / 1000, TZ) for b in bars]
    O, H, L, C, V = ([b[k] for b in bars] for k in (1, 2, 3, 4, 5))
    gen_ms = int(dt.datetime.fromisoformat(D["generated"]).timestamp() * 1000)
    last_open = bars[-1][0] + ivms > gen_ms
    sym = D["symbol"]; src = D["kline_source"].split("（")[0]
    sd = os.path.dirname(os.path.abspath(a.spec))   # -o 相对当前目录；spec.out 相对 spec 所在目录
    out = os.path.abspath(a.out) if a.out else os.path.join(sd, S.get("out") or f"{sym}-逻辑图.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=BG)
    R = fig.canvas.get_renderer()
    def width_px(s, fp):
        return R.get_text_width_height_descent(s, fp, ismath=False)[0]
    def fit_size(s, bold, start, min_size, max_px):
        sz = start
        while sz > min_size and width_px(s, F(sz, bold)) > max_px: sz -= 0.5
        return sz
    def truncate(s, fp, max_px):
        if width_px(s, fp) <= max_px: return s
        while s and width_px(s + "…", fp) > max_px: s = s[:-1]
        return s + "…"
    def wrap(s, fp, max_px, indent="  "):
        toks = re.findall(r"[A-Za-z0-9$.%+\-−/:,#×~→←]+|\s+|.", s); lines = []; cur = ""
        for tk in toks:
            if width_px(cur + tk, fp) <= max_px or not cur.strip() or tk in "，。、；：）」』！？,.;:)%":
                cur += tk
            else:
                lines.append(cur.rstrip()); cur = indent + tk.lstrip()
        if cur.strip(): lines.append(cur.rstrip())
        return lines or [""]

    gs = GridSpec(5, 2, figure=fig, height_ratios=[0.52, 3.75, 1.05, 0.30, 0.66], width_ratios=[3.45, 1.40],
                  left=0.05, right=0.975, top=0.945, bottom=0.05, hspace=0.07, wspace=0.05)
    # ---------------- title
    ax_t = fig.add_subplot(gs[0, :]); ax_t.axis("off"); ax_t.set_xlim(0, 1); ax_t.set_ylim(0, 1)
    W = fig.get_figwidth() * fig.dpi * 0.92
    ttl = S["title"]; ax_t.text(0.5, 0.62, ttl, ha="center", va="center", color=TEXT, fontproperties=F(fit_size(ttl, True, 19, 13, W), True))
    kind = "现货" if "现货" in D["kline_source"] else "永续"
    sub = S.get("subtitle") or (f"{sym}USDT {kind} {iv}（{src}）｜{T[0]:%m-%d %H:%M} → {dt.datetime.fromtimestamp(gen_ms/1000, TZ):%m-%d %H:%M} UTC+8"
                                + ("｜末根未完成（半透明）" if last_open else "") + "｜K 线按开盘时间")
    ax_t.text(0.5, 0.06, truncate(sub, F(10.5), W), ha="center", va="center", color=MUTED, fontproperties=F(10.5))

    # ---------------- price + volume
    ax = fig.add_subplot(gs[1, 0]); ax.set_facecolor(PANEL)
    axv = fig.add_subplot(gs[2, 0], sharex=ax); axv.set_facecolor(PANEL)
    for q in (ax, axv):
        for s_ in q.spines.values(): s_.set_color(GRID)
        q.tick_params(colors=MUTED, labelsize=9); q.grid(color=GRID, lw=0.6)
    lv = S.get("levels", {}); levels = []
    def norm(v, name, col, ls, bold):
        if v is None: return
        if isinstance(v, (int, float)): v = {"price": v}
        levels.append({"price": float(v["price"]), "text": f"{name} {fmtp(float(v['price']))}" + (f"（{v['label']}）" if v.get("label") else ""), "col": col, "ls": ls, "bold": bold})
    norm(lv.get("确认线"), "确认线", UP, "-", True); norm(lv.get("失效线"), "失效线", DOWN, "-", True)
    for j, r in enumerate(lv.get("refs") or []):
        norm(r, r.get("name", ""), r.get("color") or (ACCENT if j == 0 else MUTED), "--" if j == 0 else ":", False)
    for v in levels: v["text"] = v["text"].strip()
    lo, hi = min(L + [v["price"] for v in levels]), max(H + [v["price"] for v in levels])
    rng = hi - lo or hi * 0.01
    ylo, yhi = lo - rng * 0.06, hi + rng * 0.32
    ax.set_ylim(ylo, yhi); ax.set_xlim(-0.8, n - 0.2)
    yr = yhi - ylo
    # EMA tunnel (clip to view)
    ax.fill_between(x, e144, e169, color=BLUE, alpha=0.10, lw=0)
    ax.plot(x, e144, color=BLUE, lw=1.1, alpha=0.9, label=f"EMA144（{iv}）")
    ax.plot(x, e169, color=BLUE2, lw=1.1, alpha=0.9, label=f"EMA169（{iv}）")
    w = 0.66
    for i in range(n):
        col = UP if C[i] >= O[i] else DOWN; al = 0.45 if (i == n - 1 and last_open) else 1.0
        ax.vlines(i, L[i], H[i], color=col, lw=1.0, alpha=al)
        b0, b1 = sorted([O[i], C[i]])
        ax.add_patch(plt.Rectangle((i - w / 2, b0), w, max(b1 - b0, yr * 0.0015), color=col, alpha=al, lw=0))
        axv.bar(i, V[i], width=w, color=col, alpha=0.85 * al)
    # levels with label de-overlap
    gap = yr * 0.045; placed = []
    for v in sorted(levels, key=lambda z: -z["price"]):
        ax.axhline(v["price"], color=v["col"], ls=v["ls"], lw=1.3 if v["bold"] else 0.9, alpha=0.95 if v["bold"] else 0.75)
        ylab = v["price"] + yr * 0.006
        for p in placed:
            if abs(ylab - p) < gap: ylab = p - gap
        placed.append(ylab)
        ax.text(0.6, ylab, v["text"], color=v["col"], fontproperties=F(9.5 if v["bold"] else 8.5, v["bold"]), ha="left", va="bottom",
                bbox=dict(boxstyle="round,pad=0.15", fc=PANEL, ec="none", alpha=0.75), zorder=6)
    # events
    evx = []
    for k, e in enumerate((S.get("events") or [])[:4]):
        xx = (to_ms(e["time"]) - t0) / ivms - 0.5
        if not (-0.8 <= xx <= n - 0.2): continue
        col = e.get("color") or EVENT_COLORS[k % 4]
        ax.axvline(xx, color=col, ls="--", lw=1.0, alpha=0.9); axv.axvline(xx, color=col, ls="--", lw=1.0, alpha=0.9)
        row = sum(1 for px in evx if abs(px - xx) < n * 0.18) % 2; evx.append(xx)
        right = xx < n * 0.8
        ax.text(xx + (0.4 if right else -0.4), 0.86 - row * 0.05, f"{e['time'][11:]} {e['label']}", transform=ax.get_xaxis_transform(),
                color=col, fontproperties=F(9, True), ha="left" if right else "right", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc=PANEL, ec="none", alpha=0.8), zorder=7)
    # optional notes
    for k, nt in enumerate((S.get("notes") or [])[:4]):
        xx = (to_ms(nt["time"]) - t0) / ivms
        if not (0 <= xx <= n): continue
        yy = float(nt["price"]); below = yy > (ylo + yhi) / 2
        ax.annotate(nt["text"], xy=(xx, yy), xytext=(max(3, min(n - 6, xx - n * 0.08)), yy - yr * 0.09 if below else yy + yr * 0.09),
                    color=TEXT, fontproperties=F(8.8), ha="center", va="center", zorder=8,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7), bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec=MUTED, lw=0.6, alpha=0.9))
    # info box
    info = S.get("info")
    if info is None:
        fr = "｜".join(f"{f['venue'].replace('(CoinGecko)', '(CG)')} {f['rate']:+.4f}%" for f in D.get("funding", []))
        oi = D.get("oi", {}); hk = f"chg{D.get('hours')}h"
        oit = f"OI（{(oi.get('source') or '').split('（')[0]}）24h {oi['chg24h']:+.1f}%" if oi.get("chg24h") is not None else ""
        if oi.get(hk) is not None: oit += f"｜{D.get('hours')}h {oi[hk]:+.1f}%"
        info = f"资金费率（当期预估/期）：{fr}\n{oit}"
    if info:
        ax.text(0.012, 0.975, info, transform=ax.transAxes, color=TEXT, fontproperties=F(8.6), va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.4", fc="#1a1e24", ec=GRID, lw=0.8), zorder=9)
    ax.legend(loc="upper right", prop=F(8.5), facecolor="#1a1e24", edgecolor=GRID, labelcolor=MUTED, framealpha=0.9)
    ax.yaxis.tick_right(); plt.setp(ax.get_xticklabels(), visible=False)
    # volume panel
    axv.yaxis.tick_right()
    vmax = max(V) or 1; unit, div = ("B", 1e9) if vmax >= 3e9 else ("M", 1e6) if vmax >= 3e6 else ("K", 1e3)
    axv.set_ylim(0, vmax * 1.25)
    axv.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/div:.0f}{unit}" if v else "0"))
    axv.text(0.006, 0.9, f"成交额（USDT，{src}）", transform=axv.transAxes, color=MUTED, fontproperties=F(8.5), va="top")
    vol = D.get("volume", {}); med = vol.get("median7d_1h")
    if iv == "1h" and med:
        im = max(range(n - (1 if last_open else 0)), key=lambda i: V[i])
        axv.text(im + (-0.6 if im > n * 0.5 else 0.6), V[im], f"{T[im]:%m-%d %H:%M} = 7 日小时中位数 {V[im]/med:.0f}×",
                 color=ACCENT, fontproperties=F(8.8, True), ha="right" if im > n * 0.5 else "left", va="top")
    step = 1 if iv == "15m" else (12 if n <= 100 else 24)
    if iv == "15m": ticks = [i for i, t in enumerate(T) if t.minute == 0 and t.hour % 6 == 0]
    else: ticks = [i for i, t in enumerate(T) if t.hour % step == 0]
    axv.set_xticks(ticks); axv.set_xticklabels([T[i].strftime("%m-%d %H:%M") for i in ticks], fontproperties=F(8.5), color=MUTED)

    # ---------------- cards
    axc = fig.add_subplot(gs[1:3, 1]); axc.axis("off"); axc.set_xlim(0, 1); axc.set_ylim(0, 1)
    fig.canvas.draw(); bb = axc.get_window_extent(R); cw_px, ch_px = bb.width, bb.height
    cgap = 0.0225; h = (1 - 2 * cgap) / 3; y = 1.0
    body = F(9.8); LH = 0.037                      # 行距（axes 单位，≈22px）
    cap = int((h - 0.085 - 0.02) / LH) + 1         # 每卡最多行数（=6）
    for k, cd in enumerate((S.get("cards") or [])[:3]):
        col = cd.get("color") or CARD_COLORS[k]; y0 = y - h
        axc.add_patch(FancyBboxPatch((0.02, y0), 0.96, h, boxstyle="round,pad=0.004,rounding_size=0.02", fc="#161a20", ec=col, lw=1.2))
        axc.add_patch(plt.Rectangle((0.02, y0 + h - 0.052), 0.96, 0.052, color=col, alpha=0.18, lw=0))
        maxw = cw_px * 0.86
        axc.text(0.06, y0 + h - 0.026, truncate(cd.get("title", ""), F(12, True), maxw), color=col, fontproperties=F(12, True), va="center")
        src_lines = cd.get("lines") or [cd.get("text", "")]
        out_lines = []
        for ln in src_lines: out_lines += wrap(ln, body, maxw)
        if len(out_lines) > cap:
            out_lines = out_lines[:cap]; out_lines[-1] = truncate(out_lines[-1] + "……", body, maxw)
        for j, ln in enumerate(out_lines):
            axc.text(0.06, y0 + h - 0.085 - j * LH, ln, color=TEXT, fontproperties=body, va="center")
        y = y0 - cgap

    # ---------------- banner + footer
    axb = fig.add_subplot(gs[4, :]); axb.axis("off"); axb.set_xlim(0, 1); axb.set_ylim(0, 1)
    axb.add_patch(FancyBboxPatch((0.0, 0.40), 1.0, 0.56, boxstyle="round,pad=0.005,rounding_size=0.02", fc="#1a1e24", ec=ACCENT, lw=1.0))
    pl = S.get("punchline", ""); axb.text(0.5, 0.68, pl, color=ACCENT, fontproperties=F(fit_size(pl, True, 17, 11, W), True), ha="center", va="center")
    if S.get("footer"): foot = S["footer"]
    else:
        fv = "/".join(f["venue"].replace("(CoinGecko)", "") for f in D.get("funding", []))
        foot = (f"数据：{D['kline_source']} K 线；{D['btc_source']}；资金费率 {fv}（Binance 取 CoinGecko 快照）；"
                f"OI {(D.get('oi', {}).get('source') or '—').split('（')[0]}；CoinGecko。截至 {dt.datetime.fromtimestamp(gen_ms/1000, TZ):%m-%d %H:%M} UTC+8")
    axb.text(0.0, 0.10, truncate(foot, F(8.6), W * 0.86), color=MUTED, fontproperties=F(8.6), ha="left", va="center")
    axb.text(1.0, 0.10, "编辑推演，不构成投资建议", color=MUTED, fontproperties=F(9, True), ha="right", va="center")
    fig.savefig(out, dpi=100, facecolor=BG)
    print(out)

if __name__ == "__main__":
    main()
