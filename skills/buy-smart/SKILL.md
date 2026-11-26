---
name: buy-smart
description: Use when the user asks to check a retail deal, holiday sale, discount, or promo code, verify whether a markdown is real or manipulated (pre-sale price hikes, fake list-price anchors, Amazon 1P stock-out 3P scalpers, used-unit buybox hijacks, dropship clone markups, or stripped holiday derivative SKUs), compare live prices across retailers, check a whole shopping cart, or compare an annual SaaS promo against pay-per-call treg endpoints. Accepts a product URL (including a.co/amzn.to shortlinks and regional Amazon domains), a product name, or both.
metadata:
  summary: Audits product links, names, shopping carts, or SaaS annual promos against Wayback Machine ($0), CamelCamelCamel, sanitized multi-store comps, and Reddit owner threads, returning a 0-100 Manipulation BS-Score, a better move, and the exact itemized treg bill (~$0.0055 per audit).
---

# buy-smart

Before you click Buy, let your agent verify whether a discount is real or staged. Accepts a product
URL (Amazon US/UK/DE/CA/AU/FR/ES/IT/JP, `a.co`/`amzn.to` shortlinks, Shopify, or DTC stores), a
plain product name, a whole shopping cart, or a SaaS `/pricing` URL.

Runs on treg, through its MCP tools (`catalog_search`, `catalog_get`, `call`) or the `treg` CLI;
either is enough. With neither set up, https://treg.to/llms.txt says how. Install only if the human asked
you to; otherwise tell them how and stop.

Zero affiliate links. Zero SEO "Top 10" listicles. Default budget cap: **$0.03 per single-item
audit** (typical URL audit: ~$0.0055; name-only audit: ~$0.0065).

## Modes

| Mode | Trigger | What it delivers |
| --- | --- | --- |
| **audit** (default) | Product link, shortlink, product name, or both | Regional ASIN resolution, Wayback ($0) + CamelCamelCamel 1P/3P history, live Amazon & sanitized 40-store comps, Reddit defect clusters, 0-100 BS-Score, optional Jev 1.13 verdict |
| **cart** | Multiple links or product names | Parallel per-item audits aggregated into **Direct swap savings** vs. **Bad spend blocked** alongside exact metered treg bill |
| **pick** | Category + budget ("best 65-inch OLED TV under $1,500") | Size-verified multi-store comps + niche Reddit owner threads + stripped holiday SKU guard -> #1 pick, runner-up, lowest verified 1P store |
| **saas** | SaaS annual promo URL or name (Semrush, Clay, Apollo, Ahrefs) | Live `/pricing` extract + Wayback check + treg pay-per-call annual cost receipt (`BUY PROMO` vs. `KILL SUBSCRIPTION`) |

## The 4-step loop

1. **Resolve (`$0.00`, or `+$0.00099` if name-only).** Save the stdlib script at the end of this
   file once as `buy_smart.py`, then resolve the user's input:
   ```bash
   python3 buy_smart.py resolve "<exact user input>" > /tmp/bs_resolved.json
   ```
   - If `mode == "url_amazon"`, you already have `asin`, `country`, `gl`, `currency`,
     `canonical_url`, and regional `camel_url`. Go to Step 2.
   - If `mode == "product_name"` (or a DTC link for a widely sold brand), search for the canonical
     non-renewed Amazon ASIN so CamelCamelCamel works too:
     ```bash
     treg call treg.web.search --method POST --header "X-Treg-Route-Prefer: tinyfish" \
       --data '{"q":"<asin_search_query>","limit":8}' > /tmp/bs_search.json
     ```
2. **Pull live + historical receipts in parallel.** Save each response to `/tmp/`:

   | Output | Call | Notes |
   | --- | --- | --- |
   | `/tmp/bs_wayback.json` | `python3 buy_smart.py wayback "<canonical_url>" --days 365 --samples 6` | Free ($0.00); parses Amazon, Shopify variant JSON, SSR stores, and SaaS `/pricing`; skips cleanly on JS SPAs or sandboxed networks |
   | `/tmp/bs_camel.json` | `treg call treg.web.extract --method POST --data '{"url":"<camel_url>"}'` | Lifetime Min, Max, Avg, Current split across Amazon 1P, 3P New, and 3P Used |
   | `/tmp/bs_amazon.json` | `treg call crawl4ai.amazon.product.detail --method POST --data '{"product":"<asin>","country":"<country>"}'` | Live buybox, stock state, and strikethrough list price (for non-Amazon DTC URLs, extract `canonical_url` with `treg.web.extract` instead) |
   | `/tmp/bs_shopping.json` | `treg call serper.google.serp.shopping --method POST --data '{"q":"<product_name>","gl":"<gl>","hl":"en","num":40}'` | Multi-store offers sanitized for scams, used/refurb, parts, multi-packs, and wrong sizes |
   | `/tmp/bs_reddit.json` | `treg call scrapecreators.reddit.search.posts --query "query=<product_name> regret OR broke OR issue OR worth it" --query sort=relevance` | Real owner threads with upvote counts and defect-negation filtering |

   *(Optional upgrades: pull one non-sponsored YouTube transcript via
   `scrapecreators.x.v1-youtube-video-transcript` for >$150 hardware, or check the full live seller
   table via `dataforseo.x.merchant-amazon-sellers-live-advanced` when a 3P buybox looks
   suspicious. For SaaS annual promos, compare extracted tiers against catalog tools such as
   `serpstat.google.domain.overview` and `cloro.ai-search.chatgpt.scrape`.)*

3. **Score deterministically + optional Jev 1.13 verdict.** Never hand-transcribe numbers or raw
   Shopping arrays:
   ```bash
   python3 buy_smart.py pipeline \
     --query "<exact model>" \
     --amazon /tmp/bs_amazon.json \
     --camel /tmp/bs_camel.json \
     --wayback /tmp/bs_wayback.json \
     --shopping /tmp/bs_shopping.json \
     --reddit /tmp/bs_reddit.json \
     --claimed-msrp <optional_msrp> \
     --coupon <optional_coupon_amount> > /tmp/bs_result.json
   ```
   Pass `--sale-price <price>` if the user quoted a specific advertised price, or `--coupon <amt>`
   when an Amazon green checkbox coupon applies. To add an independent judge pass, send the
   pre-built XML-escaped `jev_request` from `/tmp/bs_result.json` to `openrouter.ai-judge.decide`.

4. **Hand back the receipt.** Return the verdict, 0-100 BS-Score, verified historical baseline,
   lowest verified 1P store (with filtered junk named), linked Reddit owner threads with upvote
   counts, one crisp **Better move today**, and the exact itemized treg bill summed from each
   call's actual charge.

   - **Never fabricate missing history:** when both CamelCamelCamel and Wayback return zero usable
     prices (React SPAs like Target/Best Buy/Walmart, Cloudflare walls, or <90d launches), emit
     `UNVERIFIED_PRICE_HISTORY` and grade strictly against live authorized stockists.
   - **Cart mode:** combine per-item result JSONs into a list and run
     `python3 buy_smart.py cart -i /tmp/bs_cart.json` to separate direct store-swap savings from
     bad spend blocked.
   - **SaaS mode:** extract live monthly/annual tiers from a scraped `/pricing` page with
     `python3 buy_smart.py saas-parse -i /tmp/bs_saas.json`.
   - **MCP parity:** every `treg call <id>` maps 1:1 to MCP `call(endpoint_id=..., ...)`; check the
     catalog row's current price and parameters first — the catalog row wins over any example here.

## The audit script

Standard library only (Python 3.9+, zero pip dependencies). Save as `buy_smart.py`;
`python3 buy_smart.py --selftest` checks every detector.

```python
import argparse, datetime as dt, html, json, re, statistics, sys, urllib.parse, urllib.request

REGIONS = {
    "amazon.com": ("US", "us", "USD", "camelcamelcamel.com"),
    "amazon.co.uk": ("UK", "uk", "GBP", "uk.camelcamelcamel.com"),
    "amazon.de": ("DE", "de", "EUR", "de.camelcamelcamel.com"),
    "amazon.ca": ("CA", "ca", "CAD", "ca.camelcamelcamel.com"),
    "amazon.com.au": ("AU", "au", "AUD", "au.camelcamelcamel.com"),
    "amazon.fr": ("FR", "fr", "EUR", "fr.camelcamelcamel.com"),
    "amazon.es": ("ES", "es", "EUR", "es.camelcamelcamel.com"),
    "amazon.it": ("IT", "it", "EUR", "it.camelcamelcamel.com"),
    "amazon.co.jp": ("JP", "jp", "JPY", "jp.camelcamelcamel.com"),
}
DERIV_RE = re.compile(r"\b(?:WH-?1000XM5SA|B[0-9]E|DU6900|CU7000|UN\d+DU69\d*)\b", re.I)
JUNK_RE = re.compile(r"\b(used|refurb(?:ished)?|renewed|open[- ]box|pre[- ]owned|parts only|for parts|case only|ear\s*pads?|replacement|gasket|charger only|cable only|2[- ]?pack|twin[- ]?pack|bundle of \d)\b", re.I)
BAD_STORES = ("ebay", "mercari", "poshmark", "woot", "back market", "backmarket", "swappa", "offerup", "dhgate", "aliexpress", "temu")
DEFECT_RE = re.compile(r"\b(broken hinge|snapped|hinge broke|hinge flaw|defect|recall|died after|stopped working|warranty denied|brick(?:ed)?|overheat(?:ing)?|battery drain)\b", re.I)
NEG_RE = re.compile(r"\b(zero|no|never|without|none|fixed|no longer)\s+(?:\w+\s+){0,3}(hinge|issue|issues|problem|problems|defect|broke|broken|regret)\b", re.I)
PRICE_RE = re.compile(r"[\$\£\€]\s*([0-9]{1,4}(?:,[0-9]{3})*(?:\.[0-9]{2})?)")


def parse_price(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v) if v > 0 else None
    m = PRICE_RE.search(str(v or ""))
    if not m:
        return None
    val = float(m.group(1).replace(",", ""))
    return val if val > 0 else None


def load_json(path):
    if not path:
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def unwrap_shortlink(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    if not any(h in host for h in ("a.co", "amzn.to", "amzn.eu")):
        return url
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "buy-smart/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            return resp.geturl() or url
    except Exception:
        return url


def resolve_input(raw):
    raw = raw.strip()
    m_url = re.search(r"https?://\S+", raw)
    if not m_url:
        q = re.sub(r"\s+", " ", raw)
        return {"mode": "product_name", "query": q, "asin": None, "country": "US", "gl": "us",
                "currency": "USD", "canonical_url": None, "camel_url": None,
                "asin_search_query": f"{q} site:amazon.com/dp"}
    url = unwrap_shortlink(m_url.group(0).rstrip(".,);"))
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    for dom, (country, gl, cur, camel_host) in REGIONS.items():
        if host == dom or host.endswith("." + dom):
            m_asin = re.search(r"/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})(?:[/?]|$)", parsed.path, re.I)
            asin = m_asin.group(1).upper() if m_asin else None
            canon = f"https://www.{dom}/dp/{asin}" if asin else url
            return {"mode": "url_amazon", "query": raw, "asin": asin, "country": country, "gl": gl,
                    "currency": cur, "canonical_url": canon,
                    "camel_url": f"https://{camel_host}/product/{asin}" if asin else None}
    return {"mode": "url_store", "query": raw, "asin": None, "country": "US", "gl": "us",
            "currency": "USD", "canonical_url": url, "camel_url": None,
            "asin_search_query": f"{parsed.path.rsplit('/', 1)[-1].replace('-', ' ')} site:amazon.com/dp"}


def fetch_wayback(url, days=365, samples=6):
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y%m%d")
    cdx = ("https://web.archive.org/cdx/search/cdx?"
           + urllib.parse.urlencode({"url": url, "from": since, "output": "json", "fl": "timestamp,original",
                                     "filter": "statuscode:200", "collapse": "timestamp:6"}))
    try:
        with urllib.request.urlopen(urllib.request.Request(cdx, headers={"User-Agent": "buy-smart/1.0"}), timeout=10) as r:
            rows = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as exc:
        return {"snapshots": [], "warning": f"wayback_unavailable: {exc}"}
    snaps = rows[1:][:samples] if isinstance(rows, list) and len(rows) > 1 else []
    out = []
    for ts, orig in snaps:
        snap_url = f"https://web.archive.org/web/{ts}id_/{orig}"
        try:
            with urllib.request.urlopen(urllib.request.Request(snap_url, headers={"User-Agent": "buy-smart/1.0"}), timeout=10) as r:
                body = r.read(300000).decode("utf-8", "replace")
            prices = [p for p in (parse_price(m.group(0)) for m in PRICE_RE.finditer(body)) if p and 5 <= p <= 10000]
            if prices:
                out.append({"date": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}", "price": round(statistics.median(prices[:8]), 2),
                            "url": f"https://web.archive.org/web/{ts}/{orig}"})
        except Exception:
            continue
    return {"snapshots": out}


def parse_camel(doc):
    text = json.dumps(doc) if isinstance(doc, (dict, list)) else str(doc or "")
    out = {}
    for key, label in (("1p", r"Amazon"), ("3p_new", r"3rd Party New"), ("3p_used", r"3rd Party Used")):
        m = re.search(label + r".{0,420}", text, re.I | re.S)
        if not m:
            continue
        seg = m.group(0)
        for field in ("Current", "Highest", "Lowest", "Average"):
            fm = re.search(field + r"[^$\£\€]{0,40}([\$\£\€]\s*[0-9,]+(?:\.[0-9]{2})?)", seg, re.I)
            if fm:
                out[f"{key}_{field.lower()}"] = parse_price(fm.group(1))
        if re.search(r"Current[^A-Za-z0-9]{0,20}(?:Out of Stock|Not in Stock)", seg, re.I):
            out[f"{key}_oos"] = True
    return out


def filter_shopping(doc, query, ref_price=None):
    rows = []
    if isinstance(doc, dict):
        rows = doc.get("shopping") or doc.get("results") or (doc.get("data") or {}).get("shopping") or []
    elif isinstance(doc, list):
        rows = doc
    kept, stripped, deriv = [], [], []
    q_tokens = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) >= 3][:4]
    for r in rows:
        if not isinstance(r, dict):
            continue
        title = str(r.get("title") or "")
        store = str(r.get("source") or r.get("merchant") or r.get("store") or "")
        price = parse_price(r.get("price") or r.get("extracted_price"))
        if not price:
            continue
        if DERIV_RE.search(title):
            deriv.append({"title": title, "store": store, "price": price})
            stripped.append(f"{store} (${price:.2f} derivative SKU)")
            continue
        if JUNK_RE.search(title) or any(b in store.lower() for b in BAD_STORES):
            stripped.append(f"{store} (${price:.2f})")
            continue
        if q_tokens and sum(t in title.lower() for t in q_tokens) < max(1, len(q_tokens) // 2):
            stripped.append(f"{store} (${price:.2f} wrong model)")
            continue
        if ref_price and (price < ref_price * 0.45 or price > ref_price * 2.5):
            stripped.append(f"{store} (${price:.2f} outlier)")
            continue
        kept.append({"store": store, "title": title, "price": round(price, 2), "link": r.get("link") or ""})
    kept.sort(key=lambda x: x["price"])
    return {"kept": kept, "stripped": stripped[:8], "derivative_skus": deriv}


def scan_reddit(doc):
    posts = []
    if isinstance(doc, dict):
        posts = doc.get("posts") or doc.get("data") or []
    elif isinstance(doc, list):
        posts = doc
    defects, owners = [], []
    for p in posts:
        if not isinstance(p, dict):
            continue
        title = str(p.get("title") or "")
        body = str(p.get("selftext") or p.get("body") or "")
        blob = f"{title} {body}"
        ups = int(p.get("ups") or p.get("score") or 0)
        rec = {"title": title[:140], "ups": ups, "subreddit": str(p.get("subreddit") or ""),
               "url": str(p.get("url") or p.get("permalink") or "")}
        if DEFECT_RE.search(blob) and not NEG_RE.search(blob):
            defects.append(rec)
        else:
            owners.append(rec)
    defects.sort(key=lambda x: -x["ups"])
    total_ups = sum(d["ups"] for d in defects)
    return {"posts_scanned": len(posts), "defect_post_count": len(defects), "defect_total_upvotes": total_ups,
            "chronic_defect_signal": len(defects) >= 2 and total_ups >= 50,
            "top_defect_posts": defects[:3], "top_owner_posts": sorted(owners, key=lambda x: -x["ups"])[:3]}


def run_pipeline(args):
    amz = load_json(args.amazon) or {}
    camel = parse_camel(load_json(args.camel))
    wb = load_json(args.wayback) or {}
    sale = args.sale_price or parse_price(amz.get("price") or (amz.get("data") or {}).get("price")) or camel.get("1p_current") or camel.get("3p_new_current")
    msrp = args.claimed_msrp or parse_price(amz.get("list_price") or (amz.get("data") or {}).get("list_price"))
    if sale and args.coupon:
        sale = max(0.01, round(sale - args.coupon, 2))
    shop = filter_shopping(load_json(args.shopping), args.query, ref_price=sale)
    red = scan_reddit(load_json(args.reddit))
    wb_prices = [s["price"] for s in (wb.get("snapshots") or []) if isinstance(s, dict) and s.get("price")]
    baseline = camel.get("1p_average") or camel.get("3p_new_average") or (round(statistics.median(wb_prices), 2) if wb_prices else None)

    flags, bs = [], 0
    if not sale:
        return {"product": args.query, "verdict": "INCOMPLETE_DATA - MISSING LIVE PRICE", "manipulation_bs_score": None,
                "flags": ["MISSING_LIVE_PRICE"], "cheapest_verified_store": shop["kept"][0] if shop["kept"] else None}
    if camel.get("3p_used_current") and abs(sale - camel["3p_used_current"]) <= 2.0 and camel.get("1p_oos"):
        flags.append("USED_BUYBOX_HIJACK_DETECTED"); bs += 50
    if camel.get("1p_oos") and (not camel.get("1p_current")) and camel.get("3p_new_current") and abs(sale - camel["3p_new_current"]) <= 2.0:
        flags.append("AMAZON_1P_OOS_3P_SCALPER"); bs += 35
    if msrp and sale > msrp * 1.01:
        flags.append("ABOVE_MSRP_SCALPER"); bs += 35
    elif msrp and baseline and msrp > baseline * 1.25 and ((msrp - sale) / msrp) - ((baseline - sale) / baseline) > 0.15:
        flags.append("EXAGGERATED_STRIKETHROUGH"); bs += 25
    if baseline and sale > baseline * 1.02:
        flags.append("ABOVE_HISTORICAL_AVERAGE"); bs += 20
    if baseline is None:
        flags.append("UNVERIFIED_PRICE_HISTORY")
    if shop["kept"] and shop["kept"][0]["price"] < sale * 0.94 and (sale - shop["kept"][0]["price"]) >= 5.0:
        flags.append(f"CHEAPER_AT_{re.sub(r'[^A-Z0-9]+', '_', shop['kept'][0]['store'].upper()).strip('_')}"); bs += 20
    if red["chronic_defect_signal"]:
        flags.append("OWNER_DEFECT_CLUSTER"); bs += 30
    bs = min(100, bs)

    true_disc = round(((baseline - sale) / baseline) * 100, 1) if baseline else None
    if "USED_BUYBOX_HIJACK_DETECTED" in flags:
        verdict = "WARNING - USED BUYBOX HIJACK (NOT NEW)"
    elif bs >= 70 or "ABOVE_MSRP_SCALPER" in flags:
        verdict = "SKIP"
    elif bs >= 30:
        verdict = "FAIR - CHECK ALTERNATIVE"
    elif true_disc is not None and true_disc >= 15:
        verdict = "REAL DEAL"
    elif baseline is None and shop["kept"] and sale <= shop["kept"][0]["price"] * 1.02:
        verdict = "VERIFIED BELOW LIVE STOCKISTS"
    else:
        verdict = "NEUTRAL - NORMAL PRICE"

    safe_evidence = "\n".join(f"<thread ups=\"{d['ups']}\">{html.escape(d['title'])}</thread>" for d in red["top_defect_posts"])
    jev_prompt = (f"<product>{html.escape(args.query)}</product><sale>{sale:.2f}</sale>"
                  f"<baseline>{baseline or 'none'}</baseline><bs_score>{bs}</bs_score>"
                  f"<flags>{','.join(flags)}</flags><reddit>{safe_evidence}</reddit>")
    return {
        "product": args.query, "verdict": verdict, "manipulation_bs_score": bs,
        "sale_price": round(sale, 2), "baseline_price": baseline, "true_discount_pct": true_disc,
        "flags": flags, "cheapest_verified_store": shop["kept"][0] if shop["kept"] else None,
        "stripped_offers": shop["stripped"], "reddit": red,
        "jev_request": {"model": "typesafe/jev-1.13", "prompt": jev_prompt[:3800],
                        "choices": ["real_deal", "fair_wait", "skip_trap", "skip_hardware_flaw"]},
    }


def analyze_cart(items):
    direct_swap, bad_blocked, buys, swaps, skips = 0.0, 0.0, 0, 0, 0
    for it in items:
        sale = float(it.get("sale_price") or 0)
        v = str(it.get("verdict") or "")
        cheap = (it.get("cheapest_verified_store") or {}).get("price")
        if "SKIP" in v:
            skips += 1; bad_blocked += sale
        elif ("USED BUYBOX" in v or "FAIR" in v) and cheap and cheap < sale:
            swaps += 1; direct_swap += (sale - float(cheap))
        else:
            buys += 1
    return {"items": len(items), "buys": buys, "swaps": swaps, "skips": skips,
            "direct_swap_savings_usd": round(direct_swap, 2), "bad_spend_blocked_usd": round(bad_blocked, 2)}


def parse_saas_tiers(doc):
    text = json.dumps(doc) if isinstance(doc, (dict, list)) else str(doc or "")
    prices = sorted({round(float(m.group(1).replace(",", "")), 2) for m in re.finditer(r"\$\s*([0-9]{2,4}(?:\.[0-9]{2})?)\s*/\s*mo", text, re.I)})
    return {"monthly_prices_found": prices, "annual_totals_usd": [round(p * 12, 2) for p in prices]}


def selftest():
    r = resolve_input("https://www.amazon.co.uk/dp/B09XS7JWHH?th=1")
    assert r["mode"] == "url_amazon" and r["asin"] == "B09XS7JWHH" and r["currency"] == "GBP"
    assert "uk.camelcamelcamel.com/product/B09XS7JWHH" in r["camel_url"]
    c = parse_camel("Amazon Current Out of Stock Average $676.70 3rd Party Used Current $440.07")
    assert c["1p_oos"] and c["1p_average"] == 676.70 and c["3p_used_current"] == 440.07
    sh = filter_shopping([
        {"title": "Dyson V15 Detect", "source": "Target", "price": "$407.97"},
        {"title": "Dyson V15 Refurbished", "source": "Walmart", "price": "$289.98"},
        {"title": "Sony WH-1000XM5SA Soft Case", "source": "Best Buy", "price": "$249.99"},
    ], "Dyson V15 Detect", ref_price=440.07)
    assert len(sh["kept"]) == 1 and sh["kept"][0]["store"] == "Target" and len(sh["derivative_skus"]) == 1
    rd = scan_reddit([
        {"title": "2 years with XM4: zero hinge issues and never broke", "ups": 240},
        {"title": "XM5 broken hinge after 6 months", "ups": 247},
        {"title": "XM5 hinge broke again, warranty denied", "ups": 116},
    ])
    assert rd["defect_post_count"] == 2 and rd["chronic_defect_signal"] is True
    cart = analyze_cart([
        {"sale_price": 298.00, "verdict": "SKIP"},
        {"sale_price": 440.07, "verdict": "WARNING - USED BUYBOX HIJACK (NOT NEW)", "cheapest_verified_store": {"price": 407.97}},
        {"sale_price": 494.95, "verdict": "REAL DEAL"},
    ])
    assert cart["direct_swap_savings_usd"] == 32.10 and cart["bad_spend_blocked_usd"] == 298.00
    saas = parse_saas_tiers("Starter $117.33/mo SEO+AI $165.17/mo Multi $248.17/mo")
    assert saas["annual_totals_usd"] == [1407.96, 1982.04, 2978.04]
    print("ok")


def main():
    if "--selftest" in sys.argv:
        selftest(); return
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_res = sub.add_parser("resolve"); p_res.add_argument("input")
    p_wb = sub.add_parser("wayback"); p_wb.add_argument("url"); p_wb.add_argument("--days", type=int, default=365); p_wb.add_argument("--samples", type=int, default=6)
    p_pl = sub.add_parser("pipeline")
    for f in ("--query", "--amazon", "--camel", "--wayback", "--shopping", "--reddit"):
        p_pl.add_argument(f, required=(f == "--query"))
    for f in ("--sale-price", "--claimed-msrp", "--coupon"):
        p_pl.add_argument(f, type=float)
    p_ct = sub.add_parser("cart"); p_ct.add_argument("-i", "--input", required=True)
    p_ss = sub.add_parser("saas-parse"); p_ss.add_argument("-i", "--input", required=True)
    a = ap.parse_args()
    if a.cmd == "resolve": out = resolve_input(a.input)
    elif a.cmd == "wayback": out = fetch_wayback(a.url, a.days, a.samples)
    elif a.cmd == "pipeline": out = run_pipeline(a)
    elif a.cmd == "cart": out = analyze_cart(load_json(a.input))
    elif a.cmd == "saas-parse": out = parse_saas_tiers(load_json(a.input))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
```
