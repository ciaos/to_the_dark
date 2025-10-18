#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务管报压测执行脚本
支持Hologres和DWS数据库性能对比测试
"""

import time
import psycopg2
import pandas as pd
import json
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class DatabaseBenchmark:
    def __init__(self, config_file):
        """初始化压测配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.results = []
        self.lock = threading.Lock()
        
    def connect_database(self, db_config):
        """连接数据库"""
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            return conn
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return None
    
    def execute_sql(self, conn, sql, description):
        """执行SQL并记录性能指标"""
        start_time = time.time()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # 获取结果（如果是查询）
            if sql.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                row_count = len(results)
            else:
                row_count = cursor.rowcount
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            cursor.close()
            
            return {
                'description': description,
                'execution_time': execution_time,
                'row_count': row_count,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            return {
                'description': description,
                'execution_time': execution_time,
                'row_count': 0,
                'status': 'error',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_single_test(self, db_name, db_config, sql_file):
        """运行单个数据库的压测"""
        print(f"开始测试 {db_name}...")
        
        conn = self.connect_database(db_config)
        if not conn:
            return
        
        # 读取SQL文件
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        db_results = []
        
        for i, sql in enumerate(sql_statements):
            if not sql or sql.startswith('--'):
                continue
                
            description = f"场景{i+1}: {self.get_scenario_description(sql)}"
            print(f"  执行 {description}...")
            
            result = self.execute_sql(conn, sql, description)
            result['database'] = db_name
            result['sql_statement'] = sql[:100] + '...' if len(sql) > 100 else sql
            
            db_results.append(result)
            
            # 记录结果
            with self.lock:
                self.results.append(result)
        
        conn.close()
        print(f"{db_name} 测试完成")
        return db_results
    
    def get_scenario_description(self, sql):
        """根据SQL内容获取场景描述"""
        sql_upper = sql.upper()
        if 'RECURSIVE' in sql_upper:
            return "科目上卷查询"
        elif 'INTERNAL_TRANSACTIONS' in sql_upper:
            return "抵销处理"
        elif 'DISTRIBUTION_PERFORMANCE' in sql_upper:
            return "分销业绩统计"
        elif 'YTD' in sql_upper or 'OVER' in sql_upper:
            return "YTD计算"
        elif 'LAG' in sql_upper:
            return "同期数计算"
        elif 'CASE WHEN' in sql_upper:
            return "行转列"
        elif 'JOIN' in sql_upper and sql_upper.count('JOIN') > 2:
            return "维度拼接"
        else:
            return "通用查询"
    
    def run_concurrent_test(self, db_name, db_config, sql_file, concurrent_users=5):
        """运行并发压测"""
        print(f"开始并发测试 {db_name} (并发用户数: {concurrent_users})...")
        
        def worker():
            return self.run_single_test(db_name, db_config, sql_file)
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(worker) for _ in range(concurrent_users)]
            
            concurrent_results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    concurrent_results.append(result)
                except Exception as e:
                    print(f"并发测试出错: {e}")
        
        return concurrent_results
    
    def generate_report(self):
        """生成压测报告"""
        if not self.results:
            print("没有测试结果")
            return
        
        # 转换为DataFrame进行分析
        df = pd.DataFrame(self.results)
        
        # 按数据库分组统计
        summary = df.groupby('database').agg({
            'execution_time': ['mean', 'min', 'max', 'std'],
            'row_count': ['mean', 'sum'],
            'status': lambda x: (x == 'success').sum()
        }).round(4)
        
        print("\n=== 压测结果汇总 ===")
        print(summary)
        
        # 详细结果
        print("\n=== 详细测试结果 ===")
        for _, row in df.iterrows():
            status_icon = "✓" if row['status'] == 'success' else "✗"
            print(f"{status_icon} {row['database']} - {row['description']}")
            print(f"    执行时间: {row['execution_time']:.4f}s")
            print(f"    返回行数: {row['row_count']}")
            if row['status'] == 'error':
                print(f"    错误信息: {row['error_message']}")
            print()
        
        # 性能对比
        print("\n=== 性能对比分析 ===")
        db_performance = df.groupby('database')['execution_time'].agg(['mean', 'median', 'std']).round(4)
        print(db_performance)
        
        # 保存结果到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"/home/chaos/benchBD/results/benchmark_results_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细结果已保存到: {result_file}")
        
        return summary

def create_sample_config():
    """创建示例配置文件"""
    config = {
        "databases": {
            "hologres": {
                "host": "your-hologres-host",
                "port": 80,
                "database": "your_database",
                "user": "your_username",
                "password": "your_password"
            },
            "dws": {
                "host": "your-dws-host",
                "port": 8000,
                "database": "your_database",
                "user": "your_username",
                "password": "your_password"
            }
        },
        "test_settings": {
            "concurrent_users": 5,
            "test_iterations": 3
        }
    }
    
    config_file = "/home/chaos/benchBD/config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"示例配置文件已创建: {config_file}")
    print("请修改配置文件中的数据库连接信息")

def main():
    if len(sys.argv) < 2:
        print("使用方法: python benchmark.py <config_file>")
        print("示例: python benchmark.py config.json")
        print("\n首次使用请运行: python benchmark.py --create-config")
        return
    
    if sys.argv[1] == "--create-config":
        create_sample_config()
        return
    
    config_file = sys.argv[1]
    
    if not os.path.exists(config_file):
        print(f"配置文件不存在: {config_file}")
        return
    
    # 创建压测实例
    benchmark = DatabaseBenchmark(config_file)
    
    # 运行压测
    print("开始财务管报压测...")
    
    for db_name, db_config in benchmark.config['databases'].items():
        sql_file = f"/home/chaos/benchBD/sql/{db_name}_performance_tests.sql"
        
        if not os.path.exists(sql_file):
            print(f"SQL文件不存在: {sql_file}")
            continue
        
        # 运行单用户测试
        benchmark.run_single_test(db_name, db_config, sql_file)
        
        # 运行并发测试
        concurrent_users = benchmark.config['test_settings'].get('concurrent_users', 5)
        benchmark.run_concurrent_test(db_name, db_config, sql_file, concurrent_users)
    
    # 生成报告
    benchmark.generate_report()

if __name__ == "__main__":
    main()
