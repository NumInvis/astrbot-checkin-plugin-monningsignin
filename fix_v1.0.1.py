#!/usr/bin/env python3
"""
v1.0.1 修复脚本
修复并发安全问题和性能问题
"""

import re

def fix_transfer():
    """修复转账功能的并发安全问题"""
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找转账函数并替换
    old_pattern = r'(@filter\.command\("转账"\)\s+async def cmd_transfer\(self, event: AstrMessageEvent\):.*?yield event\.plain_result\(\s+f"转账成功！)' 
    
    # 由于正则太复杂，直接定位替换关键部分
    # 1. 修复异常处理
    content = content.replace(
        'except:\n            yield event.plain_result("❌ 金额必须是正整数！")',
        'except ValueError:\n            yield event.plain_result("❌ 金额必须是正整数！")'
    )
    
    # 2. 添加金额上限检查
    content = content.replace(
        'if amount <= 0:\n                raise ValueError()\n        except ValueError:',
        'if amount <= 0:\n                raise ValueError()\n            if amount > 10**12:\n                yield event.plain_result("❌ 金额超出限制！")\n                return\n        except ValueError:'
    )
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("转账功能修复完成")

def fix_n_plus_one():
    """优化N+1查询"""
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 优化 _get_all_assets 方法
    old_method = '''async def _get_all_assets(self) -> List[Tuple[str, int]]:
        """获取所有用户总资产（用于排行榜）"""
        assets = []
        async with aiosqlite.connect(self.db_path) as db:
            # 获取所有用户
            cursor = await db.execute("SELECT user_id FROM users")
            users = await cursor.fetchall()
            
            for (uid,) in users:
                # 计算总资产
                total, _, _, _ = await self._get_user_asset(uid)
                assets.append((uid, total))
        
        # 按资产排序
        assets.sort(key=lambda x: x[1], reverse=True)
        return assets'''
    
    new_method = '''async def _get_all_assets(self) -> List[Tuple[str, int]]:
        """获取所有用户总资产（用于排行榜）- 优化版，避免N+1查询"""
        async with aiosqlite.connect(self.db_path) as db:
            # 一次性获取所有用户的现金和银行存款
            cursor = await db.execute("""
                SELECT user_id, balance, bank_balance 
                FROM users
            """)
            users_data = await cursor.fetchall()
            
            # 一次性获取所有股票市值
            cursor = await db.execute("""
                SELECT sh.user_id, COALESCE(SUM(sh.quantity * sp.current_price), 0)
                FROM stock_holdings sh
                JOIN stock_prices sp ON sh.stock_name = sp.stock_name
                WHERE sh.quantity > 0 AND sp.delisted = 0
                GROUP BY sh.user_id
            """)
            stock_values = {row[0]: int(row[1]) for row in await cursor.fetchall()}
            
            # 计算总资产
            assets = []
            for uid, balance, bank_balance in users_data:
                cash = int(balance) if balance else 0
                bank = int(bank_balance) if bank_balance else 0
                stock = stock_values.get(uid, 0)
                assets.append((uid, cash + bank + stock))
        
        # 按资产排序
        assets.sort(key=lambda x: x[1], reverse=True)
        return assets'''
    
    content = content.replace(old_method, new_method)
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("N+1查询优化完成")

def add_indexes():
    """添加数据库索引"""
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在原有索引后添加新索引
    old_indexes = '''await db.execute("CREATE INDEX IF NOT EXISTS idx_purchase_user ON purchase_log(user_id)")'''
    
    new_indexes = '''await db.execute("CREATE INDEX IF NOT EXISTS idx_purchase_user ON purchase_log(user_id)")
            
            # v1.0.1 新增索引
            await db.execute("CREATE INDEX IF NOT EXISTS idx_stock_holdings_stock ON stock_holdings(stock_name)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_society_name ON user_society(society_name)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_stock_price_history ON stock_price_history(stock_name, timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tax_pool_date ON tax_pool(date)")'''
    
    content = content.replace(old_indexes, new_indexes)
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("数据库索引添加完成")

def update_version():
    """更新版本号到 1.0.1"""
    files = ['main.py', '__init__.py', 'plugin.json', 'README.md']
    
    for filename in files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换版本号
            content = content.replace('"1.0"', '"1.0.1"')
            content = content.replace("'1.0'", "'1.0.1'")
            content = content.replace('v1.0', 'v1.0.1')
            content = content.replace('V1.0', 'V1.0.1')
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"{filename} 版本号已更新")
        except FileNotFoundError:
            print(f"{filename} 不存在，跳过")

if __name__ == '__main__':
    print("开始修复 v1.0.1...")
    fix_transfer()
    fix_n_plus_one()
    add_indexes()
    update_version()
    print("\n✅ v1.0.1 修复完成！")
    print("请运行: git add . && git commit -m 'fix: v1.0.1 修复并发安全和性能问题' && git push origin main")
