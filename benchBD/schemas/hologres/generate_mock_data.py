#!/usr/bin/env python3
"""
生成模拟测试数据并以 CSV 存储到 data 目录下。

用法示例:
python3 generate_mock_data.py --accounts 200 --orgs 80 --transactions 5000 --internal 400 --channels 20 --performances 2000 --outdir ../data
"""
from __future__ import annotations
import argparse
import csv
import os
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

# 默认数量
DEFAULTS = {
    "accounts": 100,
    "orgs": 50,
    "transactions": 1000,
    "internal": 200,
    "channels": 10,
    "performances": 500,
}

TX_TYPES = ["expense", "income", "adjustment", "transfer"]
PRODUCT_TYPES = ["product_a", "product_b", "service_x", "service_y"]
CHANNEL_TYPES = ["online", "offline", "partner"]
CURRENCIES = ["CNY", "USD", "EUR"]

def fmt_decimal(v: float) -> str:
    d = Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(d, "f")

def random_date(days_back=365):
    d = datetime.utcnow().date() - timedelta(days=random.randint(0, days_back))
    return d.isoformat()

def ensure_outdir(path):
    os.makedirs(path, exist_ok=True)

def write_csv(path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

def gen_accounts(n):
    # 生成分级科目，level 1..4
    levels = min(4, max(1, int(n**0.5)))  # 简单决定层级数
    # 先创建 root 节点若干，再为每级分配子节点
    accounts = []
    by_level = {i: [] for i in range(1, levels+1)}
    # 先分配每级的数量（越底层越多）
    remaining = n
    for lvl in range(1, levels+1):
        if lvl == levels:
            cnt = remaining
        else:
            # 先给每层分配一个基础值
            cnt = max(1, remaining // 2)
        remaining -= cnt
        for i in range(cnt):
            aid = str(uuid.uuid4())
            code = f"{lvl:01d}{random.randint(1000,9999)}"
            name = f"Account_{lvl}_{len(by_level[lvl]) + 1}"
            parent = None
            if lvl > 1:
                parent = random.choice(by_level[lvl-1])
            is_leaf = (lvl == levels) or (random.random() > 0.7)
            create_time = datetime.utcnow().isoformat(sep=" ")
            update_time = create_time
            acct = {
                "account_id": aid,
                "account_code": code,
                "account_name": name,
                "account_level": lvl,
                "parent_account_id": parent,
                "account_type": "general",
                "is_leaf": str(is_leaf),
                "create_time": create_time,
                "update_time": update_time,
            }
            by_level[lvl].append(aid)
            accounts.append(acct)
    return accounts

def gen_organizations(n):
    levels = min(4, max(1, int(n**0.5)))
    orgs = []
    by_level = {i: [] for i in range(1, levels+1)}
    remaining = n
    for lvl in range(1, levels+1):
        if lvl == levels:
            cnt = remaining
        else:
            cnt = max(1, remaining // 2)
        remaining -= cnt
        for i in range(cnt):
            oid = str(uuid.uuid4())
            code = f"ORG{random.randint(1000,9999)}"
            name = f"Org_{lvl}_{len(by_level[lvl]) + 1}"
            parent = None
            if lvl > 1:
                parent = random.choice(by_level[lvl-1])
            create_time = datetime.utcnow().isoformat(sep=" ")
            org = {
                "org_id": oid,
                "org_code": code,
                "org_name": name,
                "org_level": lvl,
                "parent_org_id": parent,
                "org_type": "unit",
                "region": random.choice(["North", "South", "East", "West", None]),
                "create_time": create_time,
            }
            by_level[lvl].append(oid)
            orgs.append(org)
    return orgs

def gen_distribution_channels(n):
    channels = []
    for i in range(n):
        cid = str(uuid.uuid4())
        code = f"CH{random.randint(100,999)}"
        name = f"Channel_{i+1}"
        ctype = random.choice(CHANNEL_TYPES)
        create_time = datetime.utcnow().isoformat(sep=" ")
        channels.append({
            "channel_id": cid,
            "channel_code": code,
            "channel_name": name,
            "channel_type": ctype,
            "region": random.choice(["North", "South", "East", "West", None]),
            "create_time": create_time,
        })
    return channels

def gen_finance_transactions(n, org_ids, account_ids):
    rows = []
    for _ in range(n):
        tid = str(uuid.uuid4())
        org = random.choice(org_ids)
        acct = random.choice(account_ids)
        tdate = random_date(365)
        amt = fmt_decimal(random.uniform(1.0, 100000.0))
        currency = random.choice(CURRENCIES)
        ttype = random.choice(TX_TYPES)
        desc = f"Auto generated {ttype}"
        create_time = datetime.utcnow().isoformat(sep=" ")
        rows.append({
            "transaction_id": tid,
            "org_id": org,
            "account_id": acct,
            "transaction_date": tdate,
            "transaction_amount": amt,
            "currency": currency,
            "transaction_type": ttype,
            "description": desc,
            "create_time": create_time,
        })
    return rows

def gen_internal_transactions(n, org_ids):
    rows = []
    for _ in range(n):
        iid = str(uuid.uuid4())
        seller = random.choice(org_ids)
        buyer = random.choice(org_ids)
        # 保证买卖方不同
        if seller == buyer and len(org_ids) > 1:
            buyer = random.choice([o for o in org_ids if o != seller])
        tdate = random_date(365)
        amt = fmt_decimal(random.uniform(1.0, 200000.0))
        product = random.choice(PRODUCT_TYPES)
        create_time = datetime.utcnow().isoformat(sep=" ")
        rows.append({
            "internal_id": iid,
            "seller_org_id": seller,
            "buyer_org_id": buyer,
            "transaction_date": tdate,
            "transaction_amount": amt,
            "product_type": product,
            "create_time": create_time,
        })
    return rows

def gen_distribution_performance(n, channels, org_ids):
    rows = []
    for _ in range(n):
        pid = str(uuid.uuid4())
        ch = random.choice(channels)
        org = random.choice(org_ids)
        pdate = random_date(365)
        sales = float(random.uniform(0, 500000))
        target = sales + random.uniform(0, 50000)
        create_time = datetime.utcnow().isoformat(sep=" ")
        rows.append({
            "performance_id": pid,
            "channel_id": ch,
            "org_id": org,
            "performance_date": pdate,
            "sales_amount": fmt_decimal(sales),
            "target_amount": fmt_decimal(target),
            "create_time": create_time,
        })
    return rows

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--accounts", type=int, default=DEFAULTS["accounts"])
    p.add_argument("--orgs", type=int, default=DEFAULTS["orgs"])
    p.add_argument("--transactions", type=int, default=DEFAULTS["transactions"])
    p.add_argument("--internal", type=int, default=DEFAULTS["internal"])
    p.add_argument("--channels", type=int, default=DEFAULTS["channels"])
    p.add_argument("--performances", type=int, default=DEFAULTS["performances"])
    p.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    p.add_argument("--seed", type=int, default=None, help="随机种子（可选）")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    outdir = os.path.abspath(args.outdir)
    ensure_outdir(outdir)

    # 生成基础表
    accounts = gen_accounts(args.accounts)
    orgs = gen_organizations(args.orgs)
    channels = gen_distribution_channels(args.channels)

    # 写 finance_accounts.csv
    acct_headers = ["account_id","account_code","account_name","account_level","parent_account_id","account_type","is_leaf","create_time","update_time"]
    acct_rows = [[a[h] if a[h] is not None else "" for h in acct_headers] for a in accounts]
    write_csv(os.path.join(outdir, "finance_accounts.csv"), acct_headers, acct_rows)

    # 写 organizations.csv
    org_headers = ["org_id","org_code","org_name","org_level","parent_org_id","org_type","region","create_time"]
    org_rows = [[o[h] if o[h] is not None else "" for h in org_headers] for o in orgs]
    write_csv(os.path.join(outdir, "organizations.csv"), org_headers, org_rows)

    # 写 distribution_channels.csv
    ch_headers = ["channel_id","channel_code","channel_name","channel_type","region","create_time"]
    ch_rows = [[c[h] if c[h] is not None else "" for h in ch_headers] for c in channels]
    write_csv(os.path.join(outdir, "distribution_channels.csv"), ch_headers, ch_rows)

    # 交易类
    org_ids = [o["org_id"] for o in orgs]
    account_ids = [a["account_id"] for a in accounts]
    channel_ids = [c["channel_id"] for c in channels]

    txs = gen_finance_transactions(args.transactions, org_ids, account_ids)
    tx_headers = ["transaction_id","org_id","account_id","transaction_date","transaction_amount","currency","transaction_type","description","create_time"]
    tx_rows = [[t[h] if t[h] is not None else "" for h in tx_headers] for t in txs]
    write_csv(os.path.join(outdir, "finance_transactions.csv"), tx_headers, tx_rows)

    internals = gen_internal_transactions(args.internal, org_ids)
    int_headers = ["internal_id","seller_org_id","buyer_org_id","transaction_date","transaction_amount","product_type","create_time"]
    int_rows = [[it[h] if it[h] is not None else "" for h in int_headers] for it in internals]
    write_csv(os.path.join(outdir, "internal_transactions.csv"), int_headers, int_rows)

    performances = gen_distribution_performance(args.performances, channel_ids, org_ids)
    perf_headers = ["performance_id","channel_id","org_id","performance_date","sales_amount","target_amount","create_time"]
    perf_rows = [[p[h] if p[h] is not None else "" for h in perf_headers] for p in performances]
    write_csv(os.path.join(outdir, "distribution_performance.csv"), perf_headers, perf_rows)

    print(f"生成完成，CSV 文件写入: {outdir}")

if __name__ == "__main__":
    main()