-- Hologres表结构定义
-- 财务科目表
CREATE TABLE IF NOT EXISTS finance_accounts (
    account_id VARCHAR(50) NOT NULL,
    account_code VARCHAR(20) NOT NULL,
    account_name VARCHAR(200) NOT NULL,
    account_level INTEGER NOT NULL,
    parent_account_id VARCHAR(50),
    account_type VARCHAR(20) NOT NULL,
    is_leaf BOOLEAN DEFAULT FALSE,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id)
);

-- 组织架构表
CREATE TABLE IF NOT EXISTS organizations (
    org_id VARCHAR(50) NOT NULL,
    org_code VARCHAR(20) NOT NULL,
    org_name VARCHAR(200) NOT NULL,
    org_level INTEGER NOT NULL,
    parent_org_id VARCHAR(50),
    org_type VARCHAR(20) NOT NULL,
    region VARCHAR(50),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (org_id)
);

-- 财务交易明细表
CREATE TABLE IF NOT EXISTS finance_transactions (
    transaction_id VARCHAR(50) NOT NULL,
    org_id VARCHAR(50) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_amount DECIMAL(18,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    transaction_type VARCHAR(20) NOT NULL,
    description TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (transaction_id)
);

-- 内部交易表（用于抵销）
CREATE TABLE IF NOT EXISTS internal_transactions (
    internal_id VARCHAR(50) NOT NULL,
    seller_org_id VARCHAR(50) NOT NULL,
    buyer_org_id VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_amount DECIMAL(18,2) NOT NULL,
    product_type VARCHAR(50),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (internal_id)
);

-- 分销渠道表
CREATE TABLE IF NOT EXISTS distribution_channels (
    channel_id VARCHAR(50) NOT NULL,
    channel_code VARCHAR(20) NOT NULL,
    channel_name VARCHAR(200) NOT NULL,
    channel_type VARCHAR(20) NOT NULL,
    region VARCHAR(50),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (channel_id)
);

-- 分销业绩表
CREATE TABLE IF NOT EXISTS distribution_performance (
    performance_id VARCHAR(50) NOT NULL,
    channel_id VARCHAR(50) NOT NULL,
    org_id VARCHAR(50) NOT NULL,
    performance_date DATE NOT NULL,
    sales_amount DECIMAL(18,2) NOT NULL,
    target_amount DECIMAL(18,2),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (performance_id)
);

-- 创建索引
CREATE INDEX idx_finance_transactions_org_date ON finance_transactions(org_id, transaction_date);
CREATE INDEX idx_finance_transactions_account_date ON finance_transactions(account_id, transaction_date);
CREATE INDEX idx_internal_transactions_date ON internal_transactions(transaction_date);
CREATE INDEX idx_distribution_performance_date ON distribution_performance(performance_date);
