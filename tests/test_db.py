import sys
import asyncio
from pathlib import Path
from app.core.database import database_manager

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_connection():
    try:
        await database_manager.connect()
        health = await database_manager.health_check()
        print(f"Database connection: {health['status']}")
        await database_manager.disconnect()
    except Exception as e:
        print(f"Database connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
