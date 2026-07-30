import asyncio
import sys
import os

# Ensure backend package path is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_path)

from config import get_settings
from db import DatabaseManager

async def test_db_connection():
    settings = get_settings()
    print(f"[TEST] Environment: {settings.ENVIRONMENT}")
    print(f"[TEST] DATABASE_URL: {settings.DATABASE_URL}")

    db_manager = DatabaseManager.get_instance()
    is_healthy = await db_manager.check_health()
    print(f"[TEST] Neon DB Health Check Result: {is_healthy}")
    
    await db_manager.close()
    assert is_healthy is True, "Database health check failed"
    print("[SUCCESS] Neon PostgreSQL connection verified successfully!")

if __name__ == "__main__":
    asyncio.run(test_db_connection())
