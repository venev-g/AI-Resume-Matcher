import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    MongoDB Atlas connection manager using Motor (async MongoDB driver)
    Implements singleton pattern for efficient connection management
    """

    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    _connection_string: Optional[str] = None

    @classmethod
    async def connect(cls) -> None:
        """
        Establish connection to MongoDB Atlas
        """
        try:
            # Build connection string for MongoDB Atlas
            cls._connection_string = cls._build_connection_string()

            logger.info("Connecting to MongoDB Atlas...")

            # Create Motor client with connection options
            cls._client = AsyncIOMotorClient(
                cls._connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,  # 10 second connection timeout
                socketTimeoutMS=20000,  # 20 second socket timeout
                maxPoolSize=10,  # Maximum connection pool size
                minPoolSize=1,  # Minimum connection pool size
                maxIdleTimeMS=30000,  # Maximum idle time for connections
                retryWrites=True,  # Enable retryable writes
                retryReads=True,  # Enable retryable reads
                w="majority",  # Write concern: majority
                readpreference="primary",  # Read from primary
                readconcernlevel="majority",  # Read concern: majority
            )

            # Get database reference
            cls._database = cls._client[settings.DATABASE_NAME]

            # Test the connection
            await cls._test_connection()

            logger.info(
                f"Successfully connected to MongoDB Atlas database: {settings.DATABASE_NAME}"
            )

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {str(e)}")
            raise ConnectionFailure(f"Database connection failed: {str(e)}")

    @classmethod
    async def disconnect(cls) -> None:
        """
        Close MongoDB Atlas connection
        """
        try:
            if cls._client:
                logger.info("Closing MongoDB Atlas connection...")
                cls._client.close()
                cls._client = None
                cls._database = None
                logger.info("MongoDB Atlas connection closed successfully")
            else:
                logger.warning("No active MongoDB connection to close")

        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
            raise

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance

        Returns:
            AsyncIOMotorDatabase: Database instance

        Raises:
            ConnectionError: If database is not connected
        """
        if cls._database is None:
            raise ConnectionError(
                "Database not connected. Call DatabaseManager.connect() first."
            )
        return cls._database

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """
        Get MongoDB client instance

        Returns:
            AsyncIOMotorClient: Client instance

        Raises:
            ConnectionError: If client is not connected
        """
        if cls._client is None:
            raise ConnectionError(
                "Database client not connected. Call DatabaseManager.connect() first."
            )
        return cls._client

    @classmethod
    def is_connected(cls) -> bool:
        """
        Check if database is connected

        Returns:
            bool: True if connected, False otherwise
        """
        return cls._client is not None and cls._database is not None

    @classmethod
    async def _test_connection(cls) -> None:
        """
        Test the database connection

        Raises:
            ConnectionFailure: If connection test fails
        """
        try:
            # Ping the database to test connection
            await cls._database.command("ping")

            # Get server info to verify connection
            server_info = await cls._client.server_info()
            logger.info(
                f"Connected to MongoDB server version: {server_info.get('version', 'Unknown')}"
            )

        except ServerSelectionTimeoutError:
            raise ConnectionFailure(
                "MongoDB server selection timeout - check connection string and network"
            )
        except Exception as e:
            raise ConnectionFailure(f"Database connection test failed: {str(e)}")

    @classmethod
    def _build_connection_string(cls) -> str:
        """
        Build MongoDB Atlas connection string from configuration

        Returns:
            str: MongoDB connection string

        Raises:
            ValueError: If required configuration is missing
        """
        # Check if full connection string is provided
        if settings.MONGODB_URL and settings.MONGODB_URL.startswith("mongodb"):
            return settings.MONGODB_URL

        # Build connection string from components
        username = os.getenv("MONGODB_USERNAME")
        password = os.getenv("MONGODB_PASSWORD")
        cluster_url = os.getenv("MONGODB_CLUSTER_URL")

        if not all([username, password, cluster_url]):
            # Fallback to simple connection string
            if settings.MONGODB_URL:
                return settings.MONGODB_URL
            else:
                raise ValueError(
                    "MongoDB Atlas configuration incomplete. Please provide either:\n"
                    "1. MONGODB_URL (full connection string), or\n"
                    "2. MONGODB_USERNAME, MONGODB_PASSWORD, and MONGODB_CLUSTER_URL"
                )

        # Build Atlas connection string
        connection_string = (
            f"mongodb+srv://{username}:{password}@{cluster_url}/"
            f"{settings.DATABASE_NAME}?retryWrites=true&w=majority"
        )

        return connection_string

    @classmethod
    async def create_indexes(cls) -> None:
        """
        Create database indexes for better performance
        """
        try:
            if not cls.is_connected():
                await cls.connect()

            db = cls.get_database()

            logger.info("Creating database indexes...")

            # Documents collection indexes
            documents_collection = db.documents
            await documents_collection.create_index("document_type")
            await documents_collection.create_index("filename")
            await documents_collection.create_index("parsed_at")
            await documents_collection.create_index(
                [("document_type", 1), ("parsed_at", -1)]
            )

            # Matches collection indexes
            matches_collection = db.matches
            await matches_collection.create_index(
                [("jd_id", 1), ("resume_id", 1)], unique=True
            )
            await matches_collection.create_index("match_percentage")
            await matches_collection.create_index("processed_at")
            await matches_collection.create_index(
                [("jd_id", 1), ("match_percentage", -1)]
            )

            # Text search indexes (optional)
            await documents_collection.create_index(
                [("raw_content", "text"), ("filename", "text")]
            )

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating database indexes: {str(e)}")
            # Don't raise exception as indexes are not critical for basic functionality

    @classmethod
    async def health_check(cls) -> dict:
        """
        Perform database health check

        Returns:
            dict: Health check results
        """
        try:
            if not cls.is_connected():
                return {
                    "status": "disconnected",
                    "message": "Database not connected",
                    "details": None,
                }

            # Test basic operations
            db = cls.get_database()

            # Ping test
            import time

            start_time = time.time()
            await db.command("ping")
            ping_time = (time.time() - start_time) * 1000

            # Get server stats (simplified to avoid serialization issues)
            try:
                server_status = await db.command("serverStatus")
                server_version = str(server_status.get("version", "unknown"))
            except Exception:
                server_version = "unknown"

            # Get database stats (simplified to avoid serialization issues)
            try:
                db_stats = await db.command("dbStats")
                collections_count = db_stats.get("collections")
                data_size = db_stats.get("dataSize")
                storage_size = db_stats.get("storageSize")

                # Safely convert to proper types
                collections_count = (
                    int(collections_count)
                    if collections_count is not None
                    and str(collections_count).isdigit()
                    else 0
                )
                data_size_mb = (
                    round(float(data_size) / (1024 * 1024), 2)
                    if data_size is not None
                    else 0.0
                )
                storage_size_mb = (
                    round(float(storage_size) / (1024 * 1024), 2)
                    if storage_size is not None
                    else 0.0
                )
            except Exception as e:
                logger.warning(f"Failed to get database stats: {e}")
                collections_count = 0
                data_size_mb = 0.0
                storage_size_mb = 0.0

            # Get connection pool size safely
            try:
                pool_size = (
                    int(cls._client.max_pool_size)
                    if cls._client and hasattr(cls._client, "max_pool_size")
                    else 10
                )
            except Exception:
                pool_size = 10

            return {
                "status": "healthy",
                "message": "Database connection is healthy",
                "details": {
                    "ping_time_ms": round(float(ping_time), 2),
                    "server_version": server_version,
                    "database_name": str(settings.DATABASE_NAME),
                    "collections_count": collections_count,
                    "data_size_mb": data_size_mb,
                    "storage_size_mb": storage_size_mb,
                    "connection_pool_size": pool_size,
                },
            }

        except Exception as e:
            logger.error(f"Health check error: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "message": f"Database health check failed: {str(e)}",
                "details": None,
            }


# Global database manager instance
database_manager = DatabaseManager()


# Dependency function for FastAPI
async def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency function to get database instance

    Returns:
        AsyncIOMotorDatabase: Database instance
    """
    return database_manager.get_database()


# Context manager for database operations
@asynccontextmanager
async def database_transaction():
    """
    Context manager for database transactions (if needed in the future)
    Note: MongoDB transactions require replica sets or sharded clusters
    """
    client = database_manager.get_client()
    async with await client.start_session() as session:
        try:
            async with session.start_transaction():
                yield session
        except Exception:
            await session.abort_transaction()
            raise


# Startup and shutdown event handlers for FastAPI
async def startup_database_event():
    """
    Database startup event handler for FastAPI
    """
    try:
        await database_manager.connect()
        await database_manager.create_indexes()
        logger.info("Database startup completed successfully")
    except Exception as e:
        logger.error(f"Database startup failed: {str(e)}")
        raise


async def shutdown_database_event():
    """
    Database shutdown event handler for FastAPI
    """
    try:
        await database_manager.disconnect()
        logger.info("Database shutdown completed successfully")
    except Exception as e:
        logger.error(f"Database shutdown failed: {str(e)}")


# Utility functions for common database operations
async def ensure_database_connection():
    """
    Ensure database connection is established
    """
    if not database_manager.is_connected():
        await database_manager.connect()


async def get_collection(collection_name: str):
    """
    Get a specific collection from the database

    Args:
        collection_name (str): Name of the collection

    Returns:
        AsyncIOMotorCollection: Collection instance
    """
    await ensure_database_connection()
    db = database_manager.get_database()
    return db[collection_name]


# Collection getters for easy access
async def get_documents_collection():
    """Get documents collection"""
    return await get_collection("documents")


async def get_matches_collection():
    """Get matches collection"""
    return await get_collection("matches")


async def get_users_collection():
    """Get users collection (for future use)"""
    return await get_collection("users")


# Database migration utilities (for future use)
async def run_migrations():
    """
    Run database migrations
    """
    try:
        await ensure_database_connection()
        logger.info("Running database migrations...")

        # Add migration logic here
        # Example: Update document schemas, create new collections, etc.

        logger.info("Database migrations completed successfully")

    except Exception as e:
        logger.error(f"Database migration failed: {str(e)}")
        raise


# Backup utilities (for future use)
async def create_backup():
    """
    Create database backup (placeholder for future implementation)
    """
    logger.info("Database backup functionality not implemented yet")
    pass


# Database cleanup utilities
async def cleanup_old_data(days: int = 30):
    """
    Clean up old data from database

    Args:
        days (int): Number of days to retain data
    """
    try:
        from datetime import datetime, timedelta

        await ensure_database_connection()
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Clean up old match results
        matches_collection = await get_matches_collection()
        result = await matches_collection.delete_many(
            {"processed_at": {"$lt": cutoff_date}}
        )

        logger.info(f"Cleaned up {result.deleted_count} old match results")

    except Exception as e:
        logger.error(f"Data cleanup failed: {str(e)}")
        raise
