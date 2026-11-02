#!/usr/bin/env python3
"""单币数据卡：固定源优先级 + 自动降级 + 短超时（最多重试 1 次，仅网络错误/5xx/429）。

用法：
  python3 tools/coin_data.py SYMBOL [--hours 72] [--event "2026-10-06 15:52"] [--id C-YYYYMMDD-NN] [--out DIR] [--cg-id ID]

源优先级（锁定，见 sources.md「数据源（锁定）」）：
  K 线 15m/1h/4h：Bitget 永续 → OKX 永续 → Gate 永续 → Binance 现货（data-api.binance.vision）
  BTC 基准：Binance 现货（data-api.binance.vision）
  资金费率：Bitget + Gate + MEXC (+ OKX 若上线) + CoinGecko 衍生品快照里的 Binance
  OI：OKX rubik（若上线）否则 Gate contract_stats；+ CoinGecko 全市场合计
  永不请求（已知封锁）：api.binance.com / fapi.binance.com（451）、api.bybit.com（403）
输出：<out>/ 原始响应；<out>/../SYMBOL-data.json；<out>/../SYMBOL-数据卡.md；stdout 打印数据卡。
时间一律 UTC+8；K 线时间 = 开盘时间。
"""
import argparse, datetime as dt, glob, json, os, re, statistics, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "tools", "cache", "coingecko_ids.json")
TZ = dt.timezone(dt.timedelta(hours=8))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
TIMEOUT = 8
LOG = []          # (source, what, status)
OUT = None
STAMP = dt.datetime.now(TZ).strftime("%Y%m%dT%H%M")

# ---------------------------------------------------------------- helpers
def t8(ms):
    return dt.datetime.fromtimestamp(ms / 1000, TZ)

def hm(ms, full=False):
    return t8(ms).strftime("%m-%d %H:%M") if not full else t8(ms).strftime("%Y-%m-%d %H:%M")

def fp(x):
    if x is None: return "—"
    a = abs(x)
    if a >= 1000: return f"{x:,.1f}"
    if a >= 100: return f"{x:,.2f}"
    if a >= 1: return f"{x:.4f}".rstrip("0").rstrip(".") if a < 10 else f"{x:.3f}".rstrip("0").rstrip(".")
    return f"{x:.5g}"

def pct(a, b):
    return None if (a is None or b in (None, 0)) else (a / b - 1) * 100

def sp(x, d=2):
    return "—" if x is None else f"{x:+.{d}f}%"

def money(x):
    if x is None: return "—"
    if abs(x) >= 1e9: return f"${x/1e9:.2f}B"
    if abs(x) >= 1e6: return f"${x/1e6:.2f}M"
    if abs(x) >= 1e3: return f"${x/1e3:.1f}K"
    return f"${x:.0f}"

def save(name, body, ext="json"):
    if OUT is None: return
    fn = os.path.join(OUT, f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', name)}-{STAMP}.{ext}")
    with open(fn, "wb") as f:
        f.write(body if isinstance(body, bytes) else body.encode())

def get(url, name, src, what, keep=True):
    """GET JSON. 1 retry only on network error/5xx/429. HTTP 4xx → no retry."""
    for attempt in (0, 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                body = r.read()
            data = json.loads(body)
            if keep: save(name, body)
            return data
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt == 0:
                time.sleep(1); continue
            try: b = e.read()[:1500]
            except Exception: b = b""
            save(f"{name}-HTTP{e.code}", b"URL: " + url.encode() + b"\n" + b, "txt")
            LOG.append((src, what, f"HTTP {e.code}")); return None
        except Exception as e:
            if attempt == 0: continue
            LOG.append((src, what, f"ERR {type(e).__name__}")); return None

# ---------------------------------------------------------------- klines (normalized: [ms, o, h, l, c, quote_vol])
def k_bitget(sym, iv):
    g = {"1m": "1m", "15m": "15m", "1h": "1H", "4h": "4H"}[iv]
    d = get(f"https://api.bitget.com/api/v2/mix/market/candles?symbol={sym}USDT&productType=USDT-FUTURES&granularity={g}&limit=1000",
            f"bitget-fut-{sym}USDT-{g}", "Bitget", f"K线{iv}")
    if not d or d.get("code") != "00000" or not d.get("data"): return None
    return [[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[6])] for k in d["data"]]

def k_okx(sym, iv):
    b = {"1m": "1m", "15m": "15m", "1h": "1H", "4h": "4H"}[iv]
    inst = f"{sym}-USDT-SWAP"; rows = []; after = ""
    for page in range(3):  # 3×300 = 900 bars
        d = get(f"https://www.okx.com/api/v5/market/history-candles?instId={inst}&bar={b}&limit=300{after}",
                f"okx-swap-{inst}-{b}-p{page}", "OKX", f"K线{iv}")
        if not d or d.get("code") != "0" or not d.get("data"): break
        rows += d["data"]; after = f"&after={d['data'][-1][0]}"
        if len(d["data"]) < 300: break
    if not rows: return None
    out = {int(k[0]): [int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[7])] for k in rows}
    return [out[k] for k in sorted(out)]

def k_gate(sym, iv):
    d = get(f"https://api.gateio.ws/api/v4/futures/usdt/candlesticks?contract={sym}_USDT&interval={iv}&limit=1000",
            f"gate-fut-{sym}_USDT-{iv}", "Gate", f"K线{iv}")
    if not isinstance(d, list) or len(d) < 50: return None
    return [[int(k["t"]) * 1000, float(k["o"]), float(k["h"]), float(k["l"]), float(k["c"]), float(k.get("sum") or 0)] for k in d]

def k_bvision(sym, iv):
    d = get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}USDT&interval={iv}&limit=1000",
            f"binance-spot-{sym}USDT-{iv}", "Binance现货", f"K线{iv}")
    if not isinstance(d, list) or not d: return None
    return [[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[7])] for k in d]

KSRC = [("Bitget USDT 永续", k_bitget), ("OKX USDT 永续", k_okx), ("Gate USDT 永续", k_gate), ("Binance 现货（data-api.binance.vision）", k_bvision)]

def klines(sym, skip=()):
    for label, fn in KSRC:
        if label.split()[0].lower() in skip: LOG.append((label.split()[0], "K线", "--skip 跳过")); continue
        h1 = fn(sym, "1h")
        if not h1 or len(h1) < 50:
            LOG.append((label.split()[0], "K线1h", "无此币/失败→降级")); continue
        m15 = fn(sym, "15m"); h4 = fn(sym, "4h")
        if m15 and h4: return label, fn, m15, h1, h4
        LOG.append((label.split()[0], "K线15m/4h", "缺失→降级"))
    return None, None, None, None, None

# ---------------------------------------------------------------- calc
def ema(vals, n):
    k = 2 / (n + 1); e = vals[0]; out = []
    for v in vals:
        e = v * k + e * (1 - k); out.append(e)
    return out

def price_at(m15, ms):
    """open of the 15m bar containing ms (falls back to nearest earlier close)."""
    best = None
    for k in m15:
        if k[0] <= ms < k[0] + 900_000: return k[1]
        if k[0] + 900_000 <= ms: best = k[4]
    return best

def pivots(h1, n=3):
    hi, lo = [], []
    for i in range(n, len(h1) - n):
        win = h1[i - n:i + n + 1]
        if h1[i][2] == max(k[2] for k in win): hi.append((h1[i][0], h1[i][2]))
        if h1[i][3] == min(k[3] for k in win): lo.append((h1[i][0], h1[i][3]))
    return hi, lo

def rel_ema(p, a, b):
    lo, hi = sorted([a, b])
    return "之上" if p > hi else ("之下" if p < lo else "之间")

# ---------------------------------------------------------------- coingecko
def cg_id(sym, override=None):
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    if override:
        cache[sym] = {"id": override, "name": override, "src": "manual", "at": STAMP}
    elif sym not in cache:
        d = get(f"https://api.coingecko.com/api/v3/search?query={sym}", f"coingecko-search-{sym}", "CoinGecko", "id 解析")
        cands = [c for c in (d or {}).get("coins", []) if c.get("symbol", "").upper() == sym]
        cands.sort(key=lambda c: c.get("market_cap_rank") or 10**9)
        if not cands: return None
        c = cands[0]
        cache[sym] = {"id": c["id"], "name": c["name"], "rank": c.get("market_cap_rank"), "src": "search", "at": STAMP}
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=1)
    return cache[sym]

def cg_derivs(sym):
    d = get("https://api.coingecko.com/api/v3/derivatives", "coingecko-derivatives", "CoinGecko", "衍生品快照", keep=False)
    if not isinstance(d, list): return []
    rows = [x for x in d if (x.get("index_id") or "").upper() == sym and x.get("contract_type") == "perpetual"]
    save(f"coingecko-derivatives-{sym}-filtered", json.dumps(rows, ensure_ascii=False))
    return rows

# ---------------------------------------------------------------- main
def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol"); ap.add_argument("--hours", type=int, default=72)
    ap.add_argument("--event", help='"YYYY-MM-DD HH:MM" UTC+8'); ap.add_argument("--id", help="content_id，默认输出到 topics/<id>*/sources/raw")
    ap.add_argument("--out"); ap.add_argument("--cg-id")
    ap.add_argument("--skip", default="", help="测试降级用，如 bitget,okx")
    a = ap.parse_args(); sym = a.symbol.upper().replace("USDT", "") or a.symbol.upper()
    if a.out: OUT = a.out
    elif a.id:
        m = glob.glob(os.path.join(ROOT, "topics", a.id + "*"))
        OUT = os.path.join(m[0] if m else os.path.join(ROOT, "topics", a.id), "sources", "raw")
    else: OUT = os.path.join(ROOT, "tools", "out", f"{sym}-{STAMP}", "raw")
    OUT = os.path.abspath(OUT); os.makedirs(OUT, exist_ok=True)
    now = int(time.time() * 1000)
    ev = int(dt.datetime.strptime(a.event, "%Y-%m-%d %H:%M").replace(tzinfo=TZ).timestamp() * 1000) if a.event else None

    ksrc, kfn, m15, h1, h4 = klines(sym, tuple(x.strip().lower() for x in a.skip.split(",") if x.strip()))
    if not ksrc: print(f"[失败] {sym} 四个 K 线源都拿不到", file=sys.stderr); sys.exit(2)
    b15 = k_bvision("BTC", "15m"); b1 = k_bvision("BTC", "1h")
    if not b15:  # BTC fallback: Bitget perp
        b15 = k_bitget("BTC", "15m"); b1 = k_bitget("BTC", "1h"); btc_src = "Bitget BTCUSDT 永续"
    else: btc_src = "Binance 现货 BTCUSDT"
    cg = cg_id(sym, a.cg_id)
    mk = None
    if cg:
        r = get(f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={cg['id']}", f"coingecko-markets-{sym}", "CoinGecko", "市值")
        mk = r[0] if isinstance(r, list) and r else None
    der = cg_derivs(sym)
    der_at = max([x.get("last_traded_at") or 0 for x in der] or [0]) * 1000

    # ---- price
    last = m15[-1]; p = last[4]; pts = now
    bp = b15[-1][4] if b15 else None
    W = {}
    for key, ms in (("24h", now - 86_400_000), ("7d", now - 7 * 86_400_000)):
        c, b = pct(p, price_at(m15, ms)), (pct(bp, price_at(b15, ms)) if b15 else None)
        W[key] = {"coin": c, "btc": b, "pp": (c - b) if None not in (c, b) else None}
    event = None
    if ev:
        m1 = b1m = None
        if now - ev < 15 * 3_600_000:  # 1m 精度（1000 根 ≈ 16h 内）
            m1 = kfn(sym, "1m"); b1m = k_bvision("BTC", "1m") if btc_src.startswith("Binance") else k_bitget("BTC", "1m")
        def at1(ser1, ser15, ms):
            if ser1:
                for k in ser1:
                    if k[0] <= ms < k[0] + 60_000: return k[1]
            return price_at(ser15, ms)
        pe = at1(m1, m15, ev); be = at1(b1m, b15, ev) if b15 else None
        pre_c = pct(pe, price_at(m15, ev - 86_400_000)); pre_b = pct(be, price_at(b15, ev - 86_400_000)) if b15 else None
        post_c = pct(p, pe); post_b = pct(bp, be) if b15 else None
        after = [k for k in m1 if k[0] >= ev // 60_000 * 60_000] if m1 else [k for k in m15 if k[0] >= ev]
        mx = max(after, key=lambda k: k[2]) if after else None; mn = min(after, key=lambda k: k[3]) if after else None
        event = {"time": hm(ev, True), "precision": "1m" if m1 else "15m", "price_at": pe, "btc_at": be, "pre24h": pre_c, "pre24h_btc": pre_b,
                 "post": post_c, "post_btc": post_b, "post_pp": (post_c - post_b) if None not in (post_c, post_b) else None,
                 "post_high": [hm(mx[0]), mx[2]] if mx else None, "post_low": [hm(mn[0]), mn[3]] if mn else None}
    wk = [k for k in m15 if k[0] >= now - 7 * 86_400_000]
    hi7 = max(wk, key=lambda k: k[2]); lo7 = min(wk, key=lambda k: k[3])

    # ---- structure
    win = [k for k in h1 if k[0] >= now - a.hours * 3_600_000]
    phi, plo = pivots(h1[:-1])
    phi = [x for x in phi if x[0] >= now - a.hours * 3_600_000][-3:]; plo = [x for x in plo if x[0] >= now - a.hours * 3_600_000][-3:]
    c1 = [k[4] for k in h1]; c4 = [k[4] for k in h4]
    e1 = (ema(c1, 144), ema(c1, 169)); e4 = (ema(c4, 144), ema(c4, 169))
    done = h1[:-1]
    med = statistics.median([k[5] for k in done[-168:]]) if len(done) >= 24 else None
    top = sorted([k for k in win[:-1]], key=lambda k: -k[5])[:3]
    vol = [{"t": hm(k[0]), "quote": k[5], "x": (k[5] / med) if med else None, "bar_pct": pct(k[4], k[1])} for k in top]

    # ---- funding (% per period)
    F = []
    d = get(f"https://api.bitget.com/api/v2/mix/market/current-fund-rate?symbol={sym}USDT&productType=USDT-FUTURES", f"bitget-funding-current-{sym}USDT", "Bitget", "费率")
    if d and d.get("data"):
        x = d["data"][0]; hist = get(f"https://api.bitget.com/api/v2/mix/market/history-fund-rate?symbol={sym}USDT&productType=USDT-FUTURES&pageSize=3", f"bitget-funding-history-{sym}USDT", "Bitget", "费率历史")
        F.append({"venue": "Bitget", "rate": float(x["fundingRate"]) * 100, "interval_h": int(x.get("fundingRateInterval") or 8),
                  "next": hm(int(x["nextUpdate"])) if x.get("nextUpdate") else None,
                  "settled": [[hm(int(h["fundingTime"])), float(h["fundingRate"]) * 100] for h in (hist or {}).get("data") or []]})
    d = get(f"https://api.gateio.ws/api/v4/futures/usdt/contracts/{sym}_USDT", f"gate-contract-{sym}_USDT", "Gate", "费率")
    gate_mult = None
    if isinstance(d, dict) and "funding_rate" in d:
        gate_mult = float(d.get("quanto_multiplier") or 1)
        F.append({"venue": "Gate", "rate": float(d["funding_rate"]) * 100, "interval_h": int(d.get("funding_interval", 28800)) // 3600,
                  "next": hm(int(d["funding_next_apply"]) * 1000) if d.get("funding_next_apply") else None})
    d = get(f"https://contract.mexc.com/api/v1/contract/funding_rate/{sym}_USDT", f"mexc-funding-{sym}_USDT", "MEXC", "费率")
    if d and d.get("success") and d.get("data"):
        x = d["data"]; F.append({"venue": "MEXC", "rate": float(x["fundingRate"]) * 100, "interval_h": int(x.get("collectCycle") or 8),
                                 "next": hm(int(x["nextSettleTime"])) if x.get("nextSettleTime") else None})
    d = get(f"https://www.okx.com/api/v5/public/funding-rate?instId={sym}-USDT-SWAP", f"okx-funding-{sym}-USDT-SWAP", "OKX", "费率")
    okx_listed = bool(d and d.get("code") == "0" and d.get("data"))
    if okx_listed:
        x = d["data"][0]; ft, nt = int(x["fundingTime"]), int(x.get("nextFundingTime") or 0)
        F.append({"venue": "OKX", "rate": float(x["fundingRate"]) * 100, "interval_h": round((nt - ft) / 3_600_000) if nt else 8, "next": hm(ft)})
    bn = [x for x in der if x.get("market") == "Binance (Futures)"]
    if bn and bn[0].get("funding_rate") is not None:
        F.append({"venue": "Binance(CoinGecko)", "rate": float(bn[0]["funding_rate"]), "interval_h": None,
                  "snapshot": hm(int(bn[0]["last_traded_at"]) * 1000)})

    # ---- OI
    OI = {"source": None}
    def chg(series, hours_back, ref=None):
        if not series: return None
        tgt = ref if ref else series[-1][0] - hours_back * 3_600_000
        prev = [s for s in series if s[0] <= tgt]
        return pct(series[-1][1], prev[-1][1]) if prev else None
    ser = None
    if okx_listed:
        d = get(f"https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-volume?ccy={sym}&period=1H", f"okx-rubik-oi-volume-{sym}-1H", "OKX", "OI")
        if d and d.get("code") == "0" and d.get("data"):
            ser = sorted([(int(r[0]), float(r[1])) for r in d["data"]]); OI["source"] = "OKX rubik（全 OKX 合约，USD）"; OI["unit"] = "USD"
    if ser is None:
        d = get(f"https://api.gateio.ws/api/v4/futures/usdt/contract_stats?contract={sym}_USDT&interval=1h&limit=200", f"gate-contract-stats-{sym}_USDT-1h", "Gate", "OI")
        if isinstance(d, list) and d:
            ser = sorted([(int(r["time"]) * 1000, float(r["open_interest"])) for r in d])
            OI["source"] = "Gate contract_stats（张数，价格无关）"; OI["unit"] = "张"
            OI["usd_now"] = float(d[-1].get("open_interest_usd") or 0) if d[-1]["time"] == max(r["time"] for r in d) else None
    if ser:
        OI.update({"now": ser[-1][1], "at": hm(ser[-1][0]), "chg24h": chg(ser, 24), f"chg{a.hours}h": chg(ser, a.hours),
                   "chg_event": chg(ser, 0, ev) if ev else None})
        OI["series"] = [[hm(s[0]), s[1]] for s in ser[-min(len(ser), a.hours + 1):]]
    oi_rows = sorted([(x["market"], float(x.get("open_interest") or 0)) for x in der if x.get("open_interest")], key=lambda r: -r[1])
    OI["cg_total"] = sum(r[1] for r in oi_rows) or None; OI["cg_top"] = oi_rows[:3]; OI["cg_at"] = hm(der_at) if der_at else None

    # ---- chart payload (window bars + EMAs on full history)
    def pack(series, emas, hours):
        idx = [i for i, k in enumerate(series) if k[0] >= now - hours * 3_600_000]
        return {"bars": [series[i] for i in idx], "ema144": [round(emas[0][i], 10) for i in idx], "ema169": [round(emas[1][i], 10) for i in idx]}
    e15 = (ema([k[4] for k in m15], 144), ema([k[4] for k in m15], 169))

    data = {
        "symbol": sym, "generated": dt.datetime.now(TZ).isoformat(timespec="seconds"), "tz": "UTC+8", "hours": a.hours,
        "kline_source": ksrc, "btc_source": btc_src, "out_dir": OUT,
        "coingecko": {"id": cg["id"] if cg else None, "name": cg["name"] if cg else None,
                      "mcap": mk.get("market_cap") if mk else None, "rank": mk.get("market_cap_rank") if mk else None,
                      "price": mk.get("current_price") if mk else None},
        "now": {"price": p, "bar": hm(last[0]), "btc": bp}, "windows": W, "event": event,
        "range7d": {"high": [hm(hi7[0]), hi7[2]], "low": [hm(lo7[0]), lo7[3]]},
        "pivots": {"highs": [[hm(t), v] for t, v in phi], "lows": [[hm(t), v] for t, v in plo]},
        "ema": {"1h": [e1[0][-1], e1[1][-1]], "4h": [e4[0][-1], e4[1][-1]]},
        "volume": {"median7d_1h": med, "top": vol}, "funding": F, "oi": OI,
        "source_log": LOG,
        "chart": {"1h": pack(h1, e1, a.hours), "15m": pack(m15, e15, min(a.hours, 48))},
    }
    base = os.path.dirname(OUT)
    jpath = os.path.join(base, f"{sym}-data.json"); json.dump(data, open(jpath, "w"), ensure_ascii=False, separators=(",", ":"))

    # ---- data card (≤ 40 lines)
    ks = ksrc.split("（")[0]
    L = [f"# {sym} 数据卡｜截至 {hm(now)} UTC+8", ""]
    if cg: L.append(f"- 标的：CoinGecko `{cg['id']}`（{cg['name']}）｜市值 {money(data['coingecko']['mcap'])}｜rank {data['coingecko']['rank'] or '—'}｜源：CoinGecko")
    L.append(f"- K 线源：{ksrc}｜BTC 基准：{btc_src}｜K 线时间=开盘时间")
    L.append(f"- 现价 {fp(p)}（{hm(last[0])} 15m 末根，{ks}）｜BTC {fp(bp)}")
    for k in ("24h", "7d"):
        w = W[k]; ppt = "—" if w["pp"] is None else f"{w['pp']:+.1f}pp"
        L.append(f"- {k}：{sym} {sp(w['coin'])}｜BTC {sp(w['btc'])}｜相对 {ppt}（15m，{ks}/{btc_src.split()[0]}）")
    if event:
        e = event
        epp = "—" if e["post_pp"] is None else f"{e['post_pp']:+.1f}pp"
        L.append(f"- 事件 {e['time']}：事件价 {fp(e['price_at'])}（{e['precision']} 开盘价）｜前 24h {sp(e['pre24h'])}（BTC {sp(e['pre24h_btc'])}）")
        L.append(f"- 事件→现：{sp(e['post'])}（BTC {sp(e['post_btc'])}，相对 {epp}）｜事件后高 {fp(e['post_high'][1])}（{e['post_high'][0]}）低 {fp(e['post_low'][1])}（{e['post_low'][0]}）［{e['precision']}］")
    L.append(f"- 7d 高 {fp(hi7[2])}（{hm(hi7[0])}）｜低 {fp(lo7[3])}（{hm(lo7[0])}）［15m，{ks}］")
    L += ["", f"## 结构（1h，近 {a.hours}h，枢轴 3/3）"]
    L.append("- 摆动高：" + ("、".join(f"{fp(v)}（{hm(t)}）" for t, v in phi) or "—"))
    L.append("- 摆动低：" + ("、".join(f"{fp(v)}（{hm(t)}）" for t, v in plo) or "—"))
    L.append(f"- EMA144/169：1h {fp(e1[0][-1])}/{fp(e1[1][-1])}（价在{rel_ema(p, e1[0][-1], e1[1][-1])}）｜4h {fp(e4[0][-1])}/{fp(e4[1][-1])}（价在{rel_ema(p, e4[0][-1], e4[1][-1])}）［{ks}，{len(h1)}/{len(h4)} 根］")
    L += ["", f"## 量（{ks} 成交额 USDT；7d 1h 中位数 {money(med).replace('$', '')}）"]
    for v in vol: L.append(f"- {v['t']} 那根 1h：{money(v['quote']).replace('$', '')} = {v['x']:.1f}×（该根 {sp(v['bar_pct'], 1)}）")
    L += ["", "## 资金费率（%/期；当期预估）"]
    for f in F:
        if f["venue"].startswith("Binance"):
            L.append(f"- Binance {f['rate']:+.4f}（CoinGecko 衍生品快照 {f['snapshot']}）")
        else:
            st = ("｜近结算 " + " ".join(f"{s[0][6:]} {s[1]:+.4f}" for s in f.get("settled", [])[::-1])) if f.get("settled") else ""
            L.append(f"- {f['venue']} {f['rate']:+.4f}（{f['interval_h']}h 结算，下次 {f['next']}）{st}")
    if not okx_listed: L.append("- OKX：无该永续（跳过）")
    L += ["", "## OI"]
    if ser:
        u = (lambda v: money(v)) if OI["unit"] == "USD" else (lambda v: f"{v:,.0f} 张" + (f"（≈{money(OI.get('usd_now'))}）" if OI.get("usd_now") else ""))
        L.append(f"- {OI['source']}：{u(OI['now'])}（{OI['at']}）｜24h {sp(OI['chg24h'], 1)}｜{a.hours}h {sp(OI[f'chg{a.hours}h'], 1)}" + (f"｜事件后 {sp(OI['chg_event'], 1)}" if ev else ""))
    else: L.append("- OI 历史：OKX/Gate 均无")
    if OI["cg_total"]: L.append(f"- CoinGecko 全市场合计 {money(OI['cg_total'])}（{'、'.join(m.split()[0] + ' ' + money(v) for m, v in OI['cg_top'])}）快照 {OI['cg_at']}；各所口径不一，仅作量级")
    bad = [f"{s} {w} {st}" for s, w, st in LOG]
    L += ["", "## 源状态", "- " + ("；".join(bad) if bad else "全部成功") + f"｜原始响应：{os.path.relpath(OUT, ROOT)}/"]
    card = "\n".join(L)
    cpath = os.path.join(base, f"{sym}-数据卡.md"); open(cpath, "w").write(card + "\n")
    print(card); print(f"\n[JSON] {os.path.relpath(jpath, ROOT)}\n[CARD] {os.path.relpath(cpath, ROOT)}  ({len(L)} 行)")

if __name__ == "__main__":
    main()
