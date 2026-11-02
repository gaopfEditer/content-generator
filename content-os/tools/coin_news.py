#!/usr/bin/env python3
"""单币快讯检索：只查 sources.md「快讯消息源（锁定）」N1–N4，一次命令跑完，不交叉验证。

用法：python3 tools/coin_news.py SYMBOL [--hours 72] [--name Bedrock] [--out DIR] [--max 15]
  N1 crypto-news 看板 data.json（聚合 PANews/Odaily/CoinDesk/The Block，留存 48h）
  N2 PANews 快讯 RSS   N3 Odaily 快讯 RSS
  N4 交易所官方公告：Binance CMS / OKX / Bitget / Upbit（Bithumb 403，不请求）
输出：markdown 列表（时间 UTC+8｜源｜标题｜链接），每源失败只记一行，不重试第二次。
币名缺省取 tools/cache/coingecko_ids.json（coin_data.py 写入）。
"""
import argparse, datetime as dt, email.utils, json, os, re, time, urllib.request, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ = dt.timezone(dt.timedelta(hours=8)); UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
STAMP = dt.datetime.now(TZ).strftime("%Y%m%dT%H%M"); FAIL = []

def get(url, name, out, as_json=True):
    for attempt in (0, 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=8) as r: body = r.read()
            if out: open(os.path.join(out, f"{name}-{STAMP}.{'json' if as_json else 'xml'}"), "wb").write(body)
            return json.loads(body) if as_json else body
        except urllib.error.HTTPError as e:
            FAIL.append(f"{name} HTTP {e.code}"); return None
        except Exception as e:
            if attempt == 0: continue
            FAIL.append(f"{name} {type(e).__name__}"); return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("symbol"); ap.add_argument("--hours", type=int, default=72)
    ap.add_argument("--name"); ap.add_argument("--out"); ap.add_argument("--max", type=int, default=15)
    a = ap.parse_args(); sym = a.symbol.upper()
    if a.out: os.makedirs(a.out, exist_ok=True)
    name = a.name
    cp = os.path.join(ROOT, "tools", "cache", "coingecko_ids.json")
    if not name and os.path.exists(cp): name = (json.load(open(cp)).get(sym) or {}).get("name")
    pats = [rf"(?<![A-Za-z0-9])\$?{re.escape(sym)}(?![A-Za-z0-9])"]
    if name and name.upper() != sym and len(name) >= 4: pats.append(re.escape(name))
    rx_sym = re.compile(pats[0])  # 符号大小写敏感，避免 br/sol 误中
    hit = lambda s: bool(rx_sym.search(s or "")) or (len(pats) > 1 and bool(re.search(pats[1], s or "", re.I)))
    since = time.time() - a.hours * 3600; rows = []
    def add(ts, src, title, url):
        if ts >= since: rows.append((ts, src, re.sub(r"\s+", " ", title).strip(), url))

    d = get("https://raw.githubusercontent.com/gaopfEditer/crypto-news/gh-pages/data.json", "N1-dashboard", a.out)
    for s in (d or {}).get("stories", []):
        if sym in (s.get("coins") or []) or sym in (s.get("tokens") or []) or hit(s.get("title")):
            tag = s.get("impact_tag") or ""
            add(s.get("ts") or 0, "看板/" + "+".join(s.get("sources") or [s.get("label", "")]), (tag + " " if tag else "") + s["title"], s.get("url"))
    for nm, url in (("N2-PANews", "https://www.panewslab.com/zh/rss/newsflash.xml"), ("N3-Odaily", "https://rss.odaily.news/rss/newsflash")):
        b = get(url, nm, a.out, as_json=False)
        if not b: continue
        for it in ET.fromstring(b).findall(".//item"):
            t = it.findtext("title") or ""; desc = re.sub("<[^>]+>", "", it.findtext("description") or "")
            if hit(t) or rx_sym.search(desc):  # 正文只认符号，币名只认标题（防 Amazon Bedrock 类误中）
                add(email.utils.parsedate_to_datetime(it.findtext("pubDate")).timestamp(), nm[3:], t, it.findtext("link"))
    b = get("https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20", "N4-binance", a.out)
    for c in ((b or {}).get("data") or {}).get("catalogs", []):
        for x in c.get("articles") or []:
            if hit(x["title"]): add(x["releaseDate"] / 1000, f"Binance公告/{c['catalogName']}", x["title"], f"https://www.binance.com/zh-CN/support/announcement/detail/{x['code']}")
    o = get("https://www.okx.com/api/v5/support/announcements?page=1", "N4-okx", a.out)
    for g in (o or {}).get("data", []):
        for x in g.get("details", []):
            if hit(x["title"]): add(int(x["pTime"]) / 1000, "OKX公告", x["title"], x["url"])
    g = get("https://api.bitget.com/api/v2/public/annoucements?language=zh_CN", "N4-bitget", a.out)
    for x in (g or {}).get("data") or []:
        if hit(x["annTitle"]): add(int(x["cTime"]) / 1000, "Bitget公告", x["annTitle"], x["annUrl"])
    u = get("https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=20&category=trade", "N4-upbit", a.out)
    for x in ((u or {}).get("data") or {}).get("notices", []):
        if hit(x["title"]): add(dt.datetime.fromisoformat(x["listed_at"]).timestamp(), "Upbit公告", x["title"], f"https://upbit.com/service_center/notice?id={x['id']}")

    seen, outl = set(), []
    for ts, src, t, url in sorted(rows, key=lambda r: -r[0]):
        k = re.sub(r"\W", "", t)[:24]
        if k in seen: continue
        seen.add(k); outl.append(f"- {dt.datetime.fromtimestamp(ts, TZ):%m-%d %H:%M}｜{src}｜{t}｜{url}")
    print(f"# {sym} 快讯（锁定源 N1–N4，近 {a.hours}h，截至 {dt.datetime.now(TZ):%m-%d %H:%M} UTC+8；匹配：{sym}{'/' + name if name else ''}）")
    print("\n".join(outl[:a.max]) if outl else "- 无匹配")
    if len(outl) > a.max: print(f"- ……另有 {len(outl) - a.max} 条未列")
    print("- 源状态：" + ("；".join(FAIL) if FAIL else "N1–N4 全部成功"))

if __name__ == "__main__":
    main()
