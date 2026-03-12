"""配置管理模块 - 使用数据库存储动态配置"""
import aiosqlite
import json
from typing import Any, Optional


class ConfigManager:
    """配置管理器 - 替代修改源码的方式"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def _ensure_table(self):
        """确保配置表存在"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS plugin_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    async def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        await self._ensure_table()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT value FROM plugin_config WHERE key = ?",
                (key,)
            )
            row = await cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return row[0]
            return default

    async def set(self, key: str, value: Any):
        """设置配置值"""
        await self._ensure_table()
        value_str = json.dumps(value) if not isinstance(value, str) else value
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO plugin_config (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at""",
                (key, value_str)
            )
            await db.commit()

    async def get_season(self) -> int:
        """获取当前赛季"""
        return await self.get("current_season", 1)

    async def set_season(self, season: int):
        """设置当前赛季"""
        await self.set("current_season", season)

    async def get_admin_users(self) -> list:
        """获取管理员列表"""
        return await self.get("admin_users", ["583804899"])

    async def set_admin_users(self, users: list):
        """设置管理员列表"""
        await self.set("admin_users", users)

    async def add_admin_user(self, user_id: str):
        """添加管理员"""
        users = await self.get_admin_users()
        if user_id not in users:
            users.append(user_id)
            await self.set_admin_users(users)

    async def remove_admin_user(self, user_id: str):
        """移除管理员"""
        users = await self.get_admin_users()
        if user_id in users:
            users.remove(user_id)
            await self.set_admin_users(users)
