-- 财务管报压测SQL脚本 - DWS版本
-- 场景1: 科目上卷查询 - 递归查询科目层级汇总

-- DWS版本（使用WITH RECURSIVE）
WITH RECURSIVE account_hierarchy AS (
    -- 基础查询：叶子节点
    SELECT 
        account_id,
        account_code,
        account_name,
        account_level,
        parent_account_id,
        account_type,
        1 as level_depth
    FROM finance_accounts 
    WHERE is_leaf = TRUE
    
    UNION ALL
    
    -- 递归查询：父级节点
    SELECT 
        fa.account_id,
        fa.account_code,
        fa.account_name,
        fa.account_level,
        fa.parent_account_id,
        fa.account_type,
        ah.level_depth + 1
    FROM finance_accounts fa
    INNER JOIN account_hierarchy ah ON fa.account_id = ah.parent_account_id
    WHERE ah.level_depth < 10  -- 防止无限递归
)
SELECT 
    ah.account_id,
    ah.account_code,
    ah.account_name,
    ah.account_type,
    SUM(ft.transaction_amount) as total_amount,
    COUNT(ft.transaction_id) as transaction_count
FROM account_hierarchy ah
LEFT JOIN finance_transactions ft ON ah.account_id = ft.account_id
WHERE ft.transaction_date >= '2024-01-01'
GROUP BY ah.account_id, ah.account_code, ah.account_name, ah.account_type
ORDER BY total_amount DESC;

-- 场景2: 抵销处理 - 内部交易抵销计算
SELECT 
    seller_org_id,
    buyer_org_id,
    SUM(transaction_amount) as internal_amount,
    COUNT(*) as transaction_count,
    -- 计算抵销后净额
    CASE 
        WHEN SUM(transaction_amount) > 0 THEN SUM(transaction_amount)
        ELSE 0 
    END as net_amount
FROM internal_transactions
WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY seller_org_id, buyer_org_id
HAVING SUM(transaction_amount) != 0
ORDER BY internal_amount DESC;

-- 场景3: 分销业绩统计 - 多维度聚合
SELECT 
    dc.channel_type,
    o.region,
    o.org_type,
    DATE_TRUNC('month', dp.performance_date) as month_period,
    SUM(dp.sales_amount) as total_sales,
    SUM(dp.target_amount) as total_target,
    ROUND(SUM(dp.sales_amount) / SUM(dp.target_amount) * 100, 2) as achievement_rate,
    COUNT(DISTINCT dp.org_id) as org_count,
    COUNT(DISTINCT dp.channel_id) as channel_count
FROM distribution_performance dp
INNER JOIN distribution_channels dc ON dp.channel_id = dc.channel_id
INNER JOIN organizations o ON dp.org_id = o.org_id
WHERE dp.performance_date >= '2024-01-01'
GROUP BY dc.channel_type, o.region, o.org_type, DATE_TRUNC('month', dp.performance_date)
ORDER BY total_sales DESC;

-- 场景4: YTD计算 - 年初至今累计
SELECT 
    org_id,
    account_id,
    transaction_date,
    transaction_amount,
    -- 计算YTD累计
    SUM(transaction_amount) OVER (
        PARTITION BY org_id, account_id 
        ORDER BY transaction_date 
        ROWS UNBOUNDED PRECEDING
    ) as ytd_amount,
    -- 计算月度累计
    SUM(transaction_amount) OVER (
        PARTITION BY org_id, account_id, DATE_TRUNC('month', transaction_date)
        ORDER BY transaction_date 
        ROWS UNBOUNDED PRECEDING
    ) as monthly_amount
FROM finance_transactions
WHERE transaction_date >= '2024-01-01'
ORDER BY org_id, account_id, transaction_date;

-- 场景5: 同期数计算 - 同比分析
WITH monthly_data AS (
    SELECT 
        org_id,
        account_id,
        DATE_TRUNC('month', transaction_date) as month_period,
        SUM(transaction_amount) as monthly_amount
    FROM finance_transactions
    WHERE transaction_date >= '2023-01-01'
    GROUP BY org_id, account_id, DATE_TRUNC('month', transaction_date)
),
year_over_year AS (
    SELECT 
        org_id,
        account_id,
        month_period,
        monthly_amount,
        LAG(monthly_amount, 12) OVER (
            PARTITION BY org_id, account_id 
            ORDER BY month_period
        ) as same_period_last_year,
        ROUND(
            (monthly_amount - LAG(monthly_amount, 12) OVER (
                PARTITION BY org_id, account_id 
                ORDER BY month_period
            )) / LAG(monthly_amount, 12) OVER (
                PARTITION BY org_id, account_id 
                ORDER BY month_period
            ) * 100, 2
        ) as yoy_growth_rate
    FROM monthly_data
)
SELECT 
    org_id,
    account_id,
    month_period,
    monthly_amount,
    same_period_last_year,
    yoy_growth_rate
FROM year_over_year
WHERE month_period >= '2024-01-01'
ORDER BY org_id, account_id, month_period;

-- 场景6: 行转列 - 数据透视
SELECT 
    org_id,
    SUM(CASE WHEN account_type = '收入' THEN transaction_amount ELSE 0 END) as income_amount,
    SUM(CASE WHEN account_type = '费用' THEN transaction_amount ELSE 0 END) as expense_amount,
    SUM(CASE WHEN account_type = '资产' THEN transaction_amount ELSE 0 END) as asset_amount,
    SUM(CASE WHEN account_type = '负债' THEN transaction_amount ELSE 0 END) as liability_amount,
    SUM(CASE WHEN account_type = '所有者权益' THEN transaction_amount ELSE 0 END) as equity_amount,
    COUNT(DISTINCT CASE WHEN account_type = '收入' THEN account_id END) as income_accounts,
    COUNT(DISTINCT CASE WHEN account_type = '费用' THEN account_id END) as expense_accounts
FROM finance_transactions ft
INNER JOIN finance_accounts fa ON ft.account_id = fa.account_id
WHERE ft.transaction_date >= '2024-01-01'
GROUP BY org_id
ORDER BY income_amount DESC;

-- 场景7: 维度拼接 - 多表关联复杂查询
SELECT 
    o.org_name,
    o.region,
    o.org_type,
    fa.account_name,
    fa.account_type,
    dc.channel_name,
    dc.channel_type,
    DATE_TRUNC('quarter', ft.transaction_date) as quarter_period,
    SUM(ft.transaction_amount) as total_amount,
    COUNT(ft.transaction_id) as transaction_count,
    AVG(ft.transaction_amount) as avg_amount,
    MAX(ft.transaction_amount) as max_amount,
    MIN(ft.transaction_amount) as min_amount
FROM finance_transactions ft
INNER JOIN organizations o ON ft.org_id = o.org_id
INNER JOIN finance_accounts fa ON ft.account_id = fa.account_id
LEFT JOIN distribution_performance dp ON ft.org_id = dp.org_id 
    AND DATE_TRUNC('month', ft.transaction_date) = DATE_TRUNC('month', dp.performance_date)
LEFT JOIN distribution_channels dc ON dp.channel_id = dc.channel_id
WHERE ft.transaction_date >= '2024-01-01'
GROUP BY 
    o.org_name, o.region, o.org_type,
    fa.account_name, fa.account_type,
    dc.channel_name, dc.channel_type,
    DATE_TRUNC('quarter', ft.transaction_date)
ORDER BY total_amount DESC;
